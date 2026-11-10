"""Main entry point and CLI for the Saltbor simulation.

Supports interactive simulation runs, individual diagnostics, world inspection,
and automated behavioral experiment validation.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from saltbor.core.config import SimulationConfig
from saltbor.experiments.experiments import (
    experiment_a_different_personalities,
    experiment_autonomous_goal_generation,
    experiment_b_emotional_influence,
    experiment_behavioral_adaptation,
    experiment_c_memory_influence,
    experiment_d_personality_evolution,
    experiment_differential_reaction,
    experiment_divergent_relationships,
    experiment_e_self_improvement,
    experiment_f_relationship_arc,
    experiment_g_goal_abandonment,
    experiment_h_individual_divergence,
    experiment_selective_forgetting,
    experiment_skill_acquisition,
)
from saltbor.simulation.benchmarks.benchmark import PopulationBenchmark
from saltbor.simulation.laboratory.lab import SimulationLaboratory
from saltbor.simulation.runner import SimulationRunner
from saltbor.visualization.console import ConsoleVisualizer
from saltbor.visualization.inspector import IndividualInspector


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def cmd_run(args: argparse.Namespace) -> int:
    """Run the simulation for a specified number of ticks."""
    cfg = SimulationConfig(
        random_seed=args.seed,
        database_path=Path(args.db),
    )
    runner = SimulationRunner(config=cfg)
    print(f"\n[*] Initializing Saltbor Simulation (DB: {args.db}, Seed: {args.seed})...")
    runner.initialize(load_existing=args.resume)

    print(f"[OK] Population of {runner.population.count} individuals initialized.")
    print(f"[*] Advancing {args.ticks} ticks (1 tick = 15m, 96 ticks = 24h)...")

    interval = max(1, args.report_interval)

    try:
        for t in range(args.ticks):
            runner.step()
            if (t + 1) % interval == 0 or t == args.ticks - 1:
                print(ConsoleVisualizer.render_overview(runner))
                if args.verbose:
                    print(ConsoleVisualizer.render_location_distribution(runner))
                if args.delay > 0:
                    time.sleep(args.delay)

        # Performance summary
        metrics = runner.metrics.get_summary()
        print("\n" + "=" * 80)
        print("  SIMULATION RUN COMPLETED SUCCESSFULLY")
        print(f"  * Total Ticks: {metrics.get('total_ticks_recorded')}")
        print(f"  * Average Latency per Tick: {metrics.get('average_tick_latency_ms')} ms")
        print(f"  * Throughput: {metrics.get('ticks_per_second')} ticks/sec")
        print(f"  * Logical Memory / Human: {metrics.get('memory_per_human_kb')} KB (Target < 1024 KB: {'PASS [OK]' if metrics.get('target_1mb_compliance') else 'FAIL [X]'})")
        print("=" * 80 + "\n")

    finally:
        runner.close()

    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspect the internal psychological, memory, and social state of an individual."""
    cfg = SimulationConfig(database_path=Path(args.db))
    runner = SimulationRunner(config=cfg)
    runner.initialize(load_existing=True)

    try:
        human = runner.population.get_by_serial(args.serial)
        if human is None:
            print(f"[!] Error: Individual with serial #{args.serial} not found (Valid range: 1..{runner.population.count}).")
            return 1

        print(IndividualInspector.inspect(human, runner.social))
    finally:
        runner.close()

    return 0


def cmd_locations(args: argparse.Namespace) -> int:
    """List all registered functional locations in the Saltbor settlement."""
    cfg = SimulationConfig(database_path=Path(args.db))
    runner = SimulationRunner(config=cfg)
    runner.initialize(load_existing=True)

    try:
        print("\n" + "=" * 80)
        print("  SALTBOR SETTLEMENT LOCATIONS MAP (~500m x 500m)")
        print("=" * 80)
        print(f"{'ID':<22} {'Name':<32} {'Type':<14} {'Cap':<4} {'Pos (x,y)'}")
        print("-" * 80)
        for loc in runner.locations.get_all():
            pos_str = f"({loc.position[0]:.0f}, {loc.position[1]:.0f})"
            print(f"{loc.location_id:<22} {loc.name[:31]:<32} {loc.location_type.value:<14} {loc.capacity:<4} {pos_str}")
        print("=" * 80 + "\n")
    finally:
        runner.close()

    return 0


