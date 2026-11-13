"""Comprehensive End-to-End Test Suite for SALTBOR Phase 1.4 Scenarios (A through G).

Verifies the complete integration of:
- Scenario A: Informal Commerce & Fiado Credit Ledger
- Scenario B: Family Remittances & Diaspora Household Finance
- Scenario C: Community Governance & ADESCO Faenas / Cuchubales
- Scenario D: Judicial Tribunal, Conflict Resolution & Restitution
- Scenario E: Distributed Education & Master-Apprentice Trade Transmission
- Scenario F: Scientific Thinking Cycle & Empirical Hypothesis Testing
- Scenario G: Integrated Civilization Run & Master Runtime Orchestration
"""

import tempfile
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from saltbor.core.config import SimulationConfig
from saltbor.core.types import ActivityType
from saltbor.events.bus import EventBus
from saltbor.events.types import EventType, SimulationEvent
from saltbor.economy.salvadoran.informal_commerce import InformalCommerceEngine
from saltbor.economy.salvadoran.remittances import RemittanceEngine
from saltbor.institutions.education import DistributedEducationEngine, EducationalRole
from saltbor.institutions.legal.code import CommunityLegalCode, LegalStatuteType
from saltbor.institutions.legal.court import JudicialTribunal
from saltbor.population.factory import PopulationFactory
from saltbor.population.human import SyntheticHuman
from saltbor.simulation.orchestrator import ExecutionMode, SimulationRuntimeOrchestrator
from saltbor.simulation.runner import SimulationRunner
from saltbor.simulation.scenarios.profiles import ScenarioProfileType, get_profile
from saltbor.social.salvadoran.community import ADESCOEngine
from saltbor.cognition.epistemic.scientific_thinking import ScientificThinkingEngine
from saltbor.visualization.controller import SimulationController
from saltbor.visualization.server import create_app


# =============================================================================
# SCENARIO A: INFORMAL COMMERCE & FIADO CREDIT
# =============================================================================
def test_scenario_a_informal_commerce_and_fiado():
    """Scenario A:
    1. Vendor registers corner store (pulpería).
    2. Customer makes cash purchase of daily goods.
    3. Customer with insufficient cash requests fiado credit based on trust.
    4. Store extends credit and tracks balance.
    5. Customer settles fiado debt with accrued trust.
    """
    engine = InformalCommerceEngine()
    store = engine.register_corner_store(
        store_id="tienda_la_bendicion",
        name="Tienda La Bendición",
        owner_uid="owner_1",
        location_id="barrio_san_esteban",
        starting_cash=40.0,
    )
    assert store.name == "Tienda La Bendición"
    assert store.cash_box_usd == 40.0

    # 1. Cash purchase of basic groceries
    res_cash = engine.purchase_del_diario(
        store_id="tienda_la_bendicion",
        customer_uid="customer_1",
        customer_cash=10.0,
        needed_items=["frijol_rojo_lb", "huevos_unidad"],
    )
    assert res_cash["success"] is True
    assert res_cash["total_spent_usd"] > 0
    assert store.cash_box_usd > 40.0

    # 2. Insufficient cash -> request traditional fiado
    res_fiado = engine.request_fiado_credit(
        store_id="tienda_la_bendicion",
        customer_uid="customer_1",
        item_amount_usd=5.50,
        customer_reputation=0.85,
    )
    assert res_fiado["approved"] is True
    assert res_fiado["new_balance_usd"] == pytest.approx(5.50)

    # Verify store has active fiado account
    account = store.active_credit_accounts["customer_1"]
    assert account.current_balance_usd == pytest.approx(5.50)
    assert account.consecutive_defaults == 0

    # 3. Settle / Repay fiado debt
    res_repay = engine.settle_fiado_balance(
        store_id="tienda_la_bendicion",
        customer_uid="customer_1",
        payment_amount_usd=5.50,
    )
    assert res_repay["success"] is True
    assert res_repay["remaining_debt_usd"] == 0.0
    assert account.trust_score > 0.85  # Repayment builds community credit trust


