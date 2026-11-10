"""Cultural Transmission Engine: multi-channel non-deterministic transmission and adaptation."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from saltbor.core.types import HumanID, LocationID, Tick
from saltbor.culture.element import CulturalElement, CulturalElementType
from saltbor.lifecycle.demographics.stages import DevelopmentalStage
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class CulturalTransmissionEngine:
    """Simulates social, familial, and observational transmission of cultural practices.

    Culture spreads dynamically through interpersonal ties, developmental socialization,
    and public participation without predetermined scripts.
    """

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self._elements: dict[str, CulturalElement] = {}
        # Tracks individual practice repertoire: human_uid -> set of element_ids
        self._individual_repertoires: dict[HumanID, set[str]] = {}
        # Exposure frequency tracking: (human_uid, element_id) -> count
        self._exposure_history: dict[tuple[HumanID, str], int] = {}

    def register_element(self, element: CulturalElement) -> None:
        self._elements[element.element_id] = element

    def get_element(self, element_id: str) -> Optional[CulturalElement]:
        return self._elements.get(element_id)

    def get_all_elements(self) -> list[CulturalElement]:
        return list(self._elements.values())

    def get_individual_repertoire(self, human_uid: HumanID) -> set[str]:
        return self._individual_repertoires.get(human_uid, set())

    def has_adopted(self, human_uid: HumanID, element_id: str) -> bool:
        return element_id in self.get_individual_repertoire(human_uid)

    def grant_element_directly(
        self,
        human_uid: HumanID,
        element_id: str,
        location_id: Optional[LocationID],
        tick: Tick,
    ) -> bool:
        """Directly grant a cultural practice (e.g. founder origin or starting condition)."""
        elem = self.get_element(element_id)
        if not elem:
            return False
        if human_uid not in self._individual_repertoires:
            self._individual_repertoires[human_uid] = set()
        self._individual_repertoires[human_uid].add(element_id)
        elem.register_adoption(human_uid, location_id, tick, from_human_id=None, channel="foundational")
        return True

    def calculate_adoption_probability(
        self,
        element: CulturalElement,
        learner: SyntheticHuman,
        channel: str,
        trust_in_source: float = 0.5,
        respect_for_source: float = 0.5,
    ) -> float:
        """Compute bounded non-deterministic adoption probability based on psychology and stage."""
        # Baseline channel receptivity
        channel_weights = {
            "family": 0.40,
            "caregiver": 0.45,
            "mentorship": 0.35,
            "education": 0.30,
            "friendship": 0.25,
            "festival": 0.35,
            "dialogue": 0.20,
            "observation": 0.15,
        }
        base_p = channel_weights.get(channel, 0.20)

        # Developmental Stage Modulation:
        # Children are highly impressionable sponges; older adults are conservative preservers
        stage = learner.demographics.stage
        if stage in (DevelopmentalStage.INFANCY, DevelopmentalStage.EARLY_CHILDHOOD):
            stage_mult = 1.6 if channel in ("family", "caregiver") else 0.3
        elif stage == DevelopmentalStage.CHILDHOOD:
            stage_mult = 1.4
        elif stage == DevelopmentalStage.ADOLESCENCE:
            stage_mult = 1.2
        elif stage in (DevelopmentalStage.EARLY_ADULTHOOD, DevelopmentalStage.ADULTHOOD):
            stage_mult = 1.0
        elif stage == DevelopmentalStage.OLDER_ADULTHOOD:
            stage_mult = 0.65  # Resistant to new novel fads
        else:
            stage_mult = 1.0

        # Personality Trait Modulation:
        traits = learner.personality.traits if learner.personality else None
        if traits:
            openness = traits.get_trait_value("openness")
            agreeableness = traits.get_trait_value("agreeableness")
            conscientiousness = traits.get_trait_value("conscientiousness")
        else:
            openness, agreeableness, conscientiousness = 0.5, 0.5, 0.5

        # Relational credibility
        rel_credibility = 0.5 * trust_in_source + 0.5 * respect_for_source

        # Cumulative exposure factor
        exposures = self._exposure_history.get((learner.uid, element.element_id), 0)
        exposure_boost = min(0.30, exposures * 0.05)

        # Traditions and informal rules appeal to high conscientiousness/agreeableness;
        # Crafts and expressions appeal to openness
        if element.element_type in (CulturalElementType.TRADITION, CulturalElementType.INFORMAL_RULE):
            trait_fit = 0.4 * agreeableness + 0.4 * conscientiousness + 0.2 * (1.0 - openness)
        else:
            trait_fit = 0.6 * openness + 0.4 * agreeableness

        prob = (base_p * stage_mult * (0.6 + 0.4 * rel_credibility) * (0.7 + 0.6 * trait_fit)) + exposure_boost
        return float(np.clip(prob, 0.02, 0.95))

    def attempt_transmission(
        self,
        element_id: str,
        source_human: SyntheticHuman,
        learner: SyntheticHuman,
        channel: str,
        current_tick: Tick,
        trust_in_source: float = 0.5,
        respect_for_source: float = 0.5,
        allow_mutation: bool = True,
    ) -> tuple[bool, str, Optional[CulturalElement]]:
        """Attempt to transmit a cultural element from source to learner.

        Outcomes:
        - Accepted as-is
        - Accepted with creative reinterpretation / modification (mutation)
        - Rejected / deferred
        """
        elem = self.get_element(element_id)
        if not elem:
            return False, "Element does not exist", None

        if self.has_adopted(learner.uid, element_id):
            # Reinforce exposure
            self._exposure_history[(learner.uid, element_id)] = (
                self._exposure_history.get((learner.uid, element_id), 0) + 1
            )
            return True, "Already practicing", elem

        # Record exposure
        self._exposure_history[(learner.uid, element_id)] = (
            self._exposure_history.get((learner.uid, element_id), 0) + 1
        )

        p_adopt = self.calculate_adoption_probability(
            elem, learner, channel, trust_in_source, respect_for_source
        )

        if self.rng.random() >= p_adopt:
            # Rejected or deferred
            elem.transmission_history.append(
                elem.transmission_history[-1].__class__(
                    from_human_id=source_human.uid,
                    to_human_id=learner.uid,
                    channel=channel,
                    tick=current_tick,
                    accepted=False,
                    modified=False,
                    notes=f"Rejection probability {1.0 - p_adopt:.2f}",
                )
            )
            return False, "Transmission declined by learner", None

        # Check for mutation/reinterpretation (higher for high openness adolescents/young adults)
        openness = (
            learner.personality.traits.get_trait_value("openness")
            if learner.personality
            else 0.5
        )
        p_mutate = 0.12 * openness if allow_mutation else 0.0

        if self.rng.random() < p_mutate:
            # Create a localized variant/mutation
            mutated = elem.create_mutation(
                innovator_uid=learner.uid,
                new_name=f"{elem.name} (Modificado por {learner.identity.given_name})",
                modification_desc=f"Reinterpreted by {learner.name} during {channel}",
                current_tick=current_tick,
            )
            self.register_element(mutated)
            if learner.uid not in self._individual_repertoires:
                self._individual_repertoires[learner.uid] = set()
            self._individual_repertoires[learner.uid].add(mutated.element_id)
            return True, "Adopted with individual modification", mutated

        # Accepted faithfully
        if learner.uid not in self._individual_repertoires:
            self._individual_repertoires[learner.uid] = set()
        self._individual_repertoires[learner.uid].add(elem.element_id)

        loc = learner.physical_state.current_location_id
        elem.register_adoption(
            human_id=learner.uid,
            location_id=loc,
            tick=current_tick,
            from_human_id=source_human.uid,
            channel=channel,
            modified=False,
        )
        return True, "Adopted faithfully", elem

    def decay_unpracticed_culture(self, current_tick: Tick) -> list[str]:
        """Check all cultural elements for disuse and mark abandoned traditions."""
        abandoned_ids = []
        for elem in self._elements.values():
            still_active = elem.check_vitality(current_tick)
            if not still_active:
                abandoned_ids.append(elem.element_id)
        return abandoned_ids
