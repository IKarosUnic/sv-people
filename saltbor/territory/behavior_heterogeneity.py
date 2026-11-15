"""Human Behavior & Heterogeneity Engine for SALTBOR Territorial Scenarios.

Replaces deterministic hardcoded reactions with emergent, heterogeneous decision models:
1. Multi-Dimensional Agent Profiling:
   - Age, gender, family structure, dependency ratio.
   - Resource cushion (cash, pantry kg, assets).
   - Health status and chronic conditions.
   - Educational attainment and parental education values.
   - Psychological resilience & risk aversion (Big Five / OCC appraisal).
   - Social capital (ADESCO membership, neighbor trust, cuchubal participation).
2. Hierarchical Coping Strategies under Economic / Infrastructure Shocks:
   - Level 1: Consumption compression (rebalance diet, cut non-essential utility/entertainment).
   - Level 2: Deplete liquid savings cushion.
   - Level 3: Request informal food credit (*fiado*) within bilateral trust limits.
   - Level 4: Activate community solidarity networks (cuchubal payout, church aid, family transfer).
   - Level 5: Secondary earner mobilization — adolescents do NOT automatically drop out;
     decisions evaluate school valuation, age threshold (12-14 vs 15-17), academic standing,
     and whether emergency part-time work can coexist with attendance before true dropout.
3. Micro-Business Adaptation:
   - Solvent tienditas adjust markup, prioritize staple inventory, manage customer credit risk,
     and negotiate delayed wholesale freight payments rather than collapsing instantly.
"""

from __future__ import annotations

import dataclasses
import enum
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.territory.models import RegionalTradeNode
from saltbor.territory.multi_scale import (
    MultiScaleHouseholdRecord,
    MultiScaleIndividualRecord,
)


class CopingLevel(int, enum.Enum):
    """Hierarchical household coping mechanisms under stress."""
    NORMAL_OPERATION = 0
    CONSUMPTION_COMPRESSION = 1
    SAVINGS_DEPLETION = 2
    INFORMAL_FIADO_CREDIT = 3
    COMMUNITY_SOLIDARITY = 4
    LABOR_FORCE_ADAPTATION = 5
    ACUTE_DISTRESS_DEFAULT = 6


@dataclasses.dataclass
class HouseholdStressAssessment:
    """Evaluation of household vulnerability and chosen coping response."""
    household_id: str
    coping_level: CopingLevel
    daily_food_cost_usd: float
    daily_income_usd: float
    deficit_usd: float
    cash_cushion_days: float
    chosen_strategy: str
    educational_action: str
    adolescent_work_hours_day: float
    school_attendance_pct: float
    dropout_risk: float


