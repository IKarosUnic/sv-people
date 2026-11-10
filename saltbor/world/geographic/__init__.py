"""Geographic and territorial system package for Saltbor (Phase 0.8)."""

from saltbor.world.geographic.models import (
    TerritorialLevel,
    ValidationState,
    EstablishmentCategory,
    GeoPoint,
    GeoBoundingBox,
    GeographicEntity,
    RealPlace,
    SpatialQueryResult,
)
from saltbor.world.geographic.spatial_index import (
    EL_SALVADOR_BBOX,
    SpatialGridIndex,
    haversine_distance_km,
    haversine_distance_m,
    is_valid_salvadoran_coordinate,
    wgs84_to_local_metric_xy,
    local_metric_xy_to_wgs84,
)
from saltbor.world.geographic.establishments import EstablishmentDirectory
from saltbor.world.geographic.navigation import TerritorialNavigationEngine
from saltbor.world.geographic.updater import IncrementalGeoUpdater, DatasetDiff, DatasetVersionSnapshot
from saltbor.world.geographic.engine import RealGeographicEngine

__all__ = [
    "TerritorialLevel",
    "ValidationState",
    "EstablishmentCategory",
    "GeoPoint",
    "GeoBoundingBox",
    "GeographicEntity",
    "RealPlace",
    "SpatialQueryResult",
    "EL_SALVADOR_BBOX",
    "SpatialGridIndex",
    "haversine_distance_km",
    "haversine_distance_m",
    "is_valid_salvadoran_coordinate",
    "wgs84_to_local_metric_xy",
    "local_metric_xy_to_wgs84",
    "EstablishmentDirectory",
    "TerritorialNavigationEngine",
    "IncrementalGeoUpdater",
    "DatasetDiff",
    "DatasetVersionSnapshot",
    "RealGeographicEngine",
]
