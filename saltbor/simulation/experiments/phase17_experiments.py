"""Phase 1.7 experiment suite: EXP_17_A … EXP_17_T.

Run the whole suite with::

    python -m saltbor.simulation.experiments.phase17_experiments

or import :func:`run_all_phase17_experiments`.  Each result includes its
hypotheses with status, effect metrics, confidence intervals and a Markdown
report.  A supported hypothesis is evidence *under the recorded conditions*,
not proof of consciousness or human psychological equivalence.
"""

from __future__ import annotations

import json
import traceback
from typing import Callable, Optional

from saltbor.simulation.experiments.base import ExperimentResult
from saltbor.simulation.experiments.phase17_experiments_a_j import (
    Experiment17_A_StressAccumulation,
    Experiment17_B_IndividualResponseDiversity,
    Experiment17_C_PsychologicalBreakdown,
    Experiment17_D_AdaptiveCoping,
    Experiment17_E_CopingTradeOffs,
    Experiment17_F_EmotionalAppraisal,
    Experiment17_G_MemoryRetrieval,
    Experiment17_H_MemoryDistortion,
    Experiment17_I_GriefTrajectories,
    Experiment17_J_PhysicalPsychological,
)
from saltbor.simulation.experiments.phase17_experiments_k_t import (
    Experiment17_K_SocialSupport,
    Experiment17_L_RelationshipCrisis,
    Experiment17_M_LongitudinalDevelopment,
    Experiment17_N_BehavioralDiversity,
    Experiment17_O_AdversarialConditions,
    Experiment17_P_RecoveryRelapse,
    Experiment17_Q_CausalAblation,
    Experiment17_R_DeterministicReproducibility,
    Experiment17_S_PopulationBenchmark,
    Experiment17_T_IntegratedSimulation,
)

PHASE17_EXPERIMENTS = [
    Experiment17_A_StressAccumulation,
    Experiment17_B_IndividualResponseDiversity,
    Experiment17_C_PsychologicalBreakdown,
    Experiment17_D_AdaptiveCoping,
    Experiment17_E_CopingTradeOffs,
    Experiment17_F_EmotionalAppraisal,
    Experiment17_G_MemoryRetrieval,
    Experiment17_H_MemoryDistortion,
    Experiment17_I_GriefTrajectories,
    Experiment17_J_PhysicalPsychological,
    Experiment17_K_SocialSupport,
    Experiment17_L_RelationshipCrisis,
    Experiment17_M_LongitudinalDevelopment,
    Experiment17_N_BehavioralDiversity,
    Experiment17_O_AdversarialConditions,
    Experiment17_P_RecoveryRelapse,
    Experiment17_Q_CausalAblation,
    Experiment17_R_DeterministicReproducibility,
    Experiment17_S_PopulationBenchmark,
    Experiment17_T_IntegratedSimulation,
]

PHASE17_EXPERIMENT_IDS = [cls().config.experiment_id for cls in PHASE17_EXPERIMENTS]


def run_all_phase17_experiments(
    only: Optional[list[str]] = None,
    on_result: Optional[Callable[[ExperimentResult], None]] = None,
) -> dict[str, ExperimentResult]:
    """Execute the Phase 1.7 suite and return results keyed by experiment id."""
    results: dict[str, ExperimentResult] = {}
    for experiment_class in PHASE17_EXPERIMENTS:
        experiment = experiment_class()
        exp_id = experiment.config.experiment_id
        if only and exp_id not in only:
            continue
        try:
            result = experiment.run()
        except Exception as exc:  # surfaced as a failed experiment, never hidden
            result = ExperimentResult(
                experiment_id=exp_id,
                name=experiment.config.name,
                success=False,
                summary=f"EXPERIMENT_ERROR: {exc}",
                hypotheses=[{"id": "ERROR", "status": "EXPERIMENT_ERROR", "detail": str(exc)}],
                metrics={"traceback": traceback.format_exc()},
            )
        results[exp_id] = result
        if on_result is not None:
            on_result(result)
    return results


def results_to_json(results: dict[str, ExperimentResult]) -> str:
    payload = {}
    for exp_id, result in results.items():
        payload[exp_id] = {
            "name": result.name,
            "success": result.success,
            "summary": result.summary,
            "hypotheses": result.hypotheses,
            "metrics": result.metrics,
            "anomalies": result.observed_anomalies,
            "duration_seconds": result.duration_seconds,
        }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    print("Running Phase 1.7 experiments (EXP_17_A … EXP_17_T)\n")
    all_results = run_all_phase17_experiments(
        on_result=lambda r: print(f"{r.experiment_id:<10} {'OK ' if r.success else 'ERR'} {r.summary[:90]}")
    )
    with open("docs/reports/phase17_experiments.json", "w", encoding="utf-8") as handle:
        handle.write(results_to_json(all_results))
    print(f"\n{len(all_results)} experiments written to docs/reports/phase17_experiments.json")