def cmd_experiments(args: argparse.Namespace) -> int:
    """Run and report both Phase 0.1 and Phase 0.2 behavioral validation experiments."""
    print("\n" + "=" * 80)
    print("  RUNNING SALTBOR BEHAVIORAL VALIDATION EXPERIMENTS (PHASES 0.1 & 0.2)")
    print("=" * 80)

    # --- Phase 0.1 Baseline Suite ---
    print("\n--- Phase 0.1 Foundational Experiments ---")
    r1 = experiment_differential_reaction()
    print(f"1. Differential Reaction: {'[PASS]' if r1['differential_demonstrated'] else '[FAIL]'}")
    print(f"   Agent A (Neuroticism {r1['agent_a_neuroticism']}) Anger: {r1['agent_a_anger']} | Agent B (Neuroticism {r1['agent_b_neuroticism']}) Anger: {r1['agent_b_anger']}")

    r2 = experiment_skill_acquisition()
    print(f"2. Skill Acquisition & Diminishing Returns: {'[PASS]' if r2['diminishing_returns_demonstrated'] else '[FAIL]'}")
    print(f"   Incremental XP Gains: {r2['incremental_gains']} | Final Level: {r2['final_level']}")

    r3 = experiment_autonomous_goal_generation()
    print(f"3. Autonomous Goal Formulation: {'[PASS]' if r3['autonomy_demonstrated'] else '[FAIL]'}")
    print(f"   Formulated Goal: '{r3['primary_goal']}' (Priority: {r3['primary_goal_priority']:.2f})")

    r4 = experiment_selective_forgetting()
    print(f"4. Selective Memory Decay & Forgetting: {'[PASS]' if r4['selective_decay_demonstrated'] else '[FAIL]'}")
    print(f"   Forgotten Trivial: {r4['forgotten_count']} | Preserved Significant: {r4['preserved_count']}")

    r5 = experiment_divergent_relationships()
    print(f"5. Divergent Social Relationships: {'[PASS]' if r5['divergent_dynamics_demonstrated'] else '[FAIL]'}")
    print(f"   Person 1 Affinity: {r5['person1_affinity']} ({r5['person1_type']}) vs Person 2 Affinity: {r5['person2_affinity']} ({r5['person2_type']})")

    r6 = experiment_behavioral_adaptation()
    print(f"6. Behavioral Adaptation: {'[PASS]' if r6['adaptation_demonstrated'] else '[FAIL]'}")
    print(f"   Risk Tolerance: {r6['initial_risk_tolerance']} -> {r6['final_risk_tolerance']} | Neuroticism: {r6['initial_neuroticism']} -> {r6['final_neuroticism']}")

    # --- Phase 0.2 Cognitive Suite ---
    print("\n--- Phase 0.2 Advanced Cognitive Experiments (A - H) ---")
    ra = experiment_a_different_personalities()
    print(f"A. Different Personalities in Same Situation: {'[PASS]' if ra['success'] else '[FAIL]'}")
    print(f"   Scholar: {ra['scholar_choice']} ({ra['scholar_reasoning']}) | Socializer: {ra['social_choice']} ({ra['social_reasoning']})")

    rb = experiment_b_emotional_influence()
    print(f"B. Emotional Modulation of Decisions: {'[PASS]' if rb['emotional_modulation_demonstrated'] else '[FAIL]'}")
    print(f"   Lonely -> {rb['lonely_choice']} | Anxious -> {rb['anxious_choice']} | Curious -> {rb['curious_choice']}")

    rc = experiment_c_memory_influence()
    print(f"C. Memory Accessibility vs Dormant Archive & Aversion: {'[PASS]' if rc['success'] else '[FAIL]'}")
    print(f"   Active Forgotten: {rc['forgotten_active_memories']} | Active Preserved: {rc['preserved_active_memories']} | Total History Intact: {rc['total_persisted_in_history']} | Aversion: {rc['location_aversion_recorded']}")

    rd = experiment_d_personality_evolution()
    print(f"D. Longitudinal Personality Evolution & Audit Log: {'[PASS]' if rd['success'] else '[FAIL]'}")
    print(f"   Initial: {rd['initial_traits']} -> Final: {rd['final_traits']} (Audit events: {rd['evolution_events_recorded']})")

    re = experiment_e_self_improvement()
    print(f"E. Autonomous Self-Improvement & Practice: {'[PASS]' if re['success'] else '[FAIL]'}")
    print(f"   Goal: '{re['formulated_goal']}' | Level: {re['initial_skill_level']} -> {re['final_skill_level']} ({re['level_progression']})")

    rf = experiment_f_relationship_arc()
    print(f"F. Social Arc (Coop, Conflict, Asymmetry, Reconciliation): {'[PASS]' if rf['success'] else '[FAIL]'}")
    print(f"   Stage 1 Trust: {rf['stage_1_trust']} -> Conflict Trust: {rf['stage_2_trust']} -> P1->P2 ({rf['p1_to_p2_trust']}) vs P2->P1 ({rf['p2_to_p1_trust']}) -> Reconciled: {rf['stage_4_trust']}")

    rg = experiment_g_goal_abandonment()
    print(f"G. Goal Procrastination, Modification & Abandonment: {'[PASS]' if rg['success'] else '[FAIL]'}")
    print(f"   Initial: {rg['initial_status']} -> Failures: {rg['consecutive_failures']} -> Final: {rg['final_status']} (Reason: {rg['abandonment_reason']})")

    rh = experiment_h_individual_divergence()
    print(f"H. Individual Divergence from Shared Initial Conditions: {'[PASS]' if rh['success'] else '[FAIL]'}")
    print(f"   Twin A (Fortunate): Mood {rh['twin_a_mood']:+.2f} | Neuro: {rh['twin_a_neuroticism']} | Risk: {rh['twin_a_risk_tolerance']} | Goal: '{rh['twin_a_primary_goal']}'")
    print(f"   Twin B (Adverse):   Mood {rh['twin_b_mood']:+.2f} | Neuro: {rh['twin_b_neuroticism']} | Risk: {rh['twin_b_risk_tolerance']} | Goal: '{rh['twin_b_primary_goal']}'")

    all_passed = (
        r1["differential_demonstrated"]
        and r2["diminishing_returns_demonstrated"]
        and r3["autonomy_demonstrated"]
        and r4["selective_decay_demonstrated"]
        and r5["divergent_dynamics_demonstrated"]
        and r6["adaptation_demonstrated"]
        and ra["success"]
        and rb["emotional_modulation_demonstrated"]
        and rc["success"]
        and rd["success"]
        and re["success"]
        and rf["success"]
        and rg["success"]
        and rh["success"]
    )

    print("=" * 80)
    print(f"  OVERALL RESULT: {'ALL 14 EXPERIMENTS PASSED [OK]' if all_passed else 'SOME EXPERIMENTS FAILED [FAIL]'}")
    print("=" * 80 + "\n")
    return 0 if all_passed else 1


