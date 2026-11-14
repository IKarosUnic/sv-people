"""Execute the full Phase 1.8 Integrated World & Human Life experiment suite (EXP_18_A ... EXP_18_T).

Validates:
- Complete diurnal daily life cycle and biorhythms
- Labor market mobility and economic informal adaptation
- Zero-purchase browsing ($0.00 spend) and price comparison purchasing
- Household income shock adaptation and budget rebalancing
- Illness altering activities and relationships
- Traffic accident trajectory disruption and speed modulation
- Tropical storm impacts on road transit and flood hazards
- Road blockage detection, rerouting, and cancellation without teleportation
- Family emergency expenditure and accounting conservation
- Shared interpersonal experience strengthening relationships
- Interpersonal conflict and social repercussions
- Place capability restrictions: opening hours and inventory stockouts
- Local supply scarcity and price inflation elasticity
- ADESCO communal response to crisis (cleanup faena)
- Historical memory transmission and collective preservation
- Observer intervention and traceable Directed Acyclic Graph causality
- Frontend / GIS layer state fidelity to memory model
- Checkpoint persistence and lossless recovery
- Sustained multi-cycle simulation stability
"""

from __future__ import annotations

import pytest

from saltbor.simulation.experiments.phase18_experiments import PHASE18_EXPERIMENTS


@pytest.mark.parametrize("experiment_class", PHASE18_EXPERIMENTS)
def test_phase18_experiment_executes_and_reports(experiment_class):
    experiment = experiment_class()
    result = experiment.run()

    assert result.success is True, f"{result.experiment_id} failed: {result.summary}"
    assert result.experiment_id == experiment.config.experiment_id
    assert result.hypotheses, "an experiment must state at least one hypothesis"
    assert result.metrics, "an experiment must record measurements"
    assert result.summary, "an experiment must produce a human-readable summary"
    assert result.duration_seconds >= 0.0


def test_phase18_suite_covers_all_twenty_experiments():
    ids = [cls().config.experiment_id for cls in PHASE18_EXPERIMENTS]
    expected = [f"EXP_18_{letter}" for letter in "ABCDEFGHIJKLMNOPQRST"]
    assert sorted(ids) == sorted(expected)
