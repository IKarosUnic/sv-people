"""Orchestrator to execute and record all 15 Phase 1.5 experiments to JSON."""

import json
from pathlib import Path
import time
from saltbor.simulation.experiments.phase15_experiments import PHASE15_EXPERIMENTS

def main() -> None:
    output_dir = Path("experiments/results/phase15")
    output_dir.mkdir(parents=True, exist_ok=True)
    results_dict = {}

    print(f"Starting Phase 1.5 Experiments ({len(PHASE15_EXPERIMENTS)} total)...")
    t_start = time.perf_counter()

    for exp_cls in PHASE15_EXPERIMENTS:
        exp = exp_cls()
        t0 = time.perf_counter()
        res = exp.run()
        elapsed = time.perf_counter() - t0

        print(f"  [{res.experiment_id}] {res.name}: {'SUCCESS' if res.success else 'FAIL'} in {elapsed:.4f}s")
        results_dict[res.experiment_id] = {
            "name": res.name,
            "success": res.success,
            "summary": res.summary,
            "metrics": res.metrics,
            "duration_seconds": round(elapsed, 5),
            "hypotheses": res.hypotheses,
        }

    total_time = time.perf_counter() - t_start
    print(f"All 15 Phase 1.5 experiments completed in {total_time:.3f}s")

    json_path = output_dir / "phase15_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {json_path}")

if __name__ == "__main__":
    main()
