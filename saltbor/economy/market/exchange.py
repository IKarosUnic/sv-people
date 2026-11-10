"""Market exchange: transactions, liquidity, trade execution, and shortage logging."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID, LocationID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.economy.market.pricing import PricingModel

logger = logging.getLogger(__name__)


@dataclass
class TransactionRecord:
    """Audit record for a physical goods transaction."""

    tick: Tick
    buyer_uid: Optional[HumanID]
    seller_uid: Optional[HumanID]
    item_type: ItemType
    quantity: float
    unit_price: float
    total_amount: float
    location_id: LocationID


class MarketExchange:
    """Settlement marketplace managing inventory stocks, vendor orders, and dynamic pricing."""

    def __init__(
        self,
        market_id: str = "mercado_municipal",
        location_id: LocationID = "mercado_municipal",
        inventory_capacity: float = 1000.0,
    ) -> None:
        self.market_id = market_id
        self.location_id = location_id
        self.inventory = Inventory(capacity_volume=inventory_capacity)
        self.pricing = PricingModel()
        self.transaction_history: list[TransactionRecord] = []
        self.shortage_events_count: int = 0

    def get_stock(self, item_type: ItemType) -> float:
        return self.inventory.get_quantity(item_type)

    def get_price(self, item_type: ItemType) -> float:
        return self.pricing.get_price(item_type)

    def stock_goods(self, item_type: ItemType, quantity: float, unit: UnitType = UnitType.KG) -> float:
        """Add goods directly to market inventory (e.g. from farmers/suppliers)."""
        item = InventoryItem(
            item_type=item_type,
            quantity=quantity,
            unit=unit,
            acquisition_cost_per_unit=self.pricing.get_price(item_type) * 0.8,
            base_market_price=self.pricing.get_price(item_type),
        )
        return self.inventory.add(item)

    def buy_from_market(
        self,
        buyer_uid: HumanID,
        buyer_inventory: Inventory,
        buyer_funds: float,
        item_type: ItemType,
        desired_quantity: float,
        current_tick: Tick,
    ) -> tuple[bool, float, float, str]:
        """A customer purchases goods from the market.

        Returns (success: bool, quantity_purchased: float, total_cost: float, reason: str).
        """
        if desired_quantity <= 0:
            return False, 0.0, 0.0, "Invalid quantity"

        available_stock = self.inventory.get_quantity(item_type)
        if available_stock <= 0:
            self.pricing.record_unmet_demand(item_type, desired_quantity)
            self.shortage_events_count += 1
            return False, 0.0, 0.0, f"Out of stock: {item_type.value}"

        qty_to_buy = min(desired_quantity, available_stock)
        price_per_unit = self.pricing.get_price(item_type)
        total_cost = round(qty_to_buy * price_per_unit, 2)

        if buyer_funds < total_cost:
            # Try buying what they can afford
            affordable_qty = int(buyer_funds / price_per_unit) if price_per_unit > 0 else 0
            if affordable_qty <= 0:
                self.pricing.record_unmet_demand(item_type, desired_quantity)
                return False, 0.0, 0.0, f"Insufficient funds (${buyer_funds:.2f} < ${total_cost:.2f})"
            qty_to_buy = float(affordable_qty)
            total_cost = round(qty_to_buy * price_per_unit, 2)

        # Check buyer inventory space
        if buyer_inventory.available_capacity < qty_to_buy:
            qty_to_buy = min(qty_to_buy, buyer_inventory.available_capacity)
            total_cost = round(qty_to_buy * price_per_unit, 2)
            if qty_to_buy <= 0:
                return False, 0.0, 0.0, "Buyer inventory full"

        # Execute transfer
        extracted = self.inventory.remove(item_type, qty_to_buy)
        if not extracted:
            return False, 0.0, 0.0, "Stock extraction failed"

        buyer_inventory.add(extracted)
        self.pricing.record_transaction(item_type, qty_to_buy)

        tx = TransactionRecord(
            tick=current_tick,
            buyer_uid=buyer_uid,
            seller_uid=None, # Market itself
            item_type=item_type,
            quantity=qty_to_buy,
            unit_price=price_per_unit,
            total_amount=total_cost,
            location_id=self.location_id,
        )
        self.transaction_history.append(tx)
        return True, qty_to_buy, total_cost, "Success"

    def sell_to_market(
        self,
        seller_uid: HumanID,
        seller_inventory: Inventory,
        item_type: ItemType,
        quantity: float,
        current_tick: Tick,
    ) -> tuple[bool, float, float, str]:
        """A producer or merchant sells goods to the market.

        Returns (success: bool, quantity_sold: float, revenue_earned: float, reason: str).
        """
        if quantity <= 0:
            return False, 0.0, 0.0, "Invalid quantity"

        avail = seller_inventory.get_quantity(item_type)
        if avail < quantity:
            return False, 0.0, 0.0, f"Insufficient goods in inventory (have {avail}, want to sell {quantity})"

        if self.inventory.available_capacity < quantity:
            return False, 0.0, 0.0, "Market inventory storage full"

        # Market pays 80% of current retail price as wholesale price
        wholesale_price = round(self.pricing.get_price(item_type) * 0.80, 2)
        total_payout = round(quantity * wholesale_price, 2)

        extracted = seller_inventory.remove(item_type, quantity)
        if not extracted:
            return False, 0.0, 0.0, "Failed to remove items from seller inventory"

        self.inventory.add(extracted)

        tx = TransactionRecord(
            tick=current_tick,
            buyer_uid=None,
            seller_uid=seller_uid,
            item_type=item_type,
            quantity=quantity,
            unit_price=wholesale_price,
            total_amount=total_payout,
            location_id=self.location_id,
        )
        self.transaction_history.append(tx)
        return True, quantity, total_payout, "Success"

    def update_cycle(self) -> dict[ItemType, float]:
        """End-of-day price update based on stock levels and demand."""
        current_stocks = {itype: self.inventory.get_quantity(itype) for itype in ItemType}
        return self.pricing.update_prices(current_stocks)
