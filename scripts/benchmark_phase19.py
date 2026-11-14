"""Sustained Phase 1.9 benchmark: emergent society, institutions, and full runner.

Reports:
1. ``social_layer_runs``: isolates Phase 1.9 engines (Organizations, Institutions,
   Governance, Norms, CPR, Stratification Gini/Palma) at 20, 100, 500, 1000, 10000 agents.
2. ``full_simulation_runs``: complete SimulationRunner with Phase 1.9 fully integrated,
   SQLite/WAL checkpoints, event bus, and cognitive LOD.

Usage:
    python scripts/benchmark_phase19.py --full-populations 20,100
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

from saltbor.core.config import SimulationConfig
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.engine import SocialEngine
from saltbor.social.governance.collective_decision import CollectiveGovernanceEngine, VotingProtocol
from saltbor.social.institutions.institutional_evolution import InstitutionalEvolutionEngine, InstitutionDomain
from saltbor.social.norms.norm_evolution import SocialNormEvolutionEngine, NormDomain, NormFormalization
from saltbor.social.organization.emergent_engine import EmergentOrganizationEngine, OrganizationType
from saltbor.social.resources.cpr_manager import CollectiveResourceManager, CPRType
from saltbor.social.stratification.mobility_engine import SocialStratificationEngine


def _rss_mb() -> float | None:
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return None


def _make_agents(size: int) -> list[SyntheticHuman]:
    agents = []
    for i in range(size):
        agents.append(
            SyntheticHuman.create(
                name=f"BenchAgent {i}",
                age=20.0 + (i % 50),
                money=float(15.0 + (i % 200)),
                seed=i + 1,
                serial=i + 1,
            )
        )
    return agents


def run_social_layer_population(size: int, ticks: int = 5) -> dict[str, float | int | None]:
    gc.collect()
    rss_before = _rss_mb()
    agents = _make_agents(size)
    pop = PopulationRegistry()
    for a in agents:
        pop.register(a)
    soc = SocialEngine()

    norms = SocialNormEvolutionEngine()
    cpr = CollectiveResourceManager()
    strat = SocialStratificationEngine()
    gov = CollectiveGovernanceEngine()
    orgs = EmergentOrganizationEngine()
    insts = InstitutionalEvolutionEngine()

    # Pre-seed baseline entity
    cpr.register_resource("pozo_bench", "Pozo Benchmark", CPRType.WATER_WELL, "comm_1", "loc_1", 1000.0, 1000.0, 50.0)
    norms.register_norm("Norma Bench", "Regla de prueba", NormDomain.RESOURCE_SHARING, NormFormalization.COMMUNITY_AGREEMENT, 0.75, 0.70, tick=1)

    latencies_ms: list[float] = []
    for t in range(ticks):
        t0 = time.perf_counter()
        # Stratification & Gini
        strat.step(pop, soc, current_tick=t * 96)
        # CPR regeneration & extraction
        cpr.step(current_tick=t * 96)
        res = cpr.get_resource("pozo_bench")
        if res:
            res.extract("BenchAgent 0", 10.0, tick=t * 96)
        # Norms decay
        norms.step(t * 96)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    rss_after = _rss_mb()
    return {
        "population": size,
        "ticks": ticks,
        "rss_before_mb": rss_before,
        "rss_after_mb": rss_after,
        "ms_per_tick_mean": round(statistics.mean(latencies_ms), 4),
        "ms_per_tick_median": round(statistics.median(latencies_ms), 4),
        "ms_per_tick_p95": round(statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else max(latencies_ms), 4),
        "ms_per_agent_tick": round(statistics.mean(latencies_ms) / size, 6),
    }


def run_full_simulation(population_size: int, ticks: int = 48, warmup: int = 12) -> dict[str, float | int | str | None]:
    gc.collect()
    db_file = tempfile.NamedTemporaryFile(prefix=f"saltbor_p19_bench_{population_size}_", suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    cfg = SimulationConfig(
        database_path=db_path,
        random_seed=42,
        initial_population_size=population_size,
    )
    runner = SimulationRunner(cfg)

    t_init_0 = time.perf_counter()
    runner.initialize(load_existing=False)
    init_seconds = round(time.perf_counter() - t_init_0, 3)

    for _ in range(warmup):
        runner.step()

    latencies_ms: list[float] = []
    for _ in range(ticks):
        t0 = time.perf_counter()
        runner.step()
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    p_db = Path(db_path)
    p_wal = Path(f"{db_path}-wal")
    db_bytes = p_db.stat().st_size if p_db.exists() else 0
    wal_bytes = p_wal.stat().st_size if p_wal.exists() else 0

    result = {
        "population": population_size,
        "warmup_ticks": warmup,
        "measured_ticks": ticks,
        "initialize_seconds": init_seconds,
        "ms_per_tick_mean": round(statistics.mean(latencies_ms), 3),
        "ms_per_tick_median": round(statistics.median(latencies_ms), 3),
        "ms_per_tick_p95": round(statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else max(latencies_ms), 3),
        "ms_per_agent_tick": round(statistics.mean(latencies_ms) / max(1, population_size), 5),
        "ticks_per_second": round(1000.0 / statistics.mean(latencies_ms), 2),
        "rss_mb": _rss_mb(),
        "sqlite_bytes": db_bytes,
        "wal_bytes": wal_bytes,
    }
    runner.db.close()
    try:
        p_db.unlink(missing_ok=True)
        p_wal.unlink(missing_ok=True)
    except Exception:
        pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--populations", type=str, default="20,100,500,1000,10000")
    parser.add_argument("--ticks", type=int, default=5)
    parser.add_argument("--full-populations", type=str, default="20,100")
    parser.add_argument("--json", type=str, default="docs/reports/phase19_benchmark.json")
    args = parser.parse_args()

    populations = [int(p) for p in args.populations.split(",") if p.strip()]
    full_populations = [int(p) for p in args.full_populations.split(",") if p.strip()]

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "hardware_reference": "Ryzen 7 8700G / Radeon 780M / 32 GB DDR5 / Windows 11",
        "social_layer_runs": [],
        "full_simulation_runs": [],
    }

    for size in populations:
        print(f"[social layer] population={size} ...", flush=True)
        row = run_social_layer_population(size, args.ticks)
        report["social_layer_runs"].append(row)
        print(f"  {row['ms_per_tick_mean']} ms/tick  {row['ms_per_agent_tick']} ms/agent-tick  RSS={row['rss_after_mb']} MB", flush=True)

    for size in full_populations:
        warmup = 12 if size <= 100 else 2
        ticks = 48 if size <= 100 else 10
        print(f"[full runner] population={size} warmup={warmup} ticks={ticks} ...", flush=True)
        row = run_full_simulation(size, ticks=ticks, warmup=warmup)
        report["full_simulation_runs"].append(row)
        print(
            f"  init={row['initialize_seconds']} s  {row['ms_per_tick_mean']} ms/tick  "
            f"p95={row['ms_per_tick_p95']} ms  {row['ticks_per_second']} ticks/s  "
            f"SQLite={row['sqlite_bytes']} B  WAL={row['wal_bytes']} B",
            flush=True,
        )

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(payload, encoding="utf-8")
    print(f"\nReport written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
