"""Sustained Phase 1.7 benchmark: psychological layer and full simulation.

Two separate measurements are reported because they answer different questions:

1. ``population_runs`` exercises the psychological engine itself at 20, 100,
   500, 1000 and 10 000 individuals.  This isolates the cost of the new layer.
2. ``full_simulation_runs`` runs the complete ``SimulationRunner`` at 20 and
   100 individuals, including decisions, SQLite/WAL, events and UI snapshots.

The 10 000-individual full simulation is not attempted: it would conflate the
psychological layer with the entire existing agent architecture.  That limit is
reported explicitly rather than hidden.

Usage:
    python scripts/benchmark_phase17.py [--populations 20,100,500,1000,10000]
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from saltbor.core.config import SimulationConfig  # noqa: E402
from saltbor.population.human import SyntheticHuman  # noqa: E402
from saltbor.population.registry import PopulationRegistry  # noqa: E402
from saltbor.psychology.engine import PsychologicalEngine  # noqa: E402
from saltbor.simulation.runner import SimulationRunner  # noqa: E402


def _rss_mb() -> float | None:
    try:
        import psutil  # type: ignore

        return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return None


def _make_agents(size: int) -> list[SyntheticHuman]:
    agents = []
    for i in range(size):
        agents.append(
            SyntheticHuman.create(
                name=f"Bench {i}",
                age=30.0,
                money=80.0,
                seed=i + 1,
                serial=i + 1,
            )
        )
    return agents


def run_psychology_population(size: int, ticks: int, warmup: int = 2) -> dict:
    gc.collect()
    rss_before = _rss_mb()
    started_create = time.perf_counter()
    agents = _make_agents(size)
    create_seconds = time.perf_counter() - started_create
    pop = PopulationRegistry()
    for agent in agents:
        pop.register(agent)
    engine = PsychologicalEngine(seed=42)
    for agent in agents:
        engine.ensure(agent)
    for tick in range(warmup):
        engine.step_population(pop, tick, tick_minutes=15, force_all=True)

    timings: list[float] = []
    cpu_times: list[float] = []
    for tick in range(warmup, warmup + max(3, ticks)):
        wall0 = time.perf_counter()
        cpu0 = time.process_time()
        engine.step_population(pop, tick, tick_minutes=15)
        timings.append((time.perf_counter() - wall0) * 1000.0)
        cpu_times.append(time.process_time() - cpu0)
    payload_chars = len(str(engine.to_dict()))
    mean_ms = statistics.fmean(timings)
    result = {
        "population": size,
        "ticks_measured": len(timings),
        "create_seconds": round(create_seconds, 3),
        "ms_per_tick_mean": round(mean_ms, 3),
        "ms_per_tick_p95": round(sorted(timings)[max(0, int(len(timings) * 0.95) - 1)], 3),
        "ms_per_tick_max": round(max(timings), 3),
        "ms_per_agent_tick": round(mean_ms / size, 5),
        "cpu_ms_per_tick": round(statistics.fmean(cpu_times) * 1000.0, 3),
        "rss_before_mb": rss_before,
        "rss_after_mb": _rss_mb(),
        "checkpoint_chars": payload_chars,
        "active_crises": sum(1 for s in engine.states.values() if s.in_crisis()),
        "appraisals": engine.stats.get("appraisals", 0),
        "timeline_entries": engine.stats.get("timeline_entries", 0),
    }
    del agents, pop, engine
    gc.collect()
    return result


def run_full_simulation(size: int, ticks: int, warmup: int = 12) -> dict:
    db_path = Path(tempfile.mkdtemp()) / f"phase17_bench_{size}.db"
    cfg = SimulationConfig(
        random_seed=42,
        initial_population_size=size,
        checkpoint_interval_ticks=max(8, ticks),
        database_path=str(db_path),
    )
    runner = SimulationRunner(cfg)
    runner.initialize()
    for _ in range(warmup):
        runner.step()

    timings: list[float] = []
    started = time.perf_counter()
    for _ in range(ticks):
        t0 = time.perf_counter()
        runner.step()
        timings.append((time.perf_counter() - t0) * 1000.0)
    elapsed = time.perf_counter() - started

    sample_humans = runner.population.get_all()[:10]
    overview_latencies = []
    snapshot_latencies = []
    for _ in range(30):
        t0 = time.perf_counter()
        runner.psychology.overview()
        overview_latencies.append((time.perf_counter() - t0) * 1000.0)
    for human in sample_humans:
        t0 = time.perf_counter()
        runner.psychology.snapshot(human)
        snapshot_latencies.append((time.perf_counter() - t0) * 1000.0)

    timeline_rows = runner.db.execute("SELECT COUNT(*) c FROM psychology_timeline").fetchone()["c"]
    db_size = db_path.stat().st_size if db_path.exists() else 0
    wal_path = Path(str(db_path) + "-wal")
    wal_size = wal_path.stat().st_size if wal_path.exists() else 0
    result = {
        "population": size,
        "ticks": ticks,
        "total_seconds": round(elapsed, 3),
        "ms_per_tick_mean": round(statistics.fmean(timings), 2),
        "ms_per_tick_p95": round(sorted(timings)[int(len(timings) * 0.95) - 1], 2),
        "ms_per_agent_tick": round(statistics.fmean(timings) / size, 4),
        "ticks_per_second": round(ticks / elapsed, 2),
        "rss_mb": _rss_mb(),
        "sqlite_bytes": db_size,
        "wal_bytes": wal_size,
        "timeline_rows": timeline_rows,
        "psychology_overview_ms_median": round(statistics.median(overview_latencies), 3),
        "psychology_snapshot_ms_median": round(statistics.median(snapshot_latencies), 3)
        if snapshot_latencies
        else None,
        "psychology_stats": runner.psychology.overview()["stats"],
    }
    runner.db.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--populations", type=str, default="20,100,500,1000,10000")
    parser.add_argument("--ticks", type=int, default=5)
    parser.add_argument("--json", type=str, default="docs/reports/phase17_benchmark.json")
    args = parser.parse_args()
    populations = [int(p) for p in args.populations.split(",") if p.strip()]

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "hardware_reference": "Ryzen 7 8700G / Radeon 780M / 32 GB DDR5 / Windows 11",
        "population_runs": [],
        "full_simulation_runs": [],
        "limitations": [
            "Population runs isolate the psychological engine; they do not include decisions or SQLite writes.",
            "Full-simulation runs cover 20 and 100 individuals only; 10 000 full agents is outside the scope of this benchmark.",
        ],
    }
    for size in populations:
        print(f"[psych] population={size} ...", flush=True)
        try:
            row = run_psychology_population(size, args.ticks)
            report["population_runs"].append(row)
            print(
                f"  {row['ms_per_tick_mean']} ms/tick  {row['ms_per_agent_tick']} ms/agent  "
                f"RSS={row['rss_after_mb']} MB",
                flush=True,
            )
        except MemoryError as exc:
            report["population_runs"].append({"population": size, "error": f"MemoryError: {exc}"})
            print(f"  MemoryError: {exc}", flush=True)

    for size in (20, 100):
        print(f"[full] population={size} ...", flush=True)
        row = run_full_simulation(size, ticks=96 if size == 20 else 48)
        report["full_simulation_runs"].append(row)
        print(
            f"  {row['ms_per_tick_mean']} ms/tick  p95={row['ms_per_tick_p95']} ms  "
            f"SQLite={row['sqlite_bytes']} B  WAL={row['wal_bytes']} B",
            flush=True,
        )

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    print(payload)
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
