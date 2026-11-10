"""Extensible Knowledge Relationship schemas for Saltbor Phase 0.6.

Defines typed, directed relationships with epistemic confidence, provenance,
and metadata.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class RelationshipType(str, enum.Enum):
    """Extensible relationship types connecting knowledge nodes."""

    IS_A = "IS_A"
    PART_OF = "PART_OF"
    HAS_PROPERTY = "HAS_PROPERTY"
    REQUIRES = "REQUIRES"
    PRODUCES = "PRODUCES"
    CAUSES = "CAUSES"
    INFLUENCES = "INFLUENCES"
    DEPENDS_ON = "DEPENDS_ON"
    LOCATED_IN = "LOCATED_IN"
    USED_FOR = "USED_FOR"
    LEARNED_FROM = "LEARNED_FROM"
    TAUGHT_BY = "TAUGHT_BY"
    DISCOVERED_BY = "DISCOVERED_BY"
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"
    DERIVED_FROM = "DERIVED_FROM"
    SIMILAR_TO = "SIMILAR_TO"
    CAN_PERFORM = "CAN_PERFORM"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    BELONGS_TO = "BELONGS_TO"
    ENABLES = "ENABLES"
    INHIBITS = "INHIBITS"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    CUSTOM = "CUSTOM"


@dataclass
class KnowledgeRelationship:
    """Directed, typed relationship between two knowledge nodes."""

    rel_id: str
    source_id: str
    target_id: str
    rel_type: RelationshipType | str
    weight: float = 1.0
    confidence: float = 1.0  # [0.0, 1.0]
    provenance_source: str = "canonical"
    origin_id: Optional[str] = None
    created_tick: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rel_id": self.rel_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": str(self.rel_type.value if isinstance(self.rel_type, RelationshipType) else self.rel_type),
            "weight": self.weight,
            "confidence": self.confidence,
            "provenance_source": self.provenance_source,
            "origin_id": self.origin_id,
            "created_tick": self.created_tick,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeRelationship:
        r_type = data.get("rel_type", RelationshipType.ASSOCIATED_WITH.value)
        try:
            parsed_type = RelationshipType(r_type)
        except ValueError:
            parsed_type = r_type

        return cls(
            rel_id=data["rel_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            rel_type=parsed_type,
            weight=data.get("weight", 1.0),
            confidence=data.get("confidence", 1.0),
            provenance_source=data.get("provenance_source", "canonical"),
            origin_id=data.get("origin_id"),
            created_tick=data.get("created_tick", 0),
            metadata=data.get("metadata", {}),
        )
