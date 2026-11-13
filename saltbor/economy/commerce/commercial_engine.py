"""Commercial Establishments, Consumer Visits & Retail Dynamics (Phase 1.5).

Models authentic commercial life in El Salvador:
- Distinction between real verified GIS establishments and simulated microenterprises.
- Full consumer visit intents: window shopping, browsing, price comparison, purchasing, dining.
- Decision to purchase depends on budget, preferences, perceived value, urgency, stock, and competing obligations.
- Zero-purchase visits: individuals can browse, learn prices, socialise, and leave without spending money.
- Complete double-entry cash flow: buyer cash transfers to store cash box without arbitrary minting or deletion.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from saltbor.core.types import ActivityType, HumanID, LocationID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType

logger = logging.getLogger(__name__)


class EstablishmentType(str, enum.Enum):
    """Classification of commercial establishments."""
    PULPERIA = "pulperia"                      # Corner store / tiendita
    MERCADO_STALL = "mercado_stall"            # Stall inside municipal market
    COMEDOR_PUPUSERIA = "comedor_pupuseria"    # Dining room / pupusería
    ARTISAN_WORKSHOP = "artisan_workshop"      # Carpentry, smithy, ceramics
    HEALTH_CLINIC = "health_clinic"            # Pharmacy / clinic post
    ENTERTAINMENT_VENUE = "entertainment_venue"# Billiards, plaza kiosk, sports pitch
    STREET_VENDOR = "street_vendor"            # Mobile canastera / ambulante


class VisitIntent(str, enum.Enum):
    """Consumer intent upon visiting a commercial establishment."""
    WINDOW_SHOP = "window_shop"          # Viewing from outside / displays
    BROWSE = "browse"                    # Walking through, inspecting items out of curiosity
    COMPARE_PRICES = "compare_prices"    # Checking prices to optimize future purchases
    PURCHASE = "purchase"                # Intending to buy goods if conditions met
    DINE = "dine"                        # Eating prepared meals at eatery
    SEEK_SERVICE = "seek_service"        # Haircut, health check, repair
    ACCOMPANY = "accompany"              # Accompanying a friend or relative


@dataclasses.dataclass
class CommercialProduct:
    """A commodity, food item, or service offered by an establishment."""
    product_id: str
    name: str
    category: str                        # "staple_food", "prepared_meal", "household", "craft", "service"
    unit_price_usd: float
    current_stock: float
    unit_label: str = "unidad"           # "lb", "unidad", "plato", "servicio"
    quality: float = 0.70                # 0.0 to 1.0


@dataclasses.dataclass
class CommercialEstablishment:
    """A physical or informal commercial establishment."""
    establishment_id: str
    name: str
    establishment_type: EstablishmentType
    location_id: LocationID
    owner_uid: Optional[str] = None
    is_verified_real: bool = False       # True = verified real-world GIS location; False = simulated business

    # Inventory and Catalog
    catalog: dict[str, CommercialProduct] = dataclasses.field(default_factory=dict)
    cash_box_usd: float = 80.0
    daily_sales_volume_usd: float = 0.0
    operating_cost_per_day: float = 4.0

    # Operational Constraints
    opening_hours: tuple[int, int] = (6, 20)  # (open_hour, close_hour)
    capacity: int = 20
    current_occupants: list[str] = dataclasses.field(default_factory=list)
    reputation: float = 0.75             # 0.0 to 1.0

    # Analytics & Metrics
    total_lifetime_revenue: float = 0.0
    daily_visitors: int = 0
    daily_browsers_without_purchase: int = 0
    daily_purchasers: int = 0

    def is_open_at_hour(self, hour: int) -> bool:
        start, end = self.opening_hours
        if start <= end:
            return start <= hour < end
        return hour >= start or hour < end


@dataclasses.dataclass
class VisitOutcome:
    """Detailed result of an individual's commercial visit."""
    agent_uid: str
    establishment_id: str
    intent: VisitIntent
    purchased: bool
    total_spent_usd: float
    items_bought: dict[str, float] = dataclasses.field(default_factory=dict)
    reasoning: str = ""
    social_encounters: list[str] = dataclasses.field(default_factory=list)
    information_gained: dict[str, float] = dataclasses.field(default_factory=dict)


