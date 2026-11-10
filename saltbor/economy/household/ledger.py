"""Household economics: resource pooling, consumption models, and living costs."""

from __future__ import annotations

import dataclasses
from typing import Optional

from saltbor.core.types import HumanID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.lifecycle.demographics.stages import DevelopmentalStage


@dataclasses.dataclass
class HouseholdLedger:
    """Financial and resource account for a cohabiting domestic unit."""

    household_id: str
    inventory: Inventory = dataclasses.field(default_factory=lambda: Inventory(capacity_volume=150.0))
    shared_savings: float = 100.0
    total_income_earned: float = 0.0
    total_expenses_paid: float = 0.0
    daily_food_consumed: float = 0.0

    def deposit_income(self, earner_uid: HumanID, amount: float) -> None:
        if amount > 0:
            self.shared_savings += amount
            self.total_income_earned += amount

    def pay_expense(self, amount: float, reason: str = "") -> bool:
        if self.shared_savings >= amount:
            self.shared_savings -= amount
            self.total_expenses_paid += amount
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
        """Calculate aggregate daily food units required based on family composition.

        - Adults/Elders: 1.0 meal equivalent/day
        - Adolescents: 1.1 meal equivalent/day (growth spurt)
        - Children: 0.7 meal equivalent/day
        - Early childhood: 0.5 meal equivalent/day
        - Infancy: 0.3 meal equivalent/day
        """
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
