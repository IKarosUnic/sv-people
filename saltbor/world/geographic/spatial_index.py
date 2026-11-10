"""
Spatial Index and Coordinate Calculations for Saltbor (Phase 0.8).

Pure Python and NumPy 2D spatial indexing optimized for sub-millisecond
spatial queries without external binary C-extensions or GDAL dependencies:
- WGS84 Great-Circle Haversine distance (kilometers and meters)
- SIRGAS ES2007 / UTM Zone 16N local metric projection approximations
- Grid-partitioned Spatial Index (SpatialGridIndex)
- Sub-millisecond radius searches, nearest-neighbor lookups, and bounding box queries
- Strict bounding box validation for El Salvador territory.
"""

from __future__ import annotations
import math
from typing import Any, Callable, Generic, Optional, TypeVar

from saltbor.world.geographic.models import GeoBoundingBox, GeoPoint

T = TypeVar("T")

# Official geographic limits of the Republic of El Salvador (WGS84)
EL_SALVADOR_BBOX = GeoBoundingBox(
    min_lat=13.12,   # Golfo de Fonseca / Punta Amapala
    min_lon=-90.15,  # Desembocadura Río Paz / Garita Palmera
    max_lat=14.45,   # Trifinio Montecristo / El Pital
    max_lon=-87.68,  # Isla Meanguera del Golfo / Río Goascorán
)

# Reference origin for SIRGAS ES2007 (CNR Official Projection)
SIRGAS_ORIGIN_LAT = 13.78429934
SIRGAS_ORIGIN_LON = -88.99998297
EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two WGS84 points in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clip to [0, 1] to guard against rare floating-point precision error
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in meters."""
    return haversine_distance_km(lat1, lon1, lat2, lon2) * 1000.0


def is_valid_salvadoran_coordinate(lat: float, lon: float) -> bool:
    """Validate whether coordinates fall within El Salvador's sovereign geographic envelope."""
    return EL_SALVADOR_BBOX.contains(lat, lon)


def wgs84_to_local_metric_xy(
    lat: float,
    lon: float,
    origin_lat: float = SIRGAS_ORIGIN_LAT,
    origin_lon: float = SIRGAS_ORIGIN_LON,
) -> tuple[float, float]:
    """Convert WGS84 (lat, lon) to local planar metric coordinates (x, y in meters).

    Uses equirectangular projection centered on El Salvador's geographic midpoint,
    providing < 0.1% distortion across the entire country.
    """
    d_lat = math.radians(lat - origin_lat)
    d_lon = math.radians(lon - origin_lon)
    mean_lat = math.radians((lat + origin_lat) / 2.0)

    y = d_lat * (EARTH_RADIUS_KM * 1000.0)
    x = d_lon * (EARTH_RADIUS_KM * 1000.0) * math.cos(mean_lat)
    return (x, y)


def local_metric_xy_to_wgs84(
    x: float,
    y: float,
    origin_lat: float = SIRGAS_ORIGIN_LAT,
    origin_lon: float = SIRGAS_ORIGIN_LON,
) -> tuple[float, float]:
    """Invert local planar metric coordinates (x, y) back to WGS84 (lat, lon)."""
    d_lat_rad = y / (EARTH_RADIUS_KM * 1000.0)
    lat = origin_lat + math.degrees(d_lat_rad)
    mean_lat = math.radians((lat + origin_lat) / 2.0)
    d_lon_rad = x / ((EARTH_RADIUS_KM * 1000.0) * math.cos(mean_lat))
    lon = origin_lon + math.degrees(d_lon_rad)
    return (lat, lon)


