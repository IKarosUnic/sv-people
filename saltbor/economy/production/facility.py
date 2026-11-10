"""Production facilities and batch manufacturing execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID, LocationID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType
from saltbor.economy.production.recipe import ProductionRecipe

logger = logging.getLogger(__name__)


@dataclass
class ProductionBatch:
    """An active ongoing production task."""

    batch_id: str
    recipe: ProductionRecipe
    worker_uid: HumanID
    start_tick: Tick
    ticks_invested: int = 0
    is_complete: bool = False

    @property
    def progress(self) -> float:
        if self.recipe.labor_ticks <= 0:
            return 1.0
        return min(1.0, self.ticks_invested / float(self.recipe.labor_ticks))


class ProductionFacility:
    """A workshop, farm, or enterprise with its own inventory and machinery."""

    def __init__(
        self,
        facility_id: str,
        name: str,
        location_id: LocationID,
        inventory_capacity: float = 200.0,
    ) -> None:
        self.facility_id = facility_id
        self.name = name
        self.location_id = location_id
        self.inventory = Inventory(capacity_volume=inventory_capacity)
        self.active_batches: list[ProductionBatch] = []
        self.completed_batches_count: int = 0

    def can_produce(self, recipe: ProductionRecipe) -> tuple[bool, str]:
        """Check if inputs, tools, and storage space are available."""
        # 1. Inputs check
        for itype, required_qty in recipe.inputs.items():
            if self.inventory.get_quantity(itype) < required_qty:
                return False, f"Missing input {itype.value} (need {required_qty}, have {self.inventory.get_quantity(itype)})"

        # 2. Tools check
        for ttype in recipe.tools_required:
            tool_item = self.inventory.get_item(ttype)
            if not tool_item or tool_item.quantity < 1.0:
                return False, f"Missing required tool {ttype.value}"
            if tool_item.durability <= 0.05:
                return False, f"Tool {ttype.value} is broken or worn out"

        # 3. Space check
        total_output_qty = sum(qty for qty, _ in recipe.outputs.values())
        if self.inventory.available_capacity < total_output_qty:
            return False, f"Insufficient inventory capacity (need {total_output_qty}, free {self.inventory.available_capacity})"

        return True, "Ready"

    def start_batch(
        self,
        recipe: ProductionRecipe,
        worker_uid: HumanID,
        current_tick: Tick,
    ) -> Optional[ProductionBatch]:
        """Consume inputs and initiate a production batch."""
        can_run, reason = self.can_produce(recipe)
        if not can_run:
            logger.debug("Cannot start batch %s: %s", recipe.recipe_id, reason)
            return None

        # Deduct inputs from inventory (strict resource conservation!)
        for itype, required_qty in recipe.inputs.items():
            extracted = self.inventory.remove(itype, required_qty)
            if not extracted or extracted.quantity < required_qty:
                return None

        batch = ProductionBatch(
            batch_id=f"{self.facility_id}_{recipe.recipe_id}_{current_tick}",
            recipe=recipe,
            worker_uid=worker_uid,
            start_tick=current_tick,
        )
        self.active_batches.append(batch)
        return batch

    def advance_work(self, worker_uid: HumanID, ticks: int = 1) -> list[ProductionBatch]:
        """Advance active batches worked on by worker_uid.

        Completes batches when labor requirement is fulfilled and delivers outputs to inventory.
        """
        finished: list[ProductionBatch] = []
        for batch in self.active_batches:
            if batch.worker_uid == worker_uid and not batch.is_complete:
                batch.ticks_invested += ticks
                if batch.ticks_invested >= batch.recipe.labor_ticks:
                    batch.is_complete = True
                    self._deliver_batch_outputs(batch)
                    finished.append(batch)

        # Remove finished batches
        self.active_batches = [b for b in self.active_batches if not b.is_complete]
        self.completed_batches_count += len(finished)
        return finished

    def _deliver_batch_outputs(self, batch: ProductionBatch) -> None:
        """Add finished products to facility inventory and apply tool wear."""
        recipe = batch.recipe
        for itype, (qty, unit) in recipe.outputs.items():
            item = InventoryItem(
                item_type=itype,
                quantity=qty,
                unit=unit,
                quality=1.0,
                base_market_price=recipe.inputs.get(ItemType.WOOD, 1.0) * 2.0 + 2.0,
            )
            self.inventory.add(item)

        # Apply tool wear
        for ttype in recipe.tools_required:
            tool = self.inventory.get_item(ttype)
            if tool:
                tool.durability = max(0.0, tool.durability - recipe.tool_wear_per_batch)
                if tool.durability <= 0.0:
                    # Broken tool removed from inventory
                    self.inventory.remove(ttype, 1.0)
                    logger.info("Tool %s in %s broke during production", ttype.value, self.name)
