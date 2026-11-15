"""Public Services and Infrastructure Capacity Engine for SALTBOR Phase 1.14.

Manages physical public services and infrastructure across El Salvador:
- Educational facilities (Escuelas Básicas, Institutos Nacionales, Centros Técnicos).
- Healthcare facilities (Unidades de Salud, Hospitales Nacionales, Puestos Comunitarios).
- Public transportation (Bus trunk lines, urban routes, rural pick-ups).
- Water access (ANDA municipal pipelines, community wells, rural ADESCO hookups).
- Sanitation and waste collection systems.
- Public markets, recreational parks, community spaces, cultural centers, and emergency posts.

Guarantees:
- Strict Epistemic Integrity: Capacity is NOT inferred blindly from OSM building footprints.
  Unknown capacity remains explicitly `None` (UNCONFIGURED) until empirical evidence or
  configured assumptions are provided.
- Spatial catchment analysis: Haversine distance friction and accessibility indices.
- Service queues, daily demand surges, and unmet need tracking.
"""

from __future__ import annotations

import collections
import dataclasses
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.domain.models import DataProvenanceTier
from saltbor.territory.models import (
    PublicServiceFacility,
    ServiceCapacityStatus,
    ServiceCategory,
)

logger = logging.getLogger(__name__)


class PublicServiceCapacityEngine:
    """Simulates operational throughput, catchment areas, and accessibility of public infrastructure."""

    def __init__(self) -> None:
        self.facilities: Dict[str, PublicServiceFacility] = {}
        self._seed_default_facilities()

    def register_facility(self, facility: PublicServiceFacility) -> None:
        """Register a public service facility."""
        self.facilities[facility.facility_id] = facility

    def get_facility(self, facility_id: str) -> Optional[PublicServiceFacility]:
        return self.facilities.get(facility_id)

    def list_facilities(
        self,
        category: Optional[ServiceCategory] = None,
        department_code: Optional[str] = None,
        status: Optional[ServiceCapacityStatus] = None,
    ) -> List[PublicServiceFacility]:
        """Query facilities with optional filtering."""
        res = list(self.facilities.values())
        if category:
            res = [f for f in res if f.category == category]
        if department_code:
            res = [f for f in res if f.department_code == department_code]
        if status:
            res = [f for f in res if f.status == status]
        return res

    # =========================================================================
    # Operational Simulation: Daily Demand, Queue & Throughput
    # =========================================================================

    def submit_service_demand(
        self,
        facility_id: str,
        demanding_citizens_count: int,
    ) -> Tuple[bool, int, int]:
        """Submit service requests for a facility during a simulation period.
        
        Returns: (success, served_count, unmet_count)
        """
        facility = self.facilities.get(facility_id)
        if not facility:
            return False, 0, demanding_citizens_count

        facility.current_daily_demand += demanding_citizens_count

        # If capacity is UNCONFIGURED, service throughput is unknown
        if facility.configured_capacity_per_day is None:
            facility.status = ServiceCapacityStatus.UNCONFIGURED
            return True, 0, demanding_citizens_count

        # Effective throughput capacity adjusted by staff and equipment
        equipment_factor = facility.available_equipment_score
        effective_capacity = int(facility.configured_capacity_per_day * equipment_factor)

        available_capacity = max(0, effective_capacity - facility.served_today)
        served_now = min(available_capacity, demanding_citizens_count)
        unmet_now = demanding_citizens_count - served_now

        facility.served_today += served_now
        facility.current_waiting_queue += unmet_now
        facility.unmet_demand_today += unmet_now

        # Update operational status
        overload_ratio = facility.current_daily_demand / max(effective_capacity, 1)
        if overload_ratio > 1.35:
            facility.status = ServiceCapacityStatus.OVERLOADED
        elif overload_ratio > 0.90:
            facility.status = ServiceCapacityStatus.DEGRADED
        else:
            facility.status = ServiceCapacityStatus.OPERATIONAL

        return True, served_now, unmet_now

    def reset_daily_queues(self) -> None:
        """Reset served counts and clear daily queue bottlenecks."""
        for f in self.facilities.values():
            f.current_daily_demand = 0
            f.current_waiting_queue = 0
            f.served_today = 0
            f.unmet_demand_today = 0
            if f.configured_capacity_per_day is not None and f.status != ServiceCapacityStatus.CLOSED:
                f.status = ServiceCapacityStatus.OPERATIONAL

    # =========================================================================
    # Spatial Accessibility & Underserved Communities Analysis
    # =========================================================================

    def compute_community_accessibility(
        self,
        comm_lat: float,
        comm_lon: float,
        category: ServiceCategory,
        max_search_radius_km: float = 25.0,
    ) -> Dict[str, Any]:
        """Compute distance and accessibility friction from a settlement to the nearest facility."""
        matching_facilities = [f for f in self.facilities.values() if f.category == category]
        if not matching_facilities:
            return {
                "category": category.value,
                "has_accessible_facility": False,
                "nearest_facility_id": None,
                "distance_km": None,
                "accessibility_index": 0.0,
                "service_gap_identified": True,
            }

        distances = []
        for f in matching_facilities:
            d = self._haversine_distance_km(comm_lat, comm_lon, f.latitude, f.longitude)
            distances.append((d, f))

        distances.sort(key=lambda x: x[0])
        nearest_dist, nearest_facility = distances[0]

        is_within_coverage = nearest_dist <= nearest_facility.coverage_radius_km
        # Accessibility decay: 1.0 at 0 km, dropping exponentially
        accessibility_index = round(max(0.0, math.exp(-nearest_dist / 6.5)), 3)

        return {
            "category": category.value,
            "has_accessible_facility": is_within_coverage and nearest_dist <= max_search_radius_km,
            "nearest_facility_id": nearest_facility.facility_id,
            "nearest_facility_name": nearest_facility.name,
            "distance_km": round(nearest_dist, 2),
            "facility_coverage_radius_km": nearest_facility.coverage_radius_km,
            "accessibility_index": accessibility_index,
            "facility_status": nearest_facility.status.value,
            "service_gap_identified": nearest_dist > nearest_facility.coverage_radius_km,
        }

    def detect_infrastructure_gaps(
        self,
        communities: List[Dict[str, Any]],
        category: ServiceCategory,
    ) -> List[Dict[str, Any]]:
        """Identify communities lacking essential public service coverage."""
        gaps = []
        for c in communities:
            res = self.compute_community_accessibility(
                comm_lat=c["latitude"],
                comm_lon=c["longitude"],
                category=category,
            )
            if res["service_gap_identified"]:
                gaps.append({
                    "community_id": c.get("community_id", "unknown"),
                    "name": c.get("name", "Unknown Canton"),
                    "department_code": c.get("department_code", "XX"),
                    "category": category.value,
                    "nearest_distance_km": res["distance_km"],
                    "accessibility_index": res["accessibility_index"],
                    "priority": "HIGH" if res["distance_km"] > 15.0 else "MEDIUM",
                })
        return gaps

    # =========================================================================
    # Helpers
    # =========================================================================

    def _haversine_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance between two coordinates in kilometers."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def _seed_default_facilities(self) -> None:
        """Seed representative Salvadoran public service facilities with calibrated parameters."""
        # 1. Healthcare: Hospital Nacional Rosales (San Salvador)
        self.register_facility(
            PublicServiceFacility(
                facility_id="hosp_rosales_ss",
                category=ServiceCategory.HEALTHCARE,
                name="Hospital Nacional Rosales",
                department_code="SS",
                municipality_id="SS01",
                latitude=13.7003,
                longitude=-89.2044,
                coverage_radius_km=30.0,
                status=ServiceCapacityStatus.OPERATIONAL,
                configured_capacity_per_day=450,
                staff_count=120,
                available_equipment_score=0.90,
                service_limitations=["specialist_appointment_backlog"],
            )
        )

        # 2. Healthcare: Unidad de Salud Chalatenango
        self.register_facility(
            PublicServiceFacility(
                facility_id="salud_chalatenango",
                category=ServiceCategory.HEALTHCARE,
                name="Unidad Comunitaria de Salud Familiar Chalatenango",
                department_code="CH",
                municipality_id="CH01",
                latitude=14.0415,
                longitude=-88.9357,
                coverage_radius_km=12.0,
                status=ServiceCapacityStatus.OPERATIONAL,
                configured_capacity_per_day=65,
                staff_count=8,
                available_equipment_score=0.75,
                service_limitations=["limited_night_shift_coverage"],
            )
        )

        # 3. Education: Instituto Nacional Francisco Menéndez (INFRAMEN - San Salvador)
        self.register_facility(
            PublicServiceFacility(
                facility_id="school_inframen_ss",
                category=ServiceCategory.EDUCATION,
                name="Instituto Nacional Francisco Menéndez (INFRAMEN)",
                department_code="SS",
                municipality_id="SS01",
                latitude=13.7088,
                longitude=-89.1878,
                coverage_radius_km=8.0,
                status=ServiceCapacityStatus.OPERATIONAL,
                configured_capacity_per_day=600,
                staff_count=45,
                available_equipment_score=0.85,
            )
        )

        # 4. Education: Escuela Rural Caserío El Tamarindo (Usulután)
        self.register_facility(
            PublicServiceFacility(
                facility_id="school_rural_usulutan",
                category=ServiceCategory.EDUCATION,
                name="Centro Escolar Caserío El Tamarindo",
                department_code="US",
                municipality_id="US01",
                latitude=13.3620,
                longitude=-88.4710,
                coverage_radius_km=4.0,
                status=ServiceCapacityStatus.OPERATIONAL,
                configured_capacity_per_day=80,
                staff_count=3,
                available_equipment_score=0.60,
                service_limitations=["multigrade_single_classroom"],
            )
        )

        # 5. Public Market: Mercado Central San Salvador
        self.register_facility(
            PublicServiceFacility(
                facility_id="market_central_ss",
                category=ServiceCategory.PUBLIC_MARKET,
                name="Mercado Central de San Salvador",
                department_code="SS",
                municipality_id="SS01",
                latitude=13.6945,
                longitude=-89.1932,
                coverage_radius_km=15.0,
                status=ServiceCapacityStatus.OPERATIONAL,
                configured_capacity_per_day=2500,
                staff_count=30,
                available_equipment_score=0.80,
            )
        )

        # 6. Water Infrastructure: Planta Potabilizadora Las Pavas (San Salvador / Cuscatlán)
        self.register_facility(
            PublicServiceFacility(
                facility_id="water_las_pavas",
                category=ServiceCategory.WATER_ACCESS,
                name="Planta Potabilizadora Las Pavas (ANDA)",
                department_code="CU",
                municipality_id="CU01",
                latitude=13.7420,
                longitude=-89.0350,
                coverage_radius_km=40.0,
                status=ServiceCapacityStatus.OPERATIONAL,
                configured_capacity_per_day=85000,
                staff_count=40,
                available_equipment_score=0.92,
            )
        )

        # 7. Unconfigured Facility (Demonstrating Epistemic Safeguard)
        self.register_facility(
            PublicServiceFacility(
                facility_id="osm_unverified_school_cabañas",
                category=ServiceCategory.EDUCATION,
                name="Centro Escolar No Verificado Cabañas (OSM building)",
                department_code="CA",
                municipality_id="CA01",
                latitude=13.8640,
                longitude=-88.7510,
                coverage_radius_km=3.0,
                status=ServiceCapacityStatus.UNCONFIGURED,
                configured_capacity_per_day=None, # Strictly None until verified
                staff_count=None,
                provenance_tier=DataProvenanceTier.OBSERVED_REAL,
                service_limitations=["capacity_unknown_unverified"],
            )
        )
