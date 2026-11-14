"""Food, Gastronomy, and Consumer Activity Domain for SALTBOR.

Simulates the food ecosystem of El Salvador:
- Pupuserías, comedores populares, street food stalls (*carretones*), bakeries (*panaderías*),
  restaurants, and municipal food markets.
- Product inventory tracking (maize flour, rice flour, quesillo, chicharrón, loroco, beans, vegetables, gas).
- Dynamic consumer behavior: menu inspection, price sensitivity, word-of-mouth recommendations,
  and the critical rational choice of *not purchasing* when prices or queues exceed perceived utility.
- Analytical queries for entrepreneurs and municipal planners:
  * "What food establishments could work in this area?"
  * "What food is already being sold here?"
  * "Which products appear to have unmet demand?"
  * "What would happen if I opened a pupusería here?"
  * "How would a price increase affect consumers?"
"""

from __future__ import annotations

import dataclasses
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.domain.behavior import ContextualBehaviorEngine
from saltbor.domain.models import DomainCategory, DomainDefinition, DomainStatus

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FoodEstablishment:
    establishment_id: str
    name: str
    establishment_type: str  # "pupuseria", "comedor", "puesto_callejero", "panaderia", "restaurante"
    latitude: float
    longitude: float
    owner_id: str
    menu: Dict[str, float]  # Item name -> Price in USD
    inventory: Dict[str, float]  # Ingredient -> Units available
    daily_fixed_cost: float = 8.0  # Gas, rental, firewood, municipal permit
    cash_balance: float = 50.0
    quality_score: float = 0.75  # 0.0 to 1.0
    reputation: float = 0.50
    daily_customers_served: int = 0
    daily_revenue: float = 0.0
    is_open: bool = True
    active_promotions: Dict[str, float] = dataclasses.field(default_factory=dict)


