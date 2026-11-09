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
    """Multi-attribute utility decision engine with emotional and personality modulation."""

    def __init__(self) -> None:
        pass

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

        # Emotional bias
        mood = emotions.get_mood() if hasattr(emotions, "get_mood") else 0.0
        frustration = emotions.get_emotion("frustration") if hasattr(emotions, "get_emotion") else 0.0

        # Needs
        hunger = context.current_hunger
        exhaustion = 1.0 - context.current_energy
        social_need = context.current_needs.get(NeedType.SOCIAL, 0.0)

        # -------------------------------------------------------------------
        # 1. SLEEP (High utility when exhausted, late at night, or at home)
        # -------------------------------------------------------------------
        sleep_util = exhaustion * 1.5
        if not context.is_daytime:
            sleep_util += 0.4
        if exhaustion > 0.8:
            sleep_util += 1.0  # Acute physical fatigue override
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
        rest_util = exhaustion * 0.9 + (frustration * 0.3)
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
        # 4. WORK (Driven by daylight, daytime shift hours, conscientiousness)
        # -------------------------------------------------------------------
        if context.is_daytime and (7 <= context.hour_int <= 17):
            work_util = 0.5 + (conscientiousness * 0.5)
            if context.current_money < 30.0:
                work_util += 0.4  # Economic motivation
            if exhaustion > 0.7:
                work_util -= 0.6  # Too tired to work safely
            options.append(
                ActionOption(
                    action_type=ActivityType.WORK,
                    target_location_id=context.work_location_id or "taller_artesanal",
                    expected_utility=work_util,
                    reasoning=f"Work shift during productive hours (conscientiousness={conscientiousness:.2f}).",
                )
            )

        # -------------------------------------------------------------------
        # 5. SOCIALIZE (Driven by social need, extraversion, plaza/market presence)
        # -------------------------------------------------------------------
        social_util = (social_need * 0.8) + (extraversion * 0.5) + (mood * 0.2)
        if len(context.nearby_humans) > 0:
            social_util += 0.3
        options.append(
            ActionOption(
                action_type=ActivityType.SOCIALIZE,
                target_location_id="plaza_central",
                expected_utility=social_util,
                reasoning=f"Connecting with neighbors (social need={social_need:.2f}, extraversion={extraversion:.2f}).",
            )
        )

        # -------------------------------------------------------------------
        # 6. STUDY / LEARN (Driven by openness, school hours)
        # -------------------------------------------------------------------
        if context.is_daytime and (8 <= context.hour_int <= 16):
            study_util = (openness * 0.6) + (conscientiousness * 0.3)
            options.append(
                ActionOption(
                    action_type=ActivityType.STUDY,
                    target_location_id="escuela_comunal",
                    expected_utility=study_util,
                    reasoning=f"Engaging in study and learning (openness={openness:.2f}).",
                )
            )

        # -------------------------------------------------------------------
        # 7. EXERCISE / RELAX (Park/nature outdoors)
        # -------------------------------------------------------------------
        if context.is_daytime and exhaustion < 0.5:
            exercise_util = 0.3 + (openness * 0.3) - (neuroticism * 0.1)
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
        """Select an action using softmax utility evaluation with subtle stochastic noise."""
        options = self.evaluate_options(context, personality, emotions, memory)
        if not options:
            return ActionOption(
                action_type=ActivityType.REST,
                target_location_id=context.current_location_id,
                expected_utility=0.1,
                reasoning="Default fallback action.",
            )

        # Softmax selection with noise
        utilities = []
        for opt in options:
            noise = (
                rng.normal(0.0, exploration_noise)
                if rng is not None and hasattr(rng, "normal")
                else random.gauss(0.0, exploration_noise)
            )
            utilities.append(opt.expected_utility + noise)

        # Pick option with maximum perturbed utility (or argmax)
        best_idx = int(np.argmax(utilities)) if hasattr(np, "argmax") else max(range(len(utilities)), key=lambda i: utilities[i])
        chosen = options[best_idx]
        return chosen
