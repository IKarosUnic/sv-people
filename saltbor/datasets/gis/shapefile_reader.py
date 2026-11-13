"""Dependency-free ESRI Shapefile reader for offline OSM ingestion.

SALTBOR must ingest OpenStreetMap extracts on a machine that has no GDAL,
Fiona, GeoPandas, pyshp or network access.  Geofabrik ships the El Salvador
extract both as ``.osm.pbf`` and as an ESRI shapefile bundle; the shapefile
bundle is the most practical offline vector source because its geometry is
already split into thematic layers.

This module implements the subset of the ESRI Shapefile specification that
Geofabrik actually emits:

* ``Point`` / ``PointZ`` / ``PointM``            (places, POIs)
* ``PolyLine`` / ``PolyLineZ`` / ``PolyLineM``   (roads, waterways)
* ``Polygon`` / ``PolygonZ`` / ``PolygonM``      (buildings, landuse, water)
* ``MultiPoint`` variants are read as a list of points.

Only the ``.shp`` geometry file and the matching ``.dbf`` attribute table are
read.  ``.prj`` and ``.cpg`` are consumed as *metadata only*: the CRS and the
text encoding are recorded so downstream provenance stays honest.  No
reprojection is performed here; Geofabrik bundles are EPSG:4326 (WGS84).

The reader is a streaming iterator so that a multi-hundred-megabyte extract
can be filtered without holding the whole geometry in memory.
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shape type constants (ESRI Shapefile Technical Description, ESRI 1998)
# ---------------------------------------------------------------------------
SHAPE_NULL = 0
SHAPE_POINT = 1
SHAPE_POLYLINE = 3
SHAPE_POLYGON = 5
SHAPE_MULTIPOINT = 8
SHAPE_POINT_Z = 11
SHAPE_POLYLINE_Z = 13
SHAPE_POLYGON_Z = 15
SHAPE_MULTIPOINT_Z = 18
SHAPE_POINT_M = 21
SHAPE_POLYLINE_M = 23
SHAPE_POLYGON_M = 25
SHAPE_MULTIPOINT_M = 28

_POINT_TYPES = {SHAPE_POINT, SHAPE_POINT_Z, SHAPE_POINT_M}
_POLYLINE_TYPES = {SHAPE_POLYLINE, SHAPE_POLYLINE_Z, SHAPE_POLYLINE_M}
_POLYGON_TYPES = {SHAPE_POLYGON, SHAPE_POLYGON_Z, SHAPE_POLYGON_M}
_MULTIPOINT_TYPES = {SHAPE_MULTIPOINT, SHAPE_MULTIPOINT_Z, SHAPE_MULTIPOINT_M}

_DEFAULT_ENCODING = "utf-8"


class ShapefileError(RuntimeError):
    """Raised when a shapefile cannot be parsed."""


@dataclass
class Shape:
    """A decoded shapefile geometry with a GeoJSON ``__geo_interface__``."""

    shape_type: int
    parts: list[list[tuple[float, float]]] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    @property
    def is_point(self) -> bool:
        return self.shape_type in _POINT_TYPES

    @property
    def is_polygon(self) -> bool:
        return self.shape_type in _POLYGON_TYPES

    @property
    def is_polyline(self) -> bool:
        return self.shape_type in _POLYLINE_TYPES

    @property
    def centroid(self) -> tuple[float, float]:
        """Return the (lon, lat) centroid of the first ring / path.

        For polygons this is the area-weighted centroid of the largest ring,
        which is enough for spatial indexing and map labelling.  It is *not*
        a cartographic label point.
        """
        if not self.parts or not self.parts[0]:
            return (self.bbox[0], self.bbox[1])
        ring = max(self.parts, key=len)
        if self.is_polygon and len(ring) >= 3:
            area = 0.0
            cx = 0.0
            cy = 0.0
            for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
                cross = x0 * y1 - x1 * y0
                area += cross
                cx += (x0 + x1) * cross
                cy += (y0 + y1) * cross
            if abs(area) > 1e-16:
                return (cx / (3.0 * area), cy / (3.0 * area))
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return a GeoJSON geometry dictionary."""
        if self.shape_type == SHAPE_NULL or not self.parts:
            return {"type": "GeometryCollection", "geometries": []}
        if self.is_point:
            lon, lat = self.parts[0][0]
            return {"type": "Point", "coordinates": [lon, lat]}
        if self.shape_type in _MULTIPOINT_TYPES:
            return {
                "type": "MultiPoint",
                "coordinates": [[lon, lat] for lon, lat in self.parts[0]],
            }
        if self.is_polyline:
            if len(self.parts) == 1:
                return {
                    "type": "LineString",
                    "coordinates": [[lon, lat] for lon, lat in self.parts[0]],
                }
            return {
                "type": "MultiLineString",
                "coordinates": [
                    [[lon, lat] for lon, lat in part] for part in self.parts
                ],
            }
        # Polygon: shapefile stores exterior rings clockwise and holes
        # counter-clockwise.  GeoJSON expects the opposite winding and nests
        # holes inside their exterior ring.
        polygons: list[list[list[list[float]]]] = []
        shells: list[list[tuple[float, float]]] = []
        holes: list[list[tuple[float, float]]] = []
        for ring in self.parts:
            if len(ring) < 4:
                continue
            closed = ring if ring[0] == ring[-1] else ring + [ring[0]]
            if _signed_area(closed) <= 0:
                shells.append(closed)
            else:
                holes.append(closed)

        if not shells:
            # Degenerate / unlabelled ring order: emit every ring as a shell.
            shells, holes = [list(h) for h in holes], []

        assigned: dict[int, list[list[tuple[float, float]]]] = {i: [] for i in range(len(shells))}
        for hole in holes:
            target = _containing_shell(hole, shells)
            if target is None:
                shells.append(hole)
                assigned[len(shells) - 1] = []
            else:
                assigned[target].append(hole)

        for idx, shell in enumerate(shells):
            rings = [[[lon, lat] for lon, lat in shell]]
            for hole in assigned.get(idx, []):
                rings.append([[lon, lat] for lon, lat in hole])
            polygons.append(rings)

        if not polygons:
            return {"type": "GeometryCollection", "geometries": []}
        if len(polygons) == 1:
            return {"type": "Polygon", "coordinates": polygons[0]}
        return {"type": "MultiPolygon", "coordinates": polygons}


