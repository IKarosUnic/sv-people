"""Execute the full Phase 1.6 experiment suite (EXP_16_A ... EXP_16_T).

A passing test here means the experiment executed and produced an interpretable
result.  It does **not** mean every hypothesis was supported: several are
deliberately falsifiable and some are reported as inconclusive.
"""

from __future__ import annotations

import pytest

from saltbor.simulation.experiments.phase16_experiments import (
    PHASE16_EXPERIMENTS,
    run_all_phase16_experiments,
)

VALID_STATUSES = {
    "HYPOTHESIS_SUPPORTED",
    "HYPOTHESIS_REJECTED",
    "INCONCLUSIVE",
    "EXPERIMENT_ERROR",
}


@pytest.mark.parametrize("experiment_class", PHASE16_EXPERIMENTS)
def test_phase16_experiment_executes_and_reports(experiment_class):
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
        # Errors must not be swallowed into a passing run.
        assert hypothesis["status"] != "EXPERIMENT_ERROR"


def test_phase16_suite_covers_all_twenty_experiments():
    ids = [cls().config.experiment_id for cls in PHASE16_EXPERIMENTS]
    expected = [f"EXP_16_{letter}" for letter in "ABCDEFGHIJKLMNOPQRST"]
    assert sorted(ids) == sorted(expected)


def test_phase16_suite_runs_as_a_whole():
    results = run_all_phase16_experiments()
    assert len(results) == 20
    for experiment_id, result in results.items():
        assert result.experiment_id == experiment_id
        assert result.success, f"{experiment_id}: {result.summary}"
