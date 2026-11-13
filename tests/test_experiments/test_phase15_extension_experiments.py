"""Tests running all Phase 1.5 Extension World-Human, Romance, Health & Causal Experiments EXP_15_EXT_01 through EXP_15_EXT_16."""

import pytest
from saltbor.simulation.experiments.phase15_extension_experiments import (
    PHASE15_EXTENSION_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE15_EXTENSION_EXPERIMENTS)
def test_exp_15_extension_experiments_pass(exp_cls):
    """Execute each Phase 1.5 Extension experiment and verify validity, hypotheses and metrics."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
    for hyp in res.hypotheses:
        assert hyp["status"] in ("HYPOTHESIS_SUPPORTED", "HYPOTHESIS_REJECTED", "INCONCLUSIVE", "EXPERIMENT_ERROR")