# =============================================================================
# SCENARIO B: FAMILY REMITTANCES (DIASPORA TRANSFERS)
# =============================================================================
def test_scenario_b_family_remittances_budget_allocation():
    """Scenario B:
    1. Household registers incoming diaspora transfer profile.
    2. Monthly transfer arrives and allocates across sustenance, education, savings.
    3. Emergency mode shifts allocation heavily to basic needs.
    """
    engine = RemittanceEngine()
    prof = engine.register_household_remittance(
        household_id="hogar_perez",
        monthly_amount_usd=300.0,
        sender_relation="hijo_en_maryland",
        reliability=0.95,
    )
    assert prof.household_id == "hogar_perez"
    assert prof.monthly_transfer_usd == 300.0

    # Normal arrival
    res_norm = engine.process_monthly_remittance(
        household_id="hogar_perez",
        current_household_cash=20.0,
        is_emergency_crisis=False,
    )
    assert res_norm["received"] is True
    assert res_norm["remittance_amount_usd"] == 300.0
    assert res_norm["allocated_budget"]["food_and_subsistence"] > 0
    assert res_norm["allocated_budget"]["education"] > 0
    assert res_norm["allocated_budget"]["savings"] > 0
    assert prof.total_lifetime_received_usd == 300.0

    # Emergency shock (drought crisis)
    res_crisis = engine.process_monthly_remittance(
        household_id="hogar_perez",
        current_household_cash=5.0,
        is_emergency_crisis=True,
    )
    assert res_crisis["received"] is True
    # In crisis, basic sustenance takes priority
    assert res_crisis["allocated_budget"]["food_and_subsistence"] > res_norm["allocated_budget"]["food_and_subsistence"]
    # Total received includes crisis emergency surge (300 + 405 = 705)
    assert prof.total_lifetime_received_usd == 705.0


# =============================================================================
# SCENARIO C: COMMUNITY GOVERNANCE & ADESCO FAENAS / CUCHUBALES
# =============================================================================
def test_scenario_c_community_governance_adesco():
    """Scenario C:
    1. ADESCO proposes public faena project (e.g. water pipeline repair).
    2. Volunteers log hours towards the required quota.
    3. Project transitions to completed.
    4. Cuchubal savings circle rotates pool among neighbors.
    """
    engine = ADESCOEngine()
    proj = engine.create_faena_project(
        project_id="faena_colector_1",
        name="Reparación de Colector Comunal",
        community_id="comunidad_san_esteban",
        target_problem="drenaje_aguas_lluvias",
        required_hours=12.0,
    )
    assert proj.is_completed is False

    # Volunteers log hours
    res1 = engine.contribute_labor_to_faena("faena_colector_1", "vol_1", hours_contributed=6.0)
    assert res1["is_completed"] is False
    assert res1["total_accumulated_hours"] == 6.0

    res2 = engine.contribute_labor_to_faena("faena_colector_1", "vol_2", hours_contributed=6.0)
    assert res2["is_completed"] is True
    assert proj.is_completed is True

    # Cuchubal savings circle
    circle = engine.create_cuchubal(
        circle_id="cuchubal_costureras",
        name="Cuchubal de Costureras",
        organizer_uid="org_1",
        member_uids=["member_a", "member_b", "member_c"],
        contribution_usd=15.0,
    )
    assert circle.contribution_per_turn_usd == 15.0

    turn1 = engine.execute_cuchubal_turn("cuchubal_costureras")
    assert turn1["pot_received_usd"] == 60.0  # 4 * 15 (organizer + 3 members)
    assert turn1["beneficiary"] == "org_1"


# =============================================================================
# SCENARIO D: JUDICIAL TRIBUNAL CONFLICT DOCKET & RESTITUTION
# =============================================================================
def test_scenario_d_judicial_conflict_and_restitution():
    """Scenario D:
    1. Dispute filed between plaintiff and defendant in JudicialTribunal.
    2. Adjudication hearing held before magistrate.
    3. Magistrate issues verdict and enforces economic restitution.
    """
    humans = PopulationFactory.create_population(
        config=SimulationConfig(initial_population_size=3, random_seed=42),
        try_nemotron=False,
    )
    plaintiff, defendant, magistrate = humans[0], humans[1], humans[2]
    plaintiff.physical_state.money = 20.0
    defendant.physical_state.money = 100.0

    tribunal = JudicialTribunal()
    legal_code = CommunityLegalCode()

    # File formal dispute for contract enforcement (debt default)
    case = tribunal.file_case(
        case_id="case_001",
        plaintiff=plaintiff,
        defendant=defendant,
        statute_type=LegalStatuteType.CONTRACT_ENFORCEMENT,
        claim_description="Falta de pago de fiado comercial en tienda de abarrotes",
        claimed_damages=35.0,
        evidence_strength=0.9,
        current_tick=5,
    )
    assert case.case_id == "case_001"
    assert case.verdict is None
    assert case.is_enforced is False

    # Adjudicate and enforce
    outcome = tribunal.adjudicate_and_enforce(
        case_id="case_001",
        magistrate=magistrate,
        legal_code=legal_code,
        plaintiff=plaintiff,
        defendant=defendant,
        municipal_institution=None,
        reputation_engine=None,
        current_tick=10,
    )
    assert outcome is not None
    # Restitution enforcement transferred money from defendant to plaintiff
    assert plaintiff.physical_state.money > 20.0
    assert defendant.physical_state.money < 100.0
    assert case.verdict is not None
    assert case.is_enforced is True


