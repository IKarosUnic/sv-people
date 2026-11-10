"""Advanced Analogical Reasoning Engine for Saltbor Phase 0.7 (Section 2.5).

Transfers strategies and causal principles across distinct domains based on
underlying structural isomorphisms while strictly respecting domain boundaries
and contextual differences.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class AnalogicalDomainSchema:
    """Relational structure and principles characterizing a domain."""

    domain_id: str
    name: str
    key_entities: list[str]             # e.g., ['inventory', 'cash_flow', 'customers']
    core_principles: list[str]          # e.g., ['maintain_safety_buffer', 'track_daily_outflow']
    resource_type: str                  # e.g., 'commercial_capital' or 'household_rations'
    success_metric: str                 # e.g., 'profit_stability' or 'family_wellbeing'


@dataclasses.dataclass
class AnalogicalTransferResult:
    """The outcome of transferring knowledge from source domain to target domain."""

    transfer_id: str
    source_domain: str
    target_domain: str
    structural_similarity: float        # [0.0, 1.0]
    mapped_elements: dict[str, str]     # source_concept -> target_concept
    transferred_principles: list[str]   # principles translated to target context
    context_caveats: list[str]          # domain differences and limitations
    adapted_strategy: str
    confidence: float                   # Epistemic confidence in transfer validity
    created_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "source": self.source_domain,
            "target": self.target_domain,
            "similarity": round(self.structural_similarity, 3),
            "mappings": self.mapped_elements,
            "principles": self.transferred_principles,
            "caveats": self.context_caveats,
            "strategy": self.adapted_strategy,
            "confidence": round(self.confidence, 3),
        }


class AdvancedAnalogicalReasoningEngine:
    """Maps schemas between disparate domains to unlock novel strategies."""

    def __init__(self) -> None:
        self._schemas: dict[str, AnalogicalDomainSchema] = self._setup_domain_schemas()

    def _setup_domain_schemas(self) -> dict[str, AnalogicalDomainSchema]:
        """Pre-populate structural schemas for familiar domains."""
        return {
            "business_management": AnalogicalDomainSchema(
                domain_id="business_management",
                name="Commercial Enterprise Resource Management",
                key_entities=["commercial_inventory", "cash_reserves", "operating_expenses", "revenue_inflow"],
                core_principles=[
                    "maintain_minimum_buffer_stock",
                    "audit_and_reduce_unnecessary_outflows",
                    "reinvest_surplus_into_productive_capacity",
                    "anticipate_cyclical_shortages",
                ],
                resource_type="commercial_capital",
                success_metric="solvency_and_growth",
            ),
            "household_management": AnalogicalDomainSchema(
                domain_id="household_management",
                name="Domestic Household Resource Administration",
                key_entities=["food_pantry_rations", "family_savings", "daily_consumption", "wage_earnings"],
                core_principles=[
                    "store_emergency_food_reserves",
                    "eliminate_wasteful_spending",
                    "allocate_resources_for_children_development",
                    "prepare_for_winter_lean_seasons",
                ],
                resource_type="vital_sustenance",
                success_metric="family_survival_and_health",
            ),
            "crop_irrigation": AnalogicalDomainSchema(
                domain_id="crop_irrigation",
                name="Agricultural Water Distribution Network",
                key_entities=["water_reservoir", "main_canal", "sluice_gates", "field_furrows"],
                core_principles=[
                    "regulate_flow_at_choke_points",
                    "prevent_downstream_starvation",
                    "maintain_gradient_for_gravity_flow",
                ],
                resource_type="water_volume",
                success_metric="even_field_hydration",
            ),
            "community_food_distribution": AnalogicalDomainSchema(
                domain_id="community_food_distribution",
                name="Settlement Ration Distribution System",
                key_entities=["central_granary", "neighborhood_depots", "ration_allocators", "individual_families"],
                core_principles=[
                    "regulate_draw_rates_during_crisis",
                    "prevent_distant_neighborhood_starvation",
                    "smooth_transportation_bottlenecks",
                ],
                resource_type="grain_rations",
                success_metric="universal_nourishment",
            ),
        }

    def transfer_knowledge(
        self,
        source_domain_id: str,
        target_domain_id: str,
        graph: Optional[IndividualKnowledgeGraph] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Optional[AnalogicalTransferResult]:
        """Transfer principles from familiar source domain to novel target domain."""
        src = self._schemas.get(source_domain_id)
        tgt = self._schemas.get(target_domain_id)

        if not src or not tgt:
            return None

        # Build mapping based on structural alignment
        mappings: dict[str, str] = {}
        for i in range(min(len(src.key_entities), len(tgt.key_entities))):
            mappings[src.key_entities[i]] = tgt.key_entities[i]

        # Calculate structural similarity
        sim = len(mappings) / max(1, max(len(src.key_entities), len(tgt.key_entities)))
        if sim < 0.4:
            sim = 0.5

        # Translate principles
        transferred: list[str] = []
        for p in src.core_principles:
            if "buffer" in p or "reserve" in p:
                transferred.append(f"Adapt '{p}': Keep emergency reserves of {tgt.resource_type}")
            elif "outflow" in p or "spending" in p:
                transferred.append(f"Adapt '{p}': Track and constrain daily expenditures in {tgt.name}")
            elif "reinvest" in p or "development" in p:
                transferred.append(f"Adapt '{p}': Channel current surplus into long-term resilience")
            elif "cyclical" in p or "winter" in p or "choke" in p:
                transferred.append(f"Adapt '{p}': Buffer against predictable shortages before they strike")
            else:
                transferred.append(f"General principle: Apply {p} to {tgt.name}")

        # Caveats recognizing domain divergence
        caveats = [
            f"Domain distinction: {src.resource_type} operates under market trade rules, whereas {tgt.resource_type} governs {tgt.success_metric}",
            "Non-fungibility: Household sustenance cannot be delayed or liquidated with the same flexibility as commercial enterprise capital",
            "Human and social welfare constraints supersede pure efficiency calculations in domestic settings",
        ]

        adapted_strategy = (
            f"Organize {tgt.name} by mirroring {src.name} governance: "
            f"Establish clear accounting of {tgt.key_entities[0]} vs {tgt.key_entities[1] if len(tgt.key_entities) > 1 else 'costs'}, "
            f"enforce reserve thresholds, and eliminate non-essential drawdowns."
        )

        conf = min(0.85, sim * 0.85)

        res = AnalogicalTransferResult(
            transfer_id=f"analog_{uuid4().hex[:8]}",
            source_domain=source_domain_id,
            target_domain=target_domain_id,
            structural_similarity=sim,
            mapped_elements=mappings,
            transferred_principles=transferred,
            context_caveats=caveats,
            adapted_strategy=adapted_strategy,
            confidence=conf,
            created_tick=tick,
        )

        if epistemic:
            belief = EpistemicBelief(
                belief_id=res.transfer_id,
                subject=target_domain_id,
                predicate="analogically_informed_by",
                object_val=source_domain_id,
                belief_type=BeliefType.INFERENCE,
                confidence=conf,
                source_type="analogical_transfer",
                created_tick=tick,
                updated_tick=tick,
                evidence_items=[f"Structural similarity: {sim:.2f}; {len(transferred)} principles mapped"],
            )
            epistemic.register_belief(belief)

        return res
