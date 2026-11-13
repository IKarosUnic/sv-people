"""Standalone execution runner and benchmark for Phase 1.5 Extension experiments.

Runs all 16 experiments (EXP_15_EXT_01 through EXP_15_EXT_16), validates hypotheses,
measures runtime, and writes structured JSON outputs to experiments/results/phase15/.
"""

import json
from pathlib import Path
import sys
import time

# Allow direct execution from a source checkout without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from saltbor.simulation.experiments.phase15_extension_experiments import (
    PHASE15_EXTENSION_EXPERIMENTS,
)


def main() -> None:
    results_dir = Path("experiments/results/phase15")
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "phase15_extension_results.json"

    print("================================================================================")
    total_experiments = len(PHASE15_EXTENSION_EXPERIMENTS)
    print(f"SALTBOR PHASE 1.5 EXTENSION — {total_experiments} REPRODUCIBLE INTEGRATION EXPERIMENTS")
    print("================================================================================")

    all_results = []
    total_start = time.perf_counter()
    passed_count = 0

    for idx, exp_cls in enumerate(PHASE15_EXTENSION_EXPERIMENTS, 1):
        exp = exp_cls()
        t0 = time.perf_counter()
        try:
            res = exp.run()
            dur = time.perf_counter() - t0
            passed = res.success
            status_str = "PASS" if passed else "FAIL"
            if passed:
                passed_count += 1
            print(f"[{idx:02d}/{total_experiments}] {exp.config.experiment_id}: {exp.config.name} ... {status_str} ({dur:.3f}s)")
            all_results.append({
                "experiment_id": exp.config.experiment_id,
                "name": exp.config.name,
                "description": exp.config.description,
                "success": passed,
                "summary": res.summary,
                "hypotheses": res.hypotheses,
                "duration_sec": dur,
                "metrics": res.metrics,
                "raw_data": res.raw_data,
            })
        except Exception as ex:
            dur = time.perf_counter() - t0
            print(f"[{idx:02d}/{total_experiments}] {exp.config.experiment_id}: ERROR ({ex}) ({dur:.3f}s)")
            all_results.append({
                "experiment_id": exp.config.experiment_id,
                "name": exp.config.name,
                "success": False,
                "error": str(ex),
                "duration_sec": dur,
            })

    total_time = time.perf_counter() - total_start
    summary = {
        "timestamp": time.time(),
        "total_experiments": len(PHASE15_EXTENSION_EXPERIMENTS),
        "passed": passed_count,
        "failed": len(PHASE15_EXTENSION_EXPERIMENTS) - passed_count,
        "total_runtime_seconds": total_time,
        "experiments": all_results,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("--------------------------------------------------------------------------------")
    print(f"SUMMARY: {passed_count}/{len(PHASE15_EXTENSION_EXPERIMENTS)} PASSED in {total_time:.3f}s")
    print(f"Results written to: {out_file}")
    print("================================================================================")


if __name__ == "__main__":
    main()
