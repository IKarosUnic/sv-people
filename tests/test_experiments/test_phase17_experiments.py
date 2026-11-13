"""Execute the full Phase 1.7 experiment suite (EXP_17_A ... EXP_17_T).

A passing test means the experiment executed and produced an interpretable
result, not that every hypothesis was supported.
"""

from __future__ import annotations

import pytest

from saltbor.simulation.experiments.phase17_experiments import PHASE17_EXPERIMENTS

VALID_STATUSES = {
    "HYPOTHESIS_SUPPORTED",
    "HYPOTHESIS_REJECTED",
    "INCONCLUSIVE",
    "EXPERIMENT_ERROR",
}


@pytest.mark.parametrize("experiment_class", PHASE17_EXPERIMENTS)
def test_phase17_experiment_executes_and_reports(experiment_class):
    experiment = experiment_class()
    result = experiment.run()

    assert result.success is True, f"{result.experiment_id} failed: {result.summary}"
    assert result.experiment_id == experiment.config.experiment_id
    assert result.hypotheses, "an experiment must state at least one hypothesis"
    assert result.metrics, "an experiment must record measurements"
    assert result.summary
    for hypothesis in result.hypotheses:
        assert hypothesis["status"] in VALID_STATUSES
        assert hypothesis["statement"]
        assert hypothesis["status"] != "EXPERIMENT_ERROR"


def test_phase17_suite_covers_all_twenty_experiments():
    ids = [cls().config.experiment_id for cls in PHASE17_EXPERIMENTS]
    expected = [f"EXP_17_{letter}" for letter in "ABCDEFGHIJKLMNOPQRST"]
    assert sorted(ids) == sorted(expected)
