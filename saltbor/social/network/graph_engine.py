"""Dynamic Social Network Engine for Saltbor Phase 0.9.

Represents interpersonal relationships as dynamic, multi-relational, directed/undirected
graphs. Supports rich relationship types, independent dimensions, decay, rupture,
reconciliation, indirect social influence, and structural graph topology analysis.
"""

from __future__ import annotations

import enum
import logging
import math
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class SocialRelationType(str, enum.Enum):
    """Categorization of inter-individual ties in the dynamic social network."""

    FAMILY = "family"
    FRIEND = "friend"
    PARTNER = "partner"
    WORK = "work"
    COMMERCIAL = "commercial"
    EDUCATIONAL = "educational"
    COOPERATIVE = "cooperative"
    NEIGHBOR = "neighbor"
    POLITICAL = "political"
    COMMUNITY = "community"
    CONFLICT = "conflict"
    RIVALRY = "rivalry"
    MENTORSHIP = "mentorship"
    DEPENDENCE = "dependence"
    TRUST = "trust"
    DISTRUST = "distrust"
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"


class BondState(str, enum.Enum):
    """Lifecycle status of a social tie."""

    FORMING = "forming"
    ACTIVE = "active"
    STRAINED = "strained"
    BROKEN = "broken"
    RECONCILED = "reconciled"
    DORMANT = "dormant"


