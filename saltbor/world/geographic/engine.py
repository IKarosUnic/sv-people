"""
Real Geographic Engine for El Salvador (Phase 0.8).

Master coordinator for territorial hierarchy, spatial indexing, real establishments,
and navigation routing across El Salvador:
- 14 Departments across 4 Zones
- 44 Consolidate Municipalities (2024 reform)
- 262 Administrative Districts with accurate WGS84 coordinates & elevations
- Directory of verified establishments with strict validation states
- Graph-based road navigation engine with obstacle & bridge awareness
- Seamless climate integration with altitude temperature lapse rates.
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from saltbor.datasets.salvadoran.territory_data import (
    SALVADORAN_DEPARTMENTS_P8,
    SALVADORAN_DISTRICTS_P8,
    SALVADORAN_MUNICIPALITIES_P8,
    SALVADORAN_PHYSICAL_FEATURES_P8,
    PhysicalFeatureData,
    SalvadoranDepartmentProfile,
    SalvadoranDistrictData,
    SalvadoranMunicipalityData,
)
from saltbor.world.geographic.connectors import (
    CNRConnector,
    GoogleMapsConnector,
    OSMConnector,
)
from saltbor.world.geographic.establishments import EstablishmentDirectory
from saltbor.world.geographic.models import (
    GeoPoint,
    RealPlace,
    SpatialQueryResult,
    ValidationState,
)
from saltbor.world.geographic.navigation import TerritorialNavigationEngine
from saltbor.world.geographic.spatial_index import (
    SpatialGridIndex,
    haversine_distance_km,
    is_valid_salvadoran_coordinate,
)
from saltbor.world.geographic.updater import IncrementalGeoUpdater
from saltbor.world.salvadoran.climate import (
    SalvadoranClimateEngine,
    SalvadoranEnvironmentSnapshot,
)

logger = logging.getLogger(__name__)


class RealGeographicEngine:
    """Master territorial and spatial intelligence engine for El Salvador."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        # Datasets
        self._departments: dict[str, SalvadoranDepartmentProfile] = dict(SALVADORAN_DEPARTMENTS_P8)
        self._municipalities: dict[str, SalvadoranMunicipalityData] = dict(SALVADORAN_MUNICIPALITIES_P8)
        self._districts: dict[str, SalvadoranDistrictData] = dict(SALVADORAN_DISTRICTS_P8)
        self._physical_features: dict[str, PhysicalFeatureData] = dict(SALVADORAN_PHYSICAL_FEATURES_P8)

        # Spatial index for the 262 administrative districts
        self._district_index: SpatialGridIndex[SalvadoranDistrictData] = SpatialGridIndex(cell_size_degrees=0.03)
        for dist in self._districts.values():
            self._district_index.insert(dist.district_id, dist.latitude, dist.longitude, dist)

        # Spatial index for physical geography (volcanoes, lakes, rivers)
        self._feature_index: SpatialGridIndex[PhysicalFeatureData] = SpatialGridIndex(cell_size_degrees=0.05)
        for feat in self._physical_features.values():
            self._feature_index.insert(feat.feature_id, feat.latitude, feat.longitude, feat)

        # Subsystems
        self.establishments = EstablishmentDirectory(load_defaults=True)
        self.updater = IncrementalGeoUpdater(self.establishments)
        self.navigation = TerritorialNavigationEngine(load_defaults=True)
        self.climate = SalvadoranClimateEngine(seed=seed)

        # Connectors
        self.cnr = CNRConnector()
        self.gmaps = GoogleMapsConnector()
        self.osm = OSMConnector()

        # Fictional/experimental isolation registry
        self._experimental_entities: dict[str, dict[str, Any]] = {}

    # -------------------------------------------------------------------------
    # Territorial Hierarchy Lookups
    # -------------------------------------------------------------------------

    def get_department(self, code: str) -> Optional[SalvadoranDepartmentProfile]:
        """Lookup department by code ('SS', 'SA', 'SM', etc.)."""
        return self._departments.get(code.upper())

    def get_all_departments(self) -> list[SalvadoranDepartmentProfile]:
        return list(self._departments.values())

    def get_municipality(self, municipality_id: str) -> Optional[SalvadoranMunicipalityData]:
        return self._municipalities.get(municipality_id.lower())

    def get_all_municipalities(self) -> list[SalvadoranMunicipalityData]:
        return list(self._municipalities.values())

    def get_municipalities_in_department(self, department_code: str) -> list[SalvadoranMunicipalityData]:
        code = department_code.upper()
        return [m for m in self._municipalities.values() if m.department_code == code]

    def get_district(self, district_id: str) -> Optional[SalvadoranDistrictData]:
        return self._districts.get(district_id.lower())

    def get_all_districts(self) -> list[SalvadoranDistrictData]:
        return list(self._districts.values())

    def get_districts_in_municipality(self, municipality_id: str) -> list[SalvadoranDistrictData]:
        muni = self.get_municipality(municipality_id)
        if not muni:
            return []
        return [self._districts[did] for did in muni.district_ids if did in self._districts]

    def get_districts_in_department(self, department_code: str) -> list[SalvadoranDistrictData]:
        code = department_code.upper()
        return [d for d in self._districts.values() if d.department_code == code]

    # -------------------------------------------------------------------------
    # Reverse Geocoding & Spatial Association
    # -------------------------------------------------------------------------

    def find_nearest_district(self, lat: float, lon: float) -> tuple[SalvadoranDistrictData, float]:
        """Find the closest administrative district to a given WGS84 coordinate."""
        nearest = self._district_index.find_nearest(lat, lon, k=1)
        if not nearest:
            # Fallback
            dist = self._districts["dist_san_salvador"]
            return dist, haversine_distance_km(lat, lon, dist.latitude, dist.longitude)
        return nearest[0]

    def get_territorial_context(self, lat: float, lon: float) -> dict[str, Any]:
        """Resolve full political-administrative hierarchy for any coordinate in El Salvador."""
        is_valid = is_valid_salvadoran_coordinate(lat, lon)
        dist, dist_km = self.find_nearest_district(lat, lon)
        muni = self.get_municipality(dist.municipality_id)
        dept = self.get_department(dist.department_code)

        return {
            "is_valid_territory": is_valid,
            "latitude": lat,
            "longitude": lon,
            "nearest_district": {
                "district_id": dist.district_id,
                "name": dist.name,
                "distance_km": round(dist_km, 2),
                "elevation_m": dist.elevation_m,
                "is_urban_core": dist.is_urban_core,
            },
            "municipality": {
                "municipality_id": muni.municipality_id if muni else None,
                "name": muni.name if muni else None,
                "cabecera": muni.cabecera_municipal if muni else None,
            },
            "department": {
                "code": dept.code if dept else None,
                "name": dept.name if dept else None,
                "zone": dept.zone if dept else None,
            },
        }

    # -------------------------------------------------------------------------
    # Physical Geography Lookups
    # -------------------------------------------------------------------------

    def get_physical_features_near(
        self,
        lat: float,
        lon: float,
        radius_km: float = 20.0,
    ) -> list[tuple[PhysicalFeatureData, float]]:
        """Identify volcanoes, lakes, rivers, or bays within radius_km."""
        return self._feature_index.find_within_radius(lat, lon, radius_km)

    def get_volcanoes(self) -> list[PhysicalFeatureData]:
        return [f for f in self._physical_features.values() if f.feature_type == "volcano"]

    def get_lakes(self) -> list[PhysicalFeatureData]:
        return [f for f in self._physical_features.values() if f.feature_type == "lake"]

    def get_rivers(self) -> list[PhysicalFeatureData]:
        return [f for f in self._physical_features.values() if f.feature_type == "river"]

    # -------------------------------------------------------------------------
    # Navigation & Routing
    # -------------------------------------------------------------------------

    def calculate_route(
        self,
        origin_district_id: str,
        destination_district_id: str,
        transport_mode: str = "walking",
        is_rainy_season: bool = False,
        is_temporal: bool = False,
        extra_blocked_segments: Optional[set[str]] = None,
    ) -> dict[str, Any]:
        """Compute route between districts taking into account road surface, bridges, and weather."""
        return self.navigation.find_route(
            origin_district_id=origin_district_id,
            destination_district_id=destination_district_id,
            transport_mode=transport_mode,
            is_rainy_season=is_rainy_season,
            is_temporal=is_temporal,
            extra_blocked_segments=extra_blocked_segments,
        )

    # -------------------------------------------------------------------------
    # Climate & Environmental Intelligence by District
    # -------------------------------------------------------------------------

    def evaluate_district_climate(
        self,
        district_id: str,
        month: int,
        day_of_month: int = 15,
        consecutive_rainy_days: int = 0,
    ) -> SalvadoranEnvironmentSnapshot:
        """Evaluate local meteorological snapshot for a district considering its elevation and zone."""
        dist = self.get_district(district_id)
        elevation = dist.elevation_m if dist else 600.0
        is_coastal_or_eastern = dist.department_code in ("US", "SM", "MO", "LU", "LP", "SO") if dist else False

        return self.climate.evaluate_environment(
            month=month,
            day_of_month=day_of_month,
            elevation_m=elevation,
            is_coastal_or_eastern=is_coastal_or_eastern,
            consecutive_rainy_days=consecutive_rainy_days,
        )

    # -------------------------------------------------------------------------
    # Experimental Isolation Guard
    # -------------------------------------------------------------------------

    def is_real_world_entity(self, entity_id: str) -> bool:
        """Verify whether an entity originates from verified Salvadoran datasets."""
        if entity_id in self._departments:
            return True
        if entity_id in self._municipalities:
            return True
        if entity_id in self._districts:
            return True
        if entity_id in self._physical_features:
            return True
        if self.establishments.get_by_id(entity_id) is not None:
            return True
        return False

    def register_experimental_entity(self, entity_id: str, name: str, dept_code: str) -> None:
        """Register a fictional/experimental node without polluting real datasets."""
        self._experimental_entities[entity_id] = {
            "entity_id": entity_id,
            "name": name,
            "department_code": dept_code,
            "is_real_world": False,
        }
