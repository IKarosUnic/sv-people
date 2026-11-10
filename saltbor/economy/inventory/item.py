"""Economic inventory items and unit types."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class ItemType(enum.Enum):
    """Categorization of physical goods in Saltbor."""

    GRAIN = "grain"                    # Basic agricultural crop (maize, beans, sorghum)
    VEGETABLE = "vegetable"            # Fresh agricultural produce
    FOOD = "food"                      # Prepared meals and consumable food
    PRESERVED_FOOD = "preserved_food"  # Salted fish, cured meats, dried goods
    WOOD = "wood"                      # Raw timber / lumber for construction and carpentry
    TOOL = "tool"                      # Durable implements (hammer, saw, hoe, machete)
    CLOTHING = "clothing"              # Garments and textiles
    MEDICINE = "medicine"              # Pharmaceutical and herbal remedies
    SEEDS = "seeds"                    # Planting inputs for agriculture
    CONSTRUCTION_MATERIAL = "construction_material"  # Bricks, tiles, mortar
    FURNITURE = "furniture"            # Finished carpentry goods (chairs, tables, shelves)


class UnitType(enum.Enum):
    KG = "kg"
    PIECE = "piece"
    BUNDLE = "bundle"
    DOSE = "dose"
    MEAL = "meal"
    BUSHEL = "bushel"


@dataclass
class InventoryItem:
    """A divisible or discrete physical asset in an inventory."""

    item_type: ItemType
    quantity: float
    unit: UnitType
    quality: float = 1.0                # 0.0 to 1.0 (condition / grade)
    acquisition_cost_per_unit: float = 1.0
    base_market_price: float = 1.5
    perishability_rate: float = 0.0     # Fraction lost per day (e.g. food spoilage)
    durability: float = 1.0             # For tools: wear and tear [0.0, 1.0]

    def split(self, amount: float) -> InventoryItem:
        """Split off a portion of this item stack into a new stack."""
        if amount <= 0 or amount > self.quantity:
            raise ValueError(f"Cannot split {amount} from available quantity {self.quantity}")
        self.quantity -= amount
        return InventoryItem(
            item_type=self.item_type,
            quantity=amount,
            unit=self.unit,
            quality=self.quality,
            acquisition_cost_per_unit=self.acquisition_cost_per_unit,
            base_market_price=self.base_market_price,
            perishability_rate=self.perishability_rate,
            durability=self.durability,
        )

    def merge(self, other: InventoryItem) -> None:
        """Merge another compatible item stack into this stack."""
        if other.item_type != self.item_type or other.unit != self.unit:
            raise ValueError(f"Cannot merge incompatible items: {self.item_type} and {other.item_type}")
        total_qty = self.quantity + other.quantity
        if total_qty > 0:
            # Weighted average quality and acquisition cost
            self.quality = (self.quality * self.quantity + other.quality * other.quantity) / total_qty
            self.acquisition_cost_per_unit = (
                self.acquisition_cost_per_unit * self.quantity + other.acquisition_cost_per_unit * other.quantity
            ) / total_qty
        self.quantity = total_qty
        other.quantity = 0.0

    def apply_decay(self, days_elapsed: float) -> float:
        """Apply deterioration or spoilage over elapsed time. Returns amount lost."""
        if self.perishability_rate <= 0 or self.quantity <= 0:
            return 0.0
        lost = self.quantity * min(1.0, self.perishability_rate * days_elapsed)
        self.quantity = max(0.0, self.quantity - lost)
        return lost