@dataclass
class SocialEdge:
    """A multi-dimensional dynamic edge between two synthetic individuals.

    Maintains independent dimensions for trust, affinity, reciprocity balance,
    interaction frequency, history, and active conflict.
    """

    edge_id: str
    source_id: str
    target_id: str
    relation_types: set[SocialRelationType] = field(default_factory=lambda: {SocialRelationType.STRANGER})

    # Independent Dimensions
    intensity: float = 0.5           # [0.0, 1.0] Emotional / social engagement strength
    trust: float = 0.5               # [0.0, 1.0] Reliability & safety expectation
    affinity: float = 0.5            # [0.0, 1.0] Emotional warmth and liking
    reciprocity: float = 0.0         # [-1.0, 1.0] Negative: target owes source; Positive: source owes target
    interaction_frequency: float = 0.1 # [0.0, 1.0] Decaying interaction rate
    conflict_level: float = 0.0      # [0.0, 1.0] Active interpersonal friction
    dependence: float = 0.0          # [0.0, 1.0] Need for other's resources/support
    shared_interests: set[str] = field(default_factory=set)

    # Lifecycle & Temporal Metadata
    status: BondState = BondState.ACTIVE
    created_tick: int = 0
    last_interaction_tick: int = 0
    total_interactions: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def age_ticks(self) -> int:
        return max(0, self.last_interaction_tick - self.created_tick)

    def record_interaction(
        self,
        tick: int,
        event_type: str,
        valence: float,        # [-1.0, 1.0]
        intensity: float = 0.5, # [0.0, 1.0]
        shared_topic: Optional[str] = None,
        description: str = "",
    ) -> None:
        """Update multi-dimensional edge features following an interaction."""
        self.total_interactions += 1
        self.last_interaction_tick = tick
        self.interaction_frequency = min(1.0, self.interaction_frequency + 0.15)

        if shared_topic:
            self.shared_interests.add(shared_topic)

        clamped_intensity = max(0.0, min(1.0, intensity))
        delta = clamped_intensity * 0.15

        if valence > 0.0:
            # Positive encounter
            bonus = 1.8 if event_type in ("reconciliation", "mutual_aid", "cooperation") else 1.0
            self.trust = min(1.0, self.trust + delta * bonus * valence)
            self.affinity = min(1.0, self.affinity + delta * 1.2 * valence)
            self.conflict_level = max(0.0, self.conflict_level - delta * 1.5)

            if event_type == "reconciliation" and self.status in (BondState.BROKEN, BondState.STRAINED):
                self.status = BondState.RECONCILED
            elif self.status == BondState.FORMING and self.total_interactions >= 1:
                self.status = BondState.ACTIVE
        else:
            # Negative encounter / conflict
            penalty = 3.5 if event_type in ("betrayal", "theft", "rupture") else 1.4
            self.trust = max(0.0, self.trust - delta * penalty * abs(valence))
            self.affinity = max(0.0, self.affinity - delta * 1.2 * abs(valence))
            self.conflict_level = min(1.0, self.conflict_level + delta * 1.8 * abs(valence))

            if self.conflict_level >= 0.75 or self.trust <= 0.15:
                self.status = BondState.BROKEN
            elif self.conflict_level >= 0.45:
                self.status = BondState.STRAINED

        # Auto-update qualitative relation types based on dimensions
        self._update_relation_types()

        # Log audit trail
        entry = {
            "tick": tick,
            "event_type": event_type,
            "valence": round(valence, 3),
            "intensity": round(intensity, 3),
            "trust_after": round(self.trust, 3),
            "affinity_after": round(self.affinity, 3),
            "conflict_after": round(self.conflict_level, 3),
            "status": self.status.value,
            "description": description or f"{event_type} interaction",
        }
        self.history.append(entry)
        if len(self.history) > 100:
            self.history.pop(0)

    def decay(self, current_tick: int, decay_rate: float = 0.01) -> None:
        """Decay interaction frequency, affinity, and trust over periods of non-interaction."""
        elapsed = current_tick - self.last_interaction_tick
        if elapsed <= 96:  # Less than a day: no noticeable decay
            return

        decay_steps = elapsed // 96
        factor = math.exp(-decay_rate * decay_steps)
        self.interaction_frequency = max(0.0, self.interaction_frequency * factor)

        # Mild decay of affinity if no interaction, but strong kin/family bonds decay slower
        affinity_decay = 0.005 if SocialRelationType.FAMILY in self.relation_types else 0.02
        self.affinity = max(0.1, self.affinity * (1.0 - affinity_decay * min(5, decay_steps)))

        # Lingering conflict cools down over time
        if self.conflict_level > 0.0:
            self.conflict_level = max(0.0, self.conflict_level * 0.90)

        if self.interaction_frequency < 0.05 and self.status == BondState.ACTIVE:
            self.status = BondState.DORMANT

    def reconcile(self, tick: int, mediator_id: Optional[str] = None) -> None:
        """Formally reconcile a broken or strained relationship."""
        self.status = BondState.RECONCILED
        self.conflict_level = max(0.0, self.conflict_level * 0.3)
        self.trust = min(1.0, self.trust + 0.35)
        self.affinity = min(1.0, self.affinity + 0.30)
        self.relation_types.discard(SocialRelationType.CONFLICT)
        self.relation_types.discard(SocialRelationType.RIVALRY)
        self.relation_types.discard(SocialRelationType.DISTRUST)
        self.relation_types.add(SocialRelationType.TRUST)

        self.history.append({
            "tick": tick,
            "event_type": "reconciliation",
            "mediator": mediator_id,
            "status": self.status.value,
            "description": "Formal reconciliation achieved",
        })

    def break_bond(self, tick: int, reason: str = "irreconcilable_conflict") -> None:
        """Explicitly break this social bond."""
        self.status = BondState.BROKEN
        self.conflict_level = min(1.0, self.conflict_level + 0.5)
        self.trust = max(0.0, self.trust - 0.5)
        self.affinity = max(0.0, self.affinity - 0.4)
        self.relation_types.discard(SocialRelationType.FRIEND)
        self.relation_types.discard(SocialRelationType.COOPERATIVE)
        self.relation_types.add(SocialRelationType.CONFLICT)
        self.relation_types.add(SocialRelationType.RIVALRY)
        self.relation_types.add(SocialRelationType.DISTRUST)

        self.history.append({
            "tick": tick,
            "event_type": "rupture",
            "reason": reason,
            "status": self.status.value,
            "description": f"Bond ruptured: {reason}",
        })

    def calculate_strength(self) -> float:
        """Synthesize overall bond strength from multidimensional metrics."""
        if self.status == BondState.BROKEN:
            return 0.0
        base = 0.45 * self.trust + 0.35 * self.affinity + 0.20 * self.interaction_frequency
        penalty = 0.50 * self.conflict_level
        return round(max(0.0, min(1.0, base - penalty)), 4)

    def _update_relation_types(self) -> None:
        """Dynamically adapt qualitative relation types based on current metrics."""
        strength = self.calculate_strength()

        # Preserve structural bonds (family, partner)
        is_family = SocialRelationType.FAMILY in self.relation_types
        is_partner = SocialRelationType.PARTNER in self.relation_types

        if self.trust >= 0.70:
            self.relation_types.add(SocialRelationType.TRUST)
            self.relation_types.discard(SocialRelationType.DISTRUST)
        elif self.trust <= 0.30:
            self.relation_types.add(SocialRelationType.DISTRUST)
            self.relation_types.discard(SocialRelationType.TRUST)

        if self.conflict_level >= 0.35 or (self.conflict_level >= 0.25 and self.trust <= 0.30):
            self.relation_types.add(SocialRelationType.CONFLICT)
            self.relation_types.add(SocialRelationType.RIVALRY)
            self.relation_types.discard(SocialRelationType.FRIEND)
        else:
            self.relation_types.discard(SocialRelationType.CONFLICT)

        if not is_family and not is_partner:
            if strength >= 0.65 and self.trust >= 0.65 and self.conflict_level <= 0.25:
                self.relation_types.add(SocialRelationType.FRIEND)
                self.relation_types.discard(SocialRelationType.STRANGER)
                self.relation_types.discard(SocialRelationType.ACQUAINTANCE)
            elif strength >= 0.35 and self.total_interactions >= 2:
                self.relation_types.add(SocialRelationType.ACQUAINTANCE)
                self.relation_types.discard(SocialRelationType.STRANGER)
            elif self.total_interactions == 0:
                self.relation_types.add(SocialRelationType.STRANGER)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_types": [r.value for r in self.relation_types],
            "intensity": round(self.intensity, 3),
            "trust": round(self.trust, 3),
            "affinity": round(self.affinity, 3),
            "reciprocity": round(self.reciprocity, 3),
            "interaction_frequency": round(self.interaction_frequency, 3),
            "conflict_level": round(self.conflict_level, 3),
            "dependence": round(self.dependence, 3),
            "shared_interests": list(self.shared_interests),
            "status": self.status.value,
            "created_tick": self.created_tick,
            "last_interaction_tick": self.last_interaction_tick,
            "total_interactions": self.total_interactions,
            "history_count": len(self.history),
        }


