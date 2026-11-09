"""Procedural memory system for synthetic humans.

Maintains motor, technical, social, and practical skills.
Implements non-linear skill acquisition with diminishing returns.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import SkillCategory, SkillID


@dataclass
class Skill:
    """A learned ability or practical competency."""

    skill_id: SkillID
    name: str
    category: SkillCategory
    level: float = 0.1             # 0.0 (novice) to 1.0 (master)
    experience_points: float = 10.0
    practice_count: int = 1

    def practice(self, xp_gain: float) -> float:
        """Add practice experience, updating level via asymptotic learning curve.

        Returns the level delta.
        """
        old_level = self.level
        self.experience_points += max(0.0, xp_gain)
        self.practice_count += 1

        # Asymptotic power law: Level approaches 1.0 smoothly as XP grows
        # e.g., 10 XP -> ~0.10, 100 XP -> ~0.50, 500 XP -> ~0.90, 1000 XP -> ~0.98
        self.level = min(1.0, 1.0 - math.exp(-0.007 * self.experience_points))
        return self.level - old_level


class ProceduralMemory:
    """Repository of practical competencies and skills."""

    def __init__(self) -> None:
        self._skills: dict[SkillID, Skill] = {}

    def add_skill(self, skill: Skill) -> None:
        """Register or replace a skill."""
        self._skills[skill.skill_id] = skill

    def get_skill(self, skill_id: SkillID) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def improve_skill(self, skill_id: SkillID, xp_gain: float) -> float:
        """Add practice XP to a skill. Returns level increase."""
        skill = self._skills.get(skill_id)
        if skill is None:
            # Auto-register new generic skill
            skill = Skill(
                skill_id=skill_id,
                name=skill_id.replace("_", " ").title(),
                category=SkillCategory.TECHNICAL,
                level=0.05,
                experience_points=5.0,
            )
            self._skills[skill_id] = skill

        return skill.practice(xp_gain)

    def get_all_skills(self) -> list[Skill]:
        return list(self._skills.values())

    @property
    def count(self) -> int:
        return len(self._skills)
