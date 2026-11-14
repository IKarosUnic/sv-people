"""Comprehensive unit tests for the Scientific Experimentation, Sensitivity & Context Subsystems."""

import pytest
import numpy as np

from saltbor.events.causal_graph import CausalEventGraph
from saltbor.events.types import EventType, SimulationEvent
from saltbor.scientific.counterfactual import CounterfactualCivilizationEngine
from saltbor.scientific.experimentation import ScientificExperimentationEngine
from saltbor.scientific.models import (
    EvidenceValidationTier,
    ExperimentType,
    InterventionDomain,
    SensitivityClass,
    StratifiedSampleSpec,
)
from saltbor.scientific.salvadoran_context import (
    ElSalvadorResearchContext,
    SALVADORAN_DEPARTMENT_PROFILES,
)
from saltbor.scientific.sampling import PopulationSamplingEngine
from saltbor.scientific.sensitivity import ParameterSensitivityEngine
from saltbor.scientific.traceability import CausalEventTraceabilityEngine
from saltbor.scientific.validation import (
    SALVADORAN_EXTERNAL_BENCHMARKS,
    ScientificValidationFramework,
)


class TestScientificExperimentationEngine:
    def test_protocol_registration_and_multi_seed_run(self):
        engine = ScientificExperimentationEngine()
        protocol = engine.create_protocol(
            protocol_id="PROTO_TEST_01",
            name="Test Civic Cooperation",
            research_question="Does civic trust foster public goods contribution?",
            hypotheses=["Contribution rate exceeds 50% across runs."],
            experiment_type=ExperimentType.CONTROLLED,
            domain=InterventionDomain.SOCIAL,
            independent_variables=["civic_trust"],
            dependent_variables=["contribution_rate"],
            control_variables=["wealth"],
            treatment_definition={"trust": 0.8},
            seeds=[42, 101, 202],
        )
        assert protocol.protocol_id == "PROTO_TEST_01"

        def test_run_fn(seed: int, prot):
            rng = np.random.RandomState(seed)
            contrib = float(rng.normal(0.65, 0.05))
            return {"contribution_rate": contrib}, {"Contribution rate exceeds 50% across runs.": contrib > 0.50}, []

        result = engine.run_protocol("PROTO_TEST_01", test_run_fn)
        assert result.protocol_id == "PROTO_TEST_01"
        assert result.total_runs == 3
        assert result.successful_runs == 3
        assert result.failure_rate == 0.0

        stats = result.summary_statistics["contribution_rate"]
        assert 0.60 < stats["mean"] < 0.70
        assert stats["ci_95_low"] <= stats["mean"] <= stats["ci_95_high"]
        assert result.hypotheses_status["Contribution rate exceeds 50% across runs."]["supported"] is True


class TestParameterSensitivityEngine:
    def test_one_at_a_time_sweep(self):
        sens_eng = ParameterSensitivityEngine()

        def eval_fn(val: float) -> dict[str, float]:
            return {"output": float(val ** 2)}

        sweep = sens_eng.one_at_a_time_sweep(
            parameter_name="param_x",
            baseline_value=5.0,
            perturbation_range=(1.0, 10.0),
            steps=5,
            evaluation_fn=eval_fn,
            outcome_metrics=["output"],
        )
        assert sweep.parameter_name == "param_x"
        assert sweep.is_monotonic is True
        assert sweep.elasticities["output"] > 1.0

    def test_morris_elementary_effects_screening(self):
        sens_eng = ParameterSensitivityEngine()

        def linear_model(params: dict[str, float]) -> float:
            return 5.0 * params["important"] + 0.01 * params["trivial"]

        results = sens_eng.morris_elementary_effects(
            parameters={"important": (0.0, 10.0), "trivial": (0.0, 10.0)},
            evaluation_fn=linear_model,
            num_trajectories=6,
            seed=42,
        )
        assert results["important"]["mu_star"] > results["trivial"]["mu_star"] * 10.0


