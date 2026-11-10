"""Dynamic price formation model responding to local supply and demand."""

from __future__ import annotations

import dataclasses
from typing import Optional

from saltbor.economy.inventory.item import ItemType


@dataclasses.dataclass
class MarketGoodState:
    """Tracks stock level, current price, and demand history for a good."""

    item_type: ItemType
    current_price: float
    base_price: float
    min_price: float
    max_price: float
    current_supply: float = 0.0
    recent_demand: float = 0.0
    unmet_demand: float = 0.0
    adjustment_speed: float = 0.15 # Dampening factor to prevent oscillations


class PricingModel:
    """Equilibrium-seeking pricing engine with dampening against destabilizing feedback."""

    def __init__(self) -> None:
        self._states: dict[ItemType, MarketGoodState] = {
            ItemType.GRAIN: MarketGoodState(
                item_type=ItemType.GRAIN,
                current_price=2.0,
                base_price=2.0,
                min_price=0.8,
                max_price=8.0,
            ),
            ItemType.VEGETABLE: MarketGoodState(
                item_type=ItemType.VEGETABLE,
                current_price=3.0,
                base_price=3.0,
                min_price=1.2,
                max_price=10.0,
            ),
            ItemType.FOOD: MarketGoodState(
                item_type=ItemType.FOOD,
                current_price=5.0,
                base_price=5.0,
                min_price=2.0,
                max_price=18.0,
            ),
            ItemType.WOOD: MarketGoodState(
                item_type=ItemType.WOOD,
                current_price=4.0,
                base_price=4.0,
                min_price=1.5,
                max_price=15.0,
            ),
            ItemType.TOOL: MarketGoodState(
                item_type=ItemType.TOOL,
                current_price=25.0,
                base_price=25.0,
                min_price=12.0,
                max_price=80.0,
            ),
            ItemType.CLOTHING: MarketGoodState(
                item_type=ItemType.CLOTHING,
                current_price=20.0,
                base_price=20.0,
                min_price=8.0,
                max_price=60.0,
            ),
            ItemType.MEDICINE: MarketGoodState(
                item_type=ItemType.MEDICINE,
                current_price=15.0,
                base_price=15.0,
                min_price=5.0,
                max_price=75.0,
            ),
            ItemType.SEEDS: MarketGoodState(
                item_type=ItemType.SEEDS,
                current_price=1.5,
                base_price=1.5,
                min_price=0.5,
                max_price=6.0,
            ),
            ItemType.CONSTRUCTION_MATERIAL: MarketGoodState(
                item_type=ItemType.CONSTRUCTION_MATERIAL,
                current_price=6.0,
                base_price=6.0,
                min_price=2.5,
                max_price=25.0,
            ),
            ItemType.FURNITURE: MarketGoodState(
                item_type=ItemType.FURNITURE,
                current_price=35.0,
                base_price=35.0,
                min_price=15.0,
                max_price=120.0,
            ),
        }

    def get_price(self, item_type: ItemType) -> float:
        st = self._states.get(item_type)
        return st.current_price if st else 2.0

    def get_state(self, item_type: ItemType) -> Optional[MarketGoodState]:
        return self._states.get(item_type)

    def record_transaction(self, item_type: ItemType, quantity: float) -> None:
        """Register satisfied consumer demand."""
        st = self._states.get(item_type)
        if st:
            st.recent_demand += quantity

    def record_unmet_demand(self, item_type: ItemType, quantity: float) -> None:
        """Register purchase attempt that failed due to inventory exhaustion."""
        st = self._states.get(item_type)
        if st:
            st.unmet_demand += quantity

    def update_prices(self, current_inventory_levels: dict[ItemType, float]) -> dict[ItemType, float]:
        """Recalculate market prices based on supply, satisfied demand, and unmet demand.

        Formula:
        ratio = (demand + unmet_demand) / max(1.0, supply)
        price_delta = current_price * lambda * (ratio - 1.0)
        """
        updated_prices: dict[ItemType, float] = {}

        for itype, st in self._states.items():
            supply = current_inventory_levels.get(itype, 0.0)
            st.current_supply = supply
            total_demand = st.recent_demand + st.unmet_demand

            if supply <= 0.0 and total_demand > 0:
                # Acute shortage: price steps up toward ceiling
                ratio = 2.0
            elif total_demand <= 0.0 and supply > 10.0:
                # Glut / excess stock: price eases downward
                ratio = 0.5
            else:
                ratio = (total_demand + 1.0) / (supply + 1.0)

            # Dampened log-linear price adjustment
            delta_fraction = st.adjustment_speed * (ratio - 1.0)
            # Bound step change to [-20%, +25%] per cycle to prevent oscillation
            clipped_delta = max(-0.20, min(0.25, delta_fraction))
            new_price = st.current_price * (1.0 + clipped_delta)

            # Re-anchor gently towards base price if supply & demand are balanced
            new_price = 0.95 * new_price + 0.05 * st.base_price

            # Apply hard clamping
            st.current_price = round(max(st.min_price, min(st.max_price, new_price)), 2)
            updated_prices[itype] = st.current_price

            # Decay demand memory for next window
            st.recent_demand *= 0.3
            st.unmet_demand *= 0.3

        return updated_prices
