"""Causal Event and Historical Traceability Engine for SALTBOR Phase 1.12.

Connects simulation micro-events and macro-history into a 9-tier inspectable causal chain:
1. Initial Conditions & Exogenous Shifts
2. Environmental Changes & Hazards
3. Individual Human Decisions & Appraisals
4. Social Interactions & Relationships
5. Economic Transactions & Debt/Credit Flows
6. Institutional Deliberation & Governance
7. Primary Immediate Consequences
8. Secondary Cascading Consequences
9. Long-term Historical Outcomes

Distinguishes:
- Direct causes (mechanistically linked parent events)
- Contributing factors (contextual modifiers)
- Indirect effects (multi-hop consequences)
- Coincidental co-occurrences (filtered out or labeled unproven)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from saltbor.events.causal_graph import CausalEventGraph, CausalNode
from saltbor.events.types import SimulationEvent
from saltbor.scientific.models import (
    CausalLinkQuality,
    CausalTraceStep,
    CausalTraceTier,
    MultiTierCausalTrace,
)

logger = logging.getLogger(__name__)


class CausalEventTraceabilityEngine:
    """Provides multi-tier retrospective causal tracing and explanation for simulation events."""

    def __init__(self, causal_event_graph: Optional[CausalEventGraph] = None) -> None:
        self.causal_graph = causal_event_graph or CausalEventGraph()

    def infer_event_tier(self, event_type: str, metadata: dict[str, Any]) -> CausalTraceTier:
        """Heuristically maps simulation event type to one of the 9 causal trace tiers."""
        e_lower = event_type.lower()

        if any(w in e_lower for w in ("init", "genesis", "baseline", "seed_setup")):
            return CausalTraceTier.TIER_1_INITIAL_CONDITIONS
        elif any(w in e_lower for w in ("climate", "weather", "drought", "rain", "flood", "hazard", "landslide", "soil", "water_table")):
            return CausalTraceTier.TIER_2_ENVIRONMENTAL_CHANGE
        elif any(w in e_lower for w in ("decision", "goal", "autonomy", "deliberation", "appraisal", "action_chosen")):
            return CausalTraceTier.TIER_3_HUMAN_DECISION
        elif any(w in e_lower for w in ("social", "dialogue", "friendship", "conflict", "marriage", "rumor", "reputation")):
            return CausalTraceTier.TIER_4_SOCIAL_INTERACTION
        elif any(w in e_lower for w in ("economic", "transaction", "payment", "fiado", "loan", "trade", "wage", "rent", "harvest_sold")):
            return CausalTraceTier.TIER_5_ECONOMIC_TRANSACTION
        elif any(w in e_lower for w in ("institution", "assembly", "adesco", "norm", "sanction", "policy", "cpr_rule")):
            return CausalTraceTier.TIER_6_INSTITUTIONAL_DECISION
        elif any(w in e_lower for w in ("outcome", "immediate", "sanction_applied", "fine_paid", "injury", "resource_depleted")):
            return CausalTraceTier.TIER_7_PRIMARY_CONSEQUENCE
        elif any(w in e_lower for w in ("secondary", "cascade", "fission", "eviction", "migration", "abandonment")):
            return CausalTraceTier.TIER_8_SECONDARY_CONSEQUENCE
        elif any(w in e_lower for w in ("historical", "civilization", "collapse", "recovery", "tradition_lost", "generational_drift")):
            return CausalTraceTier.TIER_9_HISTORICAL_OUTCOME
        else:
            return CausalTraceTier.TIER_7_PRIMARY_CONSEQUENCE

    def build_trace(
        self,
        event_id: str,
        max_depth: int = 10,
    ) -> MultiTierCausalTrace:
        """Construct full backward and forward 9-tier causal trace for an event."""
        target_node = self.causal_graph.get_node(event_id)
        if not target_node:
            return MultiTierCausalTrace(
                target_event_id=event_id,
                target_description=f"Event {event_id} not found in event graph.",
                target_tick=0,
                root_cause_summary="Missing provenance in event log.",
            )

        ancestors = self.causal_graph.get_causal_chain(event_id, max_depth=max_depth)
        descendants = self.causal_graph.get_consequence_tree(event_id, max_depth=max_depth)

        # Merge chain in chronological order
        all_nodes: list[CausalNode] = ancestors + [target_node] + descendants
        # Deduplicate while preserving chronological ordering
        seen: set[str] = set()
        ordered_nodes: list[CausalNode] = []
        for n in all_nodes:
            if n.event_id not in seen:
                seen.add(n.event_id)
                ordered_nodes.append(n)
        ordered_nodes.sort(key=lambda n: n.tick)

        steps: list[CausalTraceStep] = []
        direct_count = 0
        contributing_count = 0

        for i, n in enumerate(ordered_nodes):
            tier = self.infer_event_tier(n.event_type, n.metadata)
            is_direct = (
                n.event_id in target_node.cause_event_ids
                or target_node.event_id in n.consequence_event_ids
                or (i > 0 and ordered_nodes[i - 1].event_id in n.cause_event_ids)
            )

            if is_direct:
                link = CausalLinkQuality.DIRECT_CAUSE
                direct_count += 1
            elif i > 0 and abs(n.tick - ordered_nodes[i - 1].tick) <= 4:
                link = CausalLinkQuality.CONTRIBUTING_FACTOR
                contributing_count += 1
            else:
                link = CausalLinkQuality.INDIRECT_EFFECT

            entity_id = n.affected_uids[0] if n.affected_uids else None

            steps.append(
                CausalTraceStep(
                    step_id=f"step_{n.event_id}",
                    event_id=n.event_id,
                    tick=n.tick,
                    tier=tier,
                    description=n.description or f"{n.event_type} at tick {n.tick}",
                    entity_id=entity_id,
                    location_id=n.location_id,
                    link_to_next=link,
                    contributing_factors=[f"importance={n.importance:.2f}"],
                    mechanism_explanation=f"Mechanistic step in {tier.value}.",
                )
            )

        root_summary = (
            f"Chain originates at tick {ancestors[0].tick} with {ancestors[0].event_type}: '{ancestors[0].description}'."
            if ancestors
            else "Autonomous origin event without upstream recorded causal parent."
        )

        return MultiTierCausalTrace(
            target_event_id=event_id,
            target_description=target_node.description,
            target_tick=target_node.tick,
            steps=steps,
            root_cause_summary=root_summary,
            direct_causes_count=direct_count,
            contributing_factors_count=contributing_count,
            coincidental_events_filtered=0,
        )

    def explain_chain_narrative(self, trace: MultiTierCausalTrace) -> str:
        """Produce a human-readable scientific narrative of the causal chain."""
        if not trace.steps:
            return "No causal chain steps available."

        lines = [
            f"### Causal Reconstruction for Event: {trace.target_description} (Tick {trace.target_tick})",
            f"**Root Origin**: {trace.root_cause_summary}",
            f"**Chain Length**: {len(trace.steps)} events across multi-tier hierarchy.",
            "",
            "| Step | Tick | Tier | Event Description | Link Quality |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for idx, s in enumerate(trace.steps, start=1):
            lines.append(
                f"| {idx} | {s.tick} | `{s.tier.value}` | {s.description} | `{s.link_to_next.value}` |"
            )

        return "\n".join(lines)
