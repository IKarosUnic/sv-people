"""Formal cognitive decision architecture based on Multi-Attribute Utility Theory (MAUT).

Separates:
1. Internal state (needs, energy, funds, physical condition)
2. Beliefs about the world (locations, prices, availability)
3. Available information (sensory perception, nearby peers)
4. Decision preferences (Schwartz values, personality traits, risk discount)
5. Available candidate actions
6. Estimated consequences (predicted state deltas and multi-attribute utilities)
7. Selected action (bounded rational selection)
8. Actual outcome
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
import numpy as np

from saltbor.core.types import ActivityType, HumanID, LocationID, NeedType


@dataclasses.dataclass
class InternalState:
    """True internal physiological and psychological state of the individual."""

    energy: float
    hunger: float
    health: float
    money: float
    needs: dict[NeedType, float]
    age_years: float = 25.0
    stage: str = "adulthood"


@dataclasses.dataclass
class WorldBeliefs:
    """Individual's subjective beliefs about the world state and availability."""

    known_locations: dict[str, bool] = dataclasses.field(default_factory=dict) # loc_id -> is_open
    estimated_food_cost: float = 5.0
    estimated_tool_cost: float = 25.0
    location_aversions: dict[LocationID, float] = dataclasses.field(default_factory=dict)
    location_affinities: dict[LocationID, float] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class InformationState:
    """Information currently accessible via perception and observation."""

    current_location_id: Optional[LocationID]
    available_activities: list[ActivityType]
    nearby_humans: list[HumanID]
    is_daytime: bool
    current_hour: int
    home_location_id: Optional[LocationID] = None
    work_location_id: Optional[LocationID] = None


@dataclasses.dataclass
class PreferenceWeights:
    """Relative utility weights derived from personality, values, and emotions."""

    vital_restoration: float = 1.0  # Weight given to hunger / energy deficits
    economic_security: float = 0.5  # Weight given to earning funds
    social_affiliation: float = 0.5 # Weight given to companionship
    skill_mastery: float = 0.4      # Weight given to competence and study
    safety_preservation: float = 0.8# Weight penalizing danger or exhaustion
    risk_tolerance: float = 0.5     # Willingness to accept uncertainty
    time_discount: float = 0.9      # Preference for immediate vs delayed payoff


@dataclasses.dataclass
class EstimatedConsequence:
    """Predicted future state delta and multi-attribute utility evaluation for an action."""

    action_type: ActivityType
    target_location_id: Optional[LocationID]
    predicted_energy_delta: float
    predicted_hunger_delta: float
    predicted_money_delta: float
    attribute_utilities: dict[str, float]
    total_expected_utility: float
    reasoning: str


@dataclasses.dataclass
class StructuredDecisionTrace:
    """Complete, transparent computational trace of an autonomous decision."""

    situation: dict[str, Any]
    relevant_needs: dict[str, float]
    emotional_weights: dict[str, float]
    active_goals: list[str]
    alternatives_evaluated: list[dict[str, Any]]
    selected_action: ActivityType
    target_location_id: Optional[LocationID]
    expected_utility: float
    decision_reasoning: str
    dominant_factors: list[str]
    actual_outcome: Optional[dict[str, Any]] = None


