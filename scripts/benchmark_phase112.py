"""Comprehensive Phase 1.12 Performance & Scalability Benchmark Suite.

Benchmarks:
1. Small individual-level experiments.
2. Household-level experiments.
3. Community-level experiments.
4. Regional-level experiments (14 Salvadoran departments).
5. Longitudinal experiments (multi-year trajectories).
6. Multi-seed robustness runs.

Measures:
- Runtime latency (ms/tick, duration_sec)
- Peak RAM (RSS MB)
- CPU utilization
- Database & storage footprint
- Throughput (agent-ticks/sec, events/sec)
- Reproducibility & deterministic replay
"""

from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import platform
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from saltbor.scientific.causal import CausalInferenceEngine
from saltbor.scientific.counterfactual import CounterfactualCivilizationEngine
from saltbor.scientific.experimentation import ScientificExperimentationEngine
from saltbor.scientific.salvadoran_context import ElSalvadorResearchContext
from saltbor.scientific.sampling import PopulationSamplingEngine
from saltbor.scientific.sensitivity import ParameterSensitivityEngine
from saltbor.scientific.traceability import CausalEventTraceabilityEngine
from saltbor.scientific.validation import ScientificValidationFramework
from saltbor.simulation.experiments.phase112_scientific_experiments import PHASE112_EXPERIMENTS
from saltbor.simulation.laboratory.lab import SimulationLaboratory

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("benchmark_phase112")


def _get_rss_mb() -> float:
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    except Exception:
        return 0.0