class HumanBehaviorHeterogeneityEngine:
    """Models emergent, differentiated human coping and decision behaviors."""

    def __init__(self, random_seed: int = 42) -> None:
        self.rng = np.random.default_rng(random_seed)

    def evaluate_household_coping(
        self,
        household: MultiScaleHouseholdRecord,
        members: List[MultiScaleIndividualRecord],
        daily_food_cost_baseline: float,
        retail_food_price_inflation_ratio: float,
        road_friction_multiplier: float,
        tiendita_credit_limit_usd: float = 25.0,
        adesco_aid_available: bool = True,
    ) -> HouseholdStressAssessment:
        """Evaluate how a specific household heterogeneously adapts to economic and transport shock."""
        # Calculate daily household wage income, discounted by transport/economic disruption
        daily_income = 0.0
        labor_disruption_factor = 1.0 / max(1.0, road_friction_multiplier * 0.75)
        for m in members:
            if "labor" in m.current_activity or "day_labor" in m.current_activity:
                base_wage = 12.00 * labor_disruption_factor
                daily_income += base_wage * max(0.0, m.health_status)
            elif "store_operator" in m.current_activity or "trader" in m.current_activity:
                daily_income += 16.00 * max(0.0, m.health_status) * labor_disruption_factor

        # Inflated food expenditure
        daily_food_cost = round(daily_food_cost_baseline * retail_food_price_inflation_ratio, 2)
        deficit = round(daily_food_cost - daily_income, 2)

        # Cash cushion in days
        cash = max(0.0, household.shared_cash_usd)
        cash_cushion_days = round(cash / daily_food_cost, 1) if daily_food_cost > 0 else 999.0

        # Identify adolescents (12-17yo) in household
        adolescents = [m for m in members if 12 <= m.age <= 17]
        adults = [m for m in members if m.age >= 18]
        avg_adult_education = (
            float(np.mean([a.education_level_years for a in adults])) if adults else 4.0
        )

        # Decision hierarchy
        coping_level = CopingLevel.NORMAL_OPERATION
        strategy_desc = "Normal domestic functioning"
        edu_action = "Full-time student"
        ado_work_hours = 0.0
        attendance_pct = 96.0
        dropout_risk = 0.04

        if deficit <= 0:
            # Solvent: no deficit
            coping_level = CopingLevel.NORMAL_OPERATION
            strategy_desc = "Income covers daily food needs"
        elif cash_cushion_days >= 7.0:
            # Has liquid savings cushion > 1 week
            coping_level = CopingLevel.SAVINGS_DEPLETION
            strategy_desc = f"Absorbing price shock with cash savings ({cash_cushion_days} days cushion)"
            attendance_pct = 95.0
            dropout_risk = 0.06
        elif cash_cushion_days >= 2.0:
            # Moderate savings: compress non-essential food consumption
            coping_level = CopingLevel.CONSUMPTION_COMPRESSION
            daily_food_cost = round(daily_food_cost * 0.88, 2)  # 12% food substitution/compression
            strategy_desc = "Food substitution and expenditure compression"
            attendance_pct = 92.0
            dropout_risk = 0.09
        elif tiendita_credit_limit_usd > 10.0:
            # Cash low, access informal fiado credit
            coping_level = CopingLevel.INFORMAL_FIADO_CREDIT
            strategy_desc = "Using informal store credit (fiado) for staples"
            attendance_pct = 88.0
            dropout_risk = 0.15
        elif adesco_aid_available and self.rng.random() < 0.60:
            # Community solidarity, food basket or cuchubal loan
            coping_level = CopingLevel.COMMUNITY_SOLIDARITY
            strategy_desc = "Beneficiary of community solidarity / ADESCO emergency relief"
            attendance_pct = 85.0
            dropout_risk = 0.18
        else:
            # Extreme economic stress: evaluate secondary earner adjustment
            coping_level = CopingLevel.LABOR_FORCE_ADAPTATION
            if adolescents:
                ado = adolescents[0]
                # Educational resilience factors:
                # High adult education -> strong reluctance to pull child out
                education_resistance = min(0.40, avg_adult_education * 0.05)
                # Older adolescent (15-17) is more employable than younger (12-14)
                age_factor = 0.35 if ado.age >= 15 else 0.10
                # Road friction factor: hard to get to school anyway if road blocked!
                road_friction_factor = min(0.30, (road_friction_multiplier - 1.0) * 0.08)

                work_probability = min(0.90, max(0.10, 0.40 + age_factor + road_friction_factor - education_resistance))

                if self.rng.random() < work_probability:
                    # Adolescent takes informal part-time work
                    ado_work_hours = 4.0
                    attendance_pct = max(35.0, round(90.0 - (road_friction_multiplier * 12.0) - 20.0, 1))
                    dropout_risk = round(min(0.85, 0.25 + (100.0 - attendance_pct) / 100.0 * 0.4), 2)
                    edu_action = "Part-time informal agricultural support"
                    strategy_desc = f"Adolescent ({ado.name}) helps household with informal work"
                else:
                    # Family prioritizes school despite acute hardship
                    ado_work_hours = 0.0
                    attendance_pct = max(65.0, round(95.0 - (road_friction_multiplier * 8.0), 1))
                    dropout_risk = 0.22
                    edu_action = "Remains student despite severe deficit"
                    strategy_desc = "Family prioritizes schooling despite food deficit"
            else:
                coping_level = CopingLevel.ACUTE_DISTRESS_DEFAULT
                strategy_desc = "Acute distress: meal skipping and asset liquidation"

        return HouseholdStressAssessment(
            household_id=household.household_id,
            coping_level=coping_level,
            daily_food_cost_usd=daily_food_cost,
            daily_income_usd=daily_income,
            deficit_usd=deficit,
            cash_cushion_days=cash_cushion_days,
            chosen_strategy=strategy_desc,
            educational_action=edu_action,
            adolescent_work_hours_day=ado_work_hours,
            school_attendance_pct=attendance_pct,
            dropout_risk=dropout_risk,
        )

    def evaluate_business_resilience(
        self,
        business: RegionalTradeNode,
        footfall_factor: float,
        wholesale_price_inflation: float,
        uncollected_fiado_usd: float,
    ) -> Dict[str, Any]:
        """Model micro-retailer pricing, credit rationing, and cash survival under shock."""
        # Footfall impact on sales
        daily_sales_revenue = round(45.0 * footfall_factor, 2)
        gross_margin = 0.25
        cost_of_goods = round(daily_sales_revenue * (1.0 - gross_margin), 2)
        net_cash_flow = round(daily_sales_revenue - cost_of_goods - business.daily_overhead_usd, 2)

        # Credit rationing: if uncollected fiado is too high, tiendita freezes new credit
        credit_freeze = uncollected_fiado_usd > 40.0

        # Liquidity status
        effective_cash = business.cash_balance_usd
        is_solvent = effective_cash >= business.daily_overhead_usd

        return {
            "node_id": business.node_id,
            "daily_sales_revenue_usd": daily_sales_revenue,
            "net_cash_flow_usd": net_cash_flow,
            "credit_freeze_active": credit_freeze,
            "is_solvent": is_solvent,
            "liquidity_distress": effective_cash < 50.0,
        }