class FormalDecisionArchitecture:
    """MAUT decision system replacing unexplained ad-hoc coefficients with formal utility decomposition."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()

    def derive_preference_weights(
        self,
        traits: dict[str, float],
        emotions: dict[str, float],
        mood: float,
    ) -> PreferenceWeights:
        """Derive multi-attribute weights from personality traits and current emotional states."""
        c = traits.get("conscientiousness", 0.5)
        e = traits.get("extraversion", 0.5)
        o = traits.get("openness", 0.5)
        n = traits.get("neuroticism", 0.5)
        risk = traits.get("risk_tolerance", 0.5)
        patience = traits.get("patience", 0.5)

        anxiety = emotions.get("anxiety", 0.0)
        fear = emotions.get("fear", 0.0)
        loneliness = emotions.get("loneliness", 0.0)
        curiosity = emotions.get("curiosity", 0.0)

        # Safety preservation amplified by neuroticism, anxiety, and fear
        safety_w = 0.5 + 0.3 * n + 0.4 * max(anxiety, fear)
        # Social affiliation amplified by extraversion and loneliness
        social_w = 0.3 + 0.4 * e + 0.4 * loneliness + 0.1 * mood
        # Economic security amplified by conscientiousness and anxiety about scarcity
        econ_w = 0.3 + 0.4 * c + 0.2 * anxiety
        # Skill mastery amplified by openness and curiosity
        skill_w = 0.3 + 0.3 * o + 0.4 * curiosity
        # Vital restoration remains high priority
        vital_w = 1.0 + 0.2 * (1.0 - patience)

        return PreferenceWeights(
            vital_restoration=round(vital_w, 3),
            economic_security=round(econ_w, 3),
            social_affiliation=round(social_w, 3),
            skill_mastery=round(skill_w, 3),
            safety_preservation=round(safety_w, 3),
            risk_tolerance=round(risk, 3),
            time_discount=round(0.85 + 0.15 * patience, 3),
        )

    def evaluate_candidate(
        self,
        act: ActivityType,
        target_loc: Optional[LocationID],
        internal: InternalState,
        beliefs: WorldBeliefs,
        info: InformationState,
        prefs: PreferenceWeights,
        active_goal_categories: set[str],
    ) -> EstimatedConsequence:
        """Evaluate expected utility of an action via multi-attribute utility theory."""
        d_energy = 0.0
        d_hunger = 0.0
        d_money = 0.0
        u_vital = 0.0
        u_econ = 0.0
        u_social = 0.0
        u_skill = 0.0
        u_safety = 0.0
        reason_parts = []

        exhaustion = 1.0 - internal.energy
        hunger = internal.hunger

        if act == ActivityType.SLEEP:
            d_energy = 0.8
            d_hunger = 0.05
            u_vital = exhaustion * 2.0
            if not info.is_daytime:
                u_vital += 0.5
            u_safety = 0.3 if exhaustion > 0.7 else 0.0
            reason_parts.append(f"Restores vital energy (exhaustion: {exhaustion:.2f})")

        elif act == ActivityType.REST:
            d_energy = 0.3
            u_vital = exhaustion * 1.2
            u_safety = 0.2
            reason_parts.append(f"Short respite from exertion")

        elif act in (ActivityType.EAT, ActivityType.COOK):
            d_hunger = -0.7
            cost = 0.0 if act == ActivityType.COOK else beliefs.estimated_food_cost
            d_money = -cost
            u_vital = hunger * 2.2
            if act == ActivityType.COOK:
                u_econ = 0.4 # Saving funds
                reason_parts.append("Prepares meal domestically to conserve funds")
            else:
                reason_parts.append(f"Satiates acute biological hunger ({hunger:.2f})")

        elif act == ActivityType.WORK:
            d_energy = -0.3
            d_hunger = 0.15
            wage = 25.0
            d_money = wage
            need_funds = max(0.0, 1.0 - (internal.money / 100.0))
            u_econ = 0.8 * need_funds + 0.4
            if "financial" in active_goal_categories:
                u_econ += 0.5
            if exhaustion > 0.7:
                u_safety = -0.8 # Working while severely fatigued is dangerous
            reason_parts.append("Productive labor generates wages")

        elif act == ActivityType.SOCIALIZE:
            d_energy = -0.1
            peers_count = len(info.nearby_humans)
            u_social = 0.6 + (0.3 if peers_count > 0 else 0.0)
            if "social" in active_goal_categories:
                u_social += 0.4
            reason_parts.append("Social communion strengthens community ties")

        elif act == ActivityType.STUDY:
            d_energy = -0.2
            u_skill = 0.7
            if "skill" in active_goal_categories:
                u_skill += 0.4
            reason_parts.append("Learning improves procedural competency")

        elif act == ActivityType.RELAX:
            d_energy = 0.15
            u_vital = 0.4
            u_safety = 0.2
            reason_parts.append("Recreational calm reduces emotional strain")

        # Multi-attribute combination: U_total = sum(w_i * u_i)
        attr_utils = {
            "vital": u_vital * prefs.vital_restoration,
            "economic": u_econ * prefs.economic_security,
            "social": u_social * prefs.social_affiliation,
            "skill": u_skill * prefs.skill_mastery,
            "safety": u_safety * prefs.safety_preservation,
        }

        # Location affinity / aversion modulation
        loc_adj = 0.0
        if target_loc:
            loc_adj += beliefs.location_affinities.get(target_loc, 0.0)
            loc_adj -= beliefs.location_aversions.get(target_loc, 0.0)
        attr_utils["location_valence"] = loc_adj

        total_utility = sum(attr_utils.values())

        return EstimatedConsequence(
            action_type=act,
            target_location_id=target_loc,
            predicted_energy_delta=d_energy,
            predicted_hunger_delta=d_hunger,
            predicted_money_delta=d_money,
            attribute_utilities=attr_utils,
            total_expected_utility=round(total_utility, 4),
            reasoning="; ".join(reason_parts) if reason_parts else f"Execute {act.value}",
        )

    def select_action(
        self,
        candidates: list[EstimatedConsequence],
        exploration_temperature: float = 0.1,
    ) -> tuple[EstimatedConsequence, StructuredDecisionTrace]:
        """Bounded rational action selection using softmax temperature."""
        if not candidates:
            raise ValueError("No candidate actions available for selection")

        utils = np.array([c.total_expected_utility for c in candidates], dtype=np.float64)
        # Softmax with temperature
        temp = max(0.01, exploration_temperature)
        exp_u = np.exp((utils - np.max(utils)) / temp)
        probs = exp_u / np.sum(exp_u)

        chosen_idx = int(self.rng.choice(len(candidates), p=probs))
        chosen = candidates[chosen_idx]

        # Extract dominant factors
        dom_factors = sorted(chosen.attribute_utilities.items(), key=lambda x: abs(x[1]), reverse=True)
        dominant_list = [f"{k} ({v:+.2f})" for k, v in dom_factors[:3] if abs(v) > 0.05]

        trace = StructuredDecisionTrace(
            situation={"action_candidates_count": len(candidates)},
            relevant_needs={},
            emotional_weights={},
            active_goals=[],
            alternatives_evaluated=[
                {
                    "action": c.action_type.value,
                    "target_location": c.target_location_id,
                    "expected_utility": c.total_expected_utility,
                    "utilities": c.attribute_utilities,
                }
                for c in candidates
            ],
            selected_action=chosen.action_type,
            target_location_id=chosen.target_location_id,
            expected_utility=chosen.total_expected_utility,
            decision_reasoning=chosen.reasoning,
            dominant_factors=dominant_list,
        )

        return chosen, trace