class CommercialEngine:
    """Manages commercial establishments, consumer behavior, and realistic retail dynamics."""

    def __init__(self) -> None:
        self._establishments: dict[str, CommercialEstablishment] = {}
        self.visit_history: list[VisitOutcome] = []

    def register_establishment(self, establishment: CommercialEstablishment) -> None:
        """Register a commercial establishment."""
        self._establishments[establishment.establishment_id] = establishment

    def get_establishment(self, establishment_id: str) -> Optional[CommercialEstablishment]:
        return self._establishments.get(establishment_id)

    def get_all_establishments(self) -> list[CommercialEstablishment]:
        return list(self._establishments.values())

    def get_by_type(self, est_type: EstablishmentType) -> list[CommercialEstablishment]:
        return [e for e in self._establishments.values() if e.establishment_type == est_type]

    def get_verified_real(self) -> list[CommercialEstablishment]:
        """Return only verified real GIS locations."""
        return [e for e in self._establishments.values() if e.is_verified_real]

    def get_simulated(self) -> list[CommercialEstablishment]:
        """Return explicitly tagged simulated establishments."""
        return [e for e in self._establishments.values() if not e.is_verified_real]

    # -------------------------------------------------------------------------
    # Consumer Visit Evaluation & Execution
    # -------------------------------------------------------------------------

    def execute_visit(
        self,
        agent: Any,
        establishment_id: str,
        intent: VisitIntent,
        current_hour: int = 10,
        requested_items: Optional[list[str]] = None,
        max_budget: Optional[float] = None,
        co_located_agents: Optional[list[str]] = None,
    ) -> VisitOutcome:
        """Execute a consumer visit respecting bounded rationality, budget constraints, and autonomy.
        
        Crucial requirement: visiting does NOT automatically trigger a purchase.
        Agents can window-shop, browse, compare prices, or leave empty-handed.
        """
        est = self._establishments.get(establishment_id)
        if not est:
            return VisitOutcome(
                agent_uid=str(agent.uid),
                establishment_id=establishment_id,
                intent=intent,
                purchased=False,
                total_spent_usd=0.0,
                reasoning="Establishment does not exist.",
            )

        # 1. Opening hours check
        if not est.is_open_at_hour(current_hour):
            return VisitOutcome(
                agent_uid=str(agent.uid),
                establishment_id=establishment_id,
                intent=intent,
                purchased=False,
                total_spent_usd=0.0,
                reasoning=f"Establishment '{est.name}' is closed at hour {current_hour}:00.",
            )

        est.daily_visitors += 1

        # 2. Check for social encounters with co-located customers
        encounters: list[str] = []
        if co_located_agents:
            encounters = [uid for uid in co_located_agents if uid != str(agent.uid)][:3]

        # Read agent parameters
        agent_money = getattr(agent.physical_state, "money", 0.0)
        spending_limit = min(agent_money, max_budget) if max_budget is not None else agent_money
        hunger = getattr(agent.physical_state, "hunger", 0.0)
        personality = getattr(agent, "personality", None)
        frugality = personality.get_trait("conscientiousness") if personality else 0.5
        openness = personality.get_trait("openness") if personality else 0.5

        # ---------------------------------------------------------------------
        # Scenario A: WINDOW SHOPPING (Outside, zero spend)
        # ---------------------------------------------------------------------
        if intent == VisitIntent.WINDOW_SHOP:
            est.daily_browsers_without_purchase += 1
            observed_prices = {
                pid: p.unit_price_usd
                for pid, p in list(est.catalog.items())[:4]
            }
            return VisitOutcome(
                agent_uid=str(agent.uid),
                establishment_id=establishment_id,
                intent=intent,
                purchased=False,
                total_spent_usd=0.0,
                reasoning=f"Window shopped outside {est.name}; enjoyed displays without entering.",
                social_encounters=encounters,
                information_gained=observed_prices,
            )

        # ---------------------------------------------------------------------
        # Scenario B: BROWSING (Inside store, inspecting items, usually $0 spend)
        # ---------------------------------------------------------------------
        if intent == VisitIntent.BROWSE:
            est.daily_browsers_without_purchase += 1
            observed_prices = {pid: p.unit_price_usd for pid, p in est.catalog.items()}

            # Agent browses out of curiosity
            reasoning = f"Browsed goods at {est.name} out of curiosity; decided not to buy today."
            outcome = VisitOutcome(
                agent_uid=str(agent.uid),
                establishment_id=establishment_id,
                intent=intent,
                purchased=False,
                total_spent_usd=0.0,
                reasoning=reasoning,
                social_encounters=encounters,
                information_gained=observed_prices,
            )
            self.visit_history.append(outcome)
            return outcome

        # ---------------------------------------------------------------------
        # Scenario C: PRICE COMPARISON (Gathering market intelligence, $0 spend)
        # ---------------------------------------------------------------------
        if intent == VisitIntent.COMPARE_PRICES:
            est.daily_browsers_without_purchase += 1
            observed_prices = {pid: p.unit_price_usd for pid, p in est.catalog.items()}
            outcome = VisitOutcome(
                agent_uid=str(agent.uid),
                establishment_id=establishment_id,
                intent=intent,
                purchased=False,
                total_spent_usd=0.0,
                reasoning=f"Surveyed prices at {est.name} to compare market value against other vendors.",
                social_encounters=encounters,
                information_gained=observed_prices,
            )
            self.visit_history.append(outcome)
            return outcome

        # ---------------------------------------------------------------------
        # Scenario D: DINING OUT (Eatery / Comedor / Pupusería)
        # ---------------------------------------------------------------------
        if intent == VisitIntent.DINE:
            meal_product = next(
                (p for p in est.catalog.values() if p.category in ("prepared_meal", "staple_food")),
                None,
            )
            cost = meal_product.unit_price_usd if meal_product else 2.00

            if spending_limit < cost:
                est.daily_browsers_without_purchase += 1
                outcome = VisitOutcome(
                    agent_uid=str(agent.uid),
                    establishment_id=establishment_id,
                    intent=intent,
                    purchased=False,
                    total_spent_usd=0.0,
                    reasoning=f"Wanted to dine at {est.name} but meal costs ${cost:.2f} and funds are only ${spending_limit:.2f}.",
                    social_encounters=encounters,
                )
                self.visit_history.append(outcome)
                return outcome

            # Complete dining purchase
            agent.physical_state.money = round(agent_money - cost, 2)
            est.cash_box_usd += cost
            est.daily_sales_volume_usd += cost
            est.total_lifetime_revenue += cost
            est.daily_purchasers += 1

            # Satiate hunger
            agent.physical_state.hunger = max(0.0, hunger - 0.45)
            agent.physical_state.energy = min(1.0, agent.physical_state.energy + 0.10)

            outcome = VisitOutcome(
                agent_uid=str(agent.uid),
                establishment_id=establishment_id,
                intent=intent,
                purchased=True,
                total_spent_usd=cost,
                items_bought={meal_product.name if meal_product else "Plato de Comida": 1.0},
                reasoning=f"Dined at {est.name}; enjoyed hot meal for ${cost:.2f}.",
                social_encounters=encounters,
            )
            self.visit_history.append(outcome)
            return outcome

        # ---------------------------------------------------------------------
        # Scenario E: PURCHASING GOODS (Deliberate retail transaction)
        # ---------------------------------------------------------------------
        if intent == VisitIntent.PURCHASE:
            targets = requested_items or list(est.catalog.keys())
            total_spent = 0.0
            items_bought: dict[str, float] = {}

            # Reserve cash buffer for rent/emergencies based on frugality
            reservation_buffer = 5.0 * frugality
            usable_cash = max(0.0, spending_limit - reservation_buffer)

            for item_id in targets:
                prod = est.catalog.get(item_id)
                if not prod or prod.current_stock <= 0:
                    continue

                # Willingness to pay calculation
                perceived_value = prod.unit_price_usd * (1.0 + (0.2 * openness) - (0.15 * frugality))
                if perceived_value < prod.unit_price_usd:
                    continue  # Perceived price is too expensive for consumer

                if usable_cash >= prod.unit_price_usd and prod.current_stock >= 1.0:
                    prod.current_stock -= 1.0
                    total_spent += prod.unit_price_usd
                    usable_cash -= prod.unit_price_usd
                    items_bought[prod.name] = items_bought.get(prod.name, 0.0) + 1.0

            if total_spent > 0.0:
                agent.physical_state.money = round(agent_money - total_spent, 2)
                est.cash_box_usd += total_spent
                est.daily_sales_volume_usd += total_spent
                est.total_lifetime_revenue += total_spent
                est.daily_purchasers += 1

                outcome = VisitOutcome(
                    agent_uid=str(agent.uid),
                    establishment_id=establishment_id,
                    intent=intent,
                    purchased=True,
                    total_spent_usd=round(total_spent, 2),
                    items_bought=items_bought,
                    reasoning=f"Purchased {len(items_bought)} items at {est.name} for ${total_spent:.2f}.",
                    social_encounters=encounters,
                )
            else:
                est.daily_browsers_without_purchase += 1
                outcome = VisitOutcome(
                    agent_uid=str(agent.uid),
                    establishment_id=establishment_id,
                    intent=intent,
                    purchased=False,
                    total_spent_usd=0.0,
                    reasoning=f"Visited {est.name} to buy goods, but items were unavailable, overpriced, or exceeded budget constraint.",
                    social_encounters=encounters,
                )

            self.visit_history.append(outcome)
            return outcome

        # Default fallback
        return VisitOutcome(
            agent_uid=str(agent.uid),
            establishment_id=establishment_id,
            intent=intent,
            purchased=False,
            total_spent_usd=0.0,
            reasoning="Accompanied companion or completed informal visit.",
            social_encounters=encounters,
        )

    # -------------------------------------------------------------------------
    # Daily Accounting & Solvency Evaluation
    # -------------------------------------------------------------------------

    def execute_daily_accounting(self, current_tick: Tick) -> dict[str, Any]:
        """Deduct daily overhead, reset daily counters, and assess commercial solvency."""
        total_revenue = 0.0
        total_visitors = 0
        total_browsers_no_buy = 0
        total_buyers = 0

        for est in self._establishments.values():
            overhead = est.operating_cost_per_day
            est.cash_box_usd = round(est.cash_box_usd - overhead, 2)
            total_revenue += est.daily_sales_volume_usd
            total_visitors += est.daily_visitors
            total_browsers_no_buy += est.daily_browsers_without_purchase
            total_buyers += est.daily_purchasers

            # Reset daily counters
            est.daily_sales_volume_usd = 0.0
            est.daily_visitors = 0
            est.daily_browsers_without_purchase = 0
            est.daily_purchasers = 0

        return {
            "tick": current_tick,
            "establishments_count": len(self._establishments),
            "total_daily_revenue_usd": round(total_revenue, 2),
            "total_visitors": total_visitors,
            "browsers_without_purchase": total_browsers_no_buy,
            "actual_purchasers": total_buyers,
        }
