"""Multi-dimensional interpersonal relationships with deep interaction histories."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from saltbor.core.types import HumanID, Tick


class RelationshipType(enum.Enum):
    """Primary qualitative categorization of the interpersonal bond."""

    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    COLLEAGUE = "colleague"
    BUSINESS_PARTNER = "business_partner"
    MENTOR_APPRENTICE = "mentor_apprentice"
    FAMILY = "family"
    PARTNER = "partner"
    RIVAL = "rival"
    ENEMY = "enemy"


@dataclass
class InterpersonalEvent:
    """Historical record of an interpersonal event with lasting emotional valence."""

    tick: Tick
    interaction_type: str  # "cooperate", "betrayal", "loan", "gift", "insult", "apology", "reconcile"
    description: str
    impact_affection: float
    impact_trust: float
    impact_respect: float
    impact_resentment: float


@dataclass
class MultiDimensionalRelationship:
    """A rich 10-dimensional directed or mutual interpersonal relationship.

    Tracks nuanced social attitudes where positive interactions do not automatically
    erase severe betrayals, and obligations persist over time.
    """

    relationship_id: str
    human_a_id: HumanID
    human_b_id: HumanID
    relationship_type: RelationshipType = RelationshipType.ACQUAINTANCE

    # The 10 Core Social Dimensions
    affection: float = 0.5         # Emotional warmth [-1.0, 1.0]
    trust: float = 0.5             # Perceived reliability & safety [0.0, 1.0]
    respect: float = 0.5           # Perceived competence, status, skill [0.0, 1.0]
    familiarity: float = 0.2       # Depth of shared exposure [0.0, 1.0]
    cooperation: float = 0.5       # Propensity and history of joint action [0.0, 1.0]
    dependence: float = 0.0        # Economic or physical reliance on other [0.0, 1.0]
    conflict: float = 0.0          # Current active friction [0.0, 1.0]
    resentment: float = 0.0        # Lingering hostility from past betrayals [0.0, 1.0]
    reciprocity_balance: float = 0.0 # Net favors (+A owes B, -B owes A) [-100.0, 100.0]
    social_obligation: float = 0.0 # Moral / kinship duty (e.g. elder/child care) [0.0, 1.0]

    # Interaction History & Metadata
    interaction_count: int = 0
    last_interaction_tick: Tick = 0
    history: list[InterpersonalEvent] = field(default_factory=list)

    def record_interaction(
        self,
        tick: Tick,
        interaction_type: str,
        description: str,
        affection_delta: float = 0.0,
        trust_delta: float = 0.0,
        respect_delta: float = 0.0,
        conflict_delta: float = 0.0,
        favor_delta: float = 0.0,
    ) -> None:
        """Update multi-dimensional attitudes based on an interpersonal event."""
        self.interaction_count += 1
        self.last_interaction_tick = tick
        self.familiarity = min(1.0, self.familiarity + 0.03)

        # Apply shifts
        self.affection = max(-1.0, min(1.0, self.affection + affection_delta))
        self.respect = max(0.0, min(1.0, self.respect + respect_delta))
        self.conflict = max(0.0, min(1.0, self.conflict + conflict_delta))
        self.reciprocity_balance += favor_delta

        # Resentment & Trust asymmetry:
        # Trust is hard to build and easy to break.
        # Betrayal spikes resentment which decays very slowly.
        if trust_delta < 0.0:
            self.trust = max(0.0, self.trust + trust_delta)
            # Severe trust drops spike lingering resentment
            if trust_delta <= -0.25:
                self.resentment = min(1.0, self.resentment + abs(trust_delta) * 1.2)
        else:
            # If high resentment exists, positive interactions build trust much more slowly
            damped_trust = trust_delta * max(0.2, 1.0 - self.resentment)
            self.trust = min(1.0, self.trust + damped_trust)
            # Positive cooperation gently softens resentment
            self.resentment = max(0.0, self.resentment - 0.03)

        # Update cooperation inclination
        self.cooperation = max(
            0.0,
            min(1.0, 0.4 * self.trust + 0.3 * self.affection + 0.3 * (1.0 - self.resentment)),
        )

        # Update qualitative archetype
        self._update_relationship_type()

        self.history.append(
            InterpersonalEvent(
                tick=tick,
                interaction_type=interaction_type,
                description=description,
                impact_affection=affection_delta,
                impact_trust=trust_delta,
                impact_respect=respect_delta,
                impact_resentment=self.resentment,
            )
        )

    def _update_relationship_type(self) -> None:
        """Derive qualitative relationship classification from 10-dimensional state."""
        if self.relationship_type in (RelationshipType.FAMILY, RelationshipType.PARTNER, RelationshipType.MENTOR_APPRENTICE):
            return  # Retain kinship, partnership, or mentorship status

        if self.conflict > 0.65 or self.resentment > 0.70:
            self.relationship_type = RelationshipType.ENEMY if self.resentment > 0.85 else RelationshipType.RIVAL
        elif self.trust > 0.75 and self.affection > 0.70:
            self.relationship_type = RelationshipType.CLOSE_FRIEND
        elif self.trust > 0.55 and self.affection > 0.40:
            self.relationship_type = RelationshipType.FRIEND
        elif self.respect > 0.60 and self.cooperation > 0.50:
            self.relationship_type = RelationshipType.COLLEAGUE
        elif self.familiarity > 0.30:
            self.relationship_type = RelationshipType.ACQUAINTANCE
        else:
            self.relationship_type = RelationshipType.STRANGER