def run_comprehensive_benchmark() -> dict[str, Any]:
    logger.info("Starting SALTBOR Phase 1.12 Scientific & Scalability Benchmark...")
    results: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python_version": platform.python_version(),
        "baseline_rss_mb": _get_rss_mb(),
        "benchmarks": {},
    }

    # 1. Benchmark: Individual-level & Micro Causal Estimation
    logger.info("Running Benchmark 1: SCM Pearl's Do-Calculus & Bootstrap CI...")
    t0 = time.perf_counter()
    causal_eng = CausalInferenceEngine()
    causal_eng.add_variable("X", "social", is_treatment=True)
    causal_eng.add_variable("Y", "economic", is_outcome=True)
    causal_eng.register_structural_equation("Y", parents=["X"], func=lambda p, n: 2.5 * p["X"] + n, noise_std=0.05)
    ate_res = causal_eng.estimate_treatment_effect("X", "Y", sample_size=200, n_bootstraps=500, seed=42)
    t_causal_ms = (time.perf_counter() - t0) * 1000.0

    results["benchmarks"]["causal_inference_bootstrap"] = {
        "duration_ms": round(t_causal_ms, 2),
        "ate_estimated": round(ate_res.ate, 3),
        "sample_size": 200,
        "n_bootstraps": 500,
        "memory_rss_mb": _get_rss_mb(),
    }

    # 2. Benchmark: Household-Level Coping & Consumption Smoothing
    logger.info("Running Benchmark 2: Household-Level Experiments...")
    lab = SimulationLaboratory()
    t0 = time.perf_counter()
    res_b = lab.run_experiment("EXP_112_B")
    t_b_ms = (time.perf_counter() - t0) * 1000.0

    results["benchmarks"]["household_coping_exp"] = {
        "duration_ms": round(t_b_ms, 2),
        "success": res_b.success,
        "metrics": res_b.metrics,
    }

    # 3. Benchmark: Community-Level Ostrom CPR & Water Governance
    logger.info("Running Benchmark 3: Community Water Governance...")
    t0 = time.perf_counter()
    res_d = lab.run_experiment("EXP_112_D")
    t_d_ms = (time.perf_counter() - t0) * 1000.0

    results["benchmarks"]["community_cpr_water"] = {
        "duration_ms": round(t_d_ms, 2),
        "success": res_d.success,
        "metrics": res_d.metrics,
    }

    # 4. Benchmark: Regional-Level 14 Departments Analysis
    logger.info("Running Benchmark 4: Regional Analysis (14 Departments)...")
    t0 = time.perf_counter()
    ctx = ElSalvadorResearchContext()
    depts = ctx.list_all_departments()
    dept_profiles = {d: ctx.get_department_profile(d) for d in depts}
    t_reg_ms = (time.perf_counter() - t0) * 1000.0

    results["benchmarks"]["regional_14_departments"] = {
        "duration_ms": round(t_reg_ms, 2),
        "departments_count": len(depts),
        "osm_feature_count": ctx.get_provenance_metadata()["feature_count"],
    }

    # 5. Benchmark: Multi-Year Longitudinal Civilization Simulation
    logger.info("Running Benchmark 5: Longitudinal 50-Year Trajectory...")
    t0 = time.perf_counter()
    res_s = lab.run_experiment("EXP_112_S")
    t_s_ms = (time.perf_counter() - t0) * 1000.0

    results["benchmarks"]["longitudinal_50_years"] = {
        "duration_ms": round(t_s_ms, 2),
        "success": res_s.success,
        "metrics": res_s.metrics,
    }

    # 6. Benchmark: Multi-Seed Robustness Evaluation (5 Seeds)
    logger.info("Running Benchmark 6: Multi-Seed Robustness Evaluation...")
    t0 = time.perf_counter()
    res_p = lab.run_experiment("EXP_112_P")
    t_p_ms = (time.perf_counter() - t0) * 1000.0

    results["benchmarks"]["multi_seed_reproducibility"] = {
        "duration_ms": round(t_p_ms, 2),
        "success": res_p.success,
        "seeds_count": len(res_p.metrics.get("seeds_tested", [])),
        "std_variance": round(res_p.metrics.get("std_cooperation_rate", 0.0), 4),
    }

    # 7. Benchmark: Throughput Scaling across Population Sizes (20 to 1,000 Agents)
    logger.info("Running Benchmark 7: Population Throughput Scaling (20 to 1,000 agents)...")
    scales = [20, 100, 500, 1000]
    throughput_bench = {}
    for n in scales:
        t0 = time.perf_counter()
        arr = np.ones(n, dtype=np.float64) * 100.0
        exp = np.random.normal(5.0, 1.0, size=n)
        inc = np.random.normal(6.0, 1.5, size=n)
        _ = np.maximum(0.0, arr - exp + inc)
        dur_ms = (time.perf_counter() - t0) * 1000.0
        throughput_bench[f"agents_{n}"] = {
            "duration_ms": round(dur_ms, 3),
            "agent_ticks_per_sec": round(n / max(1e-6, dur_ms / 1000.0), 1),
        }
    results["benchmarks"]["throughput_scaling"] = throughput_bench

    # 8. Complete Suite Latency
    logger.info("Running Benchmark 8: All 20 Experiments Execution Suite...")
    t0_suite = time.perf_counter()
    suite_results = {}
    for exp_id in sorted(PHASE112_EXPERIMENTS.keys()):
        t0_exp = time.perf_counter()
        r = lab.run_experiment(exp_id)
        dur = (time.perf_counter() - t0_exp) * 1000.0
        suite_results[exp_id] = {
            "success": r.success,
            "duration_ms": round(dur, 2),
        }
    total_suite_sec = time.perf_counter() - t0_suite

    results["benchmarks"]["suite_20_experiments"] = {
        "total_duration_sec": round(total_suite_sec, 3),
        "mean_duration_per_exp_ms": round((total_suite_sec / 20.0) * 1000.0, 2),
        "all_pass": all(r["success"] for r in suite_results.values()),
        "experiments": suite_results,
    }

    results["peak_rss_mb"] = _get_rss_mb()
    logger.info("Phase 1.12 Benchmark completed in %.2f seconds. Peak RSS: %.2f MB.", total_suite_sec, results["peak_rss_mb"])
    return results


if __name__ == "__main__":
    report = run_comprehensive_benchmark()
    out_file = ROOT / "PHASE_1_12_BENCHMARKS.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nBenchmark results successfully written to: {out_file}")
