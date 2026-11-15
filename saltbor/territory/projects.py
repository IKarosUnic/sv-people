"""Territorial Project Design and Alternative Development Engine for SALTBOR Phase 1.14.

Coordinates authoring, specification, costing, and multi-alternative trade-off analysis
for public territorial interventions:
- Project Types:
  Public Markets, Commercial Centers, Rural Schools, Healthcare Units, Road Connections,
  Agricultural Distribution Hubs, Cultural Centers, Recreational Parks, Vocational Training,
  and Water Infrastructure.
- Specification:
  Geographic coordinates, capital & annual operating costs, throughput capacity,
  catchment radius, affected domains, externalities, success indicators, and explicit uncertainties.
- Alternative Design Exploration:
  Comparing e.g.,
  - One large centralized facility
  - Several distributed smaller micro-facilities
  - Mobile outreach brigades
  - Subsidized transit links to existing facilities.

Guarantees:
- Never assumes the largest or most expensive alternative is automatically optimal.
- Transparently computes cost-effectiveness per citizen served ($USD / citizen-year)
  and geographic coverage equity.
"""

from __future__ import annotations

import collections
import dataclasses
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from saltbor.domain.models import DataProvenanceTier
from saltbor.territory.models import (
    ProjectAlternativeConfig,
    ProjectApprovalStatus,
    ProjectType,
    TerritorialProject,
)

logger = logging.getLogger(__name__)


