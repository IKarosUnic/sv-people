"""Unit and property-based tests for CausalInferenceEngine in SALTBOR Phase 1.12."""

import pytest
import numpy as np

from saltbor.scientific.causal import CausalInferenceEngine
from saltbor.scientific.models import (
    CausalRelationshipType,
    InterventionDomain,
)


class TestCausalInferenceEngine:
    def test_variable_and_edge_registration(self):
        engine = CausalInferenceEngine()
        x = engine.add_variable("X", InterventionDomain.SOCIAL, is_treatment=True)
        y = engine.add_variable("Y", InterventionDomain.ECONOMIC, is_outcome=True)
        assert x.name == "X"
        assert y.name == "Y"

        edge = engine.add_edge("X", "Y", CausalRelationshipType.MECHANISTIC_HYPOTHESIS, weight=1.5)
        assert edge.source == "X"
        assert edge.target == "Y"
        assert (engine.get_children("X")) == ["Y"]
        assert (engine.get_parents("Y")) == ["X"]

    def test_cycle_detection_prevents_feedback_loops_in_dag(self):
        engine = CausalInferenceEngine()
        engine.add_variable("A", InterventionDomain.SOCIAL)
        engine.add_variable("B", InterventionDomain.SOCIAL)
        engine.add_variable("C", InterventionDomain.SOCIAL)

        engine.add_edge("A", "B")
        engine.add_edge("B", "C")

        # Trying to add C -> A should raise ValueError because it creates cycle A -> B -> C -> A
        with pytest.raises(ValueError, match="creates a cycle"):
            engine.add_edge("C", "A")

    def test_find_confounders_and_backdoor_criterion(self):
        engine = CausalInferenceEngine()
        # Confounder Z causes both X (treatment) and Y (outcome)
        engine.add_variable("Z", InterventionDomain.ECONOMIC, is_confounder=True)
        engine.add_variable("X", InterventionDomain.SOCIAL, is_treatment=True)
        engine.add_variable("Y", InterventionDomain.ECONOMIC, is_outcome=True)
        engine.add_variable("M", InterventionDomain.SOCIAL, is_mediator=True)

        engine.add_edge("Z", "X")
        engine.add_edge("Z", "Y")
        engine.add_edge("X", "M")
        engine.add_edge("M", "Y")

        confounders = engine.find_confounders("X", "Y")
        assert "Z" in confounders
        assert "M" not in confounders # M is mediator, not confounder

        # Adjustment without Z is not admissible
        admissible, reasons = engine.check_backdoor_admissibility("X", "Y", set())
        assert admissible is False
        assert len(reasons) > 0

        # Adjusting for Z satisfies backdoor criterion
        admissible_z, reasons_z = engine.check_backdoor_admissibility("X", "Y", {"Z"})
        assert admissible_z is True
        assert len(reasons_z) == 0

    def test_scm_simulation_and_do_operator(self):
        engine = CausalInferenceEngine()
        engine.add_variable("X", InterventionDomain.SOCIAL, baseline_value=0.0)
        engine.add_variable("Y", InterventionDomain.ECONOMIC, baseline_value=0.0)

        # Structural equation: Y = 2.0 * X + Noise
        engine.register_structural_equation(
            "Y",
            parents=["X"],
            func=lambda p, n: 2.0 * p["X"] + n,
            noise_std=0.01,
        )

        # Observational / baseline state
        state_base = engine.simulate_scm(seed=42)
        assert abs(state_base["X"]) < 0.01

        # Intervention do(X = 5.0)
        state_intervened = engine.simulate_scm(interventions={"X": 5.0}, seed=42)
        assert state_intervened["X"] == 5.0
        # Expected Y ~ 10.0
        assert 9.9 < state_intervened["Y"] < 10.1

    def test_treatment_effect_estimation_ate_and_cate(self):
        engine = CausalInferenceEngine()
        engine.add_variable("X", InterventionDomain.SOCIAL, is_treatment=True)
        engine.add_variable("Y", InterventionDomain.ECONOMIC, is_outcome=True)

        engine.register_structural_equation(
            "Y",
            parents=["X"],
            func=lambda p, n: 3.5 * p["X"] + n,
            noise_std=0.1,
        )

        estimate = engine.estimate_treatment_effect(
            treatment_var="X",
            outcome_var="Y",
            treatment_value=1.0,
            control_value=0.0,
            sample_size=100,
            n_bootstraps=200,
            seed=42,
        )

        # Expected ATE ~ 3.5
        assert 3.3 < estimate.ate < 3.7
        assert estimate.is_statistically_significant is True
        assert estimate.is_practically_significant is True
        assert estimate.confidence_interval_95[0] > 3.0
        assert estimate.confidence_interval_95[1] < 4.0

    def test_mediation_analysis(self):
        engine = CausalInferenceEngine()
        engine.add_variable("X", InterventionDomain.SOCIAL, is_treatment=True)
        engine.add_variable("M", InterventionDomain.SOCIAL, is_mediator=True)
        engine.add_variable("Y", InterventionDomain.ECONOMIC, is_outcome=True)

        engine.add_edge("X", "M")
        engine.add_edge("M", "Y")
        engine.add_edge("X", "Y")

        # M = 2.0 * X
        engine.register_structural_equation("M", parents=["X"], func=lambda p, n: 2.0 * p["X"], noise_std=0.01)
        # Y = 1.0 * X (direct) + 2.0 * M (indirect) = 1.0 * X + 4.0 * X = 5.0 * X (total)
        engine.register_structural_equation("Y", parents=["X", "M"], func=lambda p, n: 1.0 * p["X"] + 2.0 * p["M"] + n, noise_std=0.01)

        med_res = engine.analyze_mediation(
            treatment_var="X",
            mediator_var="M",
            outcome_var="Y",
            sample_size=60,
            seed=42,
        )

        assert 4.8 < med_res.total_effect < 5.2
        assert 0.8 < med_res.natural_direct_effect < 1.2
        assert 3.8 < med_res.natural_indirect_effect < 4.2
        assert med_res.is_mediated is True
        assert 0.70 < med_res.proportion_mediated < 0.90

    def test_confounding_sensitivity_oster(self):
        engine = CausalInferenceEngine()
        engine.add_variable("Z", InterventionDomain.ECONOMIC)
        engine.add_variable("X", InterventionDomain.SOCIAL)
        engine.add_variable("Y", InterventionDomain.ECONOMIC)
        engine.add_edge("Z", "X")
        engine.add_edge("Z", "Y")

        sens = engine.assess_confounding_sensitivity("X", "Y", estimated_ate=15.0)
        assert sens["is_robust_to_unobserved_confounding"] is True
        assert sens["delta_degree_to_null"] > 1.0
