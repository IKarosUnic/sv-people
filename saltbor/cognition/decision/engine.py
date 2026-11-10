"""Decision engine — context-aware, utility-driven action selection.

Integrates physiological needs, emotional states, personality traits,
memories, active goals, and environmental constraints into actionable decisions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from saltbor.cognition.autonomy.engine import Goal
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import ActivityType, HumanID, LocationID, NeedType


@dataclass
class ActionOption:
    """A candidate action evaluated by the decision engine."""

    action_type: ActivityType
    target_location_id: Optional[LocationID] = None
    expected_utility: float = 0.0
    reasoning: str = ""


@dataclass
class DecisionTrace:
    """Audit and explanation record for an individual's decision."""

    chosen_action: ActivityType
    target_location_id: Optional[LocationID]
    expected_utility: float
    reasoning: str
    dominant_factors: list[str]
    alternatives: list[dict[str, Any]]


@dataclass
class DecisionContext:
    """The situational context upon which a decision is made."""

    current_location_id: Optional[LocationID]
    available_activities: list[ActivityType]
    current_needs: dict[NeedType, float]
    current_energy: float
    current_hunger: float
    current_money: float
    is_daytime: bool
    hour_int: int
    active_goals: list[Goal] = field(default_factory=list)
    nearby_humans: list[HumanID] = field(default_factory=list)
    home_location_id: Optional[LocationID] = None
    work_location_id: Optional[LocationID] = None


