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
    learning_rate: float = 1.0     # Individual learning speed multiplier
    retention: float = 0.95        # Resistance to decay over prolonged inactivity
    confidence: float = 0.5        # Subjective confidence in competency
    last_practiced_tick: int = 0

    @property
    def proficiency(self) -> float:
        """Alias for level."""
        return self.level

    def practice(self, xp_gain: float, talent_factor: float = 1.0, current_tick: int = 0) -> float:
        """Add practice experience, updating level via asymptotic learning curve.

        Returns the level delta.
        """
        old_level = self.level
        effective_xp = max(0.0, xp_gain) * self.learning_rate * talent_factor
        self.experience_points += effective_xp
        self.practice_count += 1
        self.last_practiced_tick = current_tick

        # Asymptotic power law: Level approaches 1.0 smoothly as XP grows
        # e.g., 10 XP -> ~0.10, 100 XP -> ~0.50, 500 XP -> ~0.90, 1000 XP -> ~0.98
        self.level = min(1.0, 1.0 - math.exp(-0.007 * self.experience_points))
        self.confidence = min(1.0, 0.35 + self.level * 0.65)
        return self.level - old_level

    def decay_from_inactivity(self, elapsed_ticks: int) -> float:
        """Slightly reduce proficiency after extended inactivity (e.g. > 960 ticks / 10 days)."""
        if elapsed_ticks < 960:
            return 0.0
        # Gentle atrophy: at most 0.05 reduction per 10 days of disuse, protected by retention
        decay_amount = (elapsed_ticks / 960.0) * 0.015 * (1.0 - min(0.99, self.retention))
        old_level = self.level
        self.level = max(0.05, self.level - decay_amount)
        self.confidence = max(0.2, self.confidence - decay_amount)
        return old_level - self.level


class ProceduralMemory:
    """Repository of practical competencies and skills."""

    def __init__(self) -> None:
        self._skills: dict[SkillID, Skill] = {}

    def add_skill(self, skill: Skill) -> None:
        """Register or replace a skill."""
        self._skills[skill.skill_id] = skill

    def register_skill(
        self,
        skill_id: SkillID,
        name: str,
        initial_level: float = 0.1,
        category: SkillCategory = SkillCategory.TECHNICAL,
    ) -> Skill:
        """Register or configure a skill with a given initial level."""
        xp = -math.log(max(0.01, 1.0 - min(0.99, initial_level))) / 0.007
        skill = Skill(
            skill_id=skill_id,
            name=name,
            category=category,
            level=initial_level,
            experience_points=xp,
            confidence=min(1.0, 0.35 + initial_level * 0.65),
        )
        self.add_skill(skill)
        return skill

    def get_skill(self, skill_id: SkillID) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def improve_skill(
        self,
        skill_id: SkillID,
        xp_gain: float,
        talent_factor: float = 1.0,
        current_tick: int = 0,
        enable_transfer: bool = True,
    ) -> float:
        """Add practice XP to a skill with diminishing returns and cross-skill knowledge transfer."""
        skill = self._skills.get(skill_id)
        if skill is None:
            # Auto-register new generic skill
            skill = Skill(
                skill_id=skill_id,
                name=skill_id.replace("_", " ").title(),
                category=SkillCategory.TECHNICAL,
                level=0.05,
                experience_points=5.0,
                last_practiced_tick=current_tick,
            )
            self._skills[skill_id] = skill

        delta = skill.practice(xp_gain, talent_factor=talent_factor, current_tick=current_tick)

        # Knowledge Transfer: related skills in the same category receive 15% synergy XP
        if enable_transfer and delta > 0:
            transfer_xp = xp_gain * 0.15
            for other_id, other_skill in self._skills.items():
                if other_id != skill_id and other_skill.category == skill.category:
                    other_skill.practice(transfer_xp, talent_factor=1.0, current_tick=current_tick)

        return delta

    def add_experience(
        self,
        skill_id: SkillID,
        xp_gain: float,
        current_tick: int = 0,
    ) -> float:
        """Alias to add practice experience to a skill."""
        return self.improve_skill(skill_id, xp_gain, current_tick=current_tick)

    def decay_inactive_skills(self, current_tick: int, threshold_ticks: int = 960) -> dict[SkillID, float]:
        """Apply skill atrophy to competencies not practiced in a prolonged time."""
        decayed: dict[SkillID, float] = {}
        for s_id, skill in self._skills.items():
            if skill.last_practiced_tick > 0:
                elapsed = max(0, current_tick - skill.last_practiced_tick)
                if elapsed >= threshold_ticks:
                    loss = skill.decay_from_inactivity(elapsed)
                    if loss > 0.001:
                        decayed[s_id] = loss
        return decayed

    def get_all_skills(self) -> list[Skill]:
        return list(self._skills.values())

    @property
    def count(self) -> int:
        return len(self._skills)
