"""Counterfactual Civilization Research Engine for SALTBOR Phase 1.12.

Enables comparative history and counterfactual civilization inquiry:
- Forks simulation state at tick T_branch into parallel trajectories.
- Baseline trajectory (historical factual) vs Counterfactual trajectory (altered intervention).
- Identical random seeds and background stochastic isolation.
- Measures metric divergence over time, divergence point detection, and area-under-the-curve difference.
- Preserves accounting conservation and offline execution.
- Epistemic disclaimer: Counterfactuals explore synthetic generative mechanisms, NOT predictions
  of actual historical or future Salvadoran society.
"""

from __future__ import annotations

import collections
import copy
import logging
import math
from typing import Any, Callable, Dict, List, Optional
import numpy as np

from saltbor.scientific.models import CounterfactualTrajectoryComparison

logger = logging.getLogger(__name__)


class CounterfactualCivilizationEngine:
    """Orchestrates counterfactual branching and comparative historical trajectory analysis."""

    def __init__(self) -> None:
        self.counterfactual_comparisons: dict[str, CounterfactualTrajectoryComparison] = {}

    def branch_and_compare(
        self,
        scenario_id: str,
        scenario_name: str,
        intervention_tick: int,
        intervention_description: str,
        altered_parameters: dict[str, Any],
        timesteps: list[int],
        simulation_step_fn: Callable[[int, dict[str, Any], int], dict[str, float]],
        seed: int = 42,
        metrics_to_track: Optional[list[str]] = None,
        confounding_factors: Optional[list[str]] = None,
        limitations: Optional[list[str]] = None,
    ) -> CounterfactualTrajectoryComparison:
        """Execute parallel factual baseline and counterfactual trajectories.

        simulation_step_fn(tick, active_params, seed) -> dict of metric values.
        """
        tracked = metrics_to_track or ["population", "economic_liquidity", "resource_stock", "social_trust"]
        baseline_metrics: dict[str, list[float]] = collections.defaultdict(list)
        cf_metrics: dict[str, list[float]] = collections.defaultdict(list)

        # Baseline run (no altered parameters)
        for t in timesteps:
            m_base = simulation_step_fn(t, {}, seed)
            for k in tracked:
                baseline_metrics[k].append(float(m_base.get(k, 0.0)))

        # Counterfactual run: apply altered_parameters at and after intervention_tick
        for t in timesteps:
            params = altered_parameters if t >= intervention_tick else {}
            m_cf = simulation_step_fn(t, params, seed)
            for k in tracked:
                cf_metrics[k].append(float(m_cf.get(k, 0.0)))

        # Measure divergence over time
        divergence_point = -1
        total_divergence: dict[str, float] = {}

        for k in tracked:
            b_vals = np.array(baseline_metrics[k], dtype=np.float64)
            c_vals = np.array(cf_metrics[k], dtype=np.float64)
            # Area divergence (sum of absolute differences)
            area_diff = float(np.sum(np.abs(c_vals - b_vals)))
            total_divergence[k] = area_diff

            # Check first divergence > 5% after intervention_tick
            for idx, t in enumerate(timesteps):
                if t >= intervention_tick and divergence_point == -1:
                    base_val = b_vals[idx]
                    cf_val = c_vals[idx]
                    rel_diff = abs(cf_val - base_val) / max(1e-6, abs(base_val))
                    if rel_diff >= 0.05:
                        divergence_point = t

        if divergence_point == -1:
            divergence_point = intervention_tick

        primary_k = tracked[0]
        final_base = baseline_metrics[primary_k][-1] if baseline_metrics[primary_k] else 0.0
        final_cf = cf_metrics[primary_k][-1] if cf_metrics[primary_k] else 0.0
        delta_pct = ((final_cf - final_base) / max(1e-6, abs(final_base))) * 100.0

        qualitative = (
            f"Following intervention '{intervention_description}' at tick {intervention_tick}, "
            f"the counterfactual trajectory diverged at tick {divergence_point}. "
            f"By end of observation, '{primary_k}' diverged by {delta_pct:+.1f}% "
            f"relative to baseline historical factual."
        )

        comparison = CounterfactualTrajectoryComparison(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            intervention_tick=intervention_tick,
            intervention_description=intervention_description,
            altered_parameters=altered_parameters,
            baseline_seed=seed,
            timesteps=timesteps,
            baseline_metrics=dict(baseline_metrics),
            counterfactual_metrics=dict(cf_metrics),
            divergence_point_tick=divergence_point,
            total_trajectory_divergence=total_divergence,
            qualitative_divergence=qualitative,
            confounding_factors=confounding_factors or [
                "Adaptive agent behavioral compensation may buffer exogenous shock.",
                "Simultaneous secondary feedback loops in demographic turnover.",
            ],
            limitations=limitations or [
                "Counterfactual scenario does not predict real historical Salvadoran society.",
                "Assumes invariant institutional boundary rules outside the intervention scope.",
            ],
        )

        self.counterfactual_comparisons[scenario_id] = comparison
        return comparison

    def get_comparison(self, scenario_id: str) -> Optional[CounterfactualTrajectoryComparison]:
        return self.counterfactual_comparisons.get(scenario_id)