class DecisionEngine:
    """Multi-attribute utility decision engine with bounded rationality and cognitive traceability."""

    def __init__(self) -> None:
        self.last_decision_trace: Optional[DecisionTrace] = None
        self.decision_history: list[DecisionTrace] = []

    def get_last_trace(self) -> Optional[DecisionTrace]:
        """Return the most recent explanatory decision trace."""
        return self.last_decision_trace

    def evaluate_options(
        self,
        context: DecisionContext,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        memory: Optional[MemoryEngine] = None,
    ) -> list[ActionOption]:
        """Compute utility score and explanatory reasoning for candidate actions."""
        options: list[ActionOption] = []

        # Trait values
        conscientiousness = personality.get_trait("conscientiousness")
        extraversion = personality.get_trait("extraversion")
        openness = personality.get_trait("openness")
        neuroticism = personality.get_trait("neuroticism")
        risk_tolerance = personality.get_trait("risk_tolerance")
        patience = personality.get_trait("patience")

        # Emotional weights & states
        weights = emotions.get_decision_weights() if hasattr(emotions, "get_decision_weights") else {}
        mood = emotions.get_mood() if hasattr(emotions, "get_mood") else 0.0
        frustration = emotions.get_emotion("frustration") if hasattr(emotions, "get_emotion") else 0.0
        loneliness = emotions.get_emotion("loneliness") if hasattr(emotions, "get_emotion") else 0.0
        anxiety = emotions.get_emotion("anxiety") if hasattr(emotions, "get_emotion") else 0.0
        fear = emotions.get_emotion("fear") if hasattr(emotions, "get_emotion") else 0.0
        curiosity = emotions.get_emotion("curiosity") if hasattr(emotions, "get_emotion") else 0.0

        # Needs
        hunger = context.current_hunger
        exhaustion = 1.0 - context.current_energy
        social_need = context.current_needs.get(NeedType.SOCIAL, 0.0)

        # Active Goals Influence
        active_goal_categories = {g.category for g in context.active_goals if getattr(g, "status", "active") in ("active", "modified")}
        primary_goal = context.active_goals[0] if context.active_goals else None

        # -------------------------------------------------------------------
        # 1. SLEEP (High utility when exhausted, late at night, or at home)
        # -------------------------------------------------------------------
        sleep_util = exhaustion * 1.5
        if not context.is_daytime:
            sleep_util += 0.4
        if exhaustion > 0.8:
            sleep_util += 1.0  # Acute physical fatigue override
        if anxiety > 0.5:
            sleep_util += 0.2  # Safety withdrawal in home sanctuary

        options.append(
            ActionOption(
                action_type=ActivityType.SLEEP,
                target_location_id=context.home_location_id,
                expected_utility=sleep_util,
                reasoning=f"Exhaustion level is {exhaustion:.2f}; nighttime sleep required.",
            )
        )

        # -------------------------------------------------------------------
        # 2. REST (Short respite)
        # -------------------------------------------------------------------
        rest_util = exhaustion * 0.9 + (frustration * 0.3) + (anxiety * 0.85) + (fear * 0.60)
        options.append(
            ActionOption(
                action_type=ActivityType.REST,
                target_location_id=context.current_location_id,
                expected_utility=rest_util,
                reasoning=f"Taking a short break to recover breath (fatigue={exhaustion:.2f}).",
            )
        )

        # -------------------------------------------------------------------
        # 3. EAT / COOK (Driven by hunger)
        # -------------------------------------------------------------------
        if hunger > 0.3:
            eat_util = hunger * 2.0
            # If money is low, prefer cooking at home over dining out
            if context.current_money < 10.0 and context.home_location_id:
                options.append(
                    ActionOption(
                        action_type=ActivityType.COOK,
                        target_location_id=context.home_location_id,
                        expected_utility=eat_util + 0.3,
                        reasoning=f"Hungry ({hunger:.2f}), low funds (${context.current_money:.2f}); cooking at home.",
                    )
                )
            else:
                target = "comedor_dona_maria" if (context.hour_int >= 6 and context.hour_int <= 20) else context.home_location_id
                options.append(
                    ActionOption(
                        action_type=ActivityType.EAT,
                        target_location_id=target,
                        expected_utility=eat_util,
                        reasoning=f"Hunger ({hunger:.2f}) requires having a meal.",
                    )
                )

        # -------------------------------------------------------------------
        # 4. WORK (Driven by daylight, daytime shift hours, conscientiousness, financial goals)
        # -------------------------------------------------------------------
        if context.is_daytime and (7 <= context.hour_int <= 17) and context.work_location_id:
            work_util = 0.5 + (conscientiousness * 0.5)
            if anxiety > 0.4:
                work_util -= (anxiety * 0.45 + fear * 0.40)
            if context.current_money < 30.0:
                work_util += 0.4  # Economic survival motivation
            if "financial" in active_goal_categories:
                work_util += 0.45  # Direct autonomous goal pursuit
            if exhaustion > 0.7:
                work_util -= 0.6  # Too tired to work safely
            options.append(
                ActionOption(
                    action_type=ActivityType.WORK,
                    target_location_id=context.work_location_id,
                    expected_utility=work_util,
                    reasoning=f"Work shift during productive hours (conscientiousness={conscientiousness:.2f}).",
                )
            )

        # -------------------------------------------------------------------
        # 5. SOCIALIZE (Driven by social need, loneliness, extraversion, plaza/market)
        # -------------------------------------------------------------------
        effective_social_drive = max(social_need, loneliness)
        social_util = (effective_social_drive * 0.8) + (extraversion * 0.5) + (mood * 0.2)
        if anxiety > 0.4:
            social_util -= anxiety * 0.35  # Fear / social withdrawal
        if "social" in active_goal_categories or (primary_goal and primary_goal.category in ("social", "reconciliation")):
            social_util += 0.4
        if len(context.nearby_humans) > 0:
            social_util += 0.3
        options.append(
            ActionOption(
                action_type=ActivityType.SOCIALIZE,
                target_location_id="plaza_central",
                expected_utility=social_util,
                reasoning=f"Connecting with neighbors (social need={effective_social_drive:.2f}, extraversion={extraversion:.2f}).",
            )
        )

        # -------------------------------------------------------------------
        # 6. STUDY / LEARN (Driven by openness, curiosity, school hours, skill goals)
        # -------------------------------------------------------------------
        if context.is_daytime and (8 <= context.hour_int <= 16):
            study_util = (openness * 0.6) + (conscientiousness * 0.3) + (curiosity * 0.75)
            if anxiety > 0.4:
                study_util -= anxiety * 0.35  # Anxiety impairs focus
            if "skill" in active_goal_categories or (primary_goal and primary_goal.category == "skill"):
                study_util += 0.55  # Pursuing autonomous skill development goal
            options.append(
                ActionOption(
                    action_type=ActivityType.STUDY,
                    target_location_id="escuela_comunal",
                    expected_utility=study_util,
                    reasoning=f"Engaging in study and learning (openness={openness:.2f}, curiosity={curiosity:.2f}).",
                )
            )

        # -------------------------------------------------------------------
        # 7. SHOP (Market commerce and supplies)
        # -------------------------------------------------------------------
        if context.is_daytime and (8 <= context.hour_int <= 17) and context.current_money >= 15.0:
            shop_util = 0.35 + (0.05 * min(5.0, context.current_money / 20.0))
            options.append(
                ActionOption(
                    action_type=ActivityType.SHOP,
                    target_location_id="mercado_municipal",
                    expected_utility=shop_util,
                    reasoning="Visiting the municipal market for supplies and trade.",
                )
            )

        # -------------------------------------------------------------------
        # 8. EXERCISE / RELAX (Park/nature outdoors)
        # -------------------------------------------------------------------
        if context.is_daytime and exhaustion < 0.5:
            exercise_util = 0.3 + (openness * 0.3) - (neuroticism * 0.1) + (curiosity * 0.2)
            options.append(
                ActionOption(
                    action_type=ActivityType.EXERCISE,
                    target_location_id="parque_la_ceiba",
                    expected_utility=exercise_util,
                    reasoning="Exercising in the open air at Parque La Ceiba.",
                )
            )

        options.append(
            ActionOption(
                action_type=ActivityType.RELAX,
                target_location_id=context.current_location_id or "plaza_central",
                expected_utility=0.25 + (1.0 - conscientiousness) * 0.2,
                reasoning="Taking quiet personal leisure time.",
            )
        )

        # -------------------------------------------------------------------
        # 8. Emotional Associations Modulation (Location Aversion & Place Affinity)
        # -------------------------------------------------------------------
        if memory and hasattr(memory, "get_location_association"):
            for opt in options:
                if opt.target_location_id:
                    loc_assoc = memory.get_location_association(opt.target_location_id)
                    val = loc_assoc.get("valence", 0.0)
                    if val < -0.15:
                        # Negative memories at location produce avoidance
                        aversion_penalty = abs(val) * 0.40
                        opt.expected_utility = max(0.01, opt.expected_utility - aversion_penalty)
                        opt.reasoning += f" [Avoidance: unpleasant memories at {opt.target_location_id}]"
                    elif val > 0.25:
                        # Positive memories at location encourage revisit
                        affinity_bonus = val * 0.25
                        opt.expected_utility += affinity_bonus
                        opt.reasoning += f" [Affinity: positive memories at {opt.target_location_id}]"

        return options

    def decide(
        self,
        context: DecisionContext,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        memory: Optional[MemoryEngine] = None,
        rng: Optional[Any] = None,
        exploration_noise: float = 0.10,
    ) -> ActionOption:
        """Select an action using softmax utility evaluation with bounded rationality and record trace."""
        options = self.evaluate_options(context, personality, emotions, memory)
        if not options:
            fallback = ActionOption(
                action_type=ActivityType.REST,
                target_location_id=context.current_location_id,
                expected_utility=0.1,
                reasoning="Default fallback action.",
            )
            return fallback

        # Bounded rationality noise modulated by personality:
        # High conscientiousness & high patience -> lower deliberation noise
        # High impulsiveness -> higher noise
        modifiers = personality.get_behavioral_modifier() if hasattr(personality, "get_behavioral_modifier") else {}
        impulsiveness = modifiers.get("impulsiveness", 0.5)
        determination = modifiers.get("determination", 0.5)
        effective_noise = max(0.02, exploration_noise * (0.6 + impulsiveness * 0.8 - determination * 0.3))

        utilities = []
        for opt in options:
            noise = (
                rng.normal(0.0, effective_noise)
                if rng is not None and hasattr(rng, "normal")
                else random.gauss(0.0, effective_noise)
            )
            utilities.append(opt.expected_utility + noise)

        best_idx = int(np.argmax(utilities)) if hasattr(np, "argmax") else max(range(len(utilities)), key=lambda i: utilities[i])
        chosen = options[best_idx]

        # Record decision trace
        dominant_factors: list[str] = []
        if context.current_hunger > 0.5:
            dominant_factors.append(f"Hunger ({context.current_hunger:.2f})")
        if context.current_energy < 0.3:
            dominant_factors.append(f"Exhaustion ({1.0 - context.current_energy:.2f})")
        if hasattr(emotions, "get_mood") and emotions.get_mood() < -0.3:
            dominant_factors.append(f"Low Mood ({emotions.get_mood():.2f})")
        if context.active_goals:
            dominant_factors.append(f"Goal: {context.active_goals[0].description}")

        trace = DecisionTrace(
            chosen_action=chosen.action_type,
            target_location_id=chosen.target_location_id,
            expected_utility=chosen.expected_utility,
            reasoning=chosen.reasoning,
            dominant_factors=dominant_factors,
            alternatives=[
                {
                    "action": opt.action_type.value,
                    "location": opt.target_location_id,
                    "utility": round(opt.expected_utility, 3),
                }
                for opt in options
            ],
        )
        self.last_decision_trace = trace
        self.decision_history.append(trace)
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)

        return chosen

    def decide_formal(
        self,
        internal_state: Any,
        beliefs: Any,
        info: Any,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        active_goal_categories: Optional[set[str]] = None,
        rng: Optional[Any] = None,
    ) -> tuple[ActionOption, Any]:
        """Execute decision using the formal MAUT architecture (Section 2.1)."""
        from saltbor.cognition.decision.formal_decision import (
            FormalDecisionArchitecture,
        )

        arch = FormalDecisionArchitecture(rng=rng)
        traits_dict = {
            t: personality.get_trait(t)
            for t in [
                "conscientiousness", "extraversion", "openness", "neuroticism",
                "risk_tolerance", "patience", "persistence"
            ]
        }
        emots_dict = {
            e: emotions.get_emotion(e) if hasattr(emotions, "get_emotion") else 0.0
            for e in ["anxiety", "fear", "loneliness", "curiosity", "frustration"]
        }
        mood = emotions.get_mood() if hasattr(emotions, "get_mood") else 0.0
        prefs = arch.derive_preference_weights(traits_dict, emots_dict, mood)

        # Build candidate consequences
        candidates = []
        for act in info.available_activities:
            # Determine appropriate target location
            target = info.current_location_id
            if act == ActivityType.SLEEP:
                target = info.home_location_id
            elif act == ActivityType.WORK:
                target = info.work_location_id
            elif act == ActivityType.STUDY:
                target = "escuela_comunal"
            elif act == ActivityType.SHOP:
                target = "mercado_municipal"
            elif act == ActivityType.EAT:
                target = "comedor_dona_maria"

            conseq = arch.evaluate_candidate(
                act=act,
                target_loc=target,
                internal=internal_state,
                beliefs=beliefs,
                info=info,
                prefs=prefs,
                active_goal_categories=active_goal_categories or set(),
            )
            candidates.append(conseq)

        chosen_conseq, structured_trace = arch.select_action(candidates)
        opt = ActionOption(
            action_type=chosen_conseq.action_type,
            target_location_id=chosen_conseq.target_location_id,
            expected_utility=chosen_conseq.total_expected_utility,
            reasoning=chosen_conseq.reasoning,
        )
        return opt, structured_trace
