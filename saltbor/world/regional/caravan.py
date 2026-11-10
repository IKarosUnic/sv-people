"""Regional trade expeditions: caravans, inter-settlement price arbitrage, and cultural exchange."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.culture.element import CulturalElement, CulturalElementType
from saltbor.economy.inventory.item import ItemType
from saltbor.world.regional.route import RegionalTradeRoute
from saltbor.world.regional.settlement import RegionalSettlement, SettlementEcology

logger = logging.getLogger(__name__)


class CaravanStatus(enum.Enum):
    """Lifecycle stage of an inter-settlement trading expedition."""

    PREPARING = "preparing"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    TRADING = "trading"
    RETURNING = "returning"
    COMPLETED = "completed"
    DELAYED = "delayed"


@dataclass
class RegionalCaravan:
    """An organized trade caravan traveling between regional nodes."""

    caravan_id: str
    origin_settlement_id: str
    destination_settlement_id: str
    route_id: str
    leader_uid: Optional[HumanID] = None

    # Cargo & Working Capital
    cargo: dict[ItemType, float] = field(default_factory=dict)
    cargo_acquired: dict[ItemType, float] = field(default_factory=dict)
    currency_budget: float = 150.0

    # Schedule & Motion
    departure_tick: Tick = 0
    duration_ticks: int = 48
    ticks_traveled: int = 0
    progress: float = 0.0          # 0.0 at departure, 1.0 at destination
    status: CaravanStatus = CaravanStatus.PREPARING

    # Cultural & Social Payloads
    carried_cultural_elements: list[CulturalElement] = field(default_factory=list)
    trade_volume_value: float = 0.0


class RegionalTradeEngine:
    """Orchestrates the macro-level settlement graph, commodity arbitrage, and trade caravans."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.settlements: dict[str, RegionalSettlement] = {}
        self.routes: dict[str, RegionalTradeRoute] = {}
        self.caravans: dict[str, RegionalCaravan] = {}
        self.total_regional_trade_value: float = 0.0

        self._initialize_default_regional_network()

    def _initialize_default_regional_network(self) -> None:
        """Procedurally establish standard Salvadoran regional network connected to Saltbor."""
        # 1. Saltbor (Central Core)
        saltbor = RegionalSettlement(
            settlement_id="settlement_saltbor",
            name="Saltbor",
            ecology=SettlementEcology.VALLEY_CORE,
            coordinates_km=(0.0, 0.0),
            population_estimate=120,
            primary_exports=[ItemType.FURNITURE, ItemType.CLOTHING],
            primary_imports=[ItemType.WOOD, ItemType.PRESERVED_FOOD],
            commodity_surpluses={ItemType.FURNITURE: 15.0, ItemType.CLOTHING: 20.0},
            price_multipliers={ItemType.WOOD: 1.3, ItemType.FURNITURE: 0.8},
        )
        self.settlements[saltbor.settlement_id] = saltbor

        # 2. Monte Verde (Highland Forestry - 18 km North in mountain forest)
        monte_verde = RegionalSettlement(
            settlement_id="settlement_monte_verde",
            name="Monte Verde",
            ecology=SettlementEcology.HIGHLAND_FOREST,
            coordinates_km=(4.0, 18.0),
            population_estimate=85,
            primary_exports=[ItemType.WOOD],
            primary_imports=[ItemType.GRAIN, ItemType.FURNITURE],
            commodity_surpluses={ItemType.WOOD: 80.0},
            price_multipliers={ItemType.WOOD: 0.5, ItemType.FURNITURE: 1.5, ItemType.GRAIN: 1.4},
        )
        self.settlements[monte_verde.settlement_id] = monte_verde

        # 3. Puerto Sal (Coastal Fishery & Salt Pans - 25 km South-West)
        puerto_sal = RegionalSettlement(
            settlement_id="settlement_puerto_sal",
            name="Puerto Sal",
            ecology=SettlementEcology.COASTAL_PORT,
            coordinates_km=(-15.0, -20.0),
            population_estimate=140,
            primary_exports=[ItemType.PRESERVED_FOOD],
            primary_imports=[ItemType.WOOD, ItemType.TOOL],
            commodity_surpluses={ItemType.PRESERVED_FOOD: 60.0},
            price_multipliers={ItemType.PRESERVED_FOOD: 0.6, ItemType.WOOD: 1.6, ItemType.TOOL: 1.4},
        )
        self.settlements[puerto_sal.settlement_id] = puerto_sal

        # Connecting Routes
        self.routes["route_saltbor_monte_verde"] = RegionalTradeRoute(
            route_id="route_saltbor_monte_verde",
            source_settlement_id="settlement_saltbor",
            target_settlement_id="settlement_monte_verde",
            distance_km=18.0,
            difficulty_multiplier=1.4,  # Uphill mountain trail
        )
        self.routes["route_saltbor_puerto_sal"] = RegionalTradeRoute(
            route_id="route_saltbor_puerto_sal",
            source_settlement_id="settlement_saltbor",
            target_settlement_id="settlement_puerto_sal",
            distance_km=25.0,
            difficulty_multiplier=1.1,  # Gentle river valley corridor
        )

    def dispatch_caravan(
        self,
        caravan_id: str,
        origin_id: str,
        destination_id: str,
        cargo: dict[ItemType, float],
        currency_budget: float,
        departure_tick: Tick,
        leader_uid: Optional[HumanID] = None,
    ) -> Optional[RegionalCaravan]:
        """Dispatch a trading expedition along the connecting regional corridor."""
        # Find matching route
        route = None
        for r in self.routes.values():
            if (r.source_settlement_id == origin_id and r.target_settlement_id == destination_id) or (
                r.source_settlement_id == destination_id and r.target_settlement_id == origin_id
            ):
                route = r
                break

        if not route:
            logger.warning("No trade corridor connects %s to %s", origin_id, destination_id)
            return None

        caravan = RegionalCaravan(
            caravan_id=caravan_id,
            origin_settlement_id=origin_id,
            destination_settlement_id=destination_id,
            route_id=route.route_id,
            leader_uid=leader_uid,
            cargo=cargo,
            currency_budget=currency_budget,
            departure_tick=departure_tick,
            duration_ticks=route.transit_ticks,
            status=CaravanStatus.IN_TRANSIT,
        )
        self.caravans[caravan_id] = caravan
        logger.info(
            "Caravan %s dispatched from %s to %s (ETA: %d ticks, cargo items: %d)",
            caravan_id,
            origin_id,
            destination_id,
            caravan.duration_ticks,
            len(cargo),
        )
        return caravan

    def step(self, current_tick: Tick) -> list[str]:
        """Advance caravans, resolve transit arrivals, and perform autonomous trade exchanges."""
        notifications: list[str] = []

        # Periodic regional production every 96 ticks (1 day)
        if current_tick % 96 == 0:
            for s in self.settlements.values():
                s.produce_periodic_surplus()

        for c_id, caravan in list(self.caravans.items()):
            if caravan.status == CaravanStatus.IN_TRANSIT:
                caravan.ticks_traveled += 1
                caravan.progress = min(1.0, caravan.ticks_traveled / float(max(1, caravan.duration_ticks)))

                # Check arrival
                if caravan.progress >= 1.0:
                    caravan.status = CaravanStatus.ARRIVED
                    dest = self.settlements.get(caravan.destination_settlement_id)
                    dest_name = dest.name if dest else caravan.destination_settlement_id
                    notifications.append(f"Caravan {c_id} safely reached destination: {dest_name}")

            elif caravan.status == CaravanStatus.ARRIVED:
                # Execute trading at destination
                self._execute_caravan_exchange(caravan, current_tick)
                caravan.status = CaravanStatus.COMPLETED

        return notifications

    def _execute_caravan_exchange(self, caravan: RegionalCaravan, current_tick: Tick) -> float:
        """Conduct mutual commodity exchange between caravan and destination settlement."""
        dest = self.settlements.get(caravan.destination_settlement_id)
        if not dest:
            return 0.0

        exchange_val = 0.0
        # 1. Sell inbound cargo to destination at destination's local market price
        for itype, qty in caravan.cargo.items():
            if qty > 0:
                price = dest.get_local_price(itype)
                revenue = round(qty * price, 2)
                caravan.currency_budget += revenue
                dest.commodity_surpluses[itype] = dest.commodity_surpluses.get(itype, 0.0) + qty
                exchange_val += revenue

        # 2. Buy destination's primary export goods with available caravan funds
        for export_type in dest.primary_exports:
            available_surplus = dest.commodity_surpluses.get(export_type, 0.0)
            if available_surplus > 0 and caravan.currency_budget > 10.0:
                price = dest.get_local_price(export_type)
                buy_qty = min(available_surplus, caravan.currency_budget / max(1.0, price))
                if buy_qty > 0.5:
                    cost = round(buy_qty * price, 2)
                    caravan.currency_budget -= cost
                    dest.commodity_surpluses[export_type] -= buy_qty
                    caravan.cargo_acquired[export_type] = caravan.cargo_acquired.get(export_type, 0.0) + buy_qty
                    exchange_val += cost

        caravan.trade_volume_value = round(exchange_val, 2)
        self.total_regional_trade_value += caravan.trade_volume_value
        dest.lifetime_goods_imported += exchange_val
        logger.info(
            "Caravan %s completed trade at %s: total exchanged volume $%.2f",
            caravan.caravan_id,
            dest.name,
            exchange_val,
        )
        return exchange_val
