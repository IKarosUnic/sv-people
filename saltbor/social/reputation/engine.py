"""Contextual reputation, domain competence, and emergent social influence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


@dataclass
class ContextualReputation:
    """An individual's multidimensional standing across distinct functional domains."""

    human_uid: HumanID
    # Domain specific standings [0.0 to 1.0]
    craft_competence: float = 0.5       # Procedural skill, quality of goods
    financial_integrity: float = 0.5    # Debt repayment, fair pricing, reliability
    civic_contribution: float = 0.5     # Assembly participation, festival volunteering
    moral_standing: float = 0.5         # Honesty, kindness, conflict de-escalation

    # Group specific reputation ratings: group_id -> score in [0.0, 1.0]
    group_ratings: dict[str, float] = field(default_factory=dict)

    def calculate_influence_in_context(
        self,
        domain: str = "general",
        target_group_id: Optional[str] = None,
        network_degree: int = 2,
    ) -> float:
        """Derive situational social influence without a single universal score."""
        domain_weights = {
            "craft": (0.6 * self.craft_competence + 0.2 * self.financial_integrity + 0.2 * self.moral_standing),
            "economic": (0.6 * self.financial_integrity + 0.3 * self.craft_competence + 0.1 * self.civic_contribution),
            "governance": (0.5 * self.civic_contribution + 0.3 * self.moral_standing + 0.2 * self.financial_integrity),
            "moral": (0.7 * self.moral_standing + 0.3 * self.civic_contribution),
            "general": (0.25 * self.craft_competence + 0.25 * self.financial_integrity + 0.25 * self.civic_contribution + 0.25 * self.moral_standing),
        }
        base_influence = domain_weights.get(domain, domain_weights["general"])

        # Group affinity modulation
        if target_group_id and target_group_id in self.group_ratings:
            base_influence = 0.6 * base_influence + 0.4 * self.group_ratings[target_group_id]

        # Network amplification: individuals with extensive ties have broader reach
        network_mult = min(1.3, 0.85 + (network_degree * 0.05))
        return float(np.clip(base_influence * network_mult, 0.05, 1.0))


class ContextualReputationEngine:
    """Evaluates and updates differentiated reputation profiles across the community."""

    def __init__(self) -> None:
        self._profiles: dict[HumanID, ContextualReputation] = {}

    def get_or_create(self, human_uid: HumanID) -> ContextualReputation:
        if human_uid not in self._profiles:
            self._profiles[human_uid] = ContextualReputation(human_uid=human_uid)
        return self._profiles[human_uid]

    def record_production_success(self, worker_uid: HumanID, quality_boost: float = 0.04) -> None:
        """High quality manufacturing improves craft competence reputation."""
        prof = self.get_or_create(worker_uid)
        prof.craft_competence = min(1.0, prof.craft_competence + quality_boost)

    def record_loan_repayment(self, borrower_uid: HumanID, on_time: bool = True) -> None:
        """Loan repayment elevates financial integrity; default severely damages it."""
        prof = self.get_or_create(borrower_uid)
        if on_time:
            prof.financial_integrity = min(1.0, prof.financial_integrity + 0.05)
        else:
            prof.financial_integrity = max(0.0, prof.financial_integrity - 0.25)

    def record_civic_service(self, volunteer_uid: HumanID, contribution_magnitude: float = 0.05) -> None:
        """Festival organization or assembly leadership elevates civic reputation."""
        prof = self.get_or_create(volunteer_uid)
        prof.civic_contribution = min(1.0, prof.civic_contribution + contribution_magnitude)

    def record_interpersonal_conduct(self, human_uid: HumanID, is_constructive: bool) -> None:
        """Cooperation or apology boosts moral standing; betrayal severely reduces it."""
        prof = self.get_or_create(human_uid)
        if is_constructive:
            prof.moral_standing = min(1.0, prof.moral_standing + 0.03)
        else:
            prof.moral_standing = max(0.0, prof.moral_standing - 0.15)

    def set_group_rating(self, human_uid: HumanID, group_id: str, rating: float) -> None:
        prof = self.get_or_create(human_uid)
        prof.group_ratings[group_id] = float(np.clip(rating, 0.0, 1.0))