class FoodActivityDomain:
    """Specialized domain orchestrating culinary commerce and consumer dynamics."""

    def __init__(self, behavior_engine: Optional[ContextualBehaviorEngine] = None) -> None:
        self.behavior_engine = behavior_engine or ContextualBehaviorEngine()
        self.establishments: Dict[str, FoodEstablishment] = {}
        self.consumer_recommendations: Dict[str, int] = {}  # establishment_id -> count of recommendations
        self._register_default_establishments()

    def get_definition(self) -> DomainDefinition:
        """Return formal DomainDefinition contract."""
        return DomainDefinition(
            domain_id="food_gastronomy",
            name="Food, Gastronomy and Consumer Activity",
            category=DomainCategory.FOOD,
            purpose="Simulate the culinary economy, consumer choices, and viability of food micro-enterprises in El Salvador.",
            geographic_scope="El Salvador",
            resources=["maize_dough", "rice_flour", "quesillo", "chicharron", "beans", "vegetables", "cooking_gas"],
            infrastructure=["pupuseria", "comedor", "mercado_municipal", "puesto_callejero", "panaderia"],
            activities=[
                "food.buy_food",
                "food.prepare_meals",
                "food.eat_outside",
                "food.visit_restaurant",
                "food.compare_prices",
                "food.recommend_establishment",
            ],
            entities=["FoodEstablishment", "Menu", "IngredientInventory"],
            indicators=["daily_foot_traffic", "unmet_demand_ratio", "average_meal_price", "solvency_rate"],
            possible_interventions=["new_pupuseria_opening", "price_subsidy", "supply_cost_shock"],
            data_sources=["OSM_establishments", "BCR_canasta_basica", "MINEC_gas_prices"],
            uncertainties=["fluctuation_in_ingredient_prices", "weather_impact_on_street_dining"],
            version="1.0.0",
            status=DomainStatus.ACTIVE,
        )

    def register_establishment(self, establishment: FoodEstablishment) -> None:
        """Register a food establishment into the domain."""
        self.establishments[establishment.establishment_id] = establishment

    def simulate_consumer_visit(
        self,
        consumer_money: float,
        consumer_hunger: float,
        consumer_lat: float,
        consumer_lon: float,
        consumer_traits: Optional[Dict[str, float]] = None,
        is_raining: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> Dict[str, Any]:
        """Simulate a single consumer deciding where and what to eat, or choosing not to buy."""
        # 1. Build list of candidate vendors with distances
        vendors = []
        for est_id, est in self.establishments.items():
            if not est.is_open:
                continue

            # Haversine distance approximation in meters
            d_lat = (est.latitude - consumer_lat) * 111000.0
            d_lon = (est.longitude - consumer_lon) * 111000.0 * math.cos(math.radians(consumer_lat))
            dist_m = math.sqrt(d_lat**2 + d_lon**2)

            # Average menu price
            avg_price = float(np.mean(list(est.menu.values()))) if est.menu else 2.0
            recs = self.consumer_recommendations.get(est_id, 0)

            vendors.append({
                "vendor_id": est_id,
                "name": est.name,
                "average_price": avg_price,
                "quality_score": est.quality_score,
                "distance_meters": dist_m,
                "familiarity": min(1.0, 0.2 + (recs * 0.1)),
                "recommendations": recs,
            })

        if not vendors:
            return {"decision": "none_available", "purchased": False, "spent": 0.0}

        # 2. Evaluate contextual choice
        chosen_opt = self.behavior_engine.evaluate_food_vendor_choice(
            vendors=vendors,
            agent_money=consumer_money,
            agent_hunger=consumer_hunger,
            agent_personality=consumer_traits,
            is_raining=is_raining,
            rng=rng,
        )

        if chosen_opt.is_non_purchase or not chosen_opt.target_entity_id:
            return {
                "decision": "walked_away_without_buying",
                "purchased": False,
                "spent": 0.0,
                "reasoning": chosen_opt.reasoning,
            }

        est = self.establishments[chosen_opt.target_entity_id]
        meal_price = chosen_opt.perceived_cost

        # Execute transaction with accounting conservation
        est.daily_customers_served += 1
        est.daily_revenue += meal_price
        est.cash_balance += meal_price

        # Word-of-mouth recommendation chance
        if est.quality_score >= 0.80 and (rng or np.random.default_rng(42)).random() < 0.35:
            self.consumer_recommendations[est.establishment_id] = (
                self.consumer_recommendations.get(est.establishment_id, 0) + 1
            )

        return {
            "decision": "purchased",
            "establishment_id": est.establishment_id,
            "establishment_name": est.name,
            "purchased": True,
            "spent": meal_price,
            "reasoning": chosen_opt.reasoning,
        }

    # =========================================================================
    # Analytical Decision Support Queries
    # =========================================================================

    def query_food_sold_in_area(self, center_lat: float, center_lon: float, radius_meters: float = 1000.0) -> List[Dict[str, Any]]:
        """Answer: 'What food is already being sold here?'"""
        results = []
        for est in self.establishments.values():
            d_lat = (est.latitude - center_lat) * 111000.0
            d_lon = (est.longitude - center_lon) * 111000.0 * math.cos(math.radians(center_lat))
            dist = math.sqrt(d_lat**2 + d_lon**2)
            if dist <= radius_meters:
                results.append({
                    "establishment_id": est.establishment_id,
                    "name": est.name,
                    "type": est.establishment_type,
                    "distance_meters": round(dist, 1),
                    "menu": est.menu,
                    "quality": est.quality_score,
                })
        return sorted(results, key=lambda x: x["distance_meters"])

    def query_unmet_demand(self, center_lat: float, center_lon: float, radius_meters: float = 1000.0) -> Dict[str, Any]:
        """Answer: 'Which products appear to have unmet demand?'"""
        nearby = self.query_food_sold_in_area(center_lat, center_lon, radius_meters)
        food_types_present = set(e["type"] for e in nearby)

        all_popular_foodways = [
            ("pupuseria", "Pupusas tradicionales (revueltas, queso, frijol con queso)"),
            ("comedor", "Almuerzos caseros / comida a la vista (plato del día)"),
            ("panaderia", "Pan dulce tradicional (quesadillas, salpores, cemitas)"),
            ("puesto_callejero", "Antojitos de tarde (yuca frita, empanadas, nuegados)"),
        ]

        unmet = []
        for f_type, desc in all_popular_foodways:
            if f_type not in food_types_present:
                unmet.append({"category": f_type, "description": desc, "competition_level": "None (High Opportunity)"})
            else:
                count = sum(1 for e in nearby if e["type"] == f_type)
                if count <= 1:
                    unmet.append({"category": f_type, "description": desc, "competition_level": "Low (1 existing vendor)"})

        return {
            "radius_analyzed_meters": radius_meters,
            "existing_vendors_count": len(nearby),
            "unmet_demand_categories": unmet,
            "estimated_foot_traffic_density": "MODERATE_URBAN",
        }

    def simulate_new_pupuseria_scenario(
        self,
        target_lat: float,
        target_lon: float,
        menu: Optional[Dict[str, float]] = None,
        daily_fixed_cost: float = 10.0,
        simulated_days: int = 7,
        potential_daily_eaters: int = 35,
    ) -> Dict[str, Any]:
        """Answer: 'What would happen if I opened a pupusería here?'"""
        test_menu = menu or {"pupusa_revuelta": 0.85, "pupusa_queso": 1.00, "refresco_natural": 0.75}
        avg_price = float(np.mean(list(test_menu.values())))

        # Inspect existing competition
        nearby = self.query_food_sold_in_area(target_lat, target_lon, radius_meters=600.0)
        direct_competitors = sum(1 for e in nearby if e["type"] == "pupuseria")

        # Estimate capture rate based on spatial competition
        base_capture_rate = 0.25 / max(1.0, float(direct_competitors + 1))
        rng = np.random.default_rng(42)

        total_customers = 0
        total_revenue = 0.0
        total_cost = daily_fixed_cost * simulated_days

        for _ in range(simulated_days):
            daily_customers = int(rng.poisson(potential_daily_eaters * base_capture_rate))
            # Average spending per customer = 2 pupusas + 1 drink ~ $2.50
            daily_rev = daily_customers * (avg_price * 2.5)
            total_customers += daily_customers
            total_revenue += daily_rev

        net_profit = total_revenue - total_cost
        is_viable = net_profit > 0

        return {
            "scenario": "new_pupuseria_opening",
            "location": {"lat": target_lat, "lon": target_lon},
            "direct_competitors_within_600m": direct_competitors,
            "simulated_days": simulated_days,
            "estimated_total_customers": total_customers,
            "estimated_average_daily_customers": round(total_customers / simulated_days, 1),
            "estimated_revenue_usd": round(total_revenue, 2),
            "estimated_operating_costs_usd": round(total_cost, 2),
            "estimated_net_profit_usd": round(net_profit, 2),
            "commercially_viable": is_viable,
            "risk_assessment": "Low risk with differentiated hygiene and quality" if is_viable else "High risk due to vendor saturation",
            "uncertainty_note": "Subject to ingredient inflation and daily weather fluctuations.",
        }

    def simulate_price_increase_elasticity(
        self,
        establishment_id: str,
        price_multiplier: float = 1.25,
        test_customers: int = 50,
    ) -> Dict[str, Any]:
        """Answer: 'How would a price increase affect consumers?'"""
        est = self.establishments.get(establishment_id)
        if not est:
            raise ValueError(f"Establishment '{establishment_id}' not found.")

        # Baseline run
        base_bought = 0
        base_revenue = 0.0
        rng = np.random.default_rng(42)

        for _ in range(test_customers):
            c_money = float(rng.uniform(1.0, 15.0))
            c_hunger = float(rng.uniform(0.4, 0.9))
            res = self.simulate_consumer_visit(
                consumer_money=c_money,
                consumer_hunger=c_hunger,
                consumer_lat=est.latitude,
                consumer_lon=est.longitude,
                rng=rng,
            )
            if res.get("purchased") and res.get("establishment_id") == est.establishment_id:
                base_bought += 1
                base_revenue += res.get("spent", 0.0)

        # Increased price run
        original_menu = dict(est.menu)
        est.menu = {item: round(p * price_multiplier, 2) for item, p in original_menu.items()}

        shock_bought = 0
        shock_revenue = 0.0
        for _ in range(test_customers):
            c_money = float(rng.uniform(1.0, 15.0))
            c_hunger = float(rng.uniform(0.4, 0.9))
            res = self.simulate_consumer_visit(
                consumer_money=c_money,
                consumer_hunger=c_hunger,
                consumer_lat=est.latitude,
                consumer_lon=est.longitude,
                rng=rng,
            )
            if res.get("purchased") and res.get("establishment_id") == est.establishment_id:
                shock_bought += 1
                shock_revenue += res.get("spent", 0.0)

        # Restore menu
        est.menu = original_menu

        demand_delta = (shock_bought - base_bought) / max(1, base_bought)
        price_delta = price_multiplier - 1.0
        elasticity = demand_delta / price_delta if price_delta != 0 else 0.0

        return {
            "establishment_id": establishment_id,
            "price_increase_ratio": price_multiplier,
            "baseline_customers_purchased": base_bought,
            "shock_customers_purchased": shock_bought,
            "customer_loss_count": max(0, base_bought - shock_bought),
            "demand_elasticity": round(elasticity, 2),
            "baseline_revenue_usd": round(base_revenue, 2),
            "shock_revenue_usd": round(shock_revenue, 2),
            "revenue_net_change_usd": round(shock_revenue - base_revenue, 2),
            "strategic_recommendation": (
                "Price increase is profitable despite lower volume"
                if shock_revenue > base_revenue
                else "Price increase destroys revenue due to high price elasticity and consumer defection"
            ),
        }

    def _register_default_establishments(self) -> None:
        """Seed realistic initial establishments situated in San Salvador Centro."""
        self.register_establishment(
            FoodEstablishment(
                establishment_id="pupuseria_dona_carmen",
                name="Pupusería Doña Carmen",
                establishment_type="pupuseria",
                latitude=13.6985,
                longitude=-89.2245,
                owner_id="human_carmen_1",
                menu={"pupusa_revuelta": 0.80, "pupusa_queso": 0.90, "pupusa_loroco": 1.00, "horchata": 0.75},
                inventory={"maize_dough": 50.0, "quesillo": 20.0, "chicharron": 15.0, "beans": 15.0},
                quality_score=0.88,
                daily_fixed_cost=9.0,
            )
        )
        self.register_establishment(
            FoodEstablishment(
                establishment_id="comedor_el_centro",
                name="Comedor Popular El Centro",
                establishment_type="comedor",
                latitude=13.6992,
                longitude=-89.2250,
                owner_id="human_marta_2",
                menu={"almuerzo_casero": 3.00, "sopa_de_res": 3.50, "fresco_tamarindo": 0.50},
                inventory={"rice": 30.0, "meat": 15.0, "vegetables": 25.0},
                quality_score=0.78,
                daily_fixed_cost=12.0,
            )
        )
        self.register_establishment(
            FoodEstablishment(
                establishment_id="puesto_calle_ruben_dario",
                name="Carretón de Antojitos Rubén Darío",
                establishment_type="puesto_callejero",
                latitude=13.6978,
                longitude=-89.2230,
                owner_id="human_pedro_3",
                menu={"yuca_con_chicharron": 1.50, "empanada_platano": 0.40, "atol_de_elote": 0.75},
                inventory={"yuca": 25.0, "plantains": 30.0, "corn": 20.0},
                quality_score=0.72,
                daily_fixed_cost=4.0,
            )
        )
