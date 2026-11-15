"""Territorial Ecosystem Engine for SALTBOR Phase 1.14.

Master coordinator unifying all territorial sub-engines into an integrated ecosystem:
- Population & Households (MultiScaleTerritorialSimulationEngine)
- Cross-Domain Causal Links (CrossDomainInteractionEngine)
- Regional Trade & Supply Chains (RegionalEconomicNetworkEngine)
- Public Services & Infrastructure Capacity (PublicServiceCapacityEngine)
- Collaborative Governance & Proposals (CollaborativeGovernanceEngine)
- Multi-Dimensional Needs Assessment (HumanNeedsAssessmentEngine)
- Territorial Project Design & Alternatives (TerritorialProjectEngine)
- Integrated Multi-Domain Impact Analysis (IntegratedImpactAnalysisEngine)

Guarantees:
- Extensible to other countries beyond El Salvador without architectural redesign.
- Offline and local-first execution.
- Strict double-entry accounting conservation across trade and public finance.
- Non-destructive spatial layering (integrating with EditableWorldEngine Layers A-D).
"""

from __future__ import annotations

import collections
import dataclasses
import logging
from typing import Any, Dict, List, Optional, Tuple

from saltbor.domain.engine import UniversalDomainEngine
from saltbor.territory.behavior_heterogeneity import HumanBehaviorHeterogeneityEngine
from saltbor.territory.causal_trace import CausalTraceEngine
from saltbor.territory.consistency import SharedEntityConsistencyValidator
from saltbor.territory.cross_domain import CrossDomainInteractionEngine
from saltbor.territory.economic_ledger import VerifiableEconomicLedger
from saltbor.territory.generalized_scenarios import GeneralizedTerritorialScenarioEngine
from saltbor.territory.governance import CollaborativeGovernanceEngine
from saltbor.territory.impact_analysis import IntegratedImpactAnalysisEngine
from saltbor.territory.models import (
    DataProvenanceTier,
    TerritorialElement,
    TerritorialElementType,
    TerritorialScale,
)
from saltbor.territory.multi_scale import MultiScaleTerritorialSimulationEngine
from saltbor.territory.needs_assessment import HumanNeedsAssessmentEngine
from saltbor.territory.projects import TerritorialProjectEngine
from saltbor.territory.public_services import PublicServiceCapacityEngine
from saltbor.territory.regional_economics import RegionalEconomicNetworkEngine

logger = logging.getLogger(__name__)


