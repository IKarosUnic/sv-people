"""Pairwise relationship between two synthetic humans."""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from saltbor.core.types import HumanID, RelationshipID, RelationshipType, Tick


class Relationship(BaseModel):
    """Directed-neutral relationship between two individuals.

    The relationship is stored once and is symmetric — field order of
    ``human_a_id`` and ``human_b_id`` has no semantic meaning.
    All float scores are in ``[0.0, 1.0]``.
    """

    relationship_id: RelationshipID = Field(default_factory=uuid.uuid4)
    human_a_id: HumanID
    human_b_id: HumanID
    relationship_type: RelationshipType = Field(default=RelationshipType.STRANGER)

    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    affinity: float = Field(default=0.5, ge=0.0, le=1.0)
    familiarity: float = Field(default=0.0, ge=0.0, le=1.0)
    interaction_count: int = Field(default=0, ge=0)
    last_interaction_tick: Optional[Tick] = None
    history: list[str] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def other_id(self, human_id: HumanID) -> HumanID:
        """Return the ID of the *other* person in this relationship.

        Raises
        ------
        ValueError
            If *human_id* is not one of the participants.
        """
        if human_id == self.human_a_id:
            return self.human_b_id
        if human_id == self.human_b_id:
            return self.human_a_id
        raise ValueError(
            f"{human_id} is not a participant of relationship {self.relationship_id}"
        )

    def update_after_interaction(
        self,
        tick: Tick,
        positive: bool,
        intensity: float = 0.5,
    ) -> None:
        """Adjust trust, affinity, and familiarity after an interaction.

        Parameters
        ----------
        tick:
            Current simulation tick.
        positive:
            Whether the interaction was positive.
        intensity:
            Strength of the interaction effect in ``[0, 1]``.
        """
        intensity = max(0.0, min(1.0, intensity))
        delta = intensity * 0.1  # small incremental change

        if positive:
            self.trust = min(1.0, self.trust + delta)
            self.affinity = min(1.0, self.affinity + delta * 1.2)
        else:
            self.trust = max(0.0, self.trust - delta * 1.5)
            self.affinity = max(0.0, self.affinity - delta)

        # Familiarity always grows with interaction
        self.familiarity = min(1.0, self.familiarity + delta * 0.5)

        self.interaction_count += 1
        self.last_interaction_tick = tick

        # Auto-promote relationship type based on familiarity/affinity
        self._auto_promote()

    def overall_quality(self) -> float:
        """Weighted average of trust and affinity.

        Trust is weighted slightly more heavily because betrayal has
        outsized consequences.
        """
        return round(0.55 * self.trust + 0.45 * self.affinity, 4)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _auto_promote(self) -> None:
        """Promote (or demote) relationship type based on current scores.

        Family and Partner types are never auto-assigned — only social
        progression through acquaintance → friend → close_friend.
        """
        if self.relationship_type in (
            RelationshipType.FAMILY,
            RelationshipType.PARTNER,
        ):
            return  # never auto-change these

        quality = self.overall_quality()

        if quality < 0.2:
            self.relationship_type = RelationshipType.RIVAL
        elif self.familiarity < 0.1:
            self.relationship_type = RelationshipType.STRANGER
        elif self.familiarity < 0.35:
            self.relationship_type = RelationshipType.ACQUAINTANCE
        elif quality >= 0.75 and self.familiarity >= 0.7:
            self.relationship_type = RelationshipType.CLOSE_FRIEND
        elif quality >= 0.55 and self.familiarity >= 0.4:
            self.relationship_type = RelationshipType.FRIEND
        else:
            self.relationship_type = RelationshipType.ACQUAINTANCE
