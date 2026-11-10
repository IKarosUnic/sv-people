"""Unit and integration tests for Phase 0.6 Regional Trade & Settlement Graph."""

import pytest
import numpy as np
from saltbor.world.regional.settlement import RegionalSettlement, SettlementEcology
from saltbor.world.regional.route import RegionalTradeRoute
from saltbor.world.regional.caravan import RegionalTradeEngine, CaravanStatus
from saltbor.economy.inventory.item import ItemType


def test_regional_settlement_pricing_and_surplus():
    settlement = RegionalSettlement(
        settlement_id="test_forest",
        name="Monte Verde",
        ecology=SettlementEcology.HIGHLAND_FOREST,
        commodity_surpluses={ItemType.WOOD: 50.0},
        price_multipliers={ItemType.WOOD: 0.5},
    )
    # High wood surplus leads to lower price
    cheap_wood_price = settlement.get_local_price(ItemType.WOOD, base_price=5.0)
    assert cheap_wood_price < 3.0

    # Low furniture stock leads to higher price
    scarce_furniture_price = settlement.get_local_price(ItemType.FURNITURE, base_price=20.0)
    assert scarce_furniture_price > 20.0

    # Periodic production generates specialized surplus
    settlement.produce_periodic_surplus()
    assert settlement.commodity_surpluses[ItemType.WOOD] == 65.0


def test_regional_trade_route_transit_duration():
    route = RegionalTradeRoute(
        route_id="r1",
        source_settlement_id="saltbor",
        target_settlement_id="monte_verde",
        distance_km=18.0,
        difficulty_multiplier=1.5,
    )
    assert route.transit_ticks > 25


def test_caravan_dispatch_and_exchange():
    trade = RegionalTradeEngine(rng=np.random.default_rng(42))

    caravan = trade.dispatch_caravan(
        caravan_id="test_caravan",
        origin_id="settlement_saltbor",
        destination_id="settlement_monte_verde",
        cargo={ItemType.FURNITURE: 3.0},
        currency_budget=80.0,
        departure_tick=1,
    )
    assert caravan is not None
    assert caravan.status == CaravanStatus.IN_TRANSIT

    # Step simulation until caravan completes journey
    for tick in range(1, 40):
        trade.step(tick)

    assert caravan.status == CaravanStatus.COMPLETED
    assert caravan.trade_volume_value > 0.0
    assert caravan.cargo_acquired.get(ItemType.WOOD, 0.0) > 0.0
