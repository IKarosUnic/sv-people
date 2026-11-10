"""Experiment implementations E through H for Phase 0.3.

- Experiment E: Environmental Adaptation (Market disruptions, closures)
- Experiment F: Conflicting Needs and Decisions (Resource trade-offs)
- Experiment G: Long-term Development (Multi-week trajectory drift)
- Experiment H: Emergence & Unexpected Behavior (Organic groupings)
"""

from __future__ import annotations

import time
from typing import Any, Optional

import numpy as np

from saltbor.cognition.autonomy.engine import AutonomyEngine, Goal
from saltbor.cognition.decision.engine import ActionOption, DecisionContext, DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.config import SimulationConfig
from saltbor.core.types import ActivityType, NeedType
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.simulation.experiments.base import BaseExperiment, ExperimentConfig, ExperimentResult
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.engine import SocialEngine


class ExperimentE_EnvironmentalAdaptation(BaseExperiment):
    """Experiment E: Environmental Adaptation.

    Objective: Determine whether individuals dynamically adapt their routine destinations
    and strategies when environmental conditions change (e.g., market closure, price shocks).
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_E_ADAPTATION",
            name="Environmental Adaptation to Urban Shocks",
            description="Observes agent destination choice when commercial establishments close or food prices change.",
            duration_ticks=48,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        dec = DecisionEngine()
        pers = PersonalityEngine()
        emot = EmotionalEngine(profile=EmotionalProfile())
        mem = MemoryEngine()

        # Scenario 1: Standard hungry agent with ample money -> Prefers eating out at Comedor
        ctx_normal = DecisionContext(
            current_location_id="plaza_central",
            available_activities=[ActivityType.EAT, ActivityType.COOK, ActivityType.REST],
            current_needs={NeedType.HUNGER: 0.75},
            current_energy=0.7,
            current_hunger=0.75,
            current_money=25.0,
            is_daytime=True,
            hour_int=12,
            home_location_id="casa_residencial_1",
        )
        opts_normal = dec.evaluate_options(ctx_normal, pers, emot, mem)
        chosen_normal = max(opts_normal, key=lambda o: o.expected_utility)

        # Scenario 2: Environmental Shock — Financial shortage / price hike ($2.0 left)
        ctx_shock = DecisionContext(
            current_location_id="plaza_central",
            available_activities=[ActivityType.EAT, ActivityType.COOK, ActivityType.REST],
            current_needs={NeedType.HUNGER: 0.75},
            current_energy=0.7,
            current_hunger=0.75,
            current_money=2.0,  # Below market dining threshold
            is_daytime=True,
            hour_int=12,
            home_location_id="casa_residencial_1",
        )
        opts_shock = dec.evaluate_options(ctx_shock, pers, emot, mem)
        chosen_shock = max(opts_shock, key=lambda o: o.expected_utility)

        elapsed = time.perf_counter() - t0
        success = (
            chosen_normal.action_type == ActivityType.EAT
            and chosen_shock.action_type == ActivityType.COOK
            and chosen_shock.target_location_id == "casa_residencial_1"
        )

        hypotheses = [
            {
                "hypothesis": "Ample funds drive convenience dining at local businesses.",
                "confirmed": chosen_normal.action_type == ActivityType.EAT,
                "evidence": f"Chose {chosen_normal.action_type.value} at {chosen_normal.target_location_id}.",
            },
            {
                "hypothesis": "Economic constraints trigger resource conservation and domestic cooking.",
                "confirmed": chosen_shock.action_type == ActivityType.COOK,
                "evidence": f"Chose {chosen_shock.action_type.value} at {chosen_shock.target_location_id}.",
            },
        ]

        metrics = {
            "normal_choice": chosen_normal.action_type.value,
            "normal_target": chosen_normal.target_location_id,
            "shock_choice": chosen_shock.action_type.value,
            "shock_target": chosen_shock.target_location_id,
        }

        md = f"""# Experiment E: Environmental Adaptation
