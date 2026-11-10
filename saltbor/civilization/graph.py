"""Historical Knowledge Graph integration for SALTBOR Phase 1.0.

Extends the Knowledge Graph architecture to support multi-generational and historical queries:
- Node entities: Person, Family, Generation, Community, Settlement, Institution, Organization, Historical Event, Innovation, Tradition, Resource, Technology, Civilization.
- Temporal relationships: Founded, Participated In, Inherited From, Learned From, Transmitted To, Lived In, Migrated To, Worked In, Belonged To, Cooperated With, Conflicted With, Transformed, Influenced, Replaced.
- Temporal provenance: tick, year, validity interval, uncertainty, sources.
- Query engine: answers historical emergence, lineage, and structural causality without fabricating events.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from saltbor.core.types import Tick
from saltbor.knowledge.graph.engine import KnowledgeGraphEngine
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType


class HistoricalNodeType(str, Enum):
    PERSON = "PERSON"
    FAMILY = "FAMILY"
    GENERATION = "GENERATION"
    COMMUNITY = "COMMUNITY"
    SETTLEMENT = "SETTLEMENT"
    INSTITUTION = "INSTITUTION"
    ORGANIZATION = "ORGANIZATION"
    HISTORICAL_EVENT = "HISTORICAL_EVENT"
    INNOVATION = "INNOVATION"
    TRADITION = "TRADITION"
    RESOURCE = "RESOURCE"
    TECHNOLOGY = "TECHNOLOGY"
    CIVILIZATION = "CIVILIZATION"


class HistoricalRelType(str, Enum):
    FOUNDED = "FOUNDED"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    INHERITED_FROM = "INHERITED_FROM"
    LEARNED_FROM = "LEARNED_FROM"
    TRANSMITTED_TO = "TRANSMITTED_TO"
    LIVED_IN = "LIVED_IN"
    MIGRATED_TO = "MIGRATED_TO"
    WORKED_IN = "WORKED_IN"
    BELONGED_TO = "BELONGED_TO"
    COOPERATED_WITH = "COOPERATED_WITH"
    CONFLICTED_WITH = "CONFLICTED_WITH"
    TRANSFORMED = "TRANSFORMED"
    INFLUENCED = "INFLUENCED"
    REPLACED = "REPLACED"


class HistoricalKnowledgeGraph:
    """Specialized historical knowledge network layer wrapping KnowledgeGraphEngine."""

    def __init__(self, base_graph: Optional[KnowledgeGraphEngine] = None) -> None:
        self.graph = base_graph or KnowledgeGraphEngine()
        self.temporal_index: Dict[str, Dict[str, Any]] = {}  # rel_id or node_id -> {year, tick, provenance}

    def add_historical_entity(
        self,
        node_id: str,
        name: str,
        entity_type: HistoricalNodeType,
        year: float,
        tick: Tick = 0,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeNode:
        attrs = attributes or {}
        attrs.update({
            "historical_type": entity_type.value,
            "year": year,
            "tick": tick,
        })
        node = self.graph.add_node(
            node_id=node_id,
            name=name,
            node_type=NodeType.CUSTOM,
            description=f"Historical entity: {entity_type.value} - {name}",
            properties=attrs,
        )
        self.temporal_index[node_id] = {"year": year, "tick": tick, "type": entity_type.value}
        return node

    def link_historical_relation(
        self,
        source_id: str,
        target_id: str,
        rel_type: HistoricalRelType,
        year: float,
        tick: Tick = 0,
        confidence: float = 0.95,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeRelationship:
        meta = metadata or {}
        meta.update({"year": year, "tick": tick})
        rel = self.graph.add_relationship(
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type.value,
            confidence=confidence,
            properties=meta,
        )
        self.temporal_index[rel.rel_id] = {"year": year, "tick": tick, "rel_type": rel_type.value}
        return rel

    def query_settlement_emergence(self, settlement_id: str) -> Dict[str, Any]:
        """Traces back who founded the settlement, early events and contributing families."""
        founders = []
        events = []
        relationships = self.graph.get_incoming_relationships(settlement_id)
        for rel in relationships:
            if rel.rel_type == HistoricalRelType.FOUNDED.value:
                founders.append(rel.source_id)
            elif rel.rel_type in (HistoricalRelType.PARTICIPATED_IN.value, HistoricalRelType.LIVED_IN.value):
                events.append(rel.source_id)

        return {
            "settlement_id": settlement_id,
            "founders": founders,
            "connected_entities": events,
            "temporal_data": self.temporal_index.get(settlement_id, {}),
        }

    def query_intergenerational_transmission(self, ancestor_id: str) -> List[Dict[str, Any]]:
        """Finds knowledge or traditions transmitted from ancestor to descendants."""
        transmissions = []
        outgoing = self.graph.get_outgoing_relationships(ancestor_id)
        for rel in outgoing:
            if rel.rel_type in (HistoricalRelType.TRANSMITTED_TO.value, HistoricalRelType.INHERITED_FROM.value):
                transmissions.append({
                    "target_id": rel.target_id,
                    "rel_type": rel.rel_type,
                    "temporal": self.temporal_index.get(rel.rel_id, {}),
                })
        return transmissions
