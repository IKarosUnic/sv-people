"""Autonomy engine — intrinsic goal generation, prioritization, and self-direction.

Allows synthetic humans to formulate their own goals driven by physical needs,
personality values, and emotional motivations, rather than executing fixed scripts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import GoalID, NeedType, Tick


@dataclass
class Goal:
    """An autonomous objective formulated by an individual."""

    goal_id: GoalID = field(default_factory=uuid.uuid4)
    description: str = ""
    priority: float = 0.5            # 0.0 to 1.0
    need_type: Optional[NeedType] = None
    progress: float = 0.0            # 0.0 (started) to 1.0 (completed)
    deadline_tick: Optional[Tick] = None
    status: str = "active"           # 'active', 'completed', 'abandoned'

    def advance(self, delta: float) -> None:
        self.progress = min(1.0, self.progress + delta)
        if self.progress >= 1.0:
            self.status = "completed"


class AutonomyEngine:
    """Self-direction and intrinsic motivation subsystem."""

    def __init__(self) -> None:
        self._goals: dict[GoalID, Goal] = {}

    def get_active_goals(self) -> list[Goal]:
        """Return all active goals sorted by priority (descending)."""
        active = [g for g in self._goals.values() if g.status == "active"]
        return sorted(active, key=lambda g: g.priority, reverse=True)

    def current_primary_goal(self) -> Optional[Goal]:
        active = self.get_active_goals()
        return active[0] if active else None

    def add_goal(self, goal: Goal) -> None:
        self._goals[goal.goal_id] = goal

    def complete_goal(self, goal_id: GoalID) -> None:
        if goal_id in self._goals:
            self._goals[goal_id].status = "completed"
            self._goals[goal_id].progress = 1.0

    def abandon_goal(self, goal_id: GoalID) -> None:
        if goal_id in self._goals:
            self._goals[goal_id].status = "abandoned"

    def generate_goals_from_needs(
        self,
        needs: dict[NeedType, float],
        personality: PersonalityEngine,
        current_tick: Tick,
    ) -> list[Goal]:
        """Formulate personal goals to address urgent deficits or pursue aspirations."""
        new_goals: list[Goal] = []
        existing_needs = {g.need_type for g in self.get_active_goals() if g.need_type}

        # 1. Biological survival needs (Hunger & Rest)
        hunger = needs.get(NeedType.HUNGER, 0.0)
        if hunger > 0.50 and NeedType.HUNGER not in existing_needs:
            urgency = min(1.0, 0.4 + hunger * 0.6)
            goal = Goal(
                description="Obtain and eat food",
                priority=urgency,
                need_type=NeedType.HUNGER,
                deadline_tick=current_tick + 32,
            )
            self.add_goal(goal)
            new_goals.append(goal)

        energy_deficit = needs.get(NeedType.REST, 0.0)
        if energy_deficit > 0.55 and NeedType.REST not in existing_needs:
            urgency = min(1.0, 0.4 + energy_deficit * 0.6)
            goal = Goal(
                description="Find rest or go home to sleep",
                priority=urgency,
                need_type=NeedType.REST,
                deadline_tick=current_tick + 48,
            )
            self.add_goal(goal)
            new_goals.append(goal)

        # 2. Social needs (modulated by extraversion)
        extraversion = personality.get_trait("extraversion")
        social_deficit = needs.get(NeedType.SOCIAL, 0.0)
        if social_deficit > 0.60 and NeedType.SOCIAL not in existing_needs:
            social_priority = min(0.9, 0.3 + (social_deficit * 0.4) + (extraversion * 0.3))
            goal = Goal(
                description="Connect or converse with friends/neighbors",
                priority=social_priority,
                need_type=NeedType.SOCIAL,
                deadline_tick=current_tick + 64,
            )
            self.add_goal(goal)
            new_goals.append(goal)

        # 3. Achievement / Work / Study needs (modulated by conscientiousness & openness)
        conscientiousness = personality.get_trait("conscientiousness")
        openness = personality.get_trait("openness")
        achievement_deficit = needs.get(NeedType.ACHIEVEMENT, 0.0)

        if achievement_deficit > 0.65 and NeedType.ACHIEVEMENT not in existing_needs:
            ach_priority = min(0.85, 0.2 + (achievement_deficit * 0.3) + (conscientiousness * 0.4))
            desc = "Work productively and advance skills" if conscientiousness > openness else "Study or learn something new"
            goal = Goal(
                description=desc,
                priority=ach_priority,
                need_type=NeedType.ACHIEVEMENT,
                deadline_tick=current_tick + 96,
            )
            self.add_goal(goal)
            new_goals.append(goal)

        return new_goals

    def cleanup_completed_or_stale(self, current_tick: Tick) -> None:
        """Prune long-past completed goals or abandoned deadlocks."""
        for g in list(self._goals.values()):
            if g.status == "active" and g.deadline_tick and current_tick > g.deadline_tick:
                # Deadline missed without completion
                g.status = "abandoned"