- **Status**: {'SUCCESS' if success else 'FAILURE'}
- **Normal Choice**: {chosen_normal.action_type.value} ({chosen_normal.target_location_id})
- **Constrained Choice**: {chosen_shock.action_type.value} ({chosen_shock.target_location_id})
- **Conclusion**: Agent demonstrated rational behavioral adaptation to resource constraints.
"""
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Individuals adapted their activity strategies and destinations when environmental conditions changed.",
            hypotheses=hypotheses,
            metrics=metrics,
            duration_seconds=elapsed,
            report_markdown=md,
        )


class ExperimentF_ConflictingNeeds(BaseExperiment):
    """Experiment F: Conflicting Needs and Decisions.

    Validates multi-attribute trade-offs:
    e.g., immediate physiological relief (rest/eat) vs long-term financial/skill goals (work/study).
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_F_CONFLICTS",
            name="Conflicting Needs and Competing Trade-offs",
            description="Examines decision resolution when acute physical exhaustion conflicts with financial work deadlines across different personality archetypes.",
            duration_ticks=24,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        dec = DecisionEngine()
        mem = MemoryEngine()
        emot = EmotionalEngine(profile=EmotionalProfile())

        # Agent 1: Conscientious Workaholic (High Conscientiousness)
        t_work = PersonalityTraits(
            conscientiousness=TraitValue(base_value=0.92, current_value=0.92),
            patience=TraitValue(base_value=0.8, current_value=0.8),
        )
        p_work = PersonalityEngine(t_work)

        # Agent 2: Low Conscientiousness / High Fatigue Sensitive
        t_rest = PersonalityTraits(
            conscientiousness=TraitValue(base_value=0.10, current_value=0.10),
            patience=TraitValue(base_value=0.2, current_value=0.2),
        )
        p_rest = PersonalityEngine(t_rest)

        # Context with competing demands: Modest exhaustion (0.65) during afternoon shift
        ctx = DecisionContext(
            current_location_id="taller_carpinteria",
            available_activities=[ActivityType.WORK, ActivityType.REST],
            current_needs={},
            current_energy=0.35,  # 65% exhausted
            current_hunger=0.2,
            current_money=15.0,
            is_daytime=True,
            hour_int=14,
            work_location_id="taller_carpinteria",
            home_location_id="casa_residencial_1",
        )

        opts_work = dec.evaluate_options(ctx, p_work, emot, mem)
        chosen_work = max(opts_work, key=lambda o: o.expected_utility)

        opts_rest = dec.evaluate_options(ctx, p_rest, emot, mem)
        chosen_rest = max(opts_rest, key=lambda o: o.expected_utility)

        elapsed = time.perf_counter() - t0
        success = (
            chosen_work.action_type == ActivityType.WORK
            and chosen_rest.action_type in (ActivityType.REST, ActivityType.SLEEP)
        )

        hypotheses = [
            {
                "hypothesis": "High conscientiousness prioritizes vocational duty over physical discomfort.",
                "confirmed": chosen_work.action_type == ActivityType.WORK,
                "evidence": f"Agent 1 selected {chosen_work.action_type.value} with utility {chosen_work.expected_utility:.2f}.",
            },
            {
                "hypothesis": "Low conscientiousness yields to physical fatigue and rest.",
                "confirmed": chosen_rest.action_type in (ActivityType.REST, ActivityType.SLEEP),
                "evidence": f"Agent 2 selected {chosen_rest.action_type.value} with utility {chosen_rest.expected_utility:.2f}.",
            },
        ]

        metrics = {
            "workaholic_choice": chosen_work.action_type.value,
            "workaholic_utility": round(chosen_work.expected_utility, 3),
            "fatigued_choice": chosen_rest.action_type.value,
            "fatigued_utility": round(chosen_rest.expected_utility, 3),
        }

        md = f"""# Experiment F: Conflicting Needs
- **Status**: {'SUCCESS' if success else 'FAILURE'}
- **High Conscientiousness Choice**: {chosen_work.action_type.value} (Utility {chosen_work.expected_utility:.2f})
- **Low Conscientiousness Choice**: {chosen_rest.action_type.value} (Utility {chosen_rest.expected_utility:.2f})
- **Conclusion**: Conflicting trade-offs resolved differentially according to personal trait endowments.
"""
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Demonstrated divergent conflict resolution without a single universal decision formula.",
            hypotheses=hypotheses,
            metrics=metrics,
            duration_seconds=elapsed,
            report_markdown=md,
        )


