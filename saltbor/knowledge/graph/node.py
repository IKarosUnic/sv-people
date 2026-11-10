"""Extensible Knowledge Node schemas for Saltbor Phase 0.6.

Represents concepts, physical objects, materials, organisms, people, locations,
events, activities, professions, skills, procedures, resources, institutions,
scientific principles, cultural practices, economic concepts, hypotheses,
problems, and solutions.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Optional


class NodeType(str, enum.Enum):
    """Extensible categories of knowledge entities."""

    CONCEPT = "concept"
    OBJECT = "object"
    MATERIAL = "material"
    ORGANISM = "organism"
    PERSON = "person"
    PLACE = "place"
    EVENT = "event"
    ACTIVITY = "activity"
    PROFESSION = "profession"
    SKILL = "skill"
    TECHNIQUE = "technique"
    PROCEDURE = "procedure"
    RESOURCE = "resource"
    INSTITUTION = "institution"
    SCIENTIFIC_PRINCIPLE = "scientific_principle"
    CULTURAL_PRACTICE = "cultural_practice"
    ECONOMIC_CONCEPT = "economic_concept"
    HYPOTHESIS = "hypothesis"
    PROBLEM = "problem"
    SOLUTION = "solution"
    CUSTOM = "custom"


class ValidationStatus(str, enum.Enum):
    """Epistemic validation status of a node or assertion."""

    PROPOSED = "proposed"
    UNTESTED = "untested"
    TESTING = "testing"
    SUPPORTED = "supported"
    REPLICATED = "replicated"
    DISPUTED = "disputed"
    REFUTED = "refuted"
    OBSOLETE = "obsolete"
    CANONICAL = "canonical"


@dataclass
class NodeEvolutionRecord:
    """Historical record of updates or revisions to a knowledge node."""

    version: int
    timestamp_tick: int
    author_id: Optional[str]
    change_summary: str
    previous_properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeNode:
    """Core entity node within the multi-layer knowledge graph."""

    node_id: str
    node_type: NodeType | str
    label: str
    description: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    created_tick: int = 0
    origin_type: str = "world_genesis"  # e.g., 'world_genesis', 'discovery', 'inference', 'transmission'
    origin_id: Optional[str] = None      # creator human UID, event ID, or theory ID
    validation_status: ValidationStatus = ValidationStatus.CANONICAL
    version: int = 1
    evolution_history: list[NodeEvolutionRecord] = field(default_factory=list)
    external_ref: Optional[str] = None
    related_concept_ids: list[str] = field(default_factory=list)

    def update_properties(
        self,
        new_properties: dict[str, Any],
        author_id: Optional[str] = None,
        tick: int = 0,
        summary: str = "Property update",
    ) -> None:
        """Update properties while maintaining an evolutionary audit trail."""
        prev = dict(self.properties)
        self.evolution_history.append(
            NodeEvolutionRecord(
                version=self.version,
                timestamp_tick=tick,
                author_id=author_id,
                change_summary=summary,
                previous_properties=prev,
            )
        )
        self.properties.update(new_properties)
        self.version += 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize node to JSON-compatible dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": str(self.node_type.value if isinstance(self.node_type, NodeType) else self.node_type),
            "label": self.label,
            "description": self.description,
            "properties": self.properties,
            "created_tick": self.created_tick,
            "origin_type": self.origin_type,
            "origin_id": self.origin_id,
            "validation_status": str(self.validation_status.value if isinstance(self.validation_status, ValidationStatus) else self.validation_status),
            "version": self.version,
            "external_ref": self.external_ref,
            "related_concept_ids": self.related_concept_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeNode:
        """Construct node from serialized dictionary."""
        node_type = data.get("node_type", NodeType.CONCEPT.value)
        try:
            parsed_type = NodeType(node_type)
        except ValueError:
            parsed_type = node_type

        val_status = data.get("validation_status", ValidationStatus.CANONICAL.value)
        try:
            parsed_val = ValidationStatus(val_status)
        except ValueError:
            parsed_val = ValidationStatus.CANONICAL

        return cls(
            node_id=data["node_id"],
            node_type=parsed_type,
            label=data["label"],
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            created_tick=data.get("created_tick", 0),
            origin_type=data.get("origin_type", "world_genesis"),
            origin_id=data.get("origin_id"),
            validation_status=parsed_val,
            version=data.get("version", 1),
            external_ref=data.get("external_ref"),
            related_concept_ids=data.get("related_concept_ids", []),
        )
