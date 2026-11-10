"""Migration and Population Dynamics Engine for SALTBOR Phase 1.0.

Simulates internal and external population mobility:
- Types: Rural to urban, urban to rural, inter-municipal, inter-departmental, labor, education, family reunification, environmental disruption, conflict.
- Multi-factorial decision model: economic opportunity, family ties, social networks, housing, transit cost, risk perception.
- Consequential impacts: origin community labor drain, destination housing demand, remittance flows, network maintenance or decay.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from saltbor.core.types import Tick


class MigrationReason(str, Enum):
    ECONOMIC_OPPORTUNITY = "economic_opportunity"
    EDUCATION = "education"
    FAMILY_REUNIFICATION = "family_reunification"
    HOUSING_AVAILABILITY = "housing_availability"
    ENVIRONMENTAL_CRISIS = "environmental_crisis"
    CONFLICT_AVOIDANCE = "conflict_avoidance"
    RETURN_MIGRATION = "return_migration"


class MigrationStatus(str, Enum):
    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    SETTLED = "settled"
    RETURNED = "returned"


@dataclass
class MigrationRecord:
    migration_id: str
    human_id: str
    origin_settlement_id: str
    destination_settlement_id: str
    reason: MigrationReason
    departure_tick: Tick
    arrival_tick: Optional[Tick] = None
    status: MigrationStatus = MigrationStatus.PLANNED
    maintains_origin_ties: bool = True
    remittances_sent_total: float = 0.0
    household_id: Optional[str] = None


class MigrationDynamicsEngine:
    """Manages migration flows, settlement relocations, remittances, and push-pull dynamics."""

    def __init__(self) -> None:
        self.migrations: Dict[str, MigrationRecord] = {}
        self.remittances_by_settlement: Dict[str, float] = {}  # settlement_id -> total remittances received

    def evaluate_migration_desire(
        self,
        human_id: str,
        current_wealth: float,
        current_settlement_opportunity: float,  # 0.0 to 1.0
        family_in_destination_count: int,
        destination_opportunity: float,  # 0.0 to 1.0
        environmental_stress: float = 0.0,  # 0.0 to 1.0
        relocation_cost: float = 50.0,
    ) -> float:
        """Calculates migration propensity (0.0 to 1.0) without mechanical wage-only determinism."""
        push_factor = (1.0 - current_settlement_opportunity) * 0.4 + environmental_stress * 0.45
        pull_factor = destination_opportunity * 0.35 + (min(family_in_destination_count, 5) * 0.07)
        affordability = 1.0 if current_wealth >= relocation_cost else max(0.1, current_wealth / (relocation_cost + 1e-5))

        score = (push_factor + pull_factor) * affordability
        return max(0.0, min(1.0, score))

    def initiate_migration(
        self,
        human_id: str,
        origin_id: str,
        destination_id: str,
        reason: MigrationReason,
        tick: Tick,
        household_id: Optional[str] = None,
    ) -> MigrationRecord:
        mig_id = f"mig_{uuid4().hex[:8]}"
        record = MigrationRecord(
            migration_id=mig_id,
            human_id=human_id,
            origin_settlement_id=origin_id,
            destination_settlement_id=destination_id,
            reason=reason,
            departure_tick=tick,
            status=MigrationStatus.IN_TRANSIT,
            maintains_origin_ties=True,
            household_id=household_id,
        )
        self.migrations[mig_id] = record
        return record

    def complete_migration(self, migration_id: str, arrival_tick: Tick) -> bool:
        if migration_id not in self.migrations:
            return False
        record = self.migrations[migration_id]
        record.status = MigrationStatus.SETTLED
        record.arrival_tick = arrival_tick
        return True

    def send_remittance(self, migration_id: str, amount: float) -> bool:
        if migration_id not in self.migrations:
            return False
        record = self.migrations[migration_id]
        if not record.maintains_origin_ties or record.status != MigrationStatus.SETTLED:
            return False
        record.remittances_sent_total += amount
        self.remittances_by_settlement[record.origin_settlement_id] = (
            self.remittances_by_settlement.get(record.origin_settlement_id, 0.0) + amount
        )
        return True

    def return_to_origin(self, migration_id: str, tick: Tick) -> bool:
        if migration_id not in self.migrations:
            return False
        record = self.migrations[migration_id]
        record.status = MigrationStatus.RETURNED
        return True
