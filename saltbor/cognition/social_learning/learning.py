"""Social learning engine: observational skill acquisition, mentorship, apprenticeship, and error propagation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


@dataclass
class MentorshipBond:
    """Formal or informal trade apprenticeship between mentor and learner."""

    mentorship_id: str
    mentor_uid: HumanID
    apprentice_uid: HumanID
    trade_skill_id: str
    started_tick: Tick
    sessions_completed: int = 0
    active: bool = True


class SocialLearningEngine:
    """Enables individuals to learn productive skills and practices through observation and mentorship."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.mentorships: dict[str, MentorshipBond] = {}
        # Track provenances of techniques: (human_uid, skill_id) -> "direct_experience" | "observed" | "mentored"
        self.technique_provenance: dict[tuple[HumanID, str], str] = {}

    def establish_mentorship(
        self,
        mentorship_id: str,
        mentor: SyntheticHuman,
        apprentice: SyntheticHuman,
        trade_skill_id: str,
        current_tick: Tick,
    ) -> MentorshipBond:
        """Formalize an apprenticeship agreement between an experienced worker and a novice."""
        bond = MentorshipBond(
            mentorship_id=mentorship_id,
            mentor_uid=mentor.uid,
            apprentice_uid=apprentice.uid,
            trade_skill_id=trade_skill_id,
            started_tick=current_tick,
        )
        self.mentorships[mentorship_id] = bond
        logger.info("Mentorship established: %s is training apprentice %s in %s", mentor.name, apprentice.name, trade_skill_id)
        return bond

    def observe_and_learn(
        self,
        observer: SyntheticHuman,
        model_worker: SyntheticHuman,
        skill_id: str,
        current_tick: Tick,
        practice_duration_ticks: int = 1,
    ) -> tuple[bool, float, str]:
        """Novice observes a competent peer executing a task and acquires proficiency.

        Observational learning is modulated by:
        - Observer openness and conscientiousness.
        - Skill difference: learner cannot absorb techniques that are excessively far beyond current mastery.
        - Model worker's demonstrated proficiency.
        """
        model_skill = model_worker.memory.procedural.get_skill(skill_id)
        if not model_skill:
            return False, 0.0, "Model worker does not possess target skill"

        observer_skill = observer.memory.procedural.get_skill(skill_id)
        observer_level = observer_skill.level if observer_skill else 0.0

        # Cannot learn effectively if model knows less than observer
        if model_skill.level <= observer_level:
            return False, 0.0, "Model does not possess superior proficiency"

        # Gap penalty: if model is master (0.9) and observer is 0.0, absorption rate is lower
        gap = model_skill.level - observer_level
        gap_efficiency = max(0.2, 1.0 - (gap * 0.7))

        openness = observer.personality.traits.get_trait_value("openness") if observer.personality else 0.5
        c_trait = observer.personality.traits.get_trait_value("conscientiousness") if observer.personality else 0.5

        # Base observational transfer rate
        transfer_rate = 0.25 * gap_efficiency * (0.6 + 0.4 * openness)
        xp_gain = round(15.0 * transfer_rate * practice_duration_ticks, 2)

        # Apply to observer's procedural memory
        if not observer_skill:
            observer.memory.procedural.register_skill(
                skill_id=skill_id,
                name=model_skill.name,
                category=model_skill.category,
                initial_level=0.05,
            )
        observer.memory.procedural.add_experience(skill_id, xp_gain, current_tick)
        new_level = observer.memory.procedural.get_skill(skill_id).level

        self.technique_provenance[(observer.uid, skill_id)] = "observed"
        summary = f"Gained {xp_gain:.1f} XP in {skill_id} observing {model_worker.name} (level: {new_level:.3f})"
        logger.info("Social learning: %s -> %s", observer.name, summary)
        return True, xp_gain, summary

    def conduct_mentorship_session(
        self,
        mentorship_id: str,
        mentor: SyntheticHuman,
        apprentice: SyntheticHuman,
        current_tick: Tick,
    ) -> tuple[bool, float, str]:
        """A dedicated instructional session between master and apprentice."""
        bond = self.mentorships.get(mentorship_id)
        if not bond or not bond.active:
            return False, 0.0, "Mentorship inactive"

        skill_id = bond.trade_skill_id
        mentor_skill = mentor.memory.procedural.get_skill(skill_id)
        if not mentor_skill:
            return False, 0.0, "Mentor lacks designated trade skill"

        appr_skill = apprentice.memory.procedural.get_skill(skill_id)
        if not appr_skill:
            apprentice.memory.procedural.register_skill(
                skill_id=skill_id,
                name=mentor_skill.name,
                category=mentor_skill.category,
                initial_level=0.10,
            )

        # Deliberate mentorship grants double the XP of casual observation
        xp_gained = 35.0 * (mentor_skill.level / max(0.2, appr_skill.level if appr_skill else 0.1))
        xp_gained = float(np.clip(xp_gained, 10.0, 60.0))

        apprentice.memory.procedural.add_experience(skill_id, xp_gained, current_tick)
        bond.sessions_completed += 1
        self.technique_provenance[(apprentice.uid, skill_id)] = "mentored"

        summary = f"Apprentice {apprentice.name} completed mentorship session #{bond.sessions_completed} with Master {mentor.name} (+{xp_gained:.1f} XP)"
        logger.info(summary)
        return True, xp_gained, summary

    def copy_suboptimal_strategy(
        self,
        imitator: SyntheticHuman,
        technique_id: str,
        flawed_belief: str,
        current_tick: Tick,
    ) -> None:
        """Simulates error propagation where an individual adopts an inefficient or superstitious technique."""
        imitator.memory.semantic.add_fact(
            subject=technique_id,
            predicate="efficacy",
            value=flawed_belief,
            tick=current_tick,
            confidence=0.55,
        )
        self.technique_provenance[(imitator.uid, technique_id)] = "copied_misconception"
