"""
Automated test suite executing and verifying all 10 Salvadoran context experiments (EXP_SV_01 through EXP_SV_10).

Covers:
- EXP_SV_01: Urban vs. Rural Contextual Differences
- EXP_SV_02: Seasonal Climate & Agricultural Consequences
- EXP_SV_03: Local Market & Informal Commerce Dynamics
- EXP_SV_04: Intergenerational Cultural Transmission
- EXP_SV_05: Regional Language Variation & Register Differentiation
- EXP_SV_06: Migration & Household Remittance Dynamics
- EXP_SV_07: Community Celebrations & Economic Multipliers
- EXP_SV_08: Geographic Accessibility & Seasonal Road Degradation
- EXP_SV_09: Community Cooperation during Environmental Disruption
- EXP_SV_10: Multi-Agent Adaptation to Distinct Salvadoran Environments
"""

import pytest
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


def test_experiment_sv_01_urban_rural_differences(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_01")
    assert result.success is True
    assert result.metrics["urban_services_level"] > result.metrics["rural_services_level"]
    assert result.metrics["urban_road"] == "paved_highway"
    assert result.metrics["rural_road"] == "unpaved_dirt_road"


def test_experiment_sv_02_seasonal_climate_agriculture(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_02")
    assert result.success is True
    assert result.metrics["maize_yield_canicula"] < result.metrics["maize_yield_normal"]
    assert result.metrics["bean_yield_temporal"] <= 0.50


def test_experiment_sv_03_local_market_informal_commerce(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_03")
    assert result.success is True
    assert result.metrics["daily_purchase_spent_usd"] <= 3.00
    assert result.metrics["credit_approved_usd"] == 8.50
    assert result.metrics["final_trust_score"] > 0.80


def test_experiment_sv_04_intergenerational_cultural_transmission(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_04")
    assert result.success is True
    assert result.metrics["acquired_proficiency"] > 0.60
    assert result.metrics["elder_folklore_score"] > result.metrics["youth_folklore_score"]


def test_experiment_sv_05_regional_language_variation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_05")
    assert result.success is True
    assert result.metrics["peer_uses_voseo"] is True
    assert result.metrics["elder_uses_voseo"] is False
    assert result.metrics["elder_register"] == "respectful_elder"


def test_experiment_sv_06_migration_remittances(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_06")
    assert result.success is True
    assert result.metrics["monthly_transfer_usd"] == 250.0
    assert result.metrics["food_allocation_usd"] == 112.50
    assert result.metrics["emergency_transfer_usd"] > 250.0


def test_experiment_sv_07_patron_saint_festival_economics(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_07")
    assert result.success is True
    assert result.metrics["total_turnover_usd"] > 1500.0
    assert result.metrics["vendors_benefited"] > 10
    assert result.metrics["social_cohesion_index"] > 0.50


def test_experiment_sv_08_transport_accessibility(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_08")
    assert result.success is True
    assert result.metrics["dirt_rain_hours"] > result.metrics["dirt_dry_hours"]
    assert result.metrics["paved_rain_hours"] < result.metrics["dirt_rain_hours"]


def test_experiment_sv_09_community_cooperation_disruption(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_09")
    assert result.success is True
    assert result.metrics["faena_hours_accumulated"] >= 24.0
    assert result.metrics["volunteers_count"] == 6
    assert result.metrics["cuchubal_pot_awarded_usd"] == 40.0


def test_experiment_sv_10_individual_adaptation_environments(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_SV_10")
    assert result.success is True
    assert result.metrics["milpa_drought_surplus"] < result.metrics["milpa_normal_surplus"]
    assert result.metrics["fishing_safe_profit_usd"] > 20.0
    assert result.metrics["pupuseria_daily_profit_usd"] > 50.0
