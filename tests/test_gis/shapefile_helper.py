"""Shared test helper to generate minimal ESRI Shapefile / DBF bundles."""

from __future__ import annotations

import struct
from pathlib import Path


def write_shapefile(
    base: Path,
    shape_type: int,
    geometries: list[list[tuple[float, float]]],
    records: list[dict],
) -> None:
    """Write a minimal ``.shp``/``.dbf`` pair for the reader to consume."""
    records_payload = b""
    record_number = 1
    for coords in geometries:
        if shape_type == 1:  # Point
            ((x, y),) = coords
            content = struct.pack("<i2d", shape_type, x, y)
        elif shape_type == 3:  # PolyLine
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            content = struct.pack("<i4d2i", shape_type, min(xs), min(ys), max(xs), max(ys), 1, len(coords))
            content += struct.pack("<i", 0)
            for x, y in coords:
                content += struct.pack("<2d", x, y)
        elif shape_type == 5:  # Polygon
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            ring = list(coords)
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            content = struct.pack("<i4d2i", shape_type, min(xs), min(ys), max(xs), max(ys), 1, len(ring))
            content += struct.pack("<i", 0)
            for x, y in ring:
                content += struct.pack("<2d", x, y)
        else:  # pragma: no cover - guard
            raise ValueError(shape_type)
        records_payload += struct.pack(">2i", record_number, len(content) // 2) + content
        record_number += 1

    xs = [c[0] for g in geometries for c in g]
    ys = [c[1] for g in geometries for c in g]
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else (0.0, 0.0, 0.0, 0.0)
    header = struct.pack(">i", 9994) + b"\x00" * 20 + struct.pack(">i", (100 + len(records_payload)) // 2)
    header += struct.pack("<ii", 1000, shape_type) + struct.pack("<4d", *bbox) + struct.pack("<4d", 0.0, 0.0, 0.0, 0.0)
    base.with_suffix(".shp").write_bytes(header + records_payload)
    base.with_suffix(".prj").write_text(
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
        encoding="utf-8",
    )
    base.with_suffix(".cpg").write_text("UTF-8", encoding="utf-8")

    # DBF
    fields = list(records[0].keys())
    field_specs = []
    for name in fields:
        sample = records[0][name]
        if isinstance(sample, (int, float)):
            field_specs.append((name, "N", 12, 3 if isinstance(sample, float) else 0))
        else:
            field_specs.append((name, "C", 40, 0))

    header_len = 32 + 32 * len(field_specs) + 1
    record_len = 1 + sum(spec[2] for spec in field_specs)
    dbf = bytearray()
    dbf += struct.pack("<4B", 0x03, 126, 1, 1)
    dbf += struct.pack("<i", len(records)) + struct.pack("<hh", header_len, record_len)
    dbf += b"\x00" * 20
    for name, ftype, length, decimals in field_specs:
        dbf += name.encode("ascii")[:11].ljust(11, b"\x00")
        dbf += ftype.encode("ascii") + b"\x00" * 4 + bytes([length, decimals]) + b"\x00" * 14
    dbf += b"\x0d"
    for record in records:
        dbf += b" "
        for name, ftype, length, decimals in field_specs:
            value = record[name]
            if ftype == "N":
                text = f"{value:.{decimals}f}" if decimals else str(int(value))
            else:
                text = str(value)
            dbf += text.encode("utf-8")[:length].ljust(length)
    dbf += b"\x1a"
    base.with_suffix(".dbf").write_bytes(bytes(dbf))