class TestCounterfactualCivilizationEngine:
    def test_branch_and_compare_divergence(self):
        cf_eng = CounterfactualCivilizationEngine()

        def step_sim(tick: int, params: dict[str, Any], seed: int) -> dict[str, float]:
            shock = params.get("drought", False)
            return {"yield": 30.0 if (tick >= 20 and shock) else 100.0}

        comp = cf_eng.branch_and_compare(
            scenario_id="TEST_CF_01",
            scenario_name="Test Drought Branch",
            intervention_tick=20,
            intervention_description="Drought introduced at tick 20",
            altered_parameters={"drought": True},
            timesteps=[10, 20, 30, 40],
            simulation_step_fn=step_sim,
            metrics_to_track=["yield"],
        )
        assert comp.scenario_id == "TEST_CF_01"
        assert comp.divergence_point_tick == 20
        assert comp.total_trajectory_divergence["yield"] > 0.0
        assert comp.counterfactual_metrics["yield"][-1] == 30.0
        assert comp.baseline_metrics["yield"][-1] == 100.0


class TestCausalEventTraceabilityEngine:
    def test_9_tier_trace_construction(self):
        g = CausalEventGraph()
        e_env = SimulationEvent(event_type=EventType.HAZARD_PERCEIVED, tick=5, data={"description": "Drought onset"})
        e_bio = SimulationEvent(event_type=EventType.RESOURCES_DEPLETED, tick=8, cause_event_id=e_env.event_id, data={"description": "Crop wilts"})
        e_civ = SimulationEvent(event_type=EventType.COOPERATION_OCCURRED, tick=12, cause_event_id=e_bio.event_id, data={"description": "ADESCO meeting"})

        g.add_event(e_env)
        g.add_event(e_bio)
        g.add_event(e_civ)

        tracer = CausalEventTraceabilityEngine(g)
        trace = tracer.build_trace(str(e_civ.event_id))

        assert trace.target_event_id == str(e_civ.event_id)
        assert len(trace.steps) == 3
        assert trace.steps[0].event_id == str(e_env.event_id)
        assert trace.direct_causes_count >= 2


class TestSamplingAndGeographicContext:
    def test_salvadoran_14_departments_coverage(self):
        ctx = ElSalvadorResearchContext()
        depts = ctx.list_all_departments()
        assert len(depts) == 14
        assert "San Salvador" in depts
        assert "Chalatenango" in depts
        assert "Morazán" in depts

        meta = ctx.get_provenance_metadata()
        assert meta["license"] == "ODbL 1.0 (https://www.openstreetmap.org/copyright)"
        assert meta["feature_count"] == 151251

    def test_stratified_population_sampling(self):
        sampler = PopulationSamplingEngine()
        spec = StratifiedSampleSpec(sample_size=30, wealth_quintiles=[1, 2, 3, 4, 5])
        sample = sampler.sample_population(spec, seed=42)

        assert len(sample) == 30
        audit = sampler.audit_sample_representation(sample)
        assert audit["sample_size"] == 30
        assert audit["is_representative"] is True


class TestScientificValidationFramework:
    def test_validation_criteria_and_benchmarking(self):
        framework = ScientificValidationFramework()
        assert len(framework.benchmarks) >= 5
        assert "remittances_household_pct" in framework.benchmarks
        assert "informal_employment_rate" in framework.benchmarks

        # Create mock result
        sci_eng = ScientificExperimentationEngine()
        protocol = sci_eng.create_protocol(
            protocol_id="PROTO_VAL_TEST",
            name="Validation Test",
            research_question="Q",
            hypotheses=["H1"],
            experiment_type=ExperimentType.CONTROLLED,
            domain=InterventionDomain.ECONOMIC,
            independent_variables=["x"],
            dependent_variables=["remittances_household_pct"],
            control_variables=[],
            treatment_definition={},
            seeds=[42, 101, 202],
        )

        def mock_run(s, p):
            return {"remittances_household_pct": 0.24}, {"H1": True}, []

        res = sci_eng.run_protocol("PROTO_VAL_TEST", mock_run)
        eval_report = framework.evaluate_experiment_validity(res, target_benchmark_key="remittances_household_pct")

        assert eval_report["criteria_checks"]["internal_consistency"]["satisfied"] is True
        assert eval_report["criteria_checks"]["reproducibility"]["satisfied"] is True
        assert eval_report["criteria_checks"]["external_evidence_compatibility"]["satisfied"] is True
        assert eval_report["validation_tier"] == EvidenceValidationTier.EMPIRICALLY_CALIBRATED.value
