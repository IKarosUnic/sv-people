"""Romantic Relationships, Dimensions, Infidelity & Heartbreak Models (Phase 1.5 Extension).

Models authentic multi-dimensional romantic trajectories:
- Not a single numerical score: explicit dimensions of attraction, affection, trust, commitment,
  compatibility, communication, jealousy, and conflict.
- Distinct stages: interest, dating, cohabitation, marriage, separation, and divorce.
- Causal emergence of jealousy and infidelity based on low commitment, proximity, and dissatisfaction.
- Non-deterministic outcomes: betrayal discovery, emotional devastation, forgiveness vs separation,
  unrequited love, and heartbreak recovery.
"""

from __future__ import annotations

import dataclasses
from typing import Any, List, Optional

from saltbor.core.types import RomanceStage, Tick


@dataclasses.dataclass
class RomanticDimensions:
    """Multi-dimensional psychological vectors of a romantic orientation toward a partner."""
    attraction: float = 0.50             # Physical/intellectual magnetic interest [0, 1]
    affection: float = 0.50              # Warmth, caring, and tenderness [0, 1]
    trust: float = 0.50                  # Confidence in partner's honesty and fidelity [0, 1]
    commitment: float = 0.10             # Desire to maintain long-term mutual bond [0, 1]
    compatibility: float = 0.50          # Shared values, temperament harmony [0, 1]
    communication_quality: float = 0.50  # Mutual openness and constructive conflict resolution [0, 1]
    jealousy: float = 0.10               # Insecurity or apprehension regarding third parties [0, 1]
    conflict_level: float = 0.10         # Active unresolved friction [0, 1]

    def to_dict(self) -> dict[str, float]:
        return {
            "attraction": round(self.attraction, 2),
            "affection": round(self.affection, 2),
            "trust": round(self.trust, 2),
            "commitment": round(self.commitment, 2),
            "compatibility": round(self.compatibility, 2),
            "communication_quality": round(self.communication_quality, 2),
            "jealousy": round(self.jealousy, 2),
            "conflict_level": round(self.conflict_level, 2),
        }


@dataclasses.dataclass
class HeartbreakRecord:
    """Psychological trauma following romantic rejection, unrequited love, or breakup."""
    record_id: str
    individual_uid: str
    former_partner_uid: str
    tick_started: Tick
    pain_intensity: float = 0.70         # Drives grief and sadness [0, 1]
    is_unrequited: bool = False
    reason: str = "Ruptura sentimental"
    recovery_progress: float = 0.0       # Reaches 1.0 as emotional healing occurs

    @property
    def is_healed(self) -> bool:
        return self.recovery_progress >= 0.99

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "individual_uid": self.individual_uid,
            "former_partner_uid": self.former_partner_uid,
            "tick_started": self.tick_started,
            "pain_intensity": self.pain_intensity,
            "is_unrequited": self.is_unrequited,
            "reason": self.reason,
            "recovery_progress": self.recovery_progress,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HeartbreakRecord":
        return cls(
            record_id=str(data.get("record_id", "")),
            individual_uid=str(data.get("individual_uid", "")),
            former_partner_uid=str(data.get("former_partner_uid", "")),
            tick_started=int(data.get("tick_started", 0)),
            pain_intensity=float(data.get("pain_intensity", 0.7)),
            is_unrequited=bool(data.get("is_unrequited", False)),
            reason=str(data.get("reason", "Ruptura sentimental")),
            recovery_progress=float(data.get("recovery_progress", 0.0)),
        )


@dataclasses.dataclass
class InfidelityRecord:
    """Historical incident of romantic betrayal and breach of commitment."""
    record_id: str
    wayward_partner_uid: str
    betrayed_partner_uid: str
    third_party_uid: str
    tick_occurred: Tick
    is_discovered: bool = False
    discovery_tick: Optional[Tick] = None
    outcome: str = "undiscovered"        # "undiscovered", "forgiven_reconciliation", "separation", "divorce"


@dataclasses.dataclass
class RomanticRelationship:
    """An interpersonal pairwise romantic bond between two synthetic individuals."""
    relationship_id: str
    partner_a_id: str
    partner_b_id: str
    stage: RomanceStage = RomanceStage.INTEREST
    dims_a: RomanticDimensions = dataclasses.field(default_factory=RomanticDimensions)
    dims_b: RomanticDimensions = dataclasses.field(default_factory=RomanticDimensions)
    shared_memories_count: int = 0
    dates_count: int = 0
    start_tick: Tick = 0
    marriage_tick: Optional[Tick] = None
    separation_tick: Optional[Tick] = None
    infidelity_history: list[InfidelityRecord] = dataclasses.field(default_factory=list)
    is_active: bool = True

    def get_partner_dims(self, agent_uid: str) -> RomanticDimensions:
        return self.dims_a if agent_uid == self.partner_a_id else self.dims_b

    def get_other_uid(self, agent_uid: str) -> str:
        return self.partner_b_id if agent_uid == self.partner_a_id else self.partner_a_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "partner_a_id": self.partner_a_id,
            "partner_b_id": self.partner_b_id,
            "stage": self.stage.value,
            "dims_a": self.dims_a.to_dict(),
            "dims_b": self.dims_b.to_dict(),
            "shared_memories_count": self.shared_memories_count,
            "dates_count": self.dates_count,
            "start_tick": self.start_tick,
            "marriage_tick": self.marriage_tick,
            "separation_tick": self.separation_tick,
            "infidelities_count": len(self.infidelity_history),
            "is_active": self.is_active,
        }
