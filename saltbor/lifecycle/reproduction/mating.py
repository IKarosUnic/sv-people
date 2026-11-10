"""Reproductive preferences, mutual compatibility, and conception mechanics."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import numpy as np

from saltbor.core.types import Gender, HumanID, Tick
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph
from saltbor.lifecycle.reproduction.pregnancy import Pregnancy

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class ReproductionEngine:
    """Evaluates relationship compatibility, reproductive intentions, and conception."""

    def __init__(
        self,
        gestation_ticks: int = 288,
        conception_probability_base: float = 0.15,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.gestation_ticks = gestation_ticks
        self.conception_probability_base = conception_probability_base
        self.rng = rng or np.random.default_rng()
        self._active_pregnancies: dict[HumanID, Pregnancy] = {}  # mother_uid -> Pregnancy

    def is_pregnant(self, mother_uid: HumanID) -> bool:
        preg = self._active_pregnancies.get(mother_uid)
        return preg is not None and not preg.is_delivered

    def get_pregnancy(self, mother_uid: HumanID) -> Optional[Pregnancy]:
        return self._active_pregnancies.get(mother_uid)

    def evaluate_mating_compatibility(
        self,
        person_a: SyntheticHuman,
        person_b: SyntheticHuman,
        genealogy: GenealogicalGraph,
        mutual_trust: float,
        mutual_affinity: float,
    ) -> float:
        """Calculate mutual reproductive compatibility score in [0.0, 1.0]."""
        # 1. Biological fertility checks
        age_a = person_a.demographics.age
        age_b = person_b.demographics.age

        # Reproductive age window (typically 18–45 for female partner, 18–60 for male partner)
        if not (18 <= age_a <= 50 and 18 <= age_b <= 65):
            return 0.0

        # Incest avoidance (no reproduction between close relatives, degree <= 2)
        kinship = genealogy.get_kinship_degree(person_a.uid, person_b.uid)
        if kinship is not None and kinship <= 2:
            return 0.0

        # Opposite sex pairing for biological conception
        gender_a = person_a.demographics.gender
        gender_b = person_b.demographics.gender
        if not ((gender_a == Gender.FEMALE and gender_b == Gender.MALE) or
                (gender_a == Gender.MALE and gender_b == Gender.FEMALE)):
            return 0.0

        # 2. Relationship readiness: trust and affinity thresholds
        if mutual_trust < 0.60 or mutual_affinity < 0.60:
            return 0.0

        # 3. Health & vitality constraints
        health_a = person_a.physical_state.health
        health_b = person_b.physical_state.health
        if health_a < 0.50 or health_b < 0.50:
            return 0.0

        # 4. Personality & value compatibility
        agree_a = person_a.personality.get_trait("agreeableness") if person_a.personality else 0.5
        agree_b = person_b.personality.get_trait("agreeableness") if person_b.personality else 0.5

        score = (mutual_trust * 0.35 + mutual_affinity * 0.35 +
                 ((health_a + health_b) / 2.0) * 0.15 +
                 ((agree_a + agree_b) / 2.0) * 0.15)
        return float(np.clip(score, 0.0, 1.0))

    def attempt_conception(
        self,
        female_partner: SyntheticHuman,
        male_partner: SyntheticHuman,
        genealogy: GenealogicalGraph,
        mutual_trust: float,
        mutual_affinity: float,
        current_tick: Tick,
    ) -> Optional[Pregnancy]:
        """Attempt conception between compatible partners."""
        if female_partner.demographics.gender != Gender.FEMALE:
            # swap if needed
            if male_partner.demographics.gender == Gender.FEMALE:
                female_partner, male_partner = male_partner, female_partner
            else:
                return None

        if self.is_pregnant(female_partner.uid):
            return None

        compatibility = self.evaluate_mating_compatibility(
            female_partner, male_partner, genealogy, mutual_trust, mutual_affinity
        )
        if compatibility < 0.60:
            return None

        # Stochastic conception probability modulated by compatibility
        p_conception = self.conception_probability_base * compatibility
        if self.rng.random() < p_conception:
            pregnancy = Pregnancy(
                mother_uid=female_partner.uid,
                father_uid=male_partner.uid,
                start_tick=current_tick,
                gestation_duration_ticks=self.gestation_ticks,
            )
            self._active_pregnancies[female_partner.uid] = pregnancy
            logger.info("Conception occurred for %s (partner: %s)", female_partner.name, male_partner.name)
            return pregnancy

        return None

    def update_pregnancies(self, delta_ticks: int = 1) -> list[Pregnancy]:
        """Advance all active pregnancies and return those ready for delivery."""
        due_list: list[Pregnancy] = []
        for mother_uid, preg in list(self._active_pregnancies.items()):
            is_due = preg.advance(delta_ticks)
            if is_due:
                due_list.append(preg)
        return due_list

    def complete_delivery(self, mother_uid: HumanID) -> None:
        preg = self._active_pregnancies.get(mother_uid)
        if preg:
            preg.deliver()