class SpatialGridIndex(Generic[T]):
    """High-performance 2D spatial grid index for geographic points.

    Partitions the geographic domain into uniform bins for $O(1)$ amortized insertion
    and rapid bounding box / radial retrieval.
    """

    def __init__(self, cell_size_degrees: float = 0.02) -> None:
        """Initialize index with grid cell resolution (default ~2.2 km)."""
        self.cell_size = cell_size_degrees
        self._grid: dict[tuple[int, int], list[tuple[float, float, str, T]]] = {}
        self._items: dict[str, tuple[float, float, T]] = {}

    def _coord_to_key(self, lat: float, lon: float) -> tuple[int, int]:
        return (math.floor(lat / self.cell_size), math.floor(lon / self.cell_size))

    def insert(self, item_id: str, lat: float, lon: float, data: T) -> None:
        """Insert or update a spatial item."""
        if item_id in self._items:
            self.remove(item_id)

        key = self._coord_to_key(lat, lon)
        if key not in self._grid:
            self._grid[key] = []
        self._grid[key].append((lat, lon, item_id, data))
        self._items[item_id] = (lat, lon, data)

    def remove(self, item_id: str) -> bool:
        """Remove an item from the index."""
        if item_id not in self._items:
            return False
        lat, lon, _ = self._items.pop(item_id)
        key = self._coord_to_key(lat, lon)
        cell = self._grid.get(key, [])
        self._grid[key] = [entry for entry in cell if entry[2] != item_id]
        if not self._grid[key]:
            del self._grid[key]
        return True

    def get_item(self, item_id: str) -> Optional[tuple[float, float, T]]:
        return self._items.get(item_id)

    def __len__(self) -> int:
        return len(self._items)

    def find_within_radius(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        predicate: Optional[Callable[[T], bool]] = None,
    ) -> list[tuple[T, float]]:
        """Find all items within radius_km, returning (item, distance_km) sorted by distance."""
        # Degree buffer approximation: 1 deg lat ~ 111 km, 1 deg lon at 13.8N ~ 108 km
        lat_buffer = (radius_km / 111.0) * 1.05
        cos_lat = max(0.2, math.cos(math.radians(center_lat)))
        lon_buffer = (radius_km / (111.0 * cos_lat)) * 1.05

        min_key_lat = math.floor((center_lat - lat_buffer) / self.cell_size)
        max_key_lat = math.floor((center_lat + lat_buffer) / self.cell_size)
        min_key_lon = math.floor((center_lon - lon_buffer) / self.cell_size)
        max_key_lon = math.floor((center_lon + lon_buffer) / self.cell_size)

        results: list[tuple[T, float]] = []

        for k_lat in range(min_key_lat, max_key_lat + 1):
            for k_lon in range(min_key_lon, max_key_lon + 1):
                cell = self._grid.get((k_lat, k_lon))
                if not cell:
                    continue
                for item_lat, item_lon, _, data in cell:
                    if predicate is not None and not predicate(data):
                        continue
                    d_km = haversine_distance_km(center_lat, center_lon, item_lat, item_lon)
                    if d_km <= radius_km:
                        results.append((data, d_km))

        results.sort(key=lambda x: x[1])
        return results

    def find_nearest(
        self,
        center_lat: float,
        center_lon: float,
        k: int = 1,
        max_radius_km: float = 100.0,
        predicate: Optional[Callable[[T], bool]] = None,
    ) -> list[tuple[T, float]]:
        """Find the k nearest items to a coordinate."""
        # Progressive expansion strategy
        search_radius = 2.0
        while search_radius <= max_radius_km:
            found = self.find_within_radius(center_lat, center_lon, search_radius, predicate)
            if len(found) >= k or search_radius >= max_radius_km:
                return found[:k]
            search_radius = min(max_radius_km, search_radius * 2.5)

        return self.find_within_radius(center_lat, center_lon, max_radius_km, predicate)[:k]

    def query_bbox(
        self,
        bbox: GeoBoundingBox,
        predicate: Optional[Callable[[T], bool]] = None,
    ) -> list[T]:
        """Retrieve all items strictly inside the given geographic bounding box."""
        min_key_lat = math.floor(bbox.min_lat / self.cell_size)
        max_key_lat = math.floor(bbox.max_lat / self.cell_size)
        min_key_lon = math.floor(bbox.min_lon / self.cell_size)
        max_key_lon = math.floor(bbox.max_lon / self.cell_size)

        matches: list[T] = []
        for k_lat in range(min_key_lat, max_key_lat + 1):
            for k_lon in range(min_key_lon, max_key_lon + 1):
                cell = self._grid.get((k_lat, k_lon))
                if not cell:
                    continue
                for item_lat, item_lon, _, data in cell:
                    if bbox.contains(item_lat, item_lon):
                        if predicate is None or predicate(data):
                            matches.append(data)
        return matches
