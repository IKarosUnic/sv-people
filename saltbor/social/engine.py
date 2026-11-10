"""Social engine — manages all inter-individual relationships."""

from __future__ import annotations

import logging
from typing import Iterator, Optional

from saltbor.core.types import HumanID, RelationshipType, Tick
from saltbor.social.relationship import DirectionalAttitude, Relationship

logger = logging.getLogger(__name__)


class SocialEngine:
    """Centralised relationship store for the entire simulation.

    Keys are normalised as ``(min(a, b), max(a, b))`` so that each pair
    is stored exactly once regardless of argument order.
    """

    def __init__(self) -> None:
        self._relationships: dict[tuple[HumanID, HumanID], Relationship] = {}

    # ------------------------------------------------------------------
    # Key normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _key(a: HumanID, b: HumanID) -> tuple[HumanID, HumanID]:
        """Return a deterministic sorted tuple key for a pair of IDs."""
        return (a, b) if a <= b else (b, a)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_relationship(self, a_id: HumanID, b_id: HumanID) -> Relationship:
        """Fetch the relationship between *a* and *b*.

        If no relationship exists yet, a new :data:`STRANGER` relationship
        is created, stored, and returned.
        """
        key = self._key(a_id, b_id)
        if key not in self._relationships:
            rel = Relationship(human_a_id=key[0], human_b_id=key[1])
            self._relationships[key] = rel
            logger.debug("Created STRANGER relationship %s ↔ %s", a_id, b_id)
        return self._relationships[key]

    def get_relationships_for(self, human_id: HumanID) -> list[Relationship]:
        """Return every relationship that *human_id* participates in."""
        return [
            rel
            for key, rel in self._relationships.items()
            if human_id in key
        ]

    def get_friends(self, human_id: HumanID) -> list[HumanID]:
        """Return IDs of everyone considered at least a friend."""
        friend_types = {
            RelationshipType.FRIEND,
            RelationshipType.CLOSE_FRIEND,
        }
        results: list[HumanID] = []
        for rel in self.get_relationships_for(human_id):
            if rel.relationship_type in friend_types:
                results.append(rel.other_id(human_id))
        return results

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def record_interaction(
        self,
        a_id: HumanID,
        b_id: HumanID,
        tick: Tick,
        positive: bool,
        intensity: float = 0.5,
        interaction_type: str = "interaction",
        from_id: Optional[HumanID] = None,
    ) -> Relationship:
        """Record an interaction between two people and update their bond.

        Returns the updated :class:`Relationship`.
        """
        rel = self.get_relationship(a_id, b_id)
        rel.update_after_interaction(
            tick=tick,
            positive=positive,
            intensity=intensity,
            interaction_type=interaction_type,
            from_id=from_id,
        )
        return rel

    def record_directional_interaction(
        self,
        from_id: HumanID,
        to_id: HumanID,
        tick: Tick,
        positive: bool,
        intensity: float = 0.5,
        interaction_type: str = "interaction",
    ) -> Relationship:
        """Record an interaction with directional impact from *from_id* to *to_id*."""
        return self.record_interaction(
            a_id=from_id,
            b_id=to_id,
            tick=tick,
            positive=positive,
            intensity=intensity,
            interaction_type=interaction_type,
            from_id=from_id,
        )

    def record_conflict(
        self,
        a_id: HumanID,
        b_id: HumanID,
        tick: Tick,
        intensity: float = 0.7,
    ) -> Relationship:
        """Record an interpersonal conflict, causing severe trust loss and rivalry."""
        return self.record_interaction(
            a_id=a_id,
            b_id=b_id,
            tick=tick,
            positive=False,
            intensity=intensity,
            interaction_type="conflict",
        )

    def record_cooperation(
        self,
        a_id: HumanID,
        b_id: HumanID,
        tick: Tick,
        intensity: float = 0.6,
    ) -> Relationship:
        """Record cooperative teamwork, strengthening trust, respect, and affinity."""
        return self.record_interaction(
            a_id=a_id,
            b_id=b_id,
            tick=tick,
            positive=True,
            intensity=intensity,
            interaction_type="cooperation",
        )

    def record_reconciliation(
        self,
        a_id: HumanID,
        b_id: HumanID,
        tick: Tick,
        intensity: float = 0.75,
    ) -> Relationship:
        """Record a reconciliation, resolving conflict and restoring trust."""
        return self.record_interaction(
            a_id=a_id,
            b_id=b_id,
            tick=tick,
            positive=True,
            intensity=intensity,
            interaction_type="reconciliation",
        )

    def get_directional_attitude(
        self,
        from_id: HumanID,
        to_id: HumanID,
    ) -> DirectionalAttitude:
        """Fetch the subjective directional attitude held by *from_id* toward *to_id*."""
        rel = self.get_relationship(from_id, to_id)
        return rel.get_attitude(from_id)

    def add_relationship(self, relationship: Relationship) -> None:
        """Directly insert or overwrite a pre-built relationship."""
        key = self._key(relationship.human_a_id, relationship.human_b_id)
        self._relationships[key] = relationship

    # ------------------------------------------------------------------
    # Bulk access
    # ------------------------------------------------------------------

    def get_all_relationships(self) -> list[Relationship]:
        """Return a list of every tracked relationship."""
        return list(self._relationships.values())

    @property
    def count(self) -> int:
        return len(self._relationships)

    def __iter__(self) -> Iterator[Relationship]:
        return iter(self._relationships.values())

    def __len__(self) -> int:
        return len(self._relationships)
