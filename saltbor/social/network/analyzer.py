"""Social network analysis: graph topology, centrality, clustering, bridges, and isolation."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID
from saltbor.social.dimensions.relationship import (
    MultiDimensionalRelationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)


@dataclass
class NetworkMetrics:
    """Network topological statistics for an individual agent."""

    human_uid: HumanID
    degree: int                        # Number of active social ties
    weighted_degree: float             # Sum of positive trust/affection tie strengths
    clustering_coefficient: float     # Density of ties among neighbors
    is_social_bridge: bool             # Connects otherwise disconnected social groups
    is_socially_isolated: bool         # Very few or zero active ties
    prominent_role: str = "member"     # "hub", "bridge", "isolated", "cohesive_member"


@dataclass
class SettlementNetworkReport:
    """Global settlement network structural diagnostics."""

    total_nodes: int
    total_edges: int
    density: float
    average_degree: float
    isolated_nodes_count: int
    bridge_nodes_count: int
    cluster_count: int
    modularity_estimate: float
    average_clustering_coefficient: float


class SocialNetworkAnalyzer:
    """Computes dynamic graph metrics over interpersonal relationship graphs."""

    def __init__(self) -> None:
        pass

    def build_graph(
        self,
        relationships: list[MultiDimensionalRelationship],
        min_trust_threshold: float = 0.40,
    ) -> dict[HumanID, set[HumanID]]:
        """Construct an adjacency list of active social ties."""
        adj: dict[HumanID, set[HumanID]] = defaultdict(set)
        for rel in relationships:
            # Positive tie requires mutual or directed trust/affection
            if rel.trust >= min_trust_threshold and rel.conflict < 0.60:
                adj[rel.human_a_id].add(rel.human_b_id)
                adj[rel.human_b_id].add(rel.human_a_id)
        return adj

    def analyze_individual(
        self,
        target_uid: HumanID,
        adj: dict[HumanID, set[HumanID]],
        relationships: list[MultiDimensionalRelationship],
    ) -> NetworkMetrics:
        """Calculate graph centrality and position metrics for an individual."""
        neighbors = adj.get(target_uid, set())
        deg = len(neighbors)

        # Weighted degree based on trust & affection
        w_deg = 0.0
        for rel in relationships:
            if rel.human_a_id == target_uid or rel.human_b_id == target_uid:
                other = rel.human_b_id if rel.human_a_id == target_uid else rel.human_a_id
                if other in neighbors:
                    w_deg += max(0.0, rel.trust * 0.5 + max(0.0, rel.affection) * 0.5)

        # Local clustering coefficient
        if deg < 2:
            cc = 0.0
        else:
            possible_edges = deg * (deg - 1) / 2.0
            actual_edges = 0
            neighbor_list = list(neighbors)
            for i in range(deg):
                for j in range(i + 1, deg):
                    if neighbor_list[j] in adj.get(neighbor_list[i], set()):
                        actual_edges += 1
            cc = actual_edges / possible_edges

        # Bridge detection: check if neighbor pairs lack direct connections
        is_bridge = deg >= 2 and cc < 0.25
        is_isolated = deg <= 1

        role = "member"
        if is_isolated:
            role = "isolated"
        elif deg >= 5:
            role = "hub"
        elif is_bridge:
            role = "bridge"

        return NetworkMetrics(
            human_uid=target_uid,
            degree=deg,
            weighted_degree=round(w_deg, 2),
            clustering_coefficient=round(cc, 3),
            is_social_bridge=is_bridge,
            is_socially_isolated=is_isolated,
            prominent_role=role,
        )

    def analyze_settlement_network(
        self,
        all_uids: list[HumanID],
        relationships: list[MultiDimensionalRelationship],
    ) -> SettlementNetworkReport:
        """Run macro-level settlement social topology analysis."""
        adj = self.build_graph(relationships)
        total_nodes = len(all_uids)
        if total_nodes == 0:
            return SettlementNetworkReport(
                total_nodes=0,
                total_edges=0,
                density=0.0,
                average_degree=0.0,
                isolated_nodes_count=0,
                bridge_nodes_count=0,
                cluster_count=0,
                modularity_estimate=0.0,
                average_clustering_coefficient=0.0,
            )

        edge_set = set()
        for u, neighbors in adj.items():
            for v in neighbors:
                edge = tuple(sorted([str(u), str(v)]))
                edge_set.add(edge)
        total_edges = len(edge_set)

        possible_edges = total_nodes * (total_nodes - 1) / 2.0
        density = round(total_edges / possible_edges, 4) if possible_edges > 0 else 0.0

        degrees = [len(adj.get(u, set())) for u in all_uids]
        avg_deg = round(float(np.mean(degrees)), 2)

        indiv_metrics = [self.analyze_individual(u, adj, relationships) for u in all_uids]
        isolated_count = sum(1 for m in indiv_metrics if m.is_socially_isolated)
        bridge_count = sum(1 for m in indiv_metrics if m.is_social_bridge)
        avg_cc = round(float(np.mean([m.clustering_coefficient for m in indiv_metrics])), 3)

        # Connected components (clusters)
        visited = set()
        clusters = 0
        for u in all_uids:
            if u not in visited:
                clusters += 1
                queue = [u]
                visited.add(u)
                while queue:
                    curr = queue.pop(0)
                    for nbr in adj.get(curr, set()):
                        if nbr not in visited:
                            visited.add(nbr)
                            queue.append(nbr)

        return SettlementNetworkReport(
            total_nodes=total_nodes,
            total_edges=total_edges,
            density=density,
            average_degree=avg_deg,
            isolated_nodes_count=isolated_count,
            bridge_nodes_count=bridge_count,
            cluster_count=clusters,
            modularity_estimate=round(max(0.1, 1.0 - density), 2),
            average_clustering_coefficient=avg_cc,
        )
