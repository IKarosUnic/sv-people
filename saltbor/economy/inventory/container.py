"""Physical inventory container supporting capacity limits, storage, and transfers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType


@dataclass
class Inventory:
    """A bounded inventory container held by an individual, household, or business."""

    capacity_volume: float = 100.0  # Storage limit in volumetric units
    _items: dict[ItemType, InventoryItem] = field(default_factory=dict)
    total_received: float = 0.0
    total_consumed: float = 0.0

    @property
    def total_quantity(self) -> float:
        return sum(item.quantity for item in self._items.values())

    @property
    def available_capacity(self) -> float:
        return max(0.0, self.capacity_volume - self.total_quantity)

    def get_quantity(self, item_type: ItemType) -> float:
        """Query quantity of a specific item type."""
        item = self._items.get(item_type)
        return item.quantity if item else 0.0

    def get_item(self, item_type: ItemType) -> Optional[InventoryItem]:
        return self._items.get(item_type)

    def add(self, item: InventoryItem) -> float:
        """Add an item stack to this inventory up to available capacity.

        Returns the actual quantity accepted.
        """
        if item.quantity <= 0:
            return 0.0

        space = self.available_capacity
        accepted = min(item.quantity, space)
        if accepted <= 0:
            return 0.0

        if item.item_type in self._items:
            existing = self._items[item.item_type]
            if accepted < item.quantity:
                split_item = item.split(accepted)
                existing.merge(split_item)
            else:
                existing.merge(item)
        else:
            if accepted < item.quantity:
                split_item = item.split(accepted)
                self._items[item.item_type] = split_item
            else:
                self._items[item.item_type] = item

        self.total_received += accepted
        return accepted

    def remove(self, item_type: ItemType, quantity: float) -> Optional[InventoryItem]:
        """Remove a specified quantity of an item type.

        Returns the extracted InventoryItem, or None if insufficient quantity.
        """
        if quantity <= 0:
            return None
        existing = self._items.get(item_type)
        if not existing or existing.quantity < quantity:
            return None

        if existing.quantity == quantity:
            extracted = self._items.pop(item_type)
        else:
            extracted = existing.split(quantity)

        self.total_consumed += quantity
        return extracted

    def transfer_to(self, other: Inventory, item_type: ItemType, quantity: float) -> float:
        """Transfer quantity of item_type from this inventory to another.

        Returns amount successfully transferred.
        """
        avail = self.get_quantity(item_type)
        desired = min(quantity, avail)
        if desired <= 0:
            return 0.0

        # Check other's space
        can_accept = min(desired, other.available_capacity)
        if can_accept <= 0:
            return 0.0

        extracted = self.remove(item_type, can_accept)
        if extracted:
            accepted = other.add(extracted)
            if accepted < extracted.quantity:
                # Refund leftover back
                self.add(extracted)
            return accepted
        return 0.0

    def apply_decay(self, days_elapsed: float) -> dict[ItemType, float]:
        """Apply spoilage and degradation to all stored goods."""
        losses: dict[ItemType, float] = {}
        empty_types = []
        for itype, item in self._items.items():
            lost = item.apply_decay(days_elapsed)
            if lost > 0:
                losses[itype] = lost
                self.total_consumed += lost
            if item.quantity <= 1e-6:
                empty_types.append(itype)

        for itype in empty_types:
            self._items.pop(itype, None)

        return losses

    def all_items(self) -> list[InventoryItem]:
        return list(self._items.values())

    def to_dict(self) -> dict[str, float]:
        return {item.item_type.value: round(item.quantity, 2) for item in self._items.values()}