class TerritorialEcosystemEngine:
    """Master orchestrator for multi-scale territorial ecosystems, public services, and governance."""

    def __init__(
        self,
        domain_engine: Optional[UniversalDomainEngine] = None,
        random_seed: int = 42,
    ) -> None:
        self.random_seed = random_seed
        self.domain_engine = domain_engine

        # Unified Sub-Engines
        self.cross_domain = CrossDomainInteractionEngine(random_seed=random_seed)
        self.multi_scale = MultiScaleTerritorialSimulationEngine()
        self.regional_economics = RegionalEconomicNetworkEngine(random_seed=random_seed)
        self.public_services = PublicServiceCapacityEngine()
        self.governance = CollaborativeGovernanceEngine()
        self.needs_assessment = HumanNeedsAssessmentEngine(random_seed=random_seed)
        self.projects = TerritorialProjectEngine()
        self.impact_analysis = IntegratedImpactAnalysisEngine()

        # Phase 1.15 Generalized Engines
        self.generalized_scenarios = GeneralizedTerritorialScenarioEngine(random_seed=random_seed)
        self.causal_trace = CausalTraceEngine()
        self.economic_ledger = VerifiableEconomicLedger()
        self.consistency_validator = SharedEntityConsistencyValidator()
        self.behavior_heterogeneity = HumanBehaviorHeterogeneityEngine(random_seed=random_seed)

        # Territorial Elements Directory
        self.elements: Dict[str, TerritorialElement] = {}
        self._populate_initial_territorial_elements()

    def register_element(self, element: TerritorialElement) -> None:
        self.elements[element.element_id] = element

    def get_element(self, element_id: str) -> Optional[TerritorialElement]:
        return self.elements.get(element_id)

    def list_elements(
        self,
        element_type: Optional[TerritorialElementType] = None,
        scale: Optional[TerritorialScale] = None,
        department_code: Optional[str] = None,
    ) -> List[TerritorialElement]:
        res = list(self.elements.values())
        if element_type:
            res = [e for e in res if e.element_type == element_type]
        if scale:
            res = [e for e in res if e.scale == scale]
        if department_code:
            res = [e for e in res if e.department_code == department_code]
        return res

    # =========================================================================
    # Discrete Tick Step
    # =========================================================================

    def step(self, current_tick: int) -> Dict[str, Any]:
        """Advance all territorial sub-engines synchronously during discrete tick loop."""
        step_summary: Dict[str, Any] = {"tick": current_tick}

        # Daily cycle (tick % 96 == 0): Economic payroll, daily queues, service resets
        if current_tick % 96 == 0:
            econ_res = self.regional_economics.execute_daily_economic_cycle(tick=current_tick)
            self.public_services.reset_daily_queues()
            step_summary["economic_cycle"] = econ_res
            step_summary["queues_reset"] = True

        return step_summary

    # =========================================================================
    # Territorial Ecosystem Summary for Observatory & UI
    # =========================================================================

    def get_territorial_summary(self) -> Dict[str, Any]:
        """Return high-level census and infrastructure summary across the active territory."""
        pop_summary = self.multi_scale.aggregate_population_by_scale(TerritorialScale.LEVEL_6_DEPARTMENT_NATIONAL)
        hh_summary = self.multi_scale.aggregate_population_by_scale(TerritorialScale.LEVEL_2_HOUSEHOLD)

        return {
            "country": "El Salvador",
            "departments_count": len(self.multi_scale.departments),
            "municipalities_count": len(self.multi_scale.municipalities),
            "communities_count": len(self.multi_scale.communities),
            "total_simulated_population": pop_summary["total_population"],
            "total_households": hh_summary["total_households"],
            "public_facilities_count": len(self.public_services.facilities),
            "trade_nodes_count": len(self.regional_economics.nodes),
            "supply_chain_links_count": len(self.regional_economics.links),
            "active_cross_domain_interactions": len(self.cross_domain.interactions),
            "governance_proposals_count": len(self.governance.proposals),
            "territorial_projects_count": len(self.projects.projects),
        }

    # =========================================================================
    # Initial Elements Population
    # =========================================================================

    def _populate_initial_territorial_elements(self) -> None:
        """Register initial representative physical, economic, and institutional elements."""
        # 1. Register Public Facilities as Territorial Elements
        for f in self.public_services.facilities.values():
            elem_type = TerritorialElementType.HEALTHCARE_FACILITY if f.category.value == "healthcare" else (
                TerritorialElementType.EDUCATIONAL_FACILITY if f.category.value == "education" else TerritorialElementType.PUBLIC_SERVICE
            )
            elem = TerritorialElement(
                element_id=f.facility_id,
                element_type=elem_type,
                scale=TerritorialScale.LEVEL_3_BUSINESS_INSTITUTION,
                name=f.name,
                latitude=f.latitude,
                longitude=f.longitude,
                department_code=f.department_code,
                municipality_id=f.municipality_id,
                operational_attributes={
                    "capacity_per_day": f.configured_capacity_per_day,
                    "coverage_radius_km": f.coverage_radius_km,
                    "status": f.status.value,
                },
                provenance_tier=f.provenance_tier,
                source_reference="CNR_MINSAL_MINED_2024",
            )
            self.register_element(elem)

        # 2. Register Regional Trade Nodes as Territorial Elements
        for n in self.regional_economics.nodes.values():
            elem = TerritorialElement(
                element_id=n.node_id,
                element_type=TerritorialElementType.BUSINESS,
                scale=TerritorialScale.LEVEL_3_BUSINESS_INSTITUTION,
                name=n.name,
                latitude=n.latitude,
                longitude=n.longitude,
                department_code=n.department_code,
                municipality_id=n.municipality_id,
                is_formal=not n.is_informal,
                operational_attributes={
                    "role": n.role.value,
                    "cash_balance_usd": n.cash_balance_usd,
                    "inventory_units": n.inventory_units,
                },
                provenance_tier=DataProvenanceTier.SIMULATED,
                source_reference="SALTBOR_ECONOMIC_LEDGER",
            )
            self.register_element(elem)
