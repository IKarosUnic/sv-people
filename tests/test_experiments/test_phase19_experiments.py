"""Execute the full Phase 1.9 Emergent Society & Institutional Evolution experiment suite (EXP_19_A ... EXP_19_X).

Validates:
- Spontaneous formation of commercial collective
- Organization failure and dissolution due to trust collapse
- Organization fission resulting from factional internal strife
- Institutionalization in response to collective societal need
- Institutional crisis and delegitimization
- Leadership succession and statutory reform
- Deliberative assembly voting with registered persistent dissent
- Intergroup dispute negotiation and compromise pact
- Common-Pool Resource (CPR) collective governance under Ostrom principles
- Tragedy of the Commons resource depletion under unmonitored free-riding
- Commercial business creation, liability accumulation, and liquidation
- Longitudinal multidimensional stratification, Gini, Palma, and mobility
- Labor strike, boycott, and mediated wage settlement
- Social norm transmission and graduated sanction enforcement
- Cultural custom decay into desuetudo and extinction
- Institutional knowledge conservation and apprentice skill acceleration
- Community territorial fragmentation into rival factions
- Inter-organizational cooperation and merger
- Asymmetric influence and social power in deliberative governance
- Institutional capacity deficit and backlog accumulation from budget strain
- Informal community substitution for an absent public service
- Historical transformation and mission shift of an institution
- Comparative divergence between societies with different initial conditions
- Sustained multi-cycle simulation stability and coevolution
"""

from __future__ import annotations

import pytest

from saltbor.simulation.experiments.phase19_experiments import PHASE19_EXPERIMENTS


@pytest.mark.parametrize("experiment_class", PHASE19_EXPERIMENTS)
def test_phase19_experiment_executes_and_reports(experiment_class):
    experiment = experiment_class()
    result = experiment.run()

    assert result.success is True, f"{result.experiment_id} failed: {result.summary}"
    assert result.experiment_id == experiment.config.experiment_id
    assert result.hypotheses, "an experiment must state at least one hypothesis"
    assert result.metrics, "an experiment must record measurements"
    assert result.summary, "an experiment must produce a human-readable summary"
    assert result.duration_seconds >= 0.0


def test_phase19_suite_covers_all_twenty_four_experiments():
    ids = [cls().config.experiment_id for cls in PHASE19_EXPERIMENTS]
    expected = [f"EXP_19_{letter}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWX"]
    assert sorted(ids) == sorted(expected)
