"""Pairwise relationship between two synthetic humans."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from saltbor.core.types import HumanID, RelationshipID, RelationshipType, Tick


class DirectionalAttitude(BaseModel):
    """Subjective directional attitude of one individual toward another.

    Represents asymmetric perceptions: Person A may hold high trust and affection
    for Person B while Person B harbors skepticism, respect, or rivalry toward Person A.
    """

    from_human_id: HumanID
    to_human_id: HumanID
    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    affinity: float = Field(default=0.5, ge=0.0, le=1.0)
    respect: float = Field(default=0.5, ge=0.0, le=1.0)
    familiarity: float = Field(default=0.0, ge=0.0, le=1.0)
    rivalry: float = Field(default=0.0, ge=0.0, le=1.0)

    def update(
        self,
        positive: bool,
        intensity: float = 0.5,
        interaction_type: str = "interaction",
    ) -> None:
        """Update attitude following an interaction."""
        intensity = max(0.0, min(1.0, intensity))
        delta = intensity * 0.1

        if positive:
            mult = 2.5 if interaction_type == "reconciliation" else 1.0
            self.trust = min(1.0, self.trust + delta * mult)
            self.affinity = min(1.0, self.affinity + delta * 1.2 * mult)
            self.respect = min(1.0, self.respect + delta * 0.8)
            self.rivalry = max(0.0, self.rivalry - delta * 1.5 * mult)
        else:
            mult = 4.0 if interaction_type in ("conflict", "betrayal") else 1.5
            self.trust = max(0.0, self.trust - delta * mult)
            self.affinity = max(0.0, self.affinity - delta * 1.2)
            self.rivalry = min(1.0, self.rivalry + delta * 1.5)

        self.familiarity = min(1.0, self.familiarity + delta * 0.5)


class Relationship(BaseModel):
    """Interpersonal relationship between two individuals with directional attitudes.

    Contains aggregate/shared metrics for backwards compatibility, along with
    rich directional perspectives for both participants.
    """

    relationship_id: RelationshipID = Field(default_factory=uuid.uuid4)
    human_a_id: HumanID
    human_b_id: HumanID
    relationship_type: RelationshipType = Field(default=RelationshipType.STRANGER)

    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    affinity: float = Field(default=0.5, ge=0.0, le=1.0)
    familiarity: float = Field(default=0.0, ge=0.0, le=1.0)
    respect: float = Field(default=0.5, ge=0.0, le=1.0)
    rivalry: float = Field(default=0.0, ge=0.0, le=1.0)
    interaction_count: int = Field(default=0, ge=0)
    last_interaction_tick: Optional[Tick] = None
    history: list[str] = Field(default_factory=list)

    # Directional attitudes
    attitude_a_to_b: Optional[DirectionalAttitude] = None
    attitude_b_to_a: Optional[DirectionalAttitude] = None

    def model_post_init(self, __context: Any) -> None:
        if self.attitude_a_to_b is None:
            self.attitude_a_to_b = DirectionalAttitude(
                from_human_id=self.human_a_id,
                to_human_id=self.human_b_id,
                trust=self.trust,
                affinity=self.affinity,
                respect=self.respect,
                familiarity=self.familiarity,
                rivalry=self.rivalry,
            )
        if self.attitude_b_to_a is None:
            self.attitude_b_to_a = DirectionalAttitude(
                from_human_id=self.human_b_id,
                to_human_id=self.human_a_id,
                trust=self.trust,
                affinity=self.affinity,
                respect=self.respect,
                familiarity=self.familiarity,
                rivalry=self.rivalry,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def other_id(self, human_id: HumanID) -> HumanID:
        """Return the ID of the *other* person in this relationship."""
        if human_id == self.human_a_id:
            return self.human_b_id
        if human_id == self.human_b_id:
            return self.human_a_id
        raise ValueError(
            f"{human_id} is not a participant of relationship {self.relationship_id}"
        )

    def get_attitude(self, from_id: HumanID) -> DirectionalAttitude:
        """Return directional attitude from *from_id* toward their peer."""
        if from_id == self.human_a_id:
            if self.attitude_a_to_b is None:
                self.model_post_init(None)
            return self.attitude_a_to_b  # type: ignore[return-value]
        elif from_id == self.human_b_id:
            if self.attitude_b_to_a is None:
                self.model_post_init(None)
            return self.attitude_b_to_a  # type: ignore[return-value]
        raise ValueError(f"{from_id} is not part of this relationship")

    def update_after_interaction(
        self,
        tick: Tick,
        positive: bool,
        intensity: float = 0.5,
        interaction_type: str = "interaction",
        from_id: Optional[HumanID] = None,
    ) -> None:
        """Adjust trust, affinity, familiarity, and directional attitudes after an interaction."""
        intensity = max(0.0, min(1.0, intensity))
        delta = intensity * 0.1  # small incremental change

        if positive:
            mult = 2.5 if interaction_type == "reconciliation" else 1.0
            self.trust = min(1.0, self.trust + delta * mult)
            self.affinity = min(1.0, self.affinity + delta * 1.2 * mult)
            self.respect = min(1.0, self.respect + delta * 0.8)
            self.rivalry = max(0.0, self.rivalry - delta * 1.5 * mult)
        else:
            mult = 4.0 if interaction_type in ("conflict", "betrayal") else 1.5
            self.trust = max(0.0, self.trust - delta * mult)
            self.affinity = max(0.0, self.affinity - delta * 1.2)
            self.rivalry = min(1.0, self.rivalry + delta * 1.5)

        # Familiarity always grows with interaction
        self.familiarity = min(1.0, self.familiarity + delta * 0.5)
        self.interaction_count += 1
        self.last_interaction_tick = tick

        # Ensure directional attitudes exist
        if self.attitude_a_to_b is None or self.attitude_b_to_a is None:
            self.model_post_init(None)

        # Update directional attitudes
        if from_id == self.human_a_id:
            self.attitude_a_to_b.update(positive, intensity, interaction_type)  # type: ignore[union-attr]
        elif from_id == self.human_b_id:
            self.attitude_b_to_a.update(positive, intensity, interaction_type)  # type: ignore[union-attr]
        else:
            self.attitude_a_to_b.update(positive, intensity, interaction_type)  # type: ignore[union-attr]
            self.attitude_b_to_a.update(positive, intensity, interaction_type)  # type: ignore[union-attr]

        # Log history
        outcome_str = "Positive" if positive else "Negative"
        entry = f"Tick {tick}: [{interaction_type}] {outcome_str} (intensity={intensity:.2f})"
        self.history.append(entry)

        # Auto-promote relationship type based on familiarity/affinity/rivalry
        self._auto_promote()

    def overall_quality(self) -> float:
        """Weighted average of trust and affinity."""
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
