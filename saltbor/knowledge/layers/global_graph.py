"""Global World Knowledge Graph (Layer 1).

Represents the canonical world knowledge of the simulated environment:
concepts, materials, objects, locations, known physical properties,
available techniques, and validated relationships.
"""

from __future__ import annotations

import logging
from typing import Optional

from saltbor.knowledge.graph.engine import KnowledgeGraphEngine
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType

logger = logging.getLogger(__name__)


class GlobalKnowledgeGraph:
    """The canonical, authoritative knowledge ground truth of the simulated world."""

    def __init__(self) -> None:
        self.engine = KnowledgeGraphEngine(name="GlobalWorldKnowledge")

    def register_concept(
        self,
        node_id: str,
        label: str,
        node_type: NodeType | str = NodeType.CONCEPT,
        description: str = "",
        properties: Optional[dict] = None,
        created_tick: int = 0,
    ) -> KnowledgeNode:
        """Register a canonical concept or entity into the global world graph."""
        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            description=description,
            properties=properties or {},
            created_tick=created_tick,
            origin_type="world_genesis",
            validation_status=ValidationStatus.CANONICAL,
        )
        self.engine.add_node(node)
        return node

    def register_relationship(
        self,
        rel_id: str,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType | str,
        weight: float = 1.0,
        metadata: Optional[dict] = None,
        created_tick: int = 0,
    ) -> KnowledgeRelationship:
        """Register a canonical, validated relationship."""
        rel = KnowledgeRelationship(
            rel_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            weight=weight,
            confidence=1.0,
            provenance_source="canonical_world_physics",
            created_tick=created_tick,
            metadata=metadata or {},
        )
        self.engine.add_relationship(rel)
        return rel

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self.engine.get_node(node_id)

    def get_relationship(self, rel_id: str) -> Optional[KnowledgeRelationship]:
        return self.engine.get_relationship(rel_id)

    def has_node(self, node_id: str) -> bool:
        return self.engine.has_node(node_id)
