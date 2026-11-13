"""Household economics: resource pooling, consumption models, and living costs (Phase 1.5).

Redesigned to model authentic household economics:
- Multi-member resource pooling and equitable cost distribution.
- Separation of household costs (utilities, rent, pantry groceries) from individual discretionary spending.
- Water, electricity, gas, and waste disposal scaled to actual member composition and dwelling type.
- Cooking consumes physical pantry inventory rather than double-charging arbitrary cash at the stove.
- Conservation of money: utility expenses transfer to municipal/community treasury; rent transfers to landlords.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, List, Optional
import uuid

from saltbor.core.types import HumanID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.lifecycle.demographics.stages import DevelopmentalStage

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class HouseholdLedger:
    """Financial and resource account for a cohabiting domestic unit."""

    household_id: str
    inventory: Inventory = dataclasses.field(default_factory=lambda: Inventory(capacity_volume=150.0))
    shared_savings: float = 100.0
    total_income_earned: float = 0.0
    total_expenses_paid: float = 0.0
    daily_food_consumed: float = 0.0

    # Phase 1.5 Enhanced Household Living Cost Model
    dwelling_unit_id: Optional[str] = None
    dwelling_type: str = "rental"                 # "owner_occupied", "rental", "shared_family", "informal", "shelter"
    head_of_household_uid: Optional[HumanID] = None
    member_uids: list[HumanID] = dataclasses.field(default_factory=list)

    # Overhead, Utility Arrears & Rent
    daily_base_utility_rate: float = 0.60         # Base electricity and community water hookup ($0.60/household)
    per_member_utility_rate: float = 0.25         # Variable water/gas per resident ($0.25/person)
    unpaid_utilities_arrears: float = 0.0
    unpaid_rent_arrears: float = 0.0
    consecutive_distress_days: int = 0

    def add_member(self, member_uid: HumanID, is_head: bool = False) -> None:
        if member_uid not in self.member_uids:
            self.member_uids.append(member_uid)
        if is_head or self.head_of_household_uid is None:
            self.head_of_household_uid = member_uid

    def remove_member(self, member_uid: HumanID) -> None:
        if member_uid in self.member_uids:
            self.member_uids.remove(member_uid)
        if self.head_of_household_uid == member_uid:
            self.head_of_household_uid = self.member_uids[0] if self.member_uids else None

    def deposit_income(self, earner_uid: HumanID, amount: float) -> None:
        if amount > 0:
            self.shared_savings = round(self.shared_savings + amount, 2)
            self.total_income_earned = round(self.total_income_earned + amount, 2)

    def pay_expense(self, amount: float, reason: str = "") -> bool:
        if self.shared_savings >= amount:
            self.shared_savings = round(self.shared_savings - amount, 2)
            self.total_expenses_paid = round(self.total_expenses_paid + amount, 2)
            return True
        return False

    def store_goods(self, item: InventoryItem) -> float:
        return self.inventory.add(item)

    def retrieve_food(self, meals_needed: float) -> float:
        """Extract food meals from domestic pantry."""
        item = self.inventory.remove(ItemType.FOOD, meals_needed)
        if item:
            self.daily_food_consumed += item.quantity
            return item.quantity
        return 0.0

    def calculate_daily_food_demand(self, member_stages: list[DevelopmentalStage]) -> float:
        """Calculate aggregate daily food units required based on family composition."""
        total = 0.0
        for stage in member_stages:
            if stage in (DevelopmentalStage.ADULTHOOD, DevelopmentalStage.EARLY_ADULTHOOD, DevelopmentalStage.OLDER_ADULTHOOD):
                total += 1.0
            elif stage == DevelopmentalStage.ADOLESCENCE:
                total += 1.1
            elif stage == DevelopmentalStage.CHILDHOOD:
                total += 0.7
            elif stage == DevelopmentalStage.EARLY_CHILDHOOD:
                total += 0.5
            elif stage == DevelopmentalStage.INFANCY:
                total += 0.3
        return round(total, 2)

    # -------------------------------------------------------------------------
    # Realistic Daily Living Overhead & Utility Execution
    # -------------------------------------------------------------------------

    def execute_daily_living_expenses(
        self,
        current_tick: Tick,
        population_registry: Any,
        utility_treasury: Optional[dict[str, float]] = None,
    ) -> dict[str, Any]:
        """Distribute living expenses according to household composition and actual consumption.
        
        Zero currency is deleted blindly:
        - Utility fees are paid to the community utility treasury.
        - Arrears accrue when funds are insufficient.
        """
        # Skip overhead for homeless shelters or informal bivouacs
        if self.dwelling_type == "shelter":
            return {"status": "exempt", "household_id": self.household_id, "amount_paid": 0.0}

        member_count = max(1, len(self.member_uids))
        utility_cost = round(
            self.daily_base_utility_rate + (member_count * self.per_member_utility_rate), 2
        )

        amount_paid = 0.0
        # 1. Try paying from pooled domestic savings
        if self.shared_savings >= utility_cost:
            self.shared_savings = round(self.shared_savings - utility_cost, 2)
            self.total_expenses_paid = round(self.total_expenses_paid + utility_cost, 2)
            amount_paid = utility_cost
            self.unpaid_utilities_arrears = 0.0
            self.consecutive_distress_days = 0
        else:
            # 2. Pool contribution from head of household or earners
            needed = utility_cost
            if self.shared_savings > 0:
                needed -= self.shared_savings
                amount_paid += self.shared_savings
                self.shared_savings = 0.0

            # Collect from members with cash in wallet
            collected_from_members = 0.0
            for uid in self.member_uids:
                member = population_registry.get_optional(uid)
                if member and member.physical_state.money >= 0.50 and needed > 0:
                    contribution = min(needed, member.physical_state.money)
                    member.physical_state.money = round(member.physical_state.money - contribution, 2)
                    needed = round(needed - contribution, 2)
                    collected_from_members += contribution
                    amount_paid += contribution

            if needed <= 0.01:
                self.total_expenses_paid = round(self.total_expenses_paid + amount_paid, 2)
                self.unpaid_utilities_arrears = 0.0
                self.consecutive_distress_days = 0
            else:
                # Inability to pay full utilities: accumulate arrears
                self.unpaid_utilities_arrears = round(self.unpaid_utilities_arrears + needed, 2)
                self.consecutive_distress_days += 1
                logger.warning(
                    "Household %s short on utilities by $%.2f (cumulative arrears: $%.2f)",
                    self.household_id, needed, self.unpaid_utilities_arrears
                )

        # Deposit paid utilities into community utility treasury (money conservation!)
        if utility_treasury is not None:
            utility_treasury["balance"] = round(utility_treasury.get("balance", 0.0) + amount_paid, 2)

        return {
            "household_id": self.household_id,
            "members": member_count,
            "utility_cost": utility_cost,
            "amount_paid": amount_paid,
            "arrears": self.unpaid_utilities_arrears,
            "distress_days": self.consecutive_distress_days,
        }
