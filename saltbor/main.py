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
    experiment_behavioral_adaptation,
    experiment_differential_reaction,
    experiment_divergent_relationships,
    experiment_selective_forgetting,
    experiment_skill_acquisition,
    experiment_autonomous_goal_generation,
)
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
    """Run and report the 6 required behavioral validation experiments."""
    print("\n" + "=" * 80)
    print("  RUNNING SALTBOR BEHAVIORAL VALIDATION EXPERIMENTS")
    print("=" * 80)

    # 1. Differential reaction
    r1 = experiment_differential_reaction()
    print(f"1. Differential Reaction: {'[PASS]' if r1['differential_demonstrated'] else '[FAIL]'}")
    print(f"   Agent A (Neuroticism {r1['agent_a_neuroticism']}) Anger: {r1['agent_a_anger']} | Agent B (Neuroticism {r1['agent_b_neuroticism']}) Anger: {r1['agent_b_anger']}")

    # 2. Skill acquisition
    r2 = experiment_skill_acquisition()
    print(f"2. Skill Acquisition & Diminishing Returns: {'[PASS]' if r2['diminishing_returns_demonstrated'] else '[FAIL]'}")
    print(f"   Incremental XP Gains: {r2['incremental_gains']} | Final Level: {r2['final_level']}")

    # 3. Autonomous goal formulation
    r3 = experiment_autonomous_goal_generation()
    print(f"3. Autonomous Goal Formulation: {'[PASS]' if r3['autonomy_demonstrated'] else '[FAIL]'}")
    print(f"   Formulated Goal: '{r3['primary_goal']}' (Priority: {r3['primary_goal_priority']:.2f})")

    # 4. Selective memory and forgetting
    r4 = experiment_selective_forgetting()
    print(f"4. Selective Memory Decay & Forgetting: {'[PASS]' if r4['selective_decay_demonstrated'] else '[FAIL]'}")
    print(f"   Forgotten Trivial: {r4['forgotten_count']} | Preserved Significant: {r4['preserved_count']}")

    # 5. Divergent relationships
    r5 = experiment_divergent_relationships()
    print(f"5. Divergent Social Relationships: {'[PASS]' if r5['divergent_dynamics_demonstrated'] else '[FAIL]'}")
    print(f"   Person 1 Affinity: {r5['person1_affinity']} ({r5['person1_type']}) vs Person 2 Affinity: {r5['person2_affinity']} ({r5['person2_type']})")

    # 6. Behavioral adaptation
    r6 = experiment_behavioral_adaptation()
    print(f"6. Behavioral Adaptation (Personality Evolution): {'[PASS]' if r6['adaptation_demonstrated'] else '[FAIL]'}")
    print(f"   Risk Tolerance: {r6['initial_risk_tolerance']} -> {r6['final_risk_tolerance']} | Neuroticism: {r6['initial_neuroticism']} -> {r6['final_neuroticism']}")

    all_passed = all([
        r1["differential_demonstrated"],
        r2["diminishing_returns_demonstrated"],
        r3["autonomy_demonstrated"],
        r4["selective_decay_demonstrated"],
        r5["divergent_dynamics_demonstrated"],
        r6["adaptation_demonstrated"],
    ])

    print("=" * 80)
    print(f"  OVERALL RESULT: {'ALL 6 EXPERIMENTS PASSED [OK]' if all_passed else 'SOME EXPERIMENTS FAILED [FAIL]'}")
    print("=" * 80 + "\n")
    return 0 if all_passed else 1
    r5 = experiment_divergent_relationships()
    print(f"5. Divergent Social Relationships: {'PASS ✅' if r5['divergent_dynamics_demonstrated'] else 'FAIL ❌'}")
    print(f"   Person 1 Affinity: {r5['person1_affinity']} ({r5['person1_type']}) vs Person 2 Affinity: {r5['person2_affinity']} ({r5['person2_type']})")

    # 6. Behavioral adaptation
    r6 = experiment_behavioral_adaptation()
    print(f"6. Behavioral Adaptation (Personality Evolution): {'PASS ✅' if r6['adaptation_demonstrated'] else 'FAIL ❌'}")
    print(f"   Risk Tolerance: {r6['initial_risk_tolerance']} → {r6['final_risk_tolerance']} | Neuroticism: {r6['initial_neuroticism']} → {r6['final_neuroticism']}")

    all_passed = all([
        r1["differential_demonstrated"],
        r2["diminishing_returns_demonstrated"],
        r3["autonomy_demonstrated"],
        r4["selective_decay_demonstrated"],
        r5["divergent_dynamics_demonstrated"],
        r6["adaptation_demonstrated"],
    ])

    print("=" * 80)
    print(f"  OVERALL RESULT: {'ALL 6 EXPERIMENTS PASSED ✅' if all_passed else 'SOME EXPERIMENTS FAILED ❌'}")
    print("=" * 80 + "\n")
    return 0 if all_passed else 1


def main() -> int:
    """CLI argument routing."""
    parser = argparse.ArgumentParser(
        prog="saltbor",
        description="Saltbor — Synthetic Human and Society Simulation (Phase 0.1)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Simulation command to execute")

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

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        if args.command is None:
            # Default to running 96 ticks
            args = parser.parse_args(["run", "--ticks", "96", "--report-interval", "24"])
        return cmd_run(args)
    elif args.command == "inspect":
        return cmd_inspect(args)
    elif args.command == "locations":
        return cmd_locations(args)
    elif args.command == "experiments":
        return cmd_experiments(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
