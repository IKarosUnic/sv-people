"""Collective Knowledge Graph (Layer 3).

Represents knowledge preserved and shared across collective aggregates:
families, businesses, schools, cooperatives, social groups, institutions,
and communities. Survives individual death through institutionalization
and cultural transmission.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.graph.relationship import KnowledgeRelationship


@dataclasses.dataclass
class CollectiveKnowledgeItem:
    """A knowledge element shared or institutionalized within a collective."""

    item_id: str                      # node_id or rel_id
    is_relationship: bool
    group_id: str                     # family_id, business_id, school_id, community_id
    group_type: str                   # 'family', 'business', 'school', 'cooperative', 'community', 'guild'
    consensus_level: float = 0.8       # [0.0, 1.0] degree of communal consensus
    documentation_type: str = "oral_tradition"  # 'oral_tradition', 'written_record', 'curriculum', 'guild_standard'
    custodian_uids: list[str] = dataclasses.field(default_factory=list)
    recorded_tick: int = 0
    transmission_count: int = 0
    is_endangered: bool = False       # If active practitioners fall below survival threshold


class CollectiveKnowledgeGraph:
    """Manages communal and institutional knowledge repositories."""

    def __init__(self) -> None:
        # group_id -> dict of item_id -> CollectiveKnowledgeItem
        self._group_repositories: dict[str, dict[str, CollectiveKnowledgeItem]] = {}
        # Shared canonical nodes registered by institutions or communities
        self._preserved_nodes: dict[str, KnowledgeNode] = {}
        self._preserved_relationships: dict[str, KnowledgeRelationship] = {}

    def institutionalize_knowledge(
        self,
        group_id: str,
        group_type: str,
        node: KnowledgeNode,
        documentation_type: str = "written_record",
        custodian_uid: Optional[str] = None,
        tick: int = 0,
    ) -> CollectiveKnowledgeItem:
        """Preserve a knowledge node in an institutional or collective repository."""
        if group_id not in self._group_repositories:
            self._group_repositories[group_id] = {}

        self._preserved_nodes[node.node_id] = node
        custodians = [custodian_uid] if custodian_uid else []

        item = CollectiveKnowledgeItem(
            item_id=node.node_id,
            is_relationship=False,
            group_id=group_id,
            group_type=group_type,
            consensus_level=0.9,
            documentation_type=documentation_type,
            custodian_uids=custodians,
            recorded_tick=tick,
        )
        self._group_repositories[group_id][node.node_id] = item
        return item

    def institutionalize_relationship(
        self,
        group_id: str,
        group_type: str,
        rel: KnowledgeRelationship,
        documentation_type: str = "written_record",
        custodian_uid: Optional[str] = None,
        tick: int = 0,
    ) -> CollectiveKnowledgeItem:
        """Preserve a relationship in the collective repository."""
        if group_id not in self._group_repositories:
            self._group_repositories[group_id] = {}

        self._preserved_relationships[rel.rel_id] = rel
        custodians = [custodian_uid] if custodian_uid else []

        item = CollectiveKnowledgeItem(
            item_id=rel.rel_id,
            is_relationship=True,
            group_id=group_id,
            group_type=group_type,
            consensus_level=0.9,
            documentation_type=documentation_type,
            custodian_uids=custodians,
            recorded_tick=tick,
        )
        self._group_repositories[group_id][rel.rel_id] = item
        return item

    def get_collective_knowledge(self, group_id: str) -> list[CollectiveKnowledgeItem]:
        """Fetch all knowledge items preserved by a group."""
        return list(self._group_repositories.get(group_id, {}).values())

    def get_preserved_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self._preserved_nodes.get(node_id)

    def check_endangered_knowledge(self, active_agent_uids: set[str]) -> list[CollectiveKnowledgeItem]:
        """Flag knowledge items whose living custodians are no longer in the active population."""
        endangered = []
        for repo in self._group_repositories.values():
            for item in repo.values():
                if item.documentation_type == "oral_tradition":
                    living_custodians = [c for c in item.custodian_uids if c in active_agent_uids]
                    if len(living_custodians) <= 1:
                        item.is_endangered = True
                        endangered.append(item)
                    else:
                        item.is_endangered = False
        return endangered
