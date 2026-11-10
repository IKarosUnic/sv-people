"""
Salvadoran Festivities and Patron Saint Celebrations Engine (Section 19.3).

Models the organization, cultural meaning, and economic stimulus of Salvadoran celebrations:
- Fiestas Patronales (Fiestas Agostinas, Carnaval de San Miguel, Fiestas Julianas)
- Traditional calendar events (Día de la Cruz, Semana Santa con alfombras de sal)
- Community organization through Mayordomías, Cofradías, and ADESCO committees
- Local economic multipliers: street vendors, sweet makers (camotes, nances), pupuserías, music
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional

from saltbor.datasets.salvadoran import (
    SALVADORAN_FESTIVITIES,
    SalvadoranFestivity,
)


@dataclasses.dataclass
class ActiveCommunityFestivity:
    """An active celebration occurring in a Salvadoran municipality."""
    festivity_id: str
    name: str
    location_id: str
    duration_days: int = 5
    accumulated_budget_usd: float = 0.0
    required_budget_usd: float = 500.0
    participating_households: set[str] = dataclasses.field(default_factory=set)
    participating_vendors: int = 0
    is_fully_funded: bool = False
    cohesion_generated: float = 0.0
    economic_turnover_usd: float = 0.0


class SalvadoranFestivityEngine:
    """Coordinates the staging, community fundraising, and economic effects of celebrations."""

    def __init__(self) -> None:
        self._catalog: dict[str, SalvadoranFestivity] = dict(SALVADORAN_FESTIVITIES)
        self._active_events: dict[str, ActiveCommunityFestivity] = {}

    def get_festivity_info(self, festivity_id: str) -> Optional[SalvadoranFestivity]:
        return self._catalog.get(festivity_id)

    def organize_festivity(
        self,
        event_id: str,
        festivity_type_id: str,
        location_id: str,
        organizing_households: list[str],
        community_fund_contribution: float = 150.0,
    ) -> ActiveCommunityFestivity:
        """Launch community preparations for a patron saint festival or celebration."""
        info = self._catalog.get(festivity_type_id)
        name = info.name if info else festivity_type_id

        event = ActiveCommunityFestivity(
            festivity_id=event_id,
            name=name,
            location_id=location_id,
            accumulated_budget_usd=community_fund_contribution,
            participating_households=set(organizing_households),
        )
        self._active_events[event_id] = event
        return event

    def contribute_to_festivity(
        self,
        event_id: str,
        household_id: str,
        amount_usd: float,
    ) -> bool:
        """Individual or household donation to community festival fund (cofradía / directiva)."""
        event = self._active_events.get(event_id)
        if not event:
            return False

        event.accumulated_budget_usd += amount_usd
        event.participating_households.add(household_id)
        if event.accumulated_budget_usd >= event.required_budget_usd:
            event.is_fully_funded = True
        return True

    def execute_celebration(
        self,
        event_id: str,
        local_pupuserias_count: int = 4,
        artisan_vendors_count: int = 8,
    ) -> dict[str, Any]:
        """Simulate the execution and economic stimulus of the celebration."""
        event = self._active_events.get(event_id)
        if not event:
            return {"error": "Festivity not found"}

        # Festival attracts attendees and stimulates informal commerce
        attendance_multiplier = 1.0 + (len(event.participating_households) * 0.05)
        if event.is_fully_funded:
            attendance_multiplier *= 1.4

        # Vendor turnover
        pupuseria_boost = round(local_pupuserias_count * 180.0 * attendance_multiplier, 2)
        street_vendor_boost = round(artisan_vendors_count * 95.0 * attendance_multiplier, 2)
        total_economic_turnover = round(pupuseria_boost + street_vendor_boost, 2)

        event.participating_vendors = local_pupuserias_count + artisan_vendors_count
        event.economic_turnover_usd = total_economic_turnover
        event.cohesion_generated = round(min(0.95, 0.40 + (len(event.participating_households) * 0.03)), 2)

        return {
            "festivity": event.name,
            "status": "Celebración concluida con éxito",
            "households_involved": len(event.participating_households),
            "vendors_benefited": event.participating_vendors,
            "pupuseria_sales_usd": pupuseria_boost,
            "artisan_vendor_sales_usd": street_vendor_boost,
            "total_economic_turnover_usd": total_economic_turnover,
            "social_cohesion_index": event.cohesion_generated,
        }
