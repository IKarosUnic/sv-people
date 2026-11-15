"""Test suite for the Connected Territorial Scenarios Demonstration (Phase 1.14).

Verifies cross-sector cascading between:
1. Commercial / Transportation
2. Education
3. Healthcare

Operating on the EXACT SAME synthetic individuals, households, and territory:
- Territory: Cantón San José Las Flores, San Vicente Sur
- Shared Cohort:
  * Familia Henríquez (José: agricultural laborer, Mateo: 15yo student)
  * Familia Vásquez (Carmen: Tiendita owner, Rosa: 72yo hypertensive elder)
"""

import pytest
from saltbor.territory.connected_scenarios import ConnectedTerritorialScenariosDemonstrator


def test_connected_scenarios_baseline():
    demo = ConnectedTerritorialScenariosDemonstrator(random_seed=42)
    base = demo.run_baseline()

    # Commercial invariants
    assert base.road_friction_multiplier == 1.0
    assert base.retail_food_price_usd == 0.65
    assert base.is_tiendita_solvent is True
    assert base.tiendita_cash_usd >= 180.0

    # Household invariants
    assert base.jose_cash_balance_usd == 48.00
    assert base.daily_food_expenditure_usd < 6.00
    assert base.food_budget_share_pct < 50.0  # Under 50% of wage
    assert base.informal_credit_fiado_usd == 0.0

    # Education invariants
    assert base.mateo_school_attendance_pct >= 95.0
    assert base.mateo_dropout_risk < 0.10
    assert base.mateo_is_working_informal is False

    # Healthcare invariants
    assert base.clinic_waiting_time_hours <= 0.30
    assert base.jose_lost_work_days == 0
    assert base.out_of_pocket_medical_usd == 0.0


def test_connected_scenarios_commercial_shock():
    demo = ConnectedTerritorialScenariosDemonstrator(random_seed=42)
    demo.run_baseline()
    shock = demo.trigger_commercial_transport_shock()

    # Commercial shock invariants
    assert shock.road_friction_multiplier >= 3.0
    assert shock.retail_food_price_usd > 0.80  # Significant food inflation
    assert shock.tiendita_footfall_factor < 0.60  # Footfall contraction

    # Household budget impact on the SAME person (José)
    assert shock.daily_food_expenditure_usd > 8.00
    assert shock.food_budget_share_pct > 70.0  # Over 70% of wage consumed by food
    assert shock.jose_cash_balance_usd < 30.00  # Rapid cash depletion


def test_connected_scenarios_educational_cascade():
    demo = ConnectedTerritorialScenariosDemonstrator(random_seed=42)
    demo.run_baseline()
    demo.trigger_commercial_transport_shock()
    edu = demo.propagate_to_education()

    # Educational impact on the SAME student (Mateo)
    assert edu.mateo_is_working_informal is True  # Engaged in child labor
    assert edu.mateo_school_attendance_pct < 50.0  # Attendance collapses
    assert edu.mateo_dropout_risk > 0.20  # Elevated dropout risk
    assert edu.school_overall_attendance_pct < 70.0


def test_connected_scenarios_healthcare_cascade_and_feedback():
    demo = ConnectedTerritorialScenariosDemonstrator(random_seed=42)
    demo.run_baseline()
    demo.trigger_commercial_transport_shock()
    demo.propagate_to_education()
    hlt = demo.propagate_to_healthcare_and_feedback()

    # Healthcare crisis on the SAME individuals (Rosa & José)
    assert hlt.clinic_waiting_time_hours >= 3.0  # Acute clinic bottleneck
    assert hlt.jose_lost_work_days >= 3          # Multiple days lost to illness & queue
    assert hlt.out_of_pocket_medical_usd >= 20.0 # Commercial medicine cost
    assert hlt.rosa_health_status < 0.50
    assert hlt.jose_health_status < 0.60

    # Household reaches insolvency
    assert hlt.jose_cash_balance_usd == 0.00
    assert hlt.informal_credit_fiado_usd > 10.00

    # Feedback into Tiendita commercial insolvency
    assert hlt.is_tiendita_solvent is False


def test_connected_scenarios_integrated_recovery():
    demo = ConnectedTerritorialScenariosDemonstrator(random_seed=42)
    snaps = demo.run_full_demonstration()
    assert len(snaps) == 5

    recovery = snaps[4]
    # Commercial recovery
    assert recovery.road_friction_multiplier == 1.0
    assert recovery.retail_food_price_usd == 0.65
    assert recovery.is_tiendita_solvent is True
    assert recovery.tiendita_cash_usd >= 200.0

    # Household finances restored on the SAME person (José)
    assert recovery.jose_cash_balance_usd >= 40.00
    assert recovery.informal_credit_fiado_usd == 0.00
    assert recovery.food_budget_share_pct < 40.0

    # Educational recovery on the SAME student (Mateo)
    assert recovery.mateo_is_working_informal is False
    assert recovery.mateo_school_attendance_pct >= 90.0
    assert recovery.mateo_dropout_risk <= 0.06

    # Healthcare recovery on the SAME individuals (Rosa & José)
    assert recovery.clinic_waiting_time_hours <= 0.30
    assert recovery.jose_lost_work_days == 0
    assert recovery.out_of_pocket_medical_usd == 0.0
    assert recovery.rosa_health_status >= 0.85
    assert recovery.jose_health_status == 1.00
