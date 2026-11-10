"""Benchmark and Scalability Test for Phase 1.0 Civilization Engine.

Evaluates performance across multi-year and multi-generational horizons:
- Horizons: 1 year, 5 years, 10 years, 25 years, 50 years, 100 years.
- Metrics: population count, active settlements, historical events recorded, memory usage, execution speed.
"""

import time
import pytest
from saltbor.civilization.engine import CivilizationEvolutionEngine, CivilizationPhase
from saltbor.civilization.settlement import SettlementType


def test_civilization_evolution_benchmarks():
    civ_engine = CivilizationEvolutionEngine()
    civ = civ_engine.found_civilization("Civilización Salvadoreña Histórica", initial_year=2026.0)

    # Initial settlements
    s1_id = civ.settlement_ids[0]
    s2 = civ_engine.settlements.found_settlement("Santa Ana Satélite", SettlementType.CIUDAD, "Santa Ana Centro", "Santa Ana", (13.99, -89.55))
    civ.settlement_ids.append(s2.settlement_id)

    # Add 150 inhabitants
    for i in range(100):
        civ_engine.settlements.add_inhabitant(s1_id, f"p_s1_{i}")
    for i in range(50):
        civ_engine.settlements.add_inhabitant(s2.settlement_id, f"p_s2_{i}")

    # Benchmark horizons
    horizons = [1, 5, 10, 25, 50, 100]
    benchmark_results = {}

    for years in horizons:
        t0 = time.perf_counter()
        # Advance simulation in accelerated macro-steps
        for step in range(years):
            civ_engine.evolve_step(civ.civilization_id, delta_years=1.0, current_tick=step)
        t_elapsed = time.perf_counter() - t0

        events_count = len(civ_engine.history.ground_truth)
        benchmark_results[f"{years}_years"] = {
            "elapsed_seconds": round(t_elapsed, 4),
            "simulated_year": civ.current_year,
            "population": civ.population_count,
            "events_logged": events_count,
            "seconds_per_virtual_year": round(t_elapsed / years, 6),
        }

    # Verify high throughput (< 0.05 seconds per simulated year)
    for res in benchmark_results.values():
        assert res["seconds_per_virtual_year"] < 0.05
    assert civ.current_year >= 2026.0 + sum(horizons)
