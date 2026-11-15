"""Test suite for Phase 1.15 Generalized Territorial Scenarios, Causal Validation & Real Engine Integration Experiments.

Verifies all 20 required experiments (EXP_115_A through EXP_115_T):
- EXP_115_A: Generalized Scenario Reproducibility
- EXP_115_B: Multi-household Transport Disruption
- EXP_115_C: Delayed Educational Consequences
- EXP_115_D: Household Health-Economic Cascade
- EXP_115_E: Small Business Liquidity
- EXP_115_F: Double-entry Accounting Consistency
- EXP_115_G: Shared Entity State Consistency
- EXP_115_H: Heterogeneous Human Responses
- EXP_115_I: Urban-Rural Comparison
- EXP_115_J: Multi-seed Robustness
- EXP_115_K: Sensitivity Analysis
- EXP_115_L: Causal Trace Completeness
- EXP_115_M: Intervention Comparison
- EXP_115_N: Combined Intervention Effects
- EXP_115_O: Unintended Consequences
- EXP_115_P: Territorial Data Provenance
- EXP_115_Q: Longitudinal Household Evolution
- EXP_115_R: Economic Conservation
- EXP_115_S: Scenario Reproducibility Across Versions
- EXP_115_T: Sustained Performance
"""

import pytest
from saltbor.simulation.experiments.phase115_territorial_experiments import PHASE115_EXPERIMENTS


@pytest.mark.parametrize("exp_id,exp_cls", list(PHASE115_EXPERIMENTS.items()))
def test_phase115_experiments(exp_id: str, exp_cls: type):
    """Execute each Phase 1.15 experiment and assert empirical success and verified hypotheses."""
    exp = exp_cls()
    result = exp.run()
    assert result.success is True, f"Experiment {exp_id} failed: {result.summary}"
    assert len(result.hypotheses) >= 1
    assert all(h["confirmed"] for h in result.hypotheses), f"Unconfirmed hypothesis in {exp_id}"
    assert result.duration_seconds >= 0.0
