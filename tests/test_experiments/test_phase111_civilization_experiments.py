"""Tests executing all Phase 1.11 Emergent Civilization Experiments EXP_111_A through EXP_111_X."""

import pytest
from saltbor.simulation.experiments.phase111_civilization_experiments import (
    PHASE111_CIVILIZATION_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE111_CIVILIZATION_EXPERIMENTS)
def test_exp_111_civilization_experiments_pass(exp_cls):
    """Execute each Phase 1.11 Civilization experiment and verify success."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