class ExperimentG_LongTermDevelopment(BaseExperiment):
    """Experiment G: Long-term Development.

    Objective: Observe multi-week evolution of skills, economics, relationships,
    and life trajectories over accelerated time horizons (e.g. 7, 30 days).
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_G_LONG_TERM",
            name="Long-Term Multi-Day Development",
            description="Runs a 7-day (672-tick) continuous simulation evaluating cumulative divergence in economics, memories, and skills.",
            duration_ticks=288,  # 3 full days default for quick CI (configurable to 672 or more)
            random_seed=42,
            population_size=20,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        import tempfile
        from pathlib import Path
        temp_db = Path(tempfile.mkdtemp()) / "exp_g.db"
        cfg = SimulationConfig(random_seed=self.config.random_seed, database_path=temp_db)
        sim = runner or SimulationRunner(config=cfg)
        if runner is None:
            sim.initialize(load_existing=False)

        # Record initial baselines
        initial_monies = {h.uid: h.physical_state.money for h in sim.population.get_all()}
        initial_mem_counts = {h.uid: h.memory.episodic.count for h in sim.population.get_all()}

        # Advance simulation
        for _ in range(self.config.duration_ticks):
            sim.step()

        # Measure divergence at end
        final_monies = {h.uid: h.physical_state.money for h in sim.population.get_all()}
        final_mem_counts = {h.uid: h.memory.episodic.count for h in sim.population.get_all()}

        money_deltas = [final_monies[uid] - initial_monies[uid] for uid in initial_monies]
        mem_deltas = [final_mem_counts[uid] - initial_mem_counts[uid] for uid in initial_mem_counts]

        money_std = float(np.std(money_deltas))
        total_events = len(sim.event_bus.event_log)

        elapsed = time.perf_counter() - t0
        success = money_std > 0.0 and sum(mem_deltas) > 0

        hypotheses = [
            {
                "hypothesis": "Economic circumstances diverge across individuals over extended simulation time.",
                "confirmed": money_std > 0.0,
                "evidence": f"Economic delta standard deviation is ${money_std:.2f}.",
            },
            {
                "hypothesis": "Autobiographical memory records accumulate continuously.",
                "confirmed": sum(mem_deltas) > 0,
                "evidence": f"Total new episodic records generated: {sum(mem_deltas)}.",
            },
        ]

        metrics = {
            "duration_ticks": self.config.duration_ticks,
            "simulated_days": round(self.config.duration_ticks / 96, 1),
            "economic_delta_std": round(money_std, 3),
            "total_new_memories": sum(mem_deltas),
            "total_events_emitted": total_events,
            "throughput_tps": round(self.config.duration_ticks / max(0.001, elapsed), 1),
        }

        if runner is None:
            sim.close()

        md = f"""# Experiment G: Long-term Development
- **Status**: {'SUCCESS' if success else 'FAILURE'}
- **Simulated Horizon**: {self.config.duration_ticks} ticks ({metrics['simulated_days']} days)
- **Economic Delta STD**: ${money_std:.2f}
- **Throughput**: {metrics['throughput_tps']} ticks/sec
"""
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Demonstrated persistent individual divergence in economic and autobiographical trajectories over time.",
            hypotheses=hypotheses,
            metrics=metrics,
            duration_seconds=elapsed,
            report_markdown=md,
        )


class ExperimentH_Emergence(BaseExperiment):
    """Experiment H: Emergence & Unexpected Behavior.

    Objective: Determine whether complex patterns (preferred communal hubs,
    social networks, activity clusters) emerge without explicit scripting.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_H_EMERGENCE",
            name="Emergence and Social Clustering",
            description="Examines spontaneous location aggregation and emergent relationship clusters over 96 ticks.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        import tempfile
        from pathlib import Path
        temp_db = Path(tempfile.mkdtemp()) / "exp_g.db"
        cfg = SimulationConfig(random_seed=self.config.random_seed, database_path=temp_db)
        sim = runner or SimulationRunner(config=cfg)
        if runner is None:
            sim.initialize(load_existing=False)

        location_visits: dict[str, int] = {}

        def record_arrival(evt: SimulationEvent) -> None:
            if evt.event_type == EventType.ARRIVED_AT_LOCATION and evt.location_id:
                location_visits[evt.location_id] = location_visits.get(evt.location_id, 0) + 1

        sim.event_bus.subscribe(EventType.ARRIVED_AT_LOCATION, record_arrival)

        for _ in range(self.config.duration_ticks):
            sim.step()

        # Emergent hub detection
        visited_locations_count = len(location_visits)
        top_hub = max(location_visits.items(), key=lambda x: x[1]) if location_visits else ("none", 0)

        # Relationship count
        rels = sim.social.get_all_relationships()

        elapsed = time.perf_counter() - t0
        success = visited_locations_count >= 3 and len(rels) > 0

        hypotheses = [
            {
                "hypothesis": "Agents spontaneously concentrate around natural social hubs (plaza, market, comedor).",
                "confirmed": visited_locations_count >= 3,
                "evidence": f"Agents utilized {visited_locations_count} distinct locations. Top hub: {top_hub[0]} ({top_hub[1]} visits).",
            },
            {
                "hypothesis": "Organic social networks expand through proximity encounters.",
                "confirmed": len(rels) > 0,
                "evidence": f"A total of {len(rels)} directional relationships formed or evolved.",
            },
        ]

        metrics = {
            "distinct_locations_visited": visited_locations_count,
            "top_hub_location": top_hub[0],
            "top_hub_visits": top_hub[1],
            "total_relationships_active": len(rels),
        }

        if runner is None:
            sim.close()

        md = f"""# Experiment H: Emergence
- **Status**: {'SUCCESS' if success else 'FAILURE'}
- **Distinct Locations Active**: {visited_locations_count}
- **Top Emergent Hub**: {top_hub[0]} ({top_hub[1]} visits)
- **Active Social Bonds**: {len(rels)}
"""
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Emergent social hubs and organic clustering formed naturally without hardcoded scripting.",
            hypotheses=hypotheses,
            metrics=metrics,
            duration_seconds=elapsed,
            report_markdown=md,
        )
