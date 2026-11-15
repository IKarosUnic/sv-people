"""Test suite for Phase 1.14 Integrated Territorial Ecosystems & Multi-Scale Governance Experiments.

Verifies all 20 required experiments (EXP_114_A through EXP_114_T):
- EXP_114_A: Cross-Domain Interaction Consistency
- EXP_114_B: Transportation and Commercial Activity
- EXP_114_C: Education and Household Economic Interaction
- EXP_114_D: Healthcare Accessibility and Household Constraints
- EXP_114_E: Agricultural Supply and Urban Food Markets
- EXP_114_F: Public Market Development
- EXP_114_G: Rural Infrastructure and Community Accessibility
- EXP_114_H: Public Service Capacity and Geographic Demand
- EXP_114_I: Regional Economic Network Disruption
- EXP_114_J: Multiple Interventions and Unintended Consequences
- EXP_114_K: Community-Level Resource Allocation
- EXP_114_L: Institutional Coordination and Project Governance
- EXP_114_M: Urban-Rural Service Accessibility
- EXP_114_N: Multi-Scale Population Consistency
- EXP_114_O: Territorial Project Comparison
- EXP_114_P: Longitudinal Regional Development
- EXP_114_Q: Environmental and Economic Feedback
- EXP_114_R: Conflicting Development Objectives
- EXP_114_S: Cross-Domain Scenario Reproducibility
- EXP_114_T: Sustained Computational Performance
"""

import pytest
from saltbor.simulation.experiments.phase114_territorial_experiments import PHASE114_EXPERIMENTS


@pytest.mark.parametrize("exp_id,exp_cls", list(PHASE114_EXPERIMENTS.items()))
def test_phase114_experiments(exp_id: str, exp_cls: type):
    """Execute each Phase 1.14 experiment and assert empirical success and valid hypotheses."""
    exp = exp_cls()
    result = exp.run()
    assert result.success is True, f"Experiment {exp_id} failed: {result.summary}"
    assert len(result.hypotheses) >= 1
    assert all(h["confirmed"] for h in result.hypotheses), f"Unconfirmed hypothesis in {exp_id}"
    assert result.duration_seconds >= 0.0
