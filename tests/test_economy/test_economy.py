"""Unit tests for the Dynamic Economy and Real Inventories (Phase 0.4)."""

import uuid
import pytest

from saltbor.economy.household.ledger import HouseholdLedger
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.economy.market.exchange import MarketExchange
from saltbor.economy.production.facility import ProductionFacility
from saltbor.economy.production.recipe import STANDARD_RECIPES
from saltbor.lifecycle.demographics.stages import DevelopmentalStage


def test_inventory_item_split_and_merge():
    """Verify divisible items can be split and merged accurately."""
    item = InventoryItem(
        item_type=ItemType.GRAIN,
        quantity=10.0,
        unit=UnitType.KG,
        quality=0.8,
        acquisition_cost_per_unit=2.0,
    )
    portion = item.split(3.0)
    assert item.quantity == 7.0
    assert portion.quantity == 3.0
    assert portion.item_type == ItemType.GRAIN

    # Merge back
    item.merge(portion)
    assert item.quantity == 10.0
    assert portion.quantity == 0.0


def test_inventory_capacity_and_transfer():
    """Verify inventory containers respect volume limits and handle transfers."""
    inv_a = Inventory(capacity_volume=20.0)
    inv_b = Inventory(capacity_volume=10.0)

    wood = InventoryItem(item_type=ItemType.WOOD, quantity=15.0, unit=UnitType.PIECE)
    accepted = inv_a.add(wood)
    assert accepted == 15.0
    assert inv_a.available_capacity == 5.0

    # Overfill test
    extra = InventoryItem(item_type=ItemType.WOOD, quantity=10.0, unit=UnitType.PIECE)
    accepted_extra = inv_a.add(extra)
    assert accepted_extra == 5.0
    assert inv_a.available_capacity == 0.0

    # Transfer from A to B (B has space for 10)
    transferred = inv_a.transfer_to(inv_b, ItemType.WOOD, 12.0)
    assert transferred == 10.0
    assert inv_b.get_quantity(ItemType.WOOD) == 10.0
    assert inv_a.get_quantity(ItemType.WOOD) == 10.0


def test_production_recipes_and_conservation():
    """Verify production requires real inputs and tools, conserving resources."""
    workshop = ProductionFacility(
        facility_id="taller_test",
        name="Taller de Prueba",
        location_id="taller_el_roble",
        inventory_capacity=100.0,
    )
    recipe = STANDARD_RECIPES["carpentry_furniture"] # 4 Wood + Tool -> 1 Furniture

    worker = uuid.uuid4()

    # Precondition fails without materials
    can, reason = workshop.can_produce(recipe)
    assert can is False

    # Add materials and tool
    workshop.inventory.add(InventoryItem(item_type=ItemType.WOOD, quantity=10.0, unit=UnitType.PIECE))
    workshop.inventory.add(InventoryItem(item_type=ItemType.TOOL, quantity=1.0, unit=UnitType.PIECE, durability=1.0))

    can, reason = workshop.can_produce(recipe)
    assert can is True

    # Start batch: 4 Wood should be deducted immediately
    batch = workshop.start_batch(recipe, worker, current_tick=10)
    assert batch is not None
    assert workshop.inventory.get_quantity(ItemType.WOOD) == 6.0

    # Advance labor until complete
    finished = workshop.advance_work(worker, ticks=4)
    assert len(finished) == 1
    assert workshop.inventory.get_quantity(ItemType.FURNITURE) == 1.0


def test_market_exchange_and_shortages():
    """Verify purchasing, stock depletion, unmet demand, and price response."""
    market = MarketExchange()
    buyer = uuid.uuid4()
    buyer_inv = Inventory(capacity_volume=50.0)

    # Initial stock: 5 Food meals
    market.stock_goods(ItemType.FOOD, 5.0, UnitType.MEAL)

    # Buyer buys 3 meals
    price = market.get_price(ItemType.FOOD)
    success, bought, cost, reason = market.buy_from_market(
        buyer_uid=buyer,
        buyer_inventory=buyer_inv,
        buyer_funds=100.0,
        item_type=ItemType.FOOD,
        desired_quantity=3.0,
        current_tick=1,
    )
    assert success is True
    assert bought == 3.0
    assert cost == pytest.approx(3.0 * price, 0.01)
    assert market.get_stock(ItemType.FOOD) == 2.0

    # Buyer wants 5 more meals (only 2 left)
    success, bought2, cost2, reason2 = market.buy_from_market(
        buyer_uid=buyer,
        buyer_inventory=buyer_inv,
        buyer_funds=100.0,
        item_type=ItemType.FOOD,
        desired_quantity=5.0,
        current_tick=2,
    )
    assert success is True
    assert bought2 == 2.0  # Partially satisfied
    assert market.get_stock(ItemType.FOOD) == 0.0

    # Now stock is exhausted; next attempt triggers shortage
    success, bought3, cost3, reason3 = market.buy_from_market(
        buyer_uid=buyer,
        buyer_inventory=buyer_inv,
        buyer_funds=100.0,
        item_type=ItemType.FOOD,
        desired_quantity=2.0,
        current_tick=3,
    )
    assert success is False
    assert "Out of stock" in reason3
    assert market.shortage_events_count >= 1

    # Price cycle update: shortage should push price upward
    old_price = market.get_price(ItemType.FOOD)
    updated_prices = market.update_cycle()
    assert updated_prices[ItemType.FOOD] > old_price


def test_household_ledger_and_demographic_demand():
    """Verify household pooling and differential food consumption across developmental stages."""
    ledger = HouseholdLedger(household_id="house_1", shared_savings=50.0)

    # Deposit wages
    worker_uid = uuid.uuid4()
    ledger.deposit_income(worker_uid, 30.0)
    assert ledger.shared_savings == 80.0

    # Pay rent/expenses
    paid = ledger.pay_expense(20.0)
    assert paid is True
    assert ledger.shared_savings == 60.0

    # Demand with parents, child, and infant
    stages = [
        DevelopmentalStage.ADULTHOOD,
        DevelopmentalStage.ADULTHOOD,
        DevelopmentalStage.CHILDHOOD,
        DevelopmentalStage.INFANCY,
    ]
    daily_demand = ledger.calculate_daily_food_demand(stages)
    # 1.0 + 1.0 + 0.7 + 0.3 = 3.0 meals/day
    assert daily_demand == pytest.approx(3.0, 0.05)
