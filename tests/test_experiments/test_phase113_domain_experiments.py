"""Test suite for Phase 1.13 Universal Human Activity & Domain Simulation Experiments.

Verifies all 20 required experiments (EXP_113_A through EXP_113_T):
- EXP_113_A: Domain Registration and Configuration
- EXP_113_B: Cross-Domain Human Activity
- EXP_113_C: Food Vendor Creation and Consumer Behavior
- EXP_113_D: Commercial Competition and Consumer Choice
- EXP_113_E: Rural Educational Accessibility
- EXP_113_F: Urban Educational Accessibility
- EXP_113_G: Healthcare Accessibility and Capacity
- EXP_113_H: Transportation and Daily Human Activity
- EXP_113_I: Agricultural Activity and Local Markets
- EXP_113_J: Business Creation Under Different Economic Conditions
- EXP_113_K: User-Created Geographic Facilities
- EXP_113_L: Editable World Layer Isolation
- EXP_113_M: Permission and Ownership Enforcement
- EXP_113_N: Institutional Intervention Scenarios
- EXP_113_O: Multiple Domain Interaction
- EXP_113_P: Real and Simulated Data Separation
- EXP_113_Q: Experiment Database Compactness and Traceability
- EXP_113_R: Recommendation Explainability
- EXP_113_S: Offline Operation
- EXP_113_T: Performance Under Multiple Active Domains
"""

import pytest
from saltbor.simulation.experiments.phase113_domain_experiments import PHASE113_EXPERIMENTS


@pytest.mark.parametrize("exp_id,exp_cls", list(PHASE113_EXPERIMENTS.items()))
def test_phase113_experiments(exp_id: str, exp_cls: type):
    """Execute each Phase 1.13 experiment and assert empirical success and valid hypotheses."""
    exp = exp_cls()
    result = exp.run()
    assert result.success is True, f"Experiment {exp_id} failed: {result.summary}"
    assert len(result.hypotheses) >= 1
    assert all(h["confirmed"] for h in result.hypotheses), f"Unconfirmed hypothesis in {exp_id}"
    assert result.duration_seconds >= 0.0