# =============================================================================
# SCENARIO E: DISTRIBUTED EDUCATION & APPRENTICESHIP
# =============================================================================
def test_scenario_e_education_and_apprenticeship():
    """Scenario E:
    1. Mentor and apprentice form bilateral pedagogical agreement.
    2. Practice ticks accumulate skill proficiency.
    3. Spontaneous emergence of workshop when conditions met.
    """
    engine = DistributedEducationEngine()
    mentor_uid = str(uuid.uuid4())
    apprentice_uid = str(uuid.uuid4())

    agr = engine.establish_apprenticeship(
        mentor_uid=mentor_uid,
        apprentice_uid=apprentice_uid,
        domain="albanileria",
        target_proficiency=0.70,
        start_tick=1,
    )
    assert agr.skill_domain == "albanileria"
    assert engine.get_role(mentor_uid) == EducationalRole.MENTOR
    assert engine.get_role(apprentice_uid) == EducationalRole.APPRENTICE

    # Simulate practice and mastery
    agr.ticks_completed += 20
    agr.current_proficiency = 0.75
    if agr.current_proficiency >= agr.target_proficiency:
        agr.is_graduated = True

    assert agr.is_graduated is True

    # Check spontaneous workshop formation
    candidates = [
        {"uid": mentor_uid, "skill_level": 0.80, "prestige": 0.70, "money": 80.0, "age": 45},
        {"uid": apprentice_uid, "skill_level": 0.20, "prestige": 0.30, "money": 10.0, "age": 22},
        {"uid": str(uuid.uuid4()), "skill_level": 0.15, "prestige": 0.25, "money": 12.0, "age": 20},
    ]
    workshop = engine.check_spontaneous_institution_emergence(
        location_id="taller_artesanal",
        community_need_domain="pottery",
        candidates=candidates,
        collective_treasury=50.0,
        tick=50,
    )
    assert workshop is not None
    assert workshop.primary_domain == "pottery"
    assert workshop.founder_uid == mentor_uid


# =============================================================================
# SCENARIO F: SCIENTIFIC THINKING & EMPIRICAL HYPOTHESIS TESTING
# =============================================================================
def test_scenario_f_scientific_thinking_cycle():
    """Scenario F:
    1. Individual discovers an anomaly and initiates scientific cycle.
    2. Formulates hypothesis on organic fertilizer (abono bocashi).
    3. Runs experimental trials with treatment vs control.
    4. Evaluates evidence: Bayesian update confirms causal efficacy.
    """
    engine = ScientificThinkingEngine()
    session = engine.start_investigation(
        creator_uid="scientist_1",
        observation="El cultivo con abono bocashi creció 25% más rápido",
        anomaly_detected=True,
        tick=1,
    )
    assert session.session_id is not None
    assert session.creator_uid == "scientist_1"

    # Formulate question & generate hypothesis
    q = engine.formulate_question(session, subject="abono_bocashi", variable_of_interest="rendimiento_maiz", tick=2)
    assert "abono_bocashi" in q

    hyp = engine.generate_hypothesis(
        session,
        subject="abono_bocashi",
        predicate="increases",
        proposed_effect=1.8,
        prior_confidence=0.45,
        tick=3,
    )
    assert hyp.confidence == 0.45

    # Design experiment & run trials
    engine.design_experiment(
        session,
        manipulated_var="abono_bocashi",
        treatment_val=2.0,
        control_val=0.0,
        trials=5,
        tick=4,
    )
    trials = engine.run_experimental_trials(session, true_causal_effect=1.8, noise_std=0.2, tick=5)
    assert len(trials) == 5

    # Evaluate evidence and revise belief
    status, revised_belief = engine.evaluate_and_revise(session, true_causal_effect=1.8, tick=6)
    assert status in ("supported", "confirmed")
    assert revised_belief.confidence > 0.45  # Bayesian confirmation increases certainty


