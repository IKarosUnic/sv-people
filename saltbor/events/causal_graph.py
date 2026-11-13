"""Explicit Causal Event Graph Architecture (Phase 1.5 Extension).

Maintains a Directed Acyclic Graph (DAG) linking causes and effects across
environmental, biological, psychological, economic, and social simulation domains.
Enables full inspectability: answers 'Why did this event happen?' and 'What were its consequences?'.
Prevents circular loops and uncontrolled cascading storms.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional, Set
import uuid

from saltbor.events.types import SimulationEvent

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CausalNode:
    """A node in the causal graph representing an immutable simulation event."""
    event_id: str
    event_type: str
    tick: int
    description: str = ""
    location_id: Optional[str] = None
    coordinates: Optional[tuple[float, float]] = None
    affected_uids: list[str] = dataclasses.field(default_factory=list)
    cause_event_ids: list[str] = dataclasses.field(default_factory=list)
    consequence_event_ids: list[str] = dataclasses.field(default_factory=list)
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
    importance: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "tick": self.tick,
            "description": self.description,
            "location_id": self.location_id,
            "coordinates": self.coordinates,
            "affected_uids": self.affected_uids,
            "cause_event_ids": self.cause_event_ids,
            "consequence_event_ids": self.consequence_event_ids,
            "importance": self.importance,
            "metadata": self.metadata,
        }


class CausalEventGraph:
    """Central causal graph storing and analyzing causal chains."""

    def __init__(self, max_nodes: int = 10000) -> None:
        self._nodes: dict[str, CausalNode] = {}
        self.max_nodes = max_nodes

    def add_event(
        self,
        event: SimulationEvent,
        cause_event_id: Optional[str] = None,
        description: str = "",
    ) -> CausalNode:
        """Register a simulation event as a node in the causal graph."""
        e_id = str(event.event_id)
        e_type = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)

        affected = []
        if event.source_human_id:
            affected.append(str(event.source_human_id))
        if event.target_human_id:
            affected.append(str(event.target_human_id))
        if "affected_uids" in event.data and isinstance(event.data["affected_uids"], list):
            for u in event.data["affected_uids"]:
                u_str = str(u)
                if u_str not in affected:
                    affected.append(u_str)

        node = CausalNode(
            event_id=e_id,
            event_type=e_type,
            tick=event.tick,
            description=description or event.data.get("description", f"{e_type} at tick {event.tick}"),
            location_id=event.location_id,
            coordinates=event.coordinates,
            affected_uids=affected,
            metadata=dict(event.data),
            importance=event.importance,
        )

        # Inherit cause from event itself if not explicitly passed
        effective_cause = cause_event_id or (str(event.cause_event_id) if event.cause_event_id else None)
        if effective_cause and effective_cause in self._nodes:
            # Check for cycle before adding
            if not self._would_create_cycle(parent_id=effective_cause, child_id=e_id):
                node.cause_event_ids.append(effective_cause)
                self._nodes[effective_cause].consequence_event_ids.append(e_id)

        # Manage capacity
        if len(self._nodes) >= self.max_nodes:
            oldest_id = next(iter(self._nodes))
            del self._nodes[oldest_id]

        self._nodes[e_id] = node
        return node

    def link_cause_effect(self, cause_event_id: str, effect_event_id: str) -> bool:
        """Explicitly link a cause event to an effect event."""
        if cause_event_id not in self._nodes or effect_event_id not in self._nodes:
            return False

        if cause_event_id == effect_event_id:
            return False

        if self._would_create_cycle(cause_event_id, effect_event_id):
            logger.warning("Rejecting causal link %s -> %s: cycle detected", cause_event_id, effect_event_id)
            return False

        cause_node = self._nodes[cause_event_id]
        effect_node = self._nodes[effect_event_id]

        if effect_event_id not in cause_node.consequence_event_ids:
            cause_node.consequence_event_ids.append(effect_event_id)
        if cause_event_id not in effect_node.cause_event_ids:
            effect_node.cause_event_ids.append(cause_event_id)

        return True

    def get_node(self, event_id: str) -> Optional[CausalNode]:
        return self._nodes.get(event_id)

    def get_causal_chain(self, event_id: str, max_depth: int = 5) -> list[CausalNode]:
        """Return all ancestor causes of this event up to max_depth."""
        chain: list[CausalNode] = []
        visited: Set[str] = set()

        def _traverse(current_id: str, depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)
            node = self._nodes.get(current_id)
            if not node:
                return
            for pid in node.cause_event_ids:
                p_node = self._nodes.get(pid)
                if p_node and pid not in visited:
                    chain.append(p_node)
                    _traverse(pid, depth + 1)

        _traverse(event_id, 1)
        # Sort in chronological order (earliest cause first)
        chain.sort(key=lambda n: n.tick)
        return chain

    def get_consequence_tree(self, event_id: str, max_depth: int = 5) -> list[CausalNode]:
        """Return all descendant consequences triggered by this event up to max_depth."""
        tree: list[CausalNode] = []
        visited: Set[str] = set()

        def _traverse(current_id: str, depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)
            node = self._nodes.get(current_id)
            if not node:
                return
            for cid in node.consequence_event_ids:
                c_node = self._nodes.get(cid)
                if c_node and cid not in visited:
                    tree.append(c_node)
                    _traverse(cid, depth + 1)

        _traverse(event_id, 1)
        tree.sort(key=lambda n: n.tick)
        return tree

    def explain_event(self, event_id: str) -> dict[str, Any]:
        """Generate a complete narrative and structured explanation for why an event occurred."""
        node = self._nodes.get(event_id)
        if not node:
            return {"error": f"Event {event_id} not found in causal graph"}

        ancestors = self.get_causal_chain(event_id)
        descendants = self.get_consequence_tree(event_id)

        causes_summary = [
            f"[Tick {a.tick}] {a.event_type}: {a.description}"
            for a in ancestors
        ]
        effects_summary = [
            f"[Tick {d.tick}] {d.event_type}: {d.description}"
            for d in descendants
        ]

        narrative = f"Event '{node.event_type}' occurred at tick {node.tick} at {node.location_id or 'general territory'}."
        if causes_summary:
            narrative += f" Triggered by {len(causes_summary)} prior cause(s): " + "; ".join(causes_summary) + "."
        else:
            narrative += " Root or autonomous initiating event."

        if effects_summary:
            narrative += f" Cascaded into {len(effects_summary)} consequence(s): " + "; ".join(effects_summary) + "."

        return {
            "target_event": node.to_dict(),
            "causal_chain_length": len(ancestors),
            "ancestor_causes": [a.to_dict() for a in ancestors],
            "consequences_count": len(descendants),
            "descendant_consequences": [d.to_dict() for d in descendants],
            "narrative_explanation": narrative,
        }

    def recent_nodes(self, limit: int = 100, min_importance: float = 0.0) -> list[CausalNode]:
        """Return the most recent causal nodes, optionally filtered by importance."""
        nodes = [n for n in self._nodes.values() if n.importance >= min_importance]
        nodes.sort(key=lambda n: (n.tick, n.importance), reverse=True)
        return nodes[:max(1, limit)]

    def find_latest_node(
        self,
        event_type: str,
        human_uid: Optional[str] = None,
        predicate: Optional[Any] = None,
    ) -> Optional[CausalNode]:
        """Find the latest node of a type, optionally involving a human/provenance predicate.

        Used to connect downstream consequences (treatment, bereavement,
        abandonment) to the concrete exposure or transition that caused them.
        """
        candidates: list[CausalNode] = []
        for node in self._nodes.values():
            if node.event_type != event_type:
                continue
            if human_uid is not None and str(human_uid) not in node.affected_uids:
                continue
            if predicate is not None and not predicate(node):
                continue
            candidates.append(node)
        if not candidates:
            return None
        return max(candidates, key=lambda n: (n.tick, n.importance))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the causal DAG for checkpoint restoration."""
        return {"nodes": [n.to_dict() for n in self._nodes.values()]}

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore a causal DAG captured by :meth:`to_dict`."""
        self._nodes.clear()
        for item in data.get("nodes", []):
            node = CausalNode(
                event_id=str(item["event_id"]),
                event_type=item.get("event_type", "unknown"),
                tick=int(item.get("tick", 0)),
                description=item.get("description", ""),
                location_id=item.get("location_id"),
                coordinates=tuple(item["coordinates"]) if item.get("coordinates") else None,
                affected_uids=[str(u) for u in item.get("affected_uids", [])],
                cause_event_ids=[str(c) for c in item.get("cause_event_ids", [])],
                consequence_event_ids=[str(c) for c in item.get("consequence_event_ids", [])],
                metadata=dict(item.get("metadata", {})),
                importance=float(item.get("importance", 0.5)),
            )
            self._nodes[node.event_id] = node

    def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """Check if adding parent_id -> child_id would create a cycle (DFS)."""
        visited: Set[str] = set()

        def _dfs(curr: str) -> bool:
            if curr == parent_id:
                return True
            visited.add(curr)
            curr_node = self._nodes.get(curr)
            if not curr_node:
                return False
            for nxt in curr_node.consequence_event_ids:
                if nxt not in visited:
                    if _dfs(nxt):
                        return True
            return False

        return _dfs(child_id)
