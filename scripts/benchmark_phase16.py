"""Sustained performance benchmark for Phase 1.6.

Measures a continuously running simulation (not isolated ticks), the cost of the
perception layer inside it, and the latency of the OSM geographic queries that
the world engine performs against the ingested SQLite database.

Usage:
    python scripts/benchmark_phase16.py [--ticks 120] [--json out.json]
"""

from __future__ import annotations

import argparse
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
from saltbor.datasets.gis.pipeline import DEFAULT_OUTPUT, IngestedGeography  # noqa: E402
from saltbor.simulation.runner import SimulationRunner  # noqa: E402


def _rss_mb() -> float | None:
    try:
        import psutil  # type: ignore

        return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return None


def run_population(size: int, ticks: int, warmup: int = 20) -> dict:
    db = Path(tempfile.mkdtemp()) / f"bench_{size}.db"
    runner = SimulationRunner(
        SimulationConfig(random_seed=42, database_path=db, initial_population_size=size)
    )
    runner.initialize()
    for _ in range(warmup):
        runner.step()

    perception_before = runner.perception.stats.get("ticks_processed", 0)
    timings: list[float] = []
    started = time.perf_counter()
    for _ in range(ticks):
        step_start = time.perf_counter()
        runner.step()
        timings.append((time.perf_counter() - step_start) * 1000.0)
    elapsed = time.perf_counter() - started

    stats = runner.perception.stats
    result = {
        "population": size,
        "ticks": ticks,
        "total_seconds": round(elapsed, 3),
        "ms_per_tick_mean": round(statistics.fmean(timings), 2),
        "ms_per_tick_p50": round(statistics.median(timings), 2),
        "ms_per_tick_p95": round(sorted(timings)[int(len(timings) * 0.95) - 1], 2),
        "ms_per_tick_max": round(max(timings), 2),
        "ticks_per_second": round(ticks / elapsed, 2),
        "ms_per_tick_per_agent": round(statistics.fmean(timings) / size, 4),
        "perception_rounds": stats.get("ticks_processed", 0) - perception_before,
        "perception_stimuli": stats.get("stimuli_considered", 0),
        "perception_detections": stats.get("observations_detected", 0),
        "perception_memories": stats.get("memories_encoded", 0),
        "alive": runner.population.get_alive_count()
        if hasattr(runner.population, "get_alive_count")
        else None,
        "rss_mb": _rss_mb(),
    }
    runner.close()
    return result


def run_geo_queries(samples: int = 500) -> dict:
    if not DEFAULT_OUTPUT.exists():
        return {"available": False}
    geography = IngestedGeography(DEFAULT_OUTPUT)
    bbox = (-89.2020, 13.6930, -89.1860, 13.7040)
    features_started = time.perf_counter()
    features = geography.features_in_bbox(bbox, layer="roads", limit=500)
    features_ms = (time.perf_counter() - features_started) * 1000.0

    road_started = time.perf_counter()
    hits = 0
    for i in range(samples):
        lat = 13.6930 + (i % 100) * 0.0001
        lon = -89.2020 + (i % 97) * 0.0001
        if geography.nearest_road(lat, lon) is not None:
            hits += 1
    road_ms = (time.perf_counter() - road_started) * 1000.0

    result = {
        "available": True,
        "features_bbox_500_ms": round(features_ms, 2),
        "features_returned": len(features),
        "nearest_road_calls": samples,
        "nearest_road_ms_mean": round(road_ms / samples, 3),
        "nearest_road_hits": hits,
        "manifest_layers": len(geography.manifest().get("layers", {})),
    }
    geography.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=120)
    parser.add_argument("--json", type=str, default="")
    parser.add_argument("--populations", type=str, default="50,200")
    args = parser.parse_args()

    populations = [int(p) for p in args.populations.split(",") if p.strip()]
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "ticks_per_run": args.ticks,
        "runs": [],
        "geography": run_geo_queries(),
    }
    for size in populations:
        print(f"[bench] population={size} ticks={args.ticks} ...", flush=True)
        run = run_population(size, args.ticks)
        report["runs"].append(run)
        print(
            f"  {run['ms_per_tick_mean']} ms/tick  p95={run['ms_per_tick_p95']} ms  "
            f"{run['ticks_per_second']} ticks/s  {run['ms_per_tick_per_agent']} ms/agent/tick",
            flush=True,
        )

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    print(payload)
    if args.json:
        Path(args.json).write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