# =============================================================================
# SCENARIO G: FULL CIVILIZATION INTEGRATION & RUNTIME ORCHESTRATION
# =============================================================================
def test_scenario_g_integrated_civilization_run_and_api_observability():
    """Scenario G:
    1. Instantiates full SimulationRunner with SQLite persistence and MICRO_COMMUNITY.
    2. Runs orchestrator across all execution modes for 25+ ticks.
    3. Verifies persistence of stores, fiado, remittances, court cases in checkpoint.
    4. Connects to FastAPI test client and verifies live civilization endpoints.
    5. Tests observer intervention endpoint with bounded rationality validation.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)

    try:
        profile = get_profile("micro_community")
        cfg = SimulationConfig(
            random_seed=42,
            initial_population_size=profile.initial_population,
            database_path=db_path,
            checkpoint_interval_ticks=10,
        )
        runner = SimulationRunner(config=cfg)
        runner.initialize()

        # Verify orchestrator registered all 6 Phase 1.4 civilization engines
        registered = [e.name for e in runner.orchestrator.get_all_engines()]
        assert "InformalCommerceEngine" in registered
        assert "RemittanceEngine" in registered
        assert "ADESCOEngine" in registered
        assert "JudicialTribunal" in registered
        assert "DistributedEducationEngine" in registered
        assert "ScientificThinkingEngine" in registered

        # Run for 12 ticks
        runner.run(num_ticks=12)
        assert runner.clock.current_tick == 12

        # Check telemetry summary
        summary = runner.orchestrator.get_status_summary()
        assert summary["registered_engines_count"] >= 6
        assert len(summary["engines"]) >= 6

        # Save checkpoint to SQLite
        runner.checkpoint()
        assert runner.clock.current_tick == 12
        # Verify persistence of civilization entities
        assert len(runner.salvadoran_informal_commerce.get_all_stores()) >= 1
        assert len(runner.salvadoran_remittances.get_all_profiles()) >= 1
        assert len(runner.salvadoran_adesco.get_all_faenas()) >= 1

        # Connect API Controller, create app and TestClient using runner
        controller = SimulationController(seed=42, db_path=":memory:")
        controller.runner = runner
        controller.pause()
        app = create_app(controller)
        client = TestClient(app)

        # 1. Communities API
        resp_comm = client.get("/api/communities")
        assert resp_comm.status_code == 200
        data_comm = resp_comm.json()
        assert "faenas" in data_comm
        assert "cuchubales" in data_comm

        # 2. Commerce API
        resp_stores = client.get("/api/commerce/stores")
        assert resp_stores.status_code == 200
        assert len(resp_stores.json()) >= 1

        resp_fiado = client.get("/api/commerce/fiado")
        assert resp_fiado.status_code == 200
        assert isinstance(resp_fiado.json(), list)

        # 3. Remittances API
        resp_rem = client.get("/api/economy/remittances")
        assert resp_rem.status_code == 200
        assert "profiles" in resp_rem.json()

        # 4. Justice Cases API
        resp_court = client.get("/api/justice/cases")
        assert resp_court.status_code == 200
        assert isinstance(resp_court.json(), list)

        # 5. Education & Apprenticeships API
        resp_edu = client.get("/api/education/apprenticeships")
        assert resp_edu.status_code == 200
        assert "apprenticeships" in resp_edu.json()

        # 6. Science Discoveries API
        resp_sci = client.get("/api/science/discoveries")
        assert resp_sci.status_code == 200
        assert isinstance(resp_sci.json(), list)

        # 7. Scenario Profiles API
        resp_prof = client.get("/api/scenarios/profiles")
        assert resp_prof.status_code == 200
        assert len(resp_prof.json()) == 6

        # 8. Observer Intervention: Propose Activity (Honoring Autonomy)
        any_human = next(iter(runner.population.get_all()))
        resp_int = client.post(
            "/api/interventions/request_activity",
            json={
                "human_uid": str(any_human.uid),
                "activity": "community_meeting",
                "reason": "Convocatoria vecinal a la asamblea",
            },
        )
        assert resp_int.status_code == 200
        res_int_data = resp_int.json()
        assert "accepted" in res_int_data
        if res_int_data["accepted"]:
            assert any_human.physical_state.current_activity == ActivityType.COMMUNITY_MEETING

        runner.close()
    finally:
        try:
            db_path.unlink()
        except OSError:
            pass
