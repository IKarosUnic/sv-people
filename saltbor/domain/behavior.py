"""Contextual Human Behavior Engine for SALTBOR Universal Domain Simulation.

Enables heterogeneous, bounded-rational human choices across varied contexts:
- Bounded rationality & imperfect information.
- Trade-offs between cost, distance, habit, and quality.
- Income elasticity: low liquidity shifts consumption towards cheaper staples or postpones care.
- Explicit non-purchase option (browsing, inspecting prices, choosing not to buy).
- Social influence & recommendations (*boca a boca*).
- Distance decay: spatial friction reduces probability of choosing distant facilities.
- Mistakes, exploration noise, and unexpected choices.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.domain.models import ContextualDecisionOption


class ContextualBehaviorEngine:
    """Evaluates contextual options for synthetic individuals and models realistic decision variability."""

    def __init__(self, exploration_noise: float = 0.05, distance_decay_beta: float = 0.001) -> None:
        self.exploration_noise = exploration_noise
        self.distance_decay_beta = distance_decay_beta  # Exponential decay per meter

    def score_option(
        self,
        option: ContextualDecisionOption,
        agent_money: float,
        agent_hunger: float,
        agent_energy: float,
        agent_personality_traits: Optional[Dict[str, float]] = None,
        is_raining: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> float:
        """Calculate subjective utility score for an action option in context.

        Returns utility value where higher is more preferred.
        """
        traits = agent_personality_traits or {
            "conscientiousness": 0.5,
            "openness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
        }

        # 1. Financial friction (liquidity elasticity)
        # If agent has low money, cost penalizes utility severely; if wealthy, cost friction drops
        financial_pressure = 1.0
        if agent_money < 5.0:
            financial_pressure = 3.0
        elif agent_money < 15.0:
            financial_pressure = 2.0
        elif agent_money >= 40.0:
            financial_pressure = 0.45

        cost_penalty = option.perceived_cost * financial_pressure * 0.40

        # If option requires cash and agent cannot afford it, severe penalty unless fiado/non-purchase
        if option.perceived_cost > agent_money and not option.is_non_purchase:
            cost_penalty += 50.0

        # 2. Distance Friction (Spatial accessibility decay)
        distance_penalty = 1.0 - math.exp(-self.distance_decay_beta * option.distance_meters)
        if is_raining:
            distance_penalty *= 2.0  # Rain exacerbates distance barrier

        # Conscientious agents care more about saving time/distance
        c_weight = traits.get("conscientiousness", 0.5)
        dist_impact = distance_penalty * (1.5 + c_weight)

        # 3. Familiarity & Habit
        # Low openness agents strongly prefer familiar vendors
        o_weight = traits.get("openness", 0.5)
        habit_bonus = option.familiarity_score * (1.5 - o_weight)

        # 4. Social recommendations (word of mouth)
        # Agreeable / extroverted agents respond heavily to recommendations
        social_weight = (traits.get("agreeableness", 0.5) + traits.get("extraversion", 0.5)) / 2.0
        social_bonus = min(1.0, option.social_recommendations * 0.25) * social_weight * 1.2

        # 5. Base Benefit
        base_benefit = option.perceived_benefit

        # 6. Non-purchase rationality
        # If prices are deemed too high relative to perceived benefit, non-purchase utility rises
        if option.is_non_purchase:
            # Browsing or leaving without buying has positive baseline utility when cash is low
            net_utility = 0.80 + (financial_pressure * 0.40) - (agent_hunger * 0.4)
        else:
            net_utility = base_benefit + habit_bonus + social_bonus - cost_penalty - dist_impact

        # 7. Add exploration noise & bounded-rational cognitive error
        noise_gen = rng or np.random.default_rng(42)
        noise = float(noise_gen.normal(0.0, self.exploration_noise))
        final_score = net_utility + noise

        option.utility_score = final_score
        option.reasoning = (
            f"benefit={base_benefit:.2f}, cost_pen={cost_penalty:.2f}, "
            f"dist_pen={dist_impact:.2f}, habit={habit_bonus:.2f}, social={social_bonus:.2f}"
        )
        return final_score

    def choose_best_option(
        self,
        options: List[ContextualDecisionOption],
        agent_money: float,
        agent_hunger: float,
        agent_energy: float,
        agent_personality_traits: Optional[Dict[str, float]] = None,
        is_raining: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> ContextualDecisionOption:
        """Select the highest scored contextual option among alternatives."""
        if not options:
            raise ValueError("No options provided for contextual decision.")

        scored_options = []
        for opt in options:
            score = self.score_option(
                opt,
                agent_money=agent_money,
                agent_hunger=agent_hunger,
                agent_energy=agent_energy,
                agent_personality_traits=agent_personality_traits,
                is_raining=is_raining,
                rng=rng,
            )
            scored_options.append((score, opt))

        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

    def evaluate_food_vendor_choice(
        self,
        vendors: List[Dict[str, Any]],
        agent_money: float,
        agent_hunger: float,
        agent_personality: Optional[Dict[str, float]] = None,
        is_raining: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> ContextualDecisionOption:
        """Simulate realistic customer choice among competing food vendors (pupuserías, stalls, restaurants).

        Includes the realistic possibility of deciding NOT to buy (leaving without purchase).
        """
        options: List[ContextualDecisionOption] = []

        for v in vendors:
            v_id = str(v.get("vendor_id", "unknown"))
            v_name = v.get("name", "Vendor")
            avg_price = float(v.get("average_price", 2.0))
            quality = float(v.get("quality_score", 0.7))
            dist_m = float(v.get("distance_meters", 100.0))
            familiarity = float(v.get("familiarity", 0.3))
            recs = int(v.get("recommendations", 0))

            options.append(
                ContextualDecisionOption(
                    option_id=f"buy_at_{v_id}",
                    activity_id="food.visit_restaurant",
                    target_entity_id=v_id,
                    perceived_cost=avg_price,
                    perceived_benefit=quality * 3.0 + (agent_hunger * 2.0),
                    distance_meters=dist_m,
                    familiarity_score=familiarity,
                    social_recommendations=recs,
                    is_non_purchase=False,
                )
            )

        # Always include the non-purchase / walk away option
        options.append(
            ContextualDecisionOption(
                option_id="walk_away_no_purchase",
                activity_id="commerce.browse_without_buying",
                target_entity_id=None,
                perceived_cost=0.0,
                perceived_benefit=0.20,
                distance_meters=0.0,
                familiarity_score=0.5,
                social_recommendations=0,
                is_non_purchase=True,
            )
        )

        return self.choose_best_option(
            options,
            agent_money=agent_money,
            agent_hunger=agent_hunger,
            agent_energy=0.7,
            agent_personality_traits=agent_personality,
            is_raining=is_raining,
            rng=rng,
        )

    def evaluate_education_vs_work_tradeoff(
        self,
        household_wealth: float,
        distance_to_school_meters: float,
        student_age: int,
        daily_wage_potential: float = 6.0,
        scholarship_active: bool = False,
        transport_provided: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> ContextualDecisionOption:
        """Simulate trade-off between school attendance and informal labor participation.

        Reflects household economic distress and distance barriers.
        """
        options: List[ContextualDecisionOption] = []

        # Option A: Attend school
        school_cost = 0.50 if not scholarship_active else 0.0
        eff_dist = 50.0 if transport_provided else distance_to_school_meters
        options.append(
            ContextualDecisionOption(
                option_id="attend_school",
                activity_id="education.attend_school",
                perceived_cost=school_cost,
                perceived_benefit=3.5 if student_age < 18 else 2.5,
                distance_meters=eff_dist,
                familiarity_score=0.8,
                is_non_purchase=False,
            )
        )

        # Option B: Informal labor to help household liquidity
        labor_benefit = 1.0 + (daily_wage_potential * 0.4)
        if household_wealth < 30.0:
            labor_benefit += 3.0  # Extreme economic distress triggers youth labor

        options.append(
            ContextualDecisionOption(
                option_id="work_informal_labor",
                activity_id="commerce.work",
                perceived_cost=0.0,
                perceived_benefit=labor_benefit,
                distance_meters=200.0,
                familiarity_score=0.4,
                is_non_purchase=False,
            )
        )

        return self.choose_best_option(
            options,
            agent_money=household_wealth,
            agent_hunger=0.3,
            agent_energy=0.8,
            rng=rng,
        )
