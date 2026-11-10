"""
Salvadoran Geography and Territorial System (Section 19.1).

Represents the geographical hierarchy of El Salvador:
- 14 Departments across 4 Zones
- Municipalities, Cantons, Caseríos, Barrios, Colonias
- National highway network (CA-1, CA-2, CA-4) and rural unpaved dirt roads (caminos vecinales)
- Volcanic calderas, stratovolcanoes, rivers, lakes, and coastal bays
- Separation of verified real-world data from simulation-specific experiment testbeds
"""

from __future__ import annotations
import math
from typing import Any, Optional

from saltbor.datasets.salvadoran import (
    SALVADORAN_DEPARTMENTS,
    SALVADORAN_SETTLEMENTS,
    SALVADORAN_GEOGRAPHIC_FEATURES,
    DepartmentData,
    SalvadoranSettlementNode,
    SalvadoranGeographicFeature,
    SalvadoranZone,
    SettlementClassification,
)


class SalvadoranGeographyEngine:
    """Manages the spatial, territorial, and topological organization of El Salvador."""

    def __init__(self) -> None:
        self._departments: dict[str, DepartmentData] = dict(SALVADORAN_DEPARTMENTS)
        self._settlements: dict[str, SalvadoranSettlementNode] = dict(SALVADORAN_SETTLEMENTS)
        self._features: dict[str, SalvadoranGeographicFeature] = dict(SALVADORAN_GEOGRAPHIC_FEATURES)
        # Separate registry for fictional/experimental nodes
        self._experimental_settlements: dict[str, dict[str, Any]] = {}

    # -------------------------------------------------------------------------
    # Territorial Hierarchy Lookups
    # -------------------------------------------------------------------------

    def get_department(self, code: str) -> Optional[DepartmentData]:
        """Retrieve departmental profile by code (e.g. 'SS', 'SA', 'SM', 'CH')."""
        return self._departments.get(code.upper())

    def get_all_departments(self) -> list[DepartmentData]:
        return list(self._departments.values())

    def get_departments_by_zone(self, zone: SalvadoranZone) -> list[DepartmentData]:
        return [d for d in self._departments.values() if d.zone == zone]

    def get_settlement(self, settlement_id: str) -> Optional[SalvadoranSettlementNode]:
        """Retrieve verified settlement node."""
        return self._settlements.get(settlement_id)

    def get_settlements_in_department(self, department_code: str) -> list[SalvadoranSettlementNode]:
        return [s for s in self._settlements.values() if s.department_code == department_code.upper()]

    def get_rural_settlements(self) -> list[SalvadoranSettlementNode]:
        return [s for s in self._settlements.values() if s.is_rural]

    def get_urban_settlements(self) -> list[SalvadoranSettlementNode]:
        return [s for s in self._settlements.values() if not s.is_rural]

    # -------------------------------------------------------------------------
    # Physical Features & Environmental Proximity
    # -------------------------------------------------------------------------

    def get_features_near_department(self, department_code: str) -> list[SalvadoranGeographicFeature]:
        """Find volcanoes, rivers, and lakes intersecting this department."""
        code = department_code.upper()
        return [f for f in self._features.values() if code in f.department_codes]

    def get_volcanoes(self) -> list[SalvadoranGeographicFeature]:
        return [f for f in self._features.values() if f.feature_type.value == "volcano"]

    def get_rivers(self) -> list[SalvadoranGeographicFeature]:
        return [f for f in self._features.values() if f.feature_type.value == "river"]

    # -------------------------------------------------------------------------
    # Route Calculation & Terrain Accessibility
    # -------------------------------------------------------------------------

    def calculate_transit_profile(
        self,
        origin_id: str,
        destination_id: str,
        is_rainy_season: bool = False,
    ) -> dict[str, Any]:
        """Calculate travel duration, accessibility, and road condition penalty between settlements."""
        orig = self._settlements.get(origin_id)
        dest = self._settlements.get(destination_id)

        if not orig or not dest:
            return {
                "origin": origin_id,
                "destination": destination_id,
                "is_accessible": False,
                "reason": "Unknown origin or destination settlement",
                "transit_hours": 0.0,
            }

        # Approximate departmental distance metric
        same_dept = orig.department_code == dest.department_code
        elevation_delta = abs(dest.elevation_m - orig.elevation_m)

        # Baseline distance heuristic
        if same_dept:
            dist_km = 15.0 if (orig.is_rural or dest.is_rural) else 8.0
        else:
            dist_km = 65.0

        # Road quality factor
        worst_road = "paved_highway"
        road_order = ["paved_highway", "secondary_asphalt", "cobblestone", "unpaved_dirt_road"]
        for r in [orig.access_road_type, dest.access_road_type]:
            if road_order.index(r) > road_order.index(worst_road):
                worst_road = r

        base_speed_kmh = 45.0
        if worst_road == "secondary_asphalt":
            base_speed_kmh = 35.0
        elif worst_road == "cobblestone":
            base_speed_kmh = 20.0
        elif worst_road == "unpaved_dirt_road":
            base_speed_kmh = 12.0

        # Rainy season penalty on dirt roads (mud, baches, desprendimientos)
        rain_speed_penalty = 1.0
        is_blocked = False
        block_reason = None

        if is_rainy_season:
            if worst_road == "unpaved_dirt_road":
                rain_speed_penalty = 0.40  # 60% speed reduction in mud
                # Steep dirt roads risk being completely washed out
                if elevation_delta > 800.0:
                    is_blocked = True
                    block_reason = "Camino vecinal anegado y derrumbe en la cuesta por lluvias intensas"
            elif worst_road == "cobblestone":
                rain_speed_penalty = 0.70
            elif worst_road == "secondary_asphalt":
                rain_speed_penalty = 0.85

        effective_speed = max(2.0, base_speed_kmh * rain_speed_penalty)
        transit_hours = round(dist_km / effective_speed, 2)

        return {
            "origin": orig.name,
            "destination": dest.name,
            "distance_km": dist_km,
            "elevation_delta_m": elevation_delta,
            "road_type": worst_road,
            "effective_speed_kmh": round(effective_speed, 1),
            "transit_hours": transit_hours,
            "is_accessible": not is_blocked,
            "block_reason": block_reason,
            "fuel_or_bus_fare_usd": round(1.25 + (dist_km * 0.05) + (0.50 if worst_road == "unpaved_dirt_road" else 0.0), 2),
        }

    # -------------------------------------------------------------------------
    # Separation of Experimental / Fictional Settlements
    # -------------------------------------------------------------------------

    def register_experimental_settlement(
        self,
        exp_settlement_id: str,
        name: str,
        simulated_department: str,
        is_rural: bool = False,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        """Register an artificial experiment testbed, cleanly tagged as non-real-world."""
        self._experimental_settlements[exp_settlement_id] = {
            "id": exp_settlement_id,
            "name": name,
            "is_real_world": False,
            "simulated_department": simulated_department,
            "is_rural": is_rural,
            "meta": meta or {},
        }

    def is_real_world_settlement(self, settlement_id: str) -> bool:
        """Verify whether a settlement corresponds to verified geographic data."""
        return settlement_id in self._settlements
