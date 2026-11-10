"""
Salvadoran Foodways and Culinary Practices Engine (Section 19.3).

Models the authentic culinary culture and microeconomic operations of Salvadoran gastronomy:
- Pupuserías: Masa de maíz vs. masa de arroz (Olocuilta style), ingredients, margins, employment
- Traditional tamales (gallina india, elote, pisques), atoles (elote, shuco con alhuashte)
- Antojitos típicos: yuca con chicharrón, empanadas de plátano, quesadilla salvadoreña
- Intergenerational recipe transmission (abuela -> madre -> hija)
- Real economic unit economics (cost of quesillo, loroco, chicharrón vs. sale price)
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional

from saltbor.datasets.salvadoran import (
    SALVADORAN_FOOD_CATALOG,
    SalvadoranFoodItem,
)


@dataclasses.dataclass
class PupuseriaBusiness:
    """An operational Salvadoran pupusería microenterprise."""
    business_id: str
    owner_uid: str
    name: str
    location_id: str
    dough_specialty: str                  # "masa_de_maiz", "masa_de_arroz", or "both"
    daily_pupusas_sold: int = 150
    average_price_usd: float = 0.85
    unit_cost_usd: float = 0.38           # Quesillo, chicharrón, frijol, curtido, salsa, leña/gas
    family_workers_count: int = 2
    reputation_score: float = 0.75        # Word-of-mouth community rating
    specialty_fillings: list[str] = dataclasses.field(default_factory=lambda: ["revuelta", "queso_loroco", "frijol_queso"])

    @property
    def daily_gross_revenue(self) -> float:
        return round(self.daily_pupusas_sold * self.average_price_usd, 2)

    @property
    def daily_operating_cost(self) -> float:
        return round(self.daily_pupusas_sold * self.unit_cost_usd, 2)

    @property
    def daily_net_profit(self) -> float:
        return round(self.daily_gross_revenue - self.daily_operating_cost, 2)


class SalvadoranFoodwaysEngine:
    """Manages recipes, culinary businesses, and intergenerational food lore."""

    def __init__(self) -> None:
        self._catalog: dict[str, SalvadoranFoodItem] = dict(SALVADORAN_FOOD_CATALOG)
        self._pupuserias: dict[str, PupuseriaBusiness] = {}

    def get_food_item(self, item_id: str) -> Optional[SalvadoranFoodItem]:
        return self._catalog.get(item_id)

    def get_all_food_items(self) -> list[SalvadoranFoodItem]:
        return list(self._catalog.values())

    # -------------------------------------------------------------------------
    # Pupusería Microenterprise Operations
    # -------------------------------------------------------------------------

    def open_pupuseria(
        self,
        business_id: str,
        owner_uid: str,
        name: str,
        location_id: str,
        dough_specialty: str = "masa_de_maiz",
        specialty_fillings: Optional[list[str]] = None,
    ) -> PupuseriaBusiness:
        """Establish a new neighborhood or roadside pupusería."""
        biz = PupuseriaBusiness(
            business_id=business_id,
            owner_uid=owner_uid,
            name=name,
            location_id=location_id,
            dough_specialty=dough_specialty,
            specialty_fillings=specialty_fillings or ["revuelta", "queso_loroco", "frijol_queso"],
        )
        self._pupuserias[business_id] = biz
        return biz

    def simulate_day_trading(
        self,
        business_id: str,
        demand_multiplier: float = 1.0,
    ) -> dict[str, Any]:
        """Simulate a day's sales and margins for a pupusería."""
        biz = self._pupuserias.get(business_id)
        if not biz:
            return {"error": "Business not found"}

        actual_sold = int(biz.daily_pupusas_sold * demand_multiplier)
        gross = round(actual_sold * biz.average_price_usd, 2)
        costs = round(actual_sold * biz.unit_cost_usd, 2)
        profit = round(gross - costs, 2)

        return {
            "business_id": biz.business_id,
            "name": biz.name,
            "pupusas_sold": actual_sold,
            "gross_revenue_usd": gross,
            "ingredient_costs_usd": costs,
            "net_profit_usd": profit,
            "owner_take_home_usd": round(profit * 0.70, 2), # 30% retained for working capital
            "family_helpers_share_usd": round(profit * 0.30, 2),
        }

    # -------------------------------------------------------------------------
    # Intergenerational Transmission
    # -------------------------------------------------------------------------

    def transmit_recipe_knowledge(
        self,
        teacher_uid: str,
        learner_uid: str,
        food_item_id: str,
        teacher_proficiency: float = 0.85,
        relationship_closeness: float = 0.80,
    ) -> dict[str, Any]:
        """Simulate passing culinary tradition from an elder/parent to younger generation."""
        item = self._catalog.get(food_item_id)
        if not item:
            return {"success": False, "reason": "Unknown recipe"}

        # Learning curve bounded by relationship and difficulty
        learning_rate = max(0.2, (relationship_closeness * 0.6) + (teacher_proficiency * 0.4))
        acquired_skill = round(min(0.95, learning_rate * (1.0 - (item.preparation_difficulty * 0.3))), 2)

        return {
            "success": True,
            "food_item": item.name,
            "teacher": teacher_uid,
            "learner": learner_uid,
            "acquired_proficiency": acquired_skill,
            "cultural_affinity_boost": round(item.cultural_salience * 0.15, 3),
            "narrative": f"Aprendió a elaborar {item.name} mediante práctica directa con ingredientes tradicionales.",
        }