def _signed_area(ring: list[tuple[float, float]]) -> float:
    """Return twice the signed area (positive = counter-clockwise)."""
    area = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        area += x0 * y1 - x1 * y0
    return area / 2.0


def _ring_contains(ring: list[tuple[float, float]], px: float, py: float) -> bool:
    """Ray-casting point-in-ring test."""
    inside = False
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        if (y0 > py) != (y1 > py):
            denom = (y1 - y0) or 1e-18
            x_cross = x0 + (py - y0) * (x1 - x0) / denom
            if px < x_cross:
                inside = not inside
    return inside


def _containing_shell(
    hole: list[tuple[float, float]],
    shells: list[list[tuple[float, float]]],
) -> Optional[int]:
    px, py = hole[0]
    for idx, shell in enumerate(shells):
        xs = [p[0] for p in shell]
        ys = [p[1] for p in shell]
        if min(xs) <= px <= max(xs) and min(ys) <= py <= max(ys):
            if _ring_contains(shell, px, py):
                return idx
    return None


class ShapefileReader:
    """Streaming reader for a ``.shp`` file and its ``.dbf`` attribute table."""

    def __init__(self, path: str | Path) -> None:
        base = Path(path)
        if base.suffix.lower() == ".shp":
            base = base.with_suffix("")
        self.stem = base
        self.shp_path = base.with_suffix(".shp")
        self.dbf_path = base.with_suffix(".dbf")
        self.prj_path = base.with_suffix(".prj")
        self.cpg_path = base.with_suffix(".cpg")

        if not self.shp_path.exists():
            raise ShapefileError(f"Shapefile not found: {self.shp_path}")

        self.encoding = self._detect_encoding()
        self.fields: list[tuple[str, str, int, int]] = []
        self.record_count = 0
        self._dbf_offsets: list[tuple[int, int]] = []
        self._dbf_bytes: bytes = b""
        self.header: dict[str, Any] = {}

        self._read_shp_header()
        if self.dbf_path.exists():
            self._read_dbf_header()
            self._dbf_bytes = self.dbf_path.read_bytes()
            self._index_dbf_records()

    # -- metadata ---------------------------------------------------------
    def _detect_encoding(self) -> str:
        if self.cpg_path.exists():
            try:
                raw = self.cpg_path.read_text(encoding="ascii", errors="ignore").strip()
                if raw:
                    return raw
            except OSError:  # pragma: no cover - unreadable .cpg
                pass
        return _DEFAULT_ENCODING

    @property
    def crs(self) -> str:
        """Return the declared CRS, read from ``.prj`` when present."""
        if not self.prj_path.exists():
            return "EPSG:4326"
        try:
            wkt = self.prj_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:  # pragma: no cover
            return "EPSG:4326"
        if "WGS_1984" in wkt or "WGS 84" in wkt:
            return "EPSG:4326"
        return "unknown (see .prj)"

    def _read_shp_header(self) -> None:
        with self.shp_path.open("rb") as fh:
            header = fh.read(100)
        if len(header) < 100:
            raise ShapefileError(f"Truncated shapefile header: {self.shp_path}")
        file_code = struct.unpack(">i", header[0:4])[0]
        if file_code != 9994:
            raise ShapefileError(f"Not an ESRI shapefile (code {file_code}): {self.shp_path}")
        file_length_words = struct.unpack(">i", header[24:28])[0]
        shape_type = struct.unpack("<i", header[32:36])[0]
        bbox = struct.unpack("<4d", header[36:68])
        self.header = {
            "file_length_bytes": file_length_words * 2,
            "shape_type": shape_type,
            "bbox": bbox,
        }

    def _read_dbf_header(self) -> None:
        raw = self.dbf_path.read_bytes()
        if len(raw) < 32:
            raise ShapefileError(f"Truncated DBF header: {self.dbf_path}")
        version = raw[0]
        self.record_count = struct.unpack("<i", raw[4:8])[0]
        header_len = struct.unpack("<h", raw[8:10])[0]
        record_len = struct.unpack("<h", raw[10:12])[0]
        self.header["dbf_version"] = version
        self.header["dbf_record_length"] = record_len

        fields: list[tuple[str, str, int, int]] = []
        offset = 32
        while offset + 32 <= header_len:
            if raw[offset] == 0x0D:
                break
            name = raw[offset: offset + 11].split(b"\x00")[0].decode(
                "ascii", errors="ignore"
            ).strip()
            ftype = chr(raw[offset + 11])
            flen = raw[offset + 16]
            fdec = raw[offset + 17]
            if name:
                fields.append((name, ftype, flen, fdec))
            offset += 32
        self.fields = fields

    def _index_dbf_records(self) -> None:
        header_len = struct.unpack("<h", self._dbf_bytes[8:10])[0]
        record_len = struct.unpack("<h", self._dbf_bytes[10:12])[0]
        total = min(self.record_count, (len(self._dbf_bytes) - header_len) // record_len)
        self.record_count = max(0, total)
        self._dbf_offsets = [
            (header_len + i * record_len, record_len) for i in range(self.record_count)
        ]

    # -- record access ----------------------------------------------------
    @property
    def field_names(self) -> list[str]:
        return [f[0] for f in self.fields]

    def read_attributes(self, index: int) -> dict[str, Any]:
        """Return the decoded attribute dictionary for record ``index``."""
        if not self._dbf_offsets:
            return {}
        offset, length = self._dbf_offsets[index]
        raw = self._dbf_bytes[offset: offset + length]
        if not raw or raw[0:1] == b"*":  # deleted record
            return {}
        attrs: dict[str, Any] = {}
        cursor = 1
        for name, ftype, flen, fdec in self.fields:
            chunk = raw[cursor: cursor + flen]
            cursor += flen
            text = chunk.decode(self.encoding, errors="replace").strip()
            if ftype in ("N", "F"):
                if not text:
                    attrs[name] = None
                else:
                    try:
                        attrs[name] = float(text) if (fdec or "." in text) else int(float(text))
                    except ValueError:
                        attrs[name] = None
            else:
                attrs[name] = text
        return attrs

    def iter_records(
        self,
        limit: Optional[int] = None,
        bbox: Optional[tuple[float, float, float, float]] = None,
        predicate: Optional[Any] = None,
    ) -> Iterator[tuple[dict[str, Any], Shape]]:
        """Yield ``(attributes, geometry)`` pairs.

        ``bbox`` is ``(min_lon, min_lat, max_lon, max_lat)`` and is applied to
        the shape bounding box before geometry decoding where possible.
        ``predicate`` receives the attribute dict and returns a bool.
        """
        emitted = 0
        record_index = 0
        with self.shp_path.open("rb") as fh:
            fh.seek(100)
            while True:
                length_prefix = fh.read(8)
                if len(length_prefix) < 8:
                    break
                _record_number, content_words = struct.unpack(">2i", length_prefix)
                content_bytes = content_words * 2
                content = fh.read(content_bytes)
                if len(content) < content_bytes:
                    logger.warning(
                        "Truncated record %d in %s", record_index, self.shp_path.name
                    )
                    break

                attrs = (
                    self.read_attributes(record_index)
                    if record_index < len(self._dbf_offsets)
                    else {}
                )
                record_index += 1

                if predicate is not None and not predicate(attrs):
                    continue

                shape = _decode_shape(content, content_bytes)
                if shape is None:
                    continue
                if bbox is not None and not _bbox_intersects(shape.bbox, bbox):
                    continue

                yield attrs, shape
                emitted += 1
                if limit is not None and emitted >= limit:
                    break

    def count_matching(self, predicate: Any) -> int:
        return sum(1 for _ in self.iter_records(predicate=predicate))


def _bbox_intersects(
    shape_bbox: tuple[float, float, float, float],
    query: tuple[float, float, float, float],
) -> bool:
    s_minx, s_miny, s_maxx, s_maxy = shape_bbox
    q_minx, q_miny, q_maxx, q_maxy = query
    return not (
        s_maxx < q_minx or s_minx > q_maxx or s_maxy < q_miny or s_miny > q_maxy
    )


def _decode_shape(content: bytes, content_bytes: int) -> Optional[Shape]:
    if content_bytes < 4:
        return None
    shape_type = struct.unpack("<i", content[0:4])[0]
    if shape_type == SHAPE_NULL:
        return None

    try:
        if shape_type in _POINT_TYPES:
            x, y = struct.unpack("<2d", content[4:20])
            return Shape(shape_type, [[(x, y)]], (x, y, x, y))

        if shape_type in _MULTIPOINT_TYPES:
            minx, miny, maxx, maxy = struct.unpack("<4d", content[4:36])
            num_points = struct.unpack("<i", content[36:40])[0]
            points = []
            cursor = 40
            for _ in range(num_points):
                x, y = struct.unpack("<2d", content[cursor: cursor + 16])
                cursor += 16
                points.append((x, y))
            return Shape(shape_type, [points], (minx, miny, maxx, maxy))

        if shape_type in _POLYLINE_TYPES or shape_type in _POLYGON_TYPES:
            minx, miny, maxx, maxy = struct.unpack("<4d", content[4:36])
            num_parts, num_points = struct.unpack("<2i", content[36:44])
            part_offsets = list(
                struct.unpack(f"<{num_parts}i", content[44: 44 + 4 * num_parts])
            )
            cursor = 44 + 4 * num_parts
            coords: list[tuple[float, float]] = []
            for _ in range(num_points):
                x, y = struct.unpack("<2d", content[cursor: cursor + 16])
                cursor += 16
                coords.append((x, y))

            parts: list[list[tuple[float, float]]] = []
            for i, start in enumerate(part_offsets):
                end = part_offsets[i + 1] if i + 1 < len(part_offsets) else len(coords)
                part = coords[start:end]
                if len(part) >= 2:
                    parts.append(part)
            return Shape(shape_type, parts, (minx, miny, maxx, maxy))
    except (struct.error, IndexError) as exc:  # pragma: no cover - malformed file
        logger.warning("Malformed shape record: %s", exc)
        return None

    return None


def read_layer(
    path: str | Path,
    limit: Optional[int] = None,
    bbox: Optional[tuple[float, float, float, float]] = None,
) -> list[tuple[dict[str, Any], Shape]]:
    """Convenience helper returning a bounded list of records."""
    reader = ShapefileReader(path)
    return list(reader.iter_records(limit=limit, bbox=bbox))
