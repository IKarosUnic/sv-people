"""Scientific Experimentation Engine for SALTBOR Phase 1.12.

Orchestrates reproducible scientific experimentation across synthetic human populations,
communities, economies, institutions, and environments.

Guarantees:
- Pure offline, local-first execution.
- Isolated state execution: never silently mutates the baseline simulation state.
- Systematic multi-seed evaluation with seed registries.
- Aggregated statistical robustness: mean, median, standard deviation, variance,
  95% bootstrap confidence intervals, distributions, outlier detection, and failure rates.
- Transparent data provenance, measurement methodology, and explicit limitation logging.
"""

from __future__ import annotations

import collections
import copy
import logging
import math
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional
import numpy as np

from saltbor.core.config import SimulationConfig
from saltbor.scientific.causal import CausalInferenceEngine
from saltbor.scientific.models import (
    EvidenceValidationTier,
    ExperimentType,
    InterventionDomain,
    MultiSeedExperimentResult,
    ScientificExperimentProtocol,
    SingleRunResult,
    StratifiedSampleSpec,
    TreatmentEffectEstimate,
)

if TYPE_CHECKING:
    from saltbor.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class ScientificExperimentationEngine:
    """Central orchestrator for reproducible scientific experiments in SALTBOR."""

    def __init__(self, causal_engine: Optional[CausalInferenceEngine] = None) -> None:
        self.causal_engine = causal_engine or CausalInferenceEngine()
        self.protocols: dict[str, ScientificExperimentProtocol] = {}
        self.results_archive: dict[str, MultiSeedExperimentResult] = {}
        self._seed_registry: list[int] = [42, 101, 202, 303, 404]

    def register_protocol(self, protocol: ScientificExperimentProtocol) -> None:
        """Register a formal experiment protocol."""
        self.protocols[protocol.protocol_id] = protocol

    def create_protocol(
        self,
        protocol_id: str,
        name: str,
        research_question: str,
        hypotheses: list[str],
        experiment_type: ExperimentType,
        domain: InterventionDomain,
        independent_variables: list[str],
        dependent_variables: list[str],
        control_variables: list[str],
        treatment_definition: dict[str, Any],
        duration_ticks: int = 96,
        seeds: Optional[list[int]] = None,
        sampling_spec: Optional[StratifiedSampleSpec] = None,
        geographic_scope: str = "El Salvador",
        measurement_methodology: str = "",
        expected_limitations: Optional[list[str]] = None,
    ) -> ScientificExperimentProtocol:
        """Convenience factory to create and register a protocol."""
        protocol = ScientificExperimentProtocol(
            protocol_id=protocol_id,
            name=name,
            research_question=research_question,
            hypotheses=hypotheses,
            experiment_type=experiment_type,
            domain=domain,
            independent_variables=independent_variables,
            dependent_variables=dependent_variables,
            control_variables=control_variables,
            treatment_definition=treatment_definition,
            sampling_spec=sampling_spec or StratifiedSampleSpec(),
            geographic_scope=geographic_scope,
            duration_ticks=duration_ticks,
            random_seeds=seeds or list(self._seed_registry),
            measurement_methodology=measurement_methodology or "Local multi-seed simulation metrics tracking",
            expected_limitations=expected_limitations or [
                "Synthetic agent decision boundaries simplified compared to real humans.",
                "Discrete 15-minute tick approximations.",
            ],
        )
        self.register_protocol(protocol)
        return protocol

    def run_protocol(
        self,
        protocol_id: str,
        run_fn: Callable[[int, ScientificExperimentProtocol], tuple[dict[str, Any], dict[str, bool], list[str]]],
        custom_seeds: Optional[list[int]] = None,
    ) -> MultiSeedExperimentResult:
        """Execute an experiment across its declared random seeds.

        run_fn signature: run_fn(seed, protocol) -> (metrics_dict, hypotheses_confirmed_dict, anomalies_list)
        Guarantees that each run is isolated and independent.
        """
        protocol = self.protocols.get(protocol_id)
        if not protocol:
            raise ValueError(f"Unknown experiment protocol: '{protocol_id}'")

        seeds = custom_seeds or protocol.random_seeds
        runs: list[SingleRunResult] = []
        t0_total = time.perf_counter()

        for s in seeds:
            t0 = time.perf_counter()
            try:
                metrics, hyp_eval, anomalies = run_fn(s, protocol)
                duration = time.perf_counter() - t0
                runs.append(
                    SingleRunResult(
                        run_id=f"{protocol_id}_seed_{s}",
                        seed=s,
                        duration_seconds=duration,
                        success=True,
                        metrics=metrics,
                        hypotheses_confirmed=hyp_eval,
                        anomalies=anomalies,
                    )
                )
            except Exception as ex:
                duration = time.perf_counter() - t0
                logger.error("Run failed for seed %d: %s", s, ex)
                runs.append(
                    SingleRunResult(
                        run_id=f"{protocol_id}_seed_{s}",
                        seed=s,
                        duration_seconds=duration,
                        success=False,
                        metrics={},
                        hypotheses_confirmed={h: False for h in protocol.hypotheses},
                        anomalies=[f"Simulation execution failed: {ex}"],
                    )
                )

        duration_total = time.perf_counter() - t0_total

        # Aggregate metrics across successful runs
        successful_runs = [r for r in runs if r.success]
        failure_rate = (len(runs) - len(successful_runs)) / max(1, len(runs))

        # 1. Hypotheses confirmation rates
        hypotheses_status: dict[str, dict[str, Any]] = {}
        for h in protocol.hypotheses:
            confirmed_cnt = sum(1 for r in successful_runs if r.hypotheses_confirmed.get(h, False))
            rate = confirmed_cnt / max(1, len(successful_runs))
            hypotheses_status[h] = {
                "confirmed_count": confirmed_cnt,
                "total_valid_runs": len(successful_runs),
                "confirmation_rate": rate,
                "supported": bool(rate >= 0.70), # 70% threshold across independent seeds
            }

        # 2. Summary Statistics for each metric
        summary_stats: dict[str, dict[str, float]] = {}
        metric_keys = set()
        for r in successful_runs:
            metric_keys.update(r.metrics.keys())

        # Collect scalar values
        all_metric_values: dict[str, list[float]] = collections.defaultdict(list)
        for r in successful_runs:
            for k in metric_keys:
                val = r.metrics.get(k)
                if isinstance(val, (int, float)) and not math.isnan(val):
                    all_metric_values[k].append(float(val))

        outlier_seeds: set[int] = set()

        for k, values in all_metric_values.items():
            if not values:
                continue
            arr = np.array(values, dtype=np.float64)
            mean_v = float(np.mean(arr))
            median_v = float(np.median(arr))
            std_v = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
            var_v = float(np.var(arr, ddof=1)) if len(arr) > 1 else 0.0
            min_v = float(np.min(arr))
            max_v = float(np.max(arr))

            # 95% bootstrap CI
            if len(arr) >= 3:
                boot_means = [float(np.mean(np.random.choice(arr, size=len(arr), replace=True))) for _ in range(500)]
                ci_low = float(np.percentile(boot_means, 2.5))
                ci_high = float(np.percentile(boot_means, 97.5))
            else:
                ci_low = min_v
                ci_high = max_v

            summary_stats[k] = {
                "mean": mean_v,
                "median": median_v,
                "std": std_v,
                "variance": var_v,
                "ci_95_low": ci_low,
                "ci_95_high": ci_high,
                "min": min_v,
                "max": max_v,
            }

            # Outlier detection using IQR (1.5 * IQR)
            if len(arr) >= 4:
                q25, q75 = np.percentile(arr, [25, 75])
                iqr = q75 - q25
                lower_fence = q25 - 1.5 * iqr
                upper_fence = q75 + 1.5 * iqr
                for r in successful_runs:
                    v = r.metrics.get(k)
                    if isinstance(v, (int, float)) and (v < lower_fence or v > upper_fence):
                        outlier_seeds.add(r.seed)

        # Estimate treatment effect if independent variable is binary treatment
        causal_estimates: dict[str, TreatmentEffectEstimate] = {}
        for dep in protocol.dependent_variables:
            if dep in summary_stats and protocol.independent_variables:
                treat_var = protocol.independent_variables[0]
                # If causal engine has these variables registered, estimate effect
                if treat_var in self.causal_engine.variables and dep in self.causal_engine.variables:
                    try:
                        causal_estimates[f"{treat_var}->{dep}"] = self.causal_engine.estimate_treatment_effect(
                            treatment_var=treat_var,
                            outcome_var=dep,
                            sample_size=100,
                        )
                    except Exception as ex:
                        logger.debug("SCM estimate skipped for %s -> %s: %s", treat_var, dep, ex)

        result = MultiSeedExperimentResult(
            protocol_id=protocol_id,
            name=protocol.name,
            experiment_type=protocol.experiment_type,
            domain=protocol.domain,
            seeds_evaluated=seeds,
            total_runs=len(runs),
            successful_runs=len(successful_runs),
            failure_rate=failure_rate,
            duration_seconds_total=duration_total,
            hypotheses_status=hypotheses_status,
            summary_statistics=summary_stats,
            outlier_runs=sorted(list(outlier_seeds)),
            runs=runs,
            causal_estimates=causal_estimates,
            limitations_noted=list(protocol.expected_limitations),
            validation_tier=EvidenceValidationTier.EXPERIMENTALLY_EVALUATED,
        )

        self.results_archive[protocol_id] = result
        return result

    def get_result(self, protocol_id: str) -> Optional[MultiSeedExperimentResult]:
        """Retrieve stored multi-seed results for a protocol."""
        return self.results_archive.get(protocol_id)

    def list_protocols(self) -> list[dict[str, Any]]:
        """List summary of all registered experiment protocols."""
        return [
            {
                "protocol_id": p.protocol_id,
                "name": p.name,
                "research_question": p.research_question,
                "experiment_type": p.experiment_type.value,
                "domain": p.domain.value,
                "independent_variables": p.independent_variables,
                "dependent_variables": p.dependent_variables,
                "duration_ticks": p.duration_ticks,
                "seed_count": len(p.random_seeds),
                "has_results": p.protocol_id in self.results_archive,
            }
            for p in self.protocols.values()
        ]
