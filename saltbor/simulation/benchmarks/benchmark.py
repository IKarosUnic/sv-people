"""Scalability and performance benchmarking suite.

Tests populations from 20 to 1,000 individuals across CPU latency, memory footprint,
and tick throughput.
"""

from __future__ import annotations

import gc
import logging
import time
from typing import Any

from saltbor.core.config import SimulationConfig
from saltbor.core.identity import IdentityFactory
from saltbor.population.factory import PopulationFactory
from saltbor.population.registry import PopulationRegistry
from saltbor.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class PopulationBenchmark:
    """Evaluates simulation speed and memory scaling across different population sizes."""

    @staticmethod
    def run_benchmark(sizes: list[int] = [20, 50, 100, 500, 1000], ticks_per_run: int = 10) -> dict[str, Any]:
        """Benchmark discrete simulation performance at varying population scale."""
        results: list[dict[str, Any]] = []

        import tempfile
        import os

        for size in sizes:
            gc.collect()
            bench_db = os.path.join(tempfile.gettempdir(), f"saltbor_bench_{size}_{os.getpid()}_{time.time_ns()}.db")
            cfg = SimulationConfig(initial_population_size=size, random_seed=42, database_path=bench_db)
            runner = SimulationRunner(config=cfg)
            try:
                runner.initialize(load_existing=False)

                # Warmup
                runner.step()

                # Timed ticks
                tick_times = []
                for _ in range(ticks_per_run):
                    t0 = time.perf_counter()
                    runner.step()
                    tick_times.append((time.perf_counter() - t0) * 1000.0)

                import numpy as np
                avg_tick_ms = float(np.mean(tick_times))
                med_tick_ms = float(np.median(tick_times))
                p95_tick_ms = float(np.percentile(tick_times, 95))
                total_time = sum(tick_times) / 1000.0
                ticks_per_sec = ticks_per_run / total_time if total_time > 0 else 0.0
                per_human_ms = avg_tick_ms / size

                summary = runner.metrics.get_summary()
                mem_per_human_kb = summary.get("memory_per_human_kb", 0.0)

                results.append({
                    "population_size": size,
                    "ticks_evaluated": ticks_per_run,
                    "avg_tick_ms": round(avg_tick_ms, 2),
                    "median_tick_ms": round(med_tick_ms, 2),
                    "p95_tick_ms": round(p95_tick_ms, 2),
                    "ticks_per_second": round(ticks_per_sec, 1),
                    "ms_per_human": round(per_human_ms, 4),
                    "memory_per_human_kb": mem_per_human_kb,
                })
            finally:
                runner.close()
                for ext in ("", "-wal", "-shm"):
                    try:
                        p = bench_db + ext
                        if os.path.exists(p):
                            os.remove(p)
                    except Exception:
                        pass

        return {
            "benchmarks": results,
            "hardware_target": "Ryzen 7 8700G (16 vCPUs) / 32 GB RAM",
            "evaluated_sizes": sizes,
        }