class SocialNetworkEngine:
    """Master engine managing dynamic social networks, graph topology, and social dynamics."""

    def __init__(self) -> None:
        # Adjacency map: source_id -> target_id -> SocialEdge
        self._adj: dict[str, dict[str, SocialEdge]] = defaultdict(dict)
        self._all_edges: dict[str, SocialEdge] = {}

    # -------------------------------------------------------------------------
    # Edge Lifecycle & Queries
    # -------------------------------------------------------------------------

    def get_or_create_edge(
        self,
        source_id: str | HumanID,
        target_id: str | HumanID,
        tick: int = 0,
        initial_types: Optional[set[SocialRelationType]] = None,
    ) -> SocialEdge:
        """Retrieve existing directed edge or create a new one."""
        s = str(source_id)
        t = str(target_id)
        if t in self._adj[s]:
            return self._adj[s][t]

        edge_id = f"edge_{s[:8]}_{t[:8]}_{uuid.uuid4().hex[:6]}"
        types = initial_types or {SocialRelationType.STRANGER}
        edge = SocialEdge(
            edge_id=edge_id,
            source_id=s,
            target_id=t,
            relation_types=types,
            created_tick=tick,
            last_interaction_tick=tick,
            status=BondState.FORMING if SocialRelationType.STRANGER in types else BondState.ACTIVE,
        )
        self._adj[s][t] = edge
        self._all_edges[edge_id] = edge
        return edge

    def get_edge(self, source_id: str | HumanID, target_id: str | HumanID) -> Optional[SocialEdge]:
        """Fetch directed edge if present."""
        return self._adj.get(str(source_id), {}).get(str(target_id))

    def get_neighbors(
        self,
        node_id: str | HumanID,
        relation_type: Optional[SocialRelationType] = None,
        min_trust: float = 0.0,
        active_only: bool = True,
    ) -> list[str]:
        """Get all target IDs with matching social relations."""
        s = str(node_id)
        results: list[str] = []
        for target, edge in self._adj.get(s, {}).items():
            if active_only and edge.status in (BondState.BROKEN, BondState.DORMANT):
                continue
            if edge.trust < min_trust:
                continue
            if relation_type is not None and relation_type not in edge.relation_types:
                continue
            results.append(target)
        return results

    def record_interaction(
        self,
        source_id: str | HumanID,
        target_id: str | HumanID,
        tick: int,
        valence: float,
        intensity: float = 0.5,
        event_type: str = "interaction",
        shared_topic: Optional[str] = None,
        bidirectional: bool = True,
    ) -> SocialEdge:
        """Record an interaction, updating directed and optionally reverse edges."""
        s = str(source_id)
        t = str(target_id)
        edge_st = self.get_or_create_edge(s, t, tick=tick)
        edge_st.record_interaction(
            tick=tick,
            event_type=event_type,
            valence=valence,
            intensity=intensity,
            shared_topic=shared_topic,
        )

        if bidirectional:
            edge_ts = self.get_or_create_edge(t, s, tick=tick)
            edge_ts.record_interaction(
                tick=tick,
                event_type=event_type,
                valence=valence,
                intensity=intensity,
                shared_topic=shared_topic,
            )

        return edge_st

    def apply_decay_all(self, current_tick: int, decay_rate: float = 0.01) -> None:
        """Apply social tie decay across all tracked edges."""
        for edge in self._all_edges.values():
            edge.decay(current_tick, decay_rate)

    # -------------------------------------------------------------------------
    # Complex Social Dynamics: Indirect Influence, Triads, Reorganization
    # -------------------------------------------------------------------------

    def get_indirect_influence(
        self,
        source_id: str | HumanID,
        target_id: str | HumanID,
        max_depth: int = 2,
    ) -> float:
        """Calculate indirect influence/trust from source to target via intermediary paths."""
        s = str(source_id)
        t = str(target_id)
        if s == t:
            return 1.0

        # Shortest paths up to max_depth
        queue: deque[tuple[str, float, int]] = deque([(s, 1.0, 0)])
        visited: dict[str, float] = {s: 1.0}
        influence_scores: list[float] = []

        while queue:
            curr, curr_trust, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for nbr, edge in self._adj.get(curr, {}).items():
                if edge.status == BondState.BROKEN or edge.trust <= 0.2:
                    continue
                path_trust = curr_trust * edge.trust * 0.85  # Dampen by distance
                if nbr == t:
                    influence_scores.append(path_trust)
                elif nbr not in visited or visited[nbr] < path_trust:
                    visited[nbr] = path_trust
                    queue.append((nbr, path_trust, depth + 1))

        if not influence_scores:
            return 0.0
        # Combine independent paths using probabilistic union
        combined = 0.0
        for score in influence_scores:
            combined = combined + score * (1.0 - combined)
        return round(combined, 4)

    def find_triadic_closure_candidates(
        self,
        node_id: str | HumanID,
        min_intermediary_trust: float = 0.50,
    ) -> list[tuple[str, str, float]]:
        """Identify potential new friendships via shared mutual trusted friends (A-B and B-C -> A-C).

        Returns list of (candidate_id, intermediary_id, predicted_affinity).
        """
        s = str(node_id)
        direct_friends = set(self.get_neighbors(s, min_trust=min_intermediary_trust))
        candidates: dict[str, list[tuple[str, float]]] = defaultdict(list)

        for friend in direct_friends:
            friends_of_friend = set(self.get_neighbors(friend, min_trust=min_intermediary_trust))
            for cand in friends_of_friend:
                if cand != s and cand not in direct_friends:
                    # Weight by mutual friend's trust
                    edge_sf = self.get_edge(s, friend)
                    edge_fc = self.get_edge(friend, cand)
                    w = (edge_sf.trust if edge_sf else 0.5) * (edge_fc.trust if edge_fc else 0.5)
                    candidates[cand].append((friend, w))

        results: list[tuple[str, str, float]] = []
        for cand, bridges in candidates.items():
            best_bridge, best_score = max(bridges, key=lambda x: x[1])
            results.append((cand, best_bridge, round(best_score, 4)))
        return results

    # -------------------------------------------------------------------------
    # Graph Topology & Metrics
    # -------------------------------------------------------------------------

    def calculate_density(self, active_only: bool = True) -> float:
        """Calculate overall social network density."""
        nodes = set(self._adj.keys())
        for s in self._adj:
            nodes.update(self._adj[s].keys())
        n = len(nodes)
        if n <= 1:
            return 0.0

        active_edges = 0
        for s in self._adj:
            for t, e in self._adj[s].items():
                if not active_only or e.status not in (BondState.BROKEN, BondState.DORMANT):
                    active_edges += 1

        possible = n * (n - 1)
        return round(active_edges / possible, 4)

    def calculate_reciprocity_ratio(self) -> float:
        """Proportion of mutual directed ties over all ties."""
        pairs_seen: set[tuple[str, str]] = set()
        mutual_count = 0
        total_count = 0

        for s in self._adj:
            for t, e in self._adj[s].items():
                if e.status in (BondState.BROKEN, BondState.DORMANT):
                    continue
                pair = (min(s, t), max(s, t))
                if pair in pairs_seen:
                    continue
                pairs_seen.add(pair)
                total_count += 1
                reverse = self.get_edge(t, s)
                if reverse and reverse.status not in (BondState.BROKEN, BondState.DORMANT):
                    mutual_count += 1

        if total_count == 0:
            return 0.0
        return round(mutual_count / total_count, 4)

    def calculate_degree_centrality(self, node_id: str | HumanID) -> int:
        """Degree of active connections for an individual."""
        return len(self.get_neighbors(node_id, active_only=True))

    def detect_connected_components(self) -> list[set[str]]:
        """Identify disconnected social cliques or clusters."""
        nodes: set[str] = set(self._adj.keys())
        for s in self._adj:
            nodes.update(self._adj[s].keys())

        visited: set[str] = set()
        components: list[set[str]] = []

        for node in nodes:
            if node in visited:
                continue
            component: set[str] = set()
            queue = deque([node])
            visited.add(node)

            while queue:
                curr = queue.popleft()
                component.add(curr)
                # Check outgoing and incoming
                neighbors = set(self.get_neighbors(curr, active_only=True))
                for s, edges in self._adj.items():
                    if curr in edges and edges[curr].status not in (BondState.BROKEN, BondState.DORMANT):
                        neighbors.add(s)

                for nbr in neighbors:
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)

            components.append(component)
        return components

    def count_total_edges(self, active_only: bool = True) -> int:
        """Return total tracked edges."""
        if not active_only:
            return len(self._all_edges)
        return sum(
            1 for e in self._all_edges.values()
            if e.status not in (BondState.BROKEN, BondState.DORMANT)
        )

    def get_all_edges(self) -> list[SocialEdge]:
        return list(self._all_edges.values())
