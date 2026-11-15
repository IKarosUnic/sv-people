"""Unit tests for Needs Assessment, Project Engine & Impact Analysis (Phase 1.14)."""

import pytest
from saltbor.territory.impact_analysis import IntegratedImpactAnalysisEngine
from saltbor.territory.models import (
    HumanNeedDimension,
    NeedEvidenceTier,
    ProjectAlternativeConfig,
    ProjectType,
)
from saltbor.territory.needs_assessment import HumanNeedsAssessmentEngine
from saltbor.territory.projects import TerritorialProjectEngine


def test_human_needs_assessment():
    engine = HumanNeedsAssessmentEngine(random_seed=42)
    needs = engine.get_territory_needs("chalatenango_dist")
    assert len(needs) >= 4

    # Verify epistemic separation
    dimensions = [n.dimension for n in needs]
    assert HumanNeedDimension.HEALTHCARE_ACCESSIBILITY in dimensions
    assert HumanNeedDimension.WATER_ACCESS in dimensions

    # Pareto multi-objective priorities
    priorities = engine.compute_pareto_priority_interventions("chalatenango_dist")
    assert len(priorities) >= 4
    assert priorities[0]["urgency_score"] >= priorities[-1]["urgency_score"]


def test_territorial_project_alternatives():
    engine = TerritorialProjectEngine()
    projects = engine.list_projects()
    assert len(projects) >= 2

    # Evaluate alternatives for Chalatenango healthcare project
    proj_ch = [p for p in projects if p.department_code == "CH"][0]
    comparison = engine.evaluate_project_alternatives(proj_ch.project_id)
    assert comparison["alternatives_compared_count"] == 3
    assert "rankings" in comparison
    assert len(comparison["rankings"]) == 3
    # Check that cost per citizen served is computed
    assert comparison["rankings"][0]["cost_per_citizen_served_annual_usd"] > 0.0


def test_integrated_impact_analysis():
    proj_engine = TerritorialProjectEngine()
    impact_engine = IntegratedImpactAnalysisEngine()
    
    proj = proj_engine.list_projects()[0]
    baseline = {
        "healthcare_care_deferral_rate": 0.42,
        "healthcare_queue_hours": 4.5,
        "economy_gini_index": 0.45,
        "economy_q1_income_usd": 110.0,
        "household_travel_cost_usd": 15.0,
    }
    intervention = {
        "healthcare_care_deferral_rate": 0.18,
        "healthcare_queue_hours": 1.5,
        "economy_gini_index": 0.42,
        "economy_q1_income_usd": 135.0,
        "household_travel_cost_usd": 5.0,
    }

    report = impact_engine.evaluate_project_impact(
        project=proj,
        baseline_metrics=baseline,
        intervention_metrics=intervention,
    )
    assert report.project_id == proj.project_id
    assert len(report.direct_effects) > 0
    assert len(report.indirect_effects) > 0
    assert report.distributional_gini_delta < 0.0  # Reduced inequality
    assert report.distributional_lowest_quintile_gain_pct > 0.0
    assert len(report.unintended_consequences) > 0
    assert "EMPIRICAL_CALIBRATION" in str(report.simulated_vs_empirical_breakdown)
