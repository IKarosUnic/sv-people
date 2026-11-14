"""Tests for Multi-Community Longitudinal Divergence (Bottom-Up Emergence).

Verifies the 6 key emergent social, institutional, and economic phenomena:
1. Spontaneous Cooperative Formation (High trust + common economic need)
2. Organizational Failure from Distrust (Low trust aborts collective action)
3. Institutional Legitimacy Degradation & Dissolution (Resource mismanagement)
4. Divergent Family Business Fates (Solvent growth vs illiquid insolvency)
5. Organizational Fission / Schism (Factional disagreement splits collective)
6. Cultural Tradition Extinction (Generational abandonment of unpracticed craft)

Verifies that none of these outcomes are guaranteed, but rather strictly contingent
upon underlying social, economic, and institutional mechanics.
"""

from __future__ import annotations

import pytest

from saltbor.simulation.scenarios.emergent_communities_divergence import (
    MultiCommunityLongitudinalSimulation,
)


def test_multi_community_divergence_all_six_phenomena_emerge():
    """Verify that all 6 emergent phenomena manifest across a 3-year multi-community run."""
    sim = MultiCommunityLongitudinalSimulation(random_seed=42)
    sim.initialize_communities()
    res = sim.run_multi_year_simulation(years=3, ticks_per_year=96)

    assert res.years_simulated == 3.0
    assert res.total_ticks == 288

    # 1. Cooperative Formation in El Roble
    assert res.cooperative_formed is True
    assert res.cooperative_members_count >= 6
    assert res.cooperative_capital_usd > 100.0

    # 2. Failed Organization in Loma Linda due to Distrust
    assert res.distrust_community_organized is False
    assert res.distrust_community_status == "fragmented"
    assert res.mean_distrust_level < 0.35

    # 3. Institutional Legitimacy Loss and Collapse
    assert res.institution_survived is False
    assert res.institution_final_legitimacy <= 0.20
    assert "recursos" in res.legitimacy_crisis_reason.lower()

    # 4. Family Business Divergence
    assert res.prosperous_business_status == "active"
    assert res.prosperous_business_jobs_created >= 1
    assert res.prosperous_business_cash > 250.0

    assert res.failed_business_status == "insolvent"
    assert res.failed_business_jobs == 0
    assert res.failed_business_cash <= 0.0

    # 5. Organizational Fission
    assert res.fission_occurred is True
    assert "Disidente" in res.splinter_community_name or "Esfuerzo" in res.splinter_community_name
    assert res.inter_group_rivalry < 0.0  # Hostile relationship

    # 6. Cultural Tradition Extinction
    assert res.extinct_tradition_extinct is True
    assert res.thriving_tradition_practitioners >= 1

    # Verify dictionary flags
    assert all(res.phenomena_observed.values())


def test_contingency_cooperative_does_not_form_when_merchants_distrust():
    """Contingency check: If merchants distrust each other, cooperative does NOT form."""
    sim = MultiCommunityLongitudinalSimulation(random_seed=99)
    sim.initialize_communities()

    # Artificially erode trust in El Roble prior to year 1
    for i, m1 in enumerate(sim.roble_merchants):
        for j, m2 in enumerate(sim.roble_merchants):
            if i < j:
                rel = sim.social_engine.get_relationship(m1.uid, m2.uid)
                rel.trust = 0.15  # Low trust

    res = sim.run_multi_year_simulation(years=1, ticks_per_year=96)
    # Cooperative must NOT form
    assert res.cooperative_formed is False


def test_contingency_institution_survives_when_managed_properly():
    """Contingency check: If an institution is stewarded cleanly, it does NOT collapse."""
    sim = MultiCommunityLongitudinalSimulation(random_seed=42)
    sim.initialize_communities()

    # Prevent corruption / crisis
    sim.water_board.suffer_legitimacy_crisis = lambda penalty, reason, tick: None  # No-op

    res = sim.run_multi_year_simulation(years=2, ticks_per_year=96)
    assert res.institution_survived is True
    assert res.institution_final_legitimacy >= 0.80