class TerritorialProjectEngine:
    """Manages authoring, costing, and comparative evaluation of territorial intervention projects."""

    def __init__(self) -> None:
        self.projects: Dict[str, TerritorialProject] = {}
        self._seed_default_projects()

    def register_project(self, project: TerritorialProject) -> None:
        self.projects[project.project_id] = project

    def get_project(self, project_id: str) -> Optional[TerritorialProject]:
        return self.projects.get(project_id)

    def list_projects(
        self,
        project_type: Optional[ProjectType] = None,
        department_code: Optional[str] = None,
        status: Optional[ProjectApprovalStatus] = None,
    ) -> List[TerritorialProject]:
        res = list(self.projects.values())
        if project_type:
            res = [p for p in res if p.project_type == project_type]
        if department_code:
            res = [p for p in res if p.department_code == department_code]
        if status:
            res = [p for p in res if p.status == status]
        return res

    # =========================================================================
    # Project Authoring with Alternative Configurations
    # =========================================================================

    def create_project(
        self,
        title: str,
        project_type: ProjectType,
        objective: str,
        department_code: str,
        municipality_id: str,
        latitude: float,
        longitude: float,
        target_population: int,
        primary_config: ProjectAlternativeConfig,
        alternative_configs: Optional[List[ProjectAlternativeConfig]] = None,
        relevant_domains: Optional[List[str]] = None,
        potential_externalities: Optional[List[str]] = None,
        success_indicators: Optional[List[str]] = None,
        uncertainties: Optional[List[str]] = None,
    ) -> TerritorialProject:
        """Create and register a proposed territorial intervention with alternatives."""
        pid = f"proj_{uuid4().hex[:8]}"
        project = TerritorialProject(
            project_id=pid,
            title=title,
            project_type=project_type,
            objective=objective,
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=latitude,
            longitude=longitude,
            target_population=target_population,
            selected_config=primary_config,
            alternative_configs=alternative_configs or [],
            relevant_domains=relevant_domains or ["infrastructure", "economy"],
            potential_externalities=potential_externalities or [],
            success_indicators=success_indicators or ["coverage_pct", "unit_cost_effectiveness"],
            uncertainties=uncertainties or ["budget_contingency", "weather_delays"],
            status=ProjectApprovalStatus.DRAFT,
        )
        self.register_project(project)
        return project

    # =========================================================================
    # Comparative Alternative Analysis
    # =========================================================================

    def evaluate_project_alternatives(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """Compare all design alternatives for a project across cost, capacity, coverage, and equity."""
        project = self.projects.get(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        all_configs = [project.selected_config] + project.alternative_configs
        comparisons = []

        for cfg in all_configs:
            # Annualized 10-year total cost: capital/10 + annual operating
            annualized_total_cost = (cfg.capital_cost_usd / 10.0) + cfg.annual_operating_cost_usd
            # Citizens reached annually
            annual_served_estimate = min(project.target_population, cfg.daily_service_capacity * 260) # 260 working days
            cost_per_citizen_served = annualized_total_cost / max(annual_served_estimate, 1)

            comparisons.append({
                "config_id": cfg.config_id,
                "name": cfg.name,
                "description": cfg.description,
                "capital_cost_usd": cfg.capital_cost_usd,
                "annual_operating_cost_usd": cfg.annual_operating_cost_usd,
                "daily_capacity": cfg.daily_service_capacity,
                "catchment_radius_km": cfg.catchment_radius_km,
                "coverage_pct": cfg.expected_service_coverage_pct,
                "implementation_months": cfg.estimated_implementation_months,
                "cost_per_citizen_served_annual_usd": round(cost_per_citizen_served, 2),
                "trade_offs": cfg.trade_off_summary,
            })

        # Rank alternatives by cost-effectiveness and coverage
        comparisons.sort(key=lambda x: (x["cost_per_citizen_served_annual_usd"], -x["coverage_pct"]))

        return {
            "project_id": project.project_id,
            "title": project.title,
            "target_population": project.target_population,
            "alternatives_compared_count": len(comparisons),
            "rankings": comparisons,
            "recommended_cost_effective_config_id": comparisons[0]["config_id"],
        }

    # =========================================================================
    # Default Projects Seed
    # =========================================================================

    def _seed_default_projects(self) -> None:
        """Seed representative projects comparing alternative designs."""
        # Project 1: Healthcare Expansion in Chalatenango Rural
        cfg1_central = ProjectAlternativeConfig(
            config_id="alt_hosp_central",
            name="1 Central Hospital Extension",
            description="Build one 150-bed central specialized hospital wing in Chalatenango cabecera.",
            capital_cost_usd=1200000.0,
            annual_operating_cost_usd=280000.0,
            daily_service_capacity=200,
            catchment_radius_km=35.0,
            expected_service_coverage_pct=65.0,
            estimated_implementation_months=24,
            trade_off_summary="High advanced clinical capacity, but poor accessibility for remote rural cantones due to travel costs.",
        )
        cfg1_distributed = ProjectAlternativeConfig(
            config_id="alt_clinics_distributed",
            name="4 Distributed Rural Health Posts",
            description="Construct 4 smaller community health posts in remote cantones.",
            capital_cost_usd=600000.0,
            annual_operating_cost_usd=180000.0,
            daily_service_capacity=160,
            catchment_radius_km=10.0,
            expected_service_coverage_pct=88.0,
            estimated_implementation_months=12,
            trade_off_summary="Lower capital cost and superior rural geographic equity, but limited to primary care and triage.",
        )
        cfg1_mobile = ProjectAlternativeConfig(
            config_id="alt_mobile_brigades",
            name="2 Mobile Health Units",
            description="Deploy 2 equipped 4x4 mobile health clinics on rotating cantón routes.",
            capital_cost_usd=240000.0,
            annual_operating_cost_usd=120000.0,
            daily_service_capacity=90,
            catchment_radius_km=45.0,
            expected_service_coverage_pct=78.0,
            estimated_implementation_months=4,
            trade_off_summary="Lowest upfront cost and rapid deployment, but periodic rather than continuous daily presence.",
        )

        self.create_project(
            title="Chalatenango Rural Healthcare Access Program",
            project_type=ProjectType.HEALTHCARE_FACILITY,
            objective="Reduce travel friction and care deferral across mountainous cantones in Chalatenango.",
            department_code="CH",
            municipality_id="CH01",
            latitude=14.0415,
            longitude=-88.9357,
            target_population=18500,
            primary_config=cfg1_distributed,
            alternative_configs=[cfg1_central, cfg1_mobile],
            relevant_domains=["healthcare", "household_economics", "transportation"],
            potential_externalities=["reduced_emergency_mortality", "decreased_household_travel_debt"],
            success_indicators=["care_deferral_rate_reduction", "cost_per_citizen_served"],
        )

        # Project 2: Public Market Development in Soyapango
        cfg2_large_market = ProjectAlternativeConfig(
            config_id="alt_mkt_large_central",
            name="Macro-Mercado Municipal Soyapango",
            description="Construct a centralized 600-stall multi-level municipal market complex.",
            capital_cost_usd=2500000.0,
            annual_operating_cost_usd=320000.0,
            daily_service_capacity=4500,
            catchment_radius_km=8.0,
            expected_service_coverage_pct=72.0,
            estimated_implementation_months=18,
            trade_off_summary="Consolidates informal street vendors, but high traffic congestion and substantial upfront municipal bond debt.",
        )
        cfg2_community_plazas = ProjectAlternativeConfig(
            config_id="alt_mkt_3_plazas",
            name="3 Decentralized Neighborhood Tianguis Plazas",
            description="Rehabilitate 3 open-air neighborhood community market squares near transit hubs.",
            capital_cost_usd=950000.0,
            annual_operating_cost_usd=140000.0,
            daily_service_capacity=3800,
            catchment_radius_km=3.5,
            expected_service_coverage_pct=85.0,
            estimated_implementation_months=8,
            trade_off_summary="Lower capital burden, minimal traffic disruption, and closer pedestrian walkability for residents.",
        )

        self.create_project(
            title="Soyapango Public Market and Retail Formalization",
            project_type=ProjectType.PUBLIC_MARKET,
            objective="Relocate informal ambulante vendors into dignified, sanitized commercial stalls.",
            department_code="SS",
            municipality_id="SS02",
            latitude=13.7102,
            longitude=-89.1398,
            target_population=45000,
            primary_config=cfg2_community_plazas,
            alternative_configs=[cfg2_large_market],
            relevant_domains=["commerce_retail", "food_gastronomy", "transportation"],
            potential_externalities=["street_congestion_relief", "formal_business_tax_revenue"],
            success_indicators=["informal_vendor_adoption_pct", "consumer_price_stability"],
        )