def cmd_lab(args: argparse.Namespace) -> int:
    """Execute Phase 0.3 Laboratory operations: experiments, observability traces, population analytics, benchmarks."""
    lab = SimulationLaboratory()
    action = args.lab_action

    if action == "experiments":
        print("\n" + "=" * 80)
        print("  SALTBOR PHASE 0.3 — BEHAVIORAL EXPERIMENTS LABORATORY SUITE (A - H)")
        print("=" * 80 + "\n")
        results = lab.run_all_experiments()
        out_dir = Path(args.export_dir)
        for key, res in results.items():
            status_str = "[PASS]" if res.success else "[FAIL]"
            print(f"{res.experiment_id}: {res.name} ... {status_str} ({res.duration_seconds:.2f}s)")
            print(f"   Summary: {res.summary}")
            if args.export:
                saved = lab.export_experiment_report(res, out_dir / key.lower())
                print(f"   Report exported -> {saved}")
        print("\n" + "=" * 80)
        all_passed = all(r.success for r in results.values())
        print(f"  LABORATORY OUTCOME: {'ALL 8 EXPERIMENTS VALIDATED [OK]' if all_passed else 'FAILURES DETECTED [FAIL]'}")
        print("=" * 80 + "\n")
        return 0 if all_passed else 1

    elif action == "trace":
        print(f"\n[*] Initializing simulation and stepping {args.ticks} ticks...")
        lab.start_simulation(seed=args.seed)
        lab.advance_ticks(args.ticks)
        trace_str = lab.explain_last_decision(args.serial)
        print("\n" + "=" * 80)
        print("  INDIVIDUAL DECISION EXPLANATION TRACE")
        print("=" * 80)
        print(trace_str)
        print("=" * 80 + "\n")
        return 0

    elif action == "population":
        print(f"\n[*] Simulating {args.ticks} ticks for population behavioral analysis...")
        lab.start_simulation(seed=args.seed)
        lab.advance_ticks(args.ticks)
        analysis = lab.analyze_population()
        print("\n" + "=" * 80)
        print("  POPULATION BEHAVIORAL & ANTI-ARTIFICIAL AUDIT")
        print("=" * 80)
        print(f"Population Size: {analysis['population_size']}")
        print(f"Personality Diversity (std): {analysis['personality_diversity']['composite_personality_diversity']}")
        print(f"Autonomy Participation: {analysis['autonomy_and_goals']['autonomy_participation_rate']}%")
        print(f"Social Relationships: {analysis['social_connectivity']['total_relationships']} (Density: {analysis['social_connectivity']['network_density']})")
        print(f"Anti-Artificial Clean: {analysis['anti_artificial_audit']['is_clean']}")
        if analysis['anti_artificial_audit']['warnings']:
            for w in analysis['anti_artificial_audit']['warnings']:
                print(f"  [WARNING] {w}")
        else:
            print("  [OK] No repetitive lock-in, false adaptation, or homogeneity failure detected.")
        print("=" * 80 + "\n")
        return 0

    elif action == "benchmark":
        print("\n" + "=" * 80)
        print("  SALTBOR HARDWARE SCALABILITY BENCHMARK (20 to 1000 Agents)")
        print("=" * 80 + "\n")
        bench = PopulationBenchmark.run_benchmark(sizes=[20, 50, 100, 500, 1000], ticks_per_run=10)
        for b in bench["benchmarks"]:
            pop = b["population_size"]
            ms = b["avg_tick_ms"]
            tps = b["ticks_per_second"]
            per_h = b["ms_per_human"]
            mem = b["memory_per_human_kb"]
            print(f"  * Pop {pop:4d}: Tick {ms:6.2f} ms | Throughput {tps:6.1f} tps | Latency/agent {per_h:6.4f} ms | Memory/agent {mem:5.2f} KB")
        print("\n" + "=" * 80 + "\n")
        return 0

    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Execute Section 1.1 Performance, Scaling, and Architectural Audit."""
    print("\n" + "=" * 80)
    print("  SALTBOR PHASE 0.5 — COMPREHENSIVE PERFORMANCE & ARCHITECTURAL AUDIT")
    print("=" * 80 + "\n")
    from saltbor.simulation.benchmarks.performance_audit import ComprehensivePerformanceAuditor

    print("[*] 1. Sustained Population Throughput & Latency Benchmarks (20 to 1,000 agents)...")
    pop_results = ComprehensivePerformanceAuditor.run_population_benchmarks(sizes=[20, 50, 100, 500, 1000], ticks_per_size=15)
    for r in pop_results:
        print(f"  Pop {r.population_size:4d}: Avg={r.avg_tick_ms:6.2f}ms, Med={r.median_tick_ms:6.2f}ms, P95={r.p95_tick_ms:6.2f}ms, TPS={r.sustained_ticks_per_second:5.1f}, Heap={r.total_process_memory_mb:5.2f}MB, PerAgent={r.memory_per_human_kb:5.2f}KB (Active={r.active_state_memory_kb:.1f}KB, Hist={r.historical_records_memory_kb:.1f}KB)")

    print("\n[*] 2. Spatial Query Performance Under Population Densities (100 to 10,000 agents)...")
    density_results = ComprehensivePerformanceAuditor.benchmark_spatial_densities(densities=[100, 500, 1000, 5000, 10000], queries_count=1000)
    for dr in density_results:
        print(f"  Agents {dr.agent_count:5d}: {dr.avg_query_microseconds:6.3f} us/query | Avg Occupants: {dr.avg_occupants_per_query:4.1f} | {dr.query_complexity_characterization}")

    print("\n[*] 3. Active vs Dormant Agent Computation Cost Reduction...")
    act_dorm = ComprehensivePerformanceAuditor.benchmark_active_vs_dormant_cost(500)
    print(f"  Active 500 Tick: {act_dorm.active_tick_ms:.2f}ms vs Active 100 + Dormant 400 Tick: {act_dorm.dormant_tick_ms:.2f}ms -> Speedup: {act_dorm.cost_reduction_ratio:.1f}x")

    print("\n[*] 4. SQLite Persistence & Serialization Overhead...")
    persist_records = ComprehensivePerformanceAuditor.benchmark_persistence_overhead([20, 100, 500])
    for pr in persist_records:
        print(f"  Pop {pr['population_size']:3d}: Save All = {pr['save_all_ms']:6.2f}ms ({pr['ms_per_agent_saved']:.3f} ms/agent) | Load All = {pr['load_all_ms']:6.2f}ms")

    print("\n" + "=" * 80)
    print("  PERFORMANCE AUDIT COMPLETED SUCCESSFULLY [PASS]")
    print("=" * 80 + "\n")
    return 0


def main() -> int:
    """CLI argument routing."""
    parser = argparse.ArgumentParser(
        prog="saltbor",
        description="Saltbor — Synthetic Human and Society Simulation (Phase 0.1)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Simulation command to execute")

    # audit command
    subparsers.add_parser("audit", help="Run Phase 0.5 Performance and Scaling Audit")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the simulation loop")
    run_parser.add_argument("--ticks", type=int, default=96, help="Number of ticks to simulate (default: 96 = 24h)")
    run_parser.add_argument("--seed", type=int, default=42, help="Master random seed for reproducibility")
    run_parser.add_argument("--db", type=str, default="saltbor.db", help="Path to SQLite persistence database")
    run_parser.add_argument("--report-interval", type=int, default=24, help="Ticks between terminal reports (default: 24 = 6h)")
    run_parser.add_argument("--delay", type=float, default=0.0, help="Delay in seconds between reports for live viewing")
    run_parser.add_argument("--resume", action="store_true", help="Resume from existing database state")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed location occupancies")

    # inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect individual internal state")
    inspect_parser.add_argument("--serial", type=int, default=1, help="Serial number of human to inspect (1..20)")
    inspect_parser.add_argument("--db", type=str, default="saltbor.db", help="Path to SQLite database")

    # locations command
    loc_parser = subparsers.add_parser("locations", help="List all settlement locations")
    loc_parser.add_argument("--db", type=str, default="saltbor.db", help="Path to SQLite database")

    # experiments command
    subparsers.add_parser("experiments", help="Run behavioral validation experiments")

    # lab command (Phase 0.3)
    lab_parser = subparsers.add_parser("lab", help="Phase 0.3 Autonomous Simulation Laboratory")
    lab_parser.add_argument("lab_action", choices=["experiments", "trace", "population", "benchmark"], help="Laboratory action")
    lab_parser.add_argument("--serial", type=int, default=1, help="Serial number of individual for trace")
    lab_parser.add_argument("--ticks", type=int, default=96, help="Ticks to advance before analyzing (default: 96)")
    lab_parser.add_argument("--seed", type=int, default=42, help="Random seed for laboratory reproducibility")
    lab_parser.add_argument("--export", action="store_true", help="Export markdown and json reports")
    lab_parser.add_argument("--export-dir", type=str, default="experiments/results", help="Destination folder for exported reports")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        if args.command is None:
            # Default to running 96 ticks
            args = parser.parse_args(["run", "--ticks", "96", "--report-interval", "24"])
        return cmd_run(args)
    elif args.command == "audit":
        return cmd_audit(args)
    elif args.command == "inspect":
        return cmd_inspect(args)
    elif args.command == "locations":
        return cmd_locations(args)
    elif args.command == "experiments":
        return cmd_experiments(args)
    elif args.command == "lab":
        return cmd_lab(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
