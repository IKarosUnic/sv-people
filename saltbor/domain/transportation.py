"""Transportation and Mobility Domain for SALTBOR.

Simulates transit corridors, bus routes (*rutas de buses/microbuses*), commuter flows,
traffic congestion, and transit disruptions (landslides, road closures, fuel price spikes).
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.domain.models import DomainCategory, DomainDefinition, DomainStatus

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TransitRoute:
    route_id: str
    name: str
    origin: str
    destination: str
    distance_km: float
    base_fare_usd: float = 0.25
    average_travel_time_minutes: float = 35.0
    congestion_factor: float = 1.0  # 1.0 = normal, 2.0 = severe delay
    is_blocked: bool = False
    blockage_reason: Optional[str] = None


class TransportationActivityDomain:
    """Specialized domain orchestrating transit routes, accessibility, and service shocks."""

    def __init__(self) -> None:
        self.routes: Dict[str, TransitRoute] = {}
        self._seed_default_routes()

    def get_definition(self) -> DomainDefinition:
        return DomainDefinition(
            domain_id="transportation",
            name="Transportation and Mobility Domain",
            category=DomainCategory.TRANSPORTATION,
            purpose="Simulate daily commuter transit, modal choice, travel times, and network resilience under road disruptions in El Salvador.",
            geographic_scope="El Salvador",
            resources=["transit_units", "fuel_diesel", "road_capacity"],
            infrastructure=["bus_stops", "transit_terminals", "highways", "arterial_roads"],
            activities=[
                "transport.commuting",
                "transport.route_choice",
                "transport.waiting_transit",
                "transport.respond_service_interruption",
            ],
            entities=["TransitRoute", "TransitStop", "RoadBlockageEvent"],
            indicators=["average_commute_time_minutes", "transit_expenditure_share", "network_accessibility_index"],
            possible_interventions=["feeder_bus_route", "fuel_subsidy", "road_clearance_emergency_response"],
            data_sources=["VMT_rutas_transporte", "FOVIAL_estado_vial", "OSM_roads"],
            uncertainties=["flash_flooding_during_tropical_storms", "informal_fare_surges"],
            version="1.0.0",
            status=DomainStatus.ACTIVE,
        )

    def register_route(self, route: TransitRoute) -> None:
        self.routes[route.route_id] = route

    def simulate_commute_trip(
        self,
        commuter_uid: str,
        origin: str,
        destination: str,
        budget_usd: float,
        rng: Optional[np.random.Generator] = None,
    ) -> Dict[str, Any]:
        """Simulate a commuter navigating transit routes with possible congestion or blockage."""
        # Find connecting route
        candidate_route = None
        for r in self.routes.values():
            if r.origin.lower() == origin.lower() and r.destination.lower() == destination.lower():
                candidate_route = r
                break

        if not candidate_route:
            # Fallback direct distance transit
            return {
                "commuter_uid": commuter_uid,
                "status": "walked_or_private",
                "travel_time_minutes": 45.0,
                "cost_usd": 0.0,
            }

        if candidate_route.is_blocked:
            # Must detour: 80% time penalty
            detour_time = candidate_route.average_travel_time_minutes * 1.80
            return {
                "commuter_uid": commuter_uid,
                "route_id": candidate_route.route_id,
                "status": "detour_due_to_blockage",
                "blockage_reason": candidate_route.blockage_reason,
                "travel_time_minutes": round(detour_time, 1),
                "cost_usd": candidate_route.base_fare_usd * 1.5,
            }

        actual_time = candidate_route.average_travel_time_minutes * candidate_route.congestion_factor
        return {
            "commuter_uid": commuter_uid,
            "route_id": candidate_route.route_id,
            "status": "commuted_normal",
            "travel_time_minutes": round(actual_time, 1),
            "cost_usd": candidate_route.base_fare_usd,
        }

    def _seed_default_routes(self) -> None:
        self.register_route(
            TransitRoute(
                route_id="ruta_42_san_salvador",
                name="Ruta 42 (Santa Tecla - San Salvador Centro)",
                origin="Santa Tecla",
                destination="San Salvador",
                distance_km=12.5,
                base_fare_usd=0.35,
                average_travel_time_minutes=35.0,
            )
        )
        self.register_route(
            TransitRoute(
                route_id="ruta_125_chalatenango",
                name="Ruta 125 (Chalatenango - San Salvador)",
                origin="Chalatenango",
                destination="San Salvador",
                distance_km=75.0,
                base_fare_usd=1.50,
                average_travel_time_minutes=110.0,
            )
        )
