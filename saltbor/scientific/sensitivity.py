"""Parameter Sensitivity and Robustness Engine for SALTBOR Phase 1.12.

Implements rigorous sensitivity analysis:
- One-At-A-Time (OAT) parameter sweeps.
- Multi-dimensional Factorial grid sweeps.
- Monte Carlo randomized parameter sampling.
- Morris Elementary Effects screening for global sensitivity.
- Classification of parameters and conclusions:
  ROBUST, FRAGILE, NON_LINEAR, INTERACTIVE, UNCERTAIN.
- Detection of threshold inflections, non-linear tipping points, and elasticity.
"""

from __future__ import annotations

import collections
import copy
import logging
import math
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from saltbor.scientific.models import (
    SensitivityClass,
    SensitivitySweepResult,
)

logger = logging.getLogger(__name__)


class ParameterSensitivityEngine:
    """Evaluates the stability and sensitivity of simulation outcomes to parameter perturbations."""

    def __init__(self) -> None:
        self.sweep_archive: dict[str, SensitivitySweepResult] = {}

    def one_at_a_time_sweep(
        self,
        parameter_name: str,
        baseline_value: float,
        perturbation_range: tuple[float, float],
        steps: int,
        evaluation_fn: Callable[[float], dict[str, float]],
        outcome_metrics: list[str],
    ) -> SensitivitySweepResult:
        """Execute a One-At-A-Time (OAT) parameter sweep.

        evaluation_fn: takes parameter value, returns dictionary of outcome metrics.
        """
        low, high = perturbation_range
        tested_values = list(np.linspace(low, high, steps))
        # Ensure baseline value is included in tested sequence
        if baseline_value not in tested_values:
            tested_values.append(baseline_value)
            tested_values.sort()

        responses: dict[str, list[float]] = collections.defaultdict(list)

        for val in tested_values:
            metrics = evaluation_fn(val)
            for m in outcome_metrics:
                responses[m].append(float(metrics.get(m, 0.0)))

        # Compute elasticity: (% Delta Metric) / (% Delta Parameter) around baseline
        elasticities: dict[str, float] = {}
        idx_base = min(range(len(tested_values)), key=lambda i: abs(tested_values[i] - baseline_value))

        for m in outcome_metrics:
            vals = responses[m]
            base_m = vals[idx_base]
            # Max deviation across sweep
            max_dev = max(abs(v - base_m) for v in vals)
            denom_param = abs(high - low) / max(1e-6, abs(baseline_value))
            denom_metric = max_dev / max(1e-6, abs(base_m))
            elasticity = denom_metric / max(1e-6, denom_param)
            elasticities[m] = float(elasticity)

        # Classify behavior: check monotonicity, inflections, fragility
        max_elasticity = max(elasticities.values()) if elasticities else 0.0
        primary_metric = outcome_metrics[0] if outcome_metrics else ""
        p_vals = responses.get(primary_metric, [])

        is_mono = bool(
            all(p_vals[i] <= p_vals[i + 1] for i in range(len(p_vals) - 1))
            or all(p_vals[i] >= p_vals[i + 1] for i in range(len(p_vals) - 1))
        )

        # Detect sharp non-linear inflections (2nd discrete derivative spikes)
        has_inflection = False
        inflection_pt: Optional[float] = None
        if len(p_vals) >= 4:
            second_diffs = [
                abs((p_vals[i + 2] - p_vals[i + 1]) - (p_vals[i + 1] - p_vals[i]))
                for i in range(len(p_vals) - 2)
            ]
            mean_2nd = float(np.mean(second_diffs))
            max_2nd = float(np.max(second_diffs))
            if max_2nd > mean_2nd * 2.8 and max_2nd > 1e-4:
                has_inflection = True
                max_idx = second_diffs.index(max_2nd) + 1
                inflection_pt = float(tested_values[max_idx])

        if has_inflection or not is_mono and max_elasticity > 1.2:
            sens_class = SensitivityClass.NON_LINEAR
        elif max_elasticity > 2.0:
            sens_class = SensitivityClass.FRAGILE
        elif max_elasticity < 0.40:
            sens_class = SensitivityClass.ROBUST
        else:
            sens_class = SensitivityClass.UNCERTAIN

        narrative = (
            f"Parameter '{parameter_name}' exhibits {sens_class.value.upper()} sensitivity "
            f"(max elasticity: {max_elasticity:.2f}). "
        )
        if has_inflection and inflection_pt is not None:
            narrative += f"Non-linear tipping point detected near parameter value {inflection_pt:.2f}."
        elif is_mono:
            narrative += "Response is strictly monotonic across tested spectrum."

        sweep_res = SensitivitySweepResult(
            parameter_name=parameter_name,
            baseline_value=baseline_value,
            tested_values=tested_values,
            outcome_metrics=outcome_metrics,
            responses=dict(responses),
            elasticities=elasticities,
            sensitivity_class=sens_class,
            is_monotonic=is_mono,
            has_threshold_inflection=has_inflection,
            inflection_point=inflection_pt,
            narrative_conclusion=narrative,
        )

        self.sweep_archive[parameter_name] = sweep_res
        return sweep_res

    def morris_elementary_effects(
        self,
        parameters: dict[str, tuple[float, float]],       # param_name -> (min, max)
        evaluation_fn: Callable[[dict[str, float]], float], # returns scalar outcome
        num_trajectories: int = 10,
        grid_levels: int = 4,
        seed: int = 42,
    ) -> dict[str, dict[str, float]]:
        """Morris Method of Elementary Effects for global parameter screening.

        Computes:
        - mu*: Mean absolute elementary effect (measure of overall parameter importance).
        - sigma: Standard deviation of elementary effects (measure of non-linearities/interactions).
        """
        rng = np.random.RandomState(seed)
        param_names = list(parameters.keys())
        k = len(param_names)
        delta = grid_levels / (2 * (grid_levels - 1)) # standard step delta

        elementary_effects: dict[str, list[float]] = collections.defaultdict(list)

        for _ in range(num_trajectories):
            # Sample random base point in normalized [0, 1]^k grid
            base_norm = rng.choice(np.linspace(0.0, 1.0 - delta, grid_levels // 2), size=k)
            # Random permutation of parameter indices
            perm = rng.permutation(k)

            current_pt = copy.copy(base_norm)

            # Function to map normalized [0, 1] to real bounds
            def to_real(norm_vec: np.ndarray) -> dict[str, float]:
                return {
                    name: float(parameters[name][0] + norm_vec[i] * (parameters[name][1] - parameters[name][0]))
                    for i, name in enumerate(param_names)
                }

            y_curr = evaluation_fn(to_real(current_pt))

            # Step through each parameter in permuted sequence
            for p_idx in perm:
                next_pt = copy.copy(current_pt)
                # Perturb parameter p_idx by +delta or -delta
                direction = 1.0 if current_pt[p_idx] + delta <= 1.0 else -1.0
                next_pt[p_idx] += direction * delta
                y_next = evaluation_fn(to_real(next_pt))

                # Elementary effect
                ee = (y_next - y_curr) / (direction * delta)
                elementary_effects[param_names[p_idx]].append(float(ee))

                current_pt = next_pt
                y_curr = y_next

        results: dict[str, dict[str, float]] = {}
        for p_name in param_names:
            ees = np.array(elementary_effects[p_name], dtype=np.float64)
            mu_star = float(np.mean(np.abs(ees)))
            sigma = float(np.std(ees, ddof=1)) if len(ees) > 1 else 0.0
            results[p_name] = {
                "mu_star": mu_star,
                "sigma": sigma,
                "is_interactive": bool(sigma > 0.5 * mu_star and mu_star > 1e-4),
            }

        return results

    def factorial_experiment(
        self,
        factors: dict[str, list[float]],
        evaluation_fn: Callable[[dict[str, float]], dict[str, float]],
        target_metric: str,
    ) -> dict[str, Any]:
        """Full factorial grid experiment across 2 or more factors."""
        factor_names = list(factors.keys())
        import itertools
        grid_combos = list(itertools.product(*[factors[f] for f in factor_names]))

        results_grid: list[dict[str, Any]] = []
        for combo in grid_combos:
            param_dict = {factor_names[i]: combo[i] for i in range(len(factor_names))}
            metrics = evaluation_fn(param_dict)
            results_grid.append({
                "parameters": param_dict,
                "outcome": float(metrics.get(target_metric, 0.0)),
            })

        return {
            "factors": factor_names,
            "combinations_count": len(grid_combos),
            "target_metric": target_metric,
            "grid_results": results_grid,
        }
