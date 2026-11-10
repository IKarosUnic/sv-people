"""Phase 0.2 Acceptance Test Suite — Cognitive Evolution, Autonomous Behavior & Synthetic Human Development.

Validates the 10 mandatory acceptance criteria established in Section 12:
1. At least two individuals responding differently to equivalent experiences.
2. An individual changing a behavioral tendency over time.
3. An individual forming an autonomous goal.
4. An individual learning a skill.
5. An individual remembering an important experience.
6. An individual gradually losing access to an irrelevant memory.
7. An individual changing a relationship.
8. An individual abandoning or modifying an objective.
9. Persistent state surviving application restart.
10. All previous functionality remaining operational.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import numpy as np
import pytest

from saltbor.core.types import ActivityType, EmotionType, NeedType, SkillCategory, SkillID
from saltbor.core.identity import HumanIdentity
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.population.factory import PopulationFactory
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.procedural import Skill
from saltbor.cognition.learning.engine import LearningEngine
from saltbor.cognition.autonomy.engine import AutonomyEngine, Goal
from saltbor.cognition.decision.engine import DecisionEngine, DecisionContext
from saltbor.social.engine import SocialEngine
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.schema import SchemaManager
from saltbor.persistence.repositories import HumanRepository
from saltbor.core.config import SimulationConfig
from saltbor.simulation.runner import SimulationRunner
from saltbor.world.locations.registry import LocationRegistry


def test_acceptance_1_differential_reactions_to_equivalent_experience():
    """Criteria 1: At least two individuals responding differently to equivalent experiences."""
    # Individual A: Resilient & Calm (Low Neuroticism, High Emotional Regulation)
    traits_a = PersonalityTraits(neuroticism=TraitValue(base_value=0.15, current_value=0.15))
    profile_a = EmotionalProfile(regulation_capacity=0.90, baseline_mood=0.70)
    pers_a = PersonalityEngine(traits_a)
    emot_a = EmotionalEngine(profile=profile_a)

    # Individual B: Sensitive & Reactive (High Neuroticism, Low Emotional Regulation)
    traits_b = PersonalityTraits(neuroticism=TraitValue(base_value=0.85, current_value=0.85))
    profile_b = EmotionalProfile(regulation_capacity=0.20, baseline_mood=0.30)
    pers_b = PersonalityEngine(traits_b)
    emot_b = EmotionalEngine(profile=profile_b)

    # Identical Stress Event: Public Social Rejection
    event = SimulationEvent(
        event_type=EventType.SOCIAL_REJECTION,
        tick=100,
        importance=0.80,
    )

    pers_a.apply_experience(event, emotional_impact=-0.70)
    emot_a.process_event(event, pers_a)

    pers_b.apply_experience(event, emotional_impact=-0.70)
    emot_b.process_event(event, pers_b)

    # Sensitive individual experiences significantly higher distress emotions (shame, loneliness)
    assert emot_b.get_emotion("shame") > emot_a.get_emotion("shame")
    assert emot_b.get_emotion("loneliness") > emot_a.get_emotion("loneliness")
    assert emot_a.regulation_capacity > emot_b.regulation_capacity


def test_acceptance_2_behavioral_tendency_change_over_time():
    """Criteria 2: An individual changing a behavioral tendency over time."""
    traits = PersonalityTraits(
        risk_tolerance=TraitValue(base_value=0.75, current_value=0.75),
        neuroticism=TraitValue(base_value=0.25, current_value=0.25),
    )
    pers = PersonalityEngine(traits)
    initial_risk = pers.get_base_trait("risk_tolerance")
    initial_neuro = pers.get_base_trait("neuroticism")

    # Series of repeated financial catastrophes
    for day in range(1, 6):
        loss_event = SimulationEvent(
            event_type=EventType.FINANCIAL_LOSS,
            tick=day * 96,
            importance=0.85,
        )
        pers.apply_experience(loss_event, emotional_impact=-0.80)

    final_risk = pers.get_base_trait("risk_tolerance")
    final_neuro = pers.get_base_trait("neuroticism")
    evolution_log = pers.get_evolution_log()

    assert final_risk < initial_risk
    assert final_neuro > initial_neuro
    assert len(evolution_log) >= 5
    assert evolution_log[0]["trait"] == "risk_tolerance"


def test_acceptance_3_autonomous_goal_formation():
    """Criteria 3: An individual forming an autonomous goal."""
    autonomy = AutonomyEngine()
    pers = PersonalityEngine(PersonalityTraits.random())
    needs = {NeedType.ACHIEVEMENT: 0.85, NeedType.HUNGER: 0.20, NeedType.REST: 0.20}
    skills = [
        Skill(
            skill_id=SkillID("skill_carpentry"),
            name="carpentry",
            category=SkillCategory.TECHNICAL,
            level=0.15,
        )
    ]

    new_goals = autonomy.generate_goals_from_needs(
        needs=needs,
        personality=pers,
        current_tick=50,
        skills=skills,
    )

    assert len(new_goals) >= 1
    skill_goal = next(g for g in new_goals if g.category == "skill")
    assert skill_goal.status == "active"
    assert len(skill_goal.plan_steps) > 0
    assert skill_goal.priority > 0.3


def test_acceptance_4_skill_acquisition():
    """Criteria 4: An individual learning a skill."""
    mem = MemoryEngine()
    learning = LearningEngine()
    mem.procedural.add_skill(
        Skill(
            skill_id=SkillID("skill_agriculture"),
            name="agriculture",
            category=SkillCategory.PHYSICAL,
            level=0.10,
            practice_count=0,
        )
    )

    initial_level = mem.procedural.get_skill("skill_agriculture").level

    # Deliberate practice sessions
    for session in range(1, 4):
        learning.practice_skill("skill_agriculture", mem, duration_ticks=4, current_tick=session * 96)

    final_skill = mem.procedural.get_skill("skill_agriculture")
    assert final_skill.level > initial_level
    assert final_skill.practice_count > 0
    assert final_skill.confidence > 0.40


def test_acceptance_5_important_experience_retention():
    """Criteria 5: An individual remembering an important experience."""
    mem = MemoryEngine()
    important_evt = SimulationEvent(
        event_type=EventType.PERSONAL_ACHIEVEMENT,
        tick=10,
        importance=0.90,
    )
    mem.record_event(important_evt, importance=0.90, emotional_valence=0.85)

    # Consolidate after 30 days
    mem.consolidate(current_tick=10 + (96 * 30))

    active_memories = mem.episodic.get_all()
    assert any("personal_achievement" in m.summary for m in active_memories)


def test_acceptance_6_irrelevant_memory_accessibility_loss():
    """Criteria 6: An individual gradually losing access to an irrelevant memory without data destruction."""
    mem = MemoryEngine()
    routine_evt = SimulationEvent(
        event_type=EventType.ACTIVITY_STARTED,
        tick=5,
        importance=0.16,
    )
    mem.record_event(routine_evt, importance=0.16, emotional_valence=0.0)

    # Initial state: active
    assert mem.episodic.count == 1
    assert mem.episodic.total_stored_count == 1

    # Advance 40 days and consolidate
    stats = mem.consolidate(current_tick=5 + (96 * 40))

    # Active access is lost (dormant archive)
    assert mem.episodic.count == 0
    # Complete persistent history is fully preserved without data loss
    assert mem.episodic.total_stored_count == 1
    assert stats["forgotten"] == 1


def test_acceptance_7_relationship_evolution():
    """Criteria 7: An individual changing a relationship."""
    social = SocialEngine()
    h1 = HumanIdentity().uid
    h2 = HumanIdentity().uid

    # 1. Start as strangers
    rel = social.get_relationship(h1, h2)
    initial_trust = rel.trust

    # 2. Cooperate and build affinity
    for t in range(1, 4):
        social.record_cooperation(h1, h2, tick=t * 10, intensity=0.7)

    rel_coop = social.get_relationship(h1, h2)
    coop_trust = rel_coop.trust
    assert coop_trust > initial_trust

    # 3. Conflict triggers trust erosion
    social.record_conflict(h1, h2, tick=50, intensity=0.85)
    rel_conflict = social.get_relationship(h1, h2)
    assert rel_conflict.trust < coop_trust

    # 4. Asymmetric directional attitudes
    social.record_directional_interaction(h1, h2, tick=60, positive=True, intensity=0.6, interaction_type="apology")
    att_h1_to_h2 = social.get_directional_attitude(h1, h2)
    att_h2_to_h1 = social.get_directional_attitude(h2, h1)
    assert att_h1_to_h2.trust > att_h2_to_h1.trust


def test_acceptance_8_goal_abandonment_or_modification():
    """Criteria 8: An individual abandoning or modifying an objective."""
    goal = Goal(
        goal_id="goal_build_shed",
        description="Build garden shed",
        category="skill",
        plan_steps=["gather wood", "build frame", "assemble roof"],
    )

    # Encounter obstacles and record failures
    goal.consecutive_failures += 1
    assert goal.consecutive_failures == 1

    # Procrastinate
    goal.procrastinate()
    assert goal.status == "procrastinated"
    assert goal.procrastination_count == 1

    # Modify plan
    goal.modify(new_description="Build smaller tool shed", new_plan_steps=["salvage planks", "assemble box"])
    assert goal.status == "modified"
    assert goal.description == "Build smaller tool shed"

    # Abandon after insurmountable roadblocks
    goal.abandon(reason="Too costly; pivoting to other priorities.")
    assert goal.status == "abandoned"
    assert "Too costly" in goal.reasoning


def test_acceptance_9_persistent_state_survives_restart():
    """Criteria 9: Persistent state surviving application restart."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)

    try:
        db = DatabaseManager(db_path)
        db.connect()
        SchemaManager.create_tables(db)
        repo = HumanRepository(db)

        # Create human with Phase 0.2 cognitive enhancements
        cfg = SimulationConfig(random_seed=42, initial_population_size=1)
        human = PopulationFactory.create_population(config=cfg, try_nemotron=False)[0]
        human.personality.temperament_value = "steady_calm"
        human.personality.personal_values = {"community": 0.9, "hard_work": 0.8}
        human.personality.behavioral_patterns = {"morning_walk": 0.8, "study_evening": 0.7}
        human.emotions.induce_emotion(EmotionType.SATISFACTION, intensity=0.82)
        human.autonomy.add_goal(
            Goal(
                goal_id="g_farm",
                description="Expand crop harvest",
                category="skill",
                plan_steps=["tillage", "sowing", "irrigation"],
            )
        )

        repo.save(human)
        db.close()

        # Restart / recreate repository with fresh connection
        db2 = DatabaseManager(db_path)
        db2.connect()
        repo2 = HumanRepository(db2)
        loaded = repo2.load(human.identity.uid)

        assert loaded is not None
        assert loaded.identity.given_name == human.identity.given_name
        assert loaded.personality.temperament_value == "steady_calm"
        assert loaded.personality.personal_values["community"] == 0.9
        assert "morning_walk" in loaded.personality.behavioral_patterns
        assert loaded.emotions.get_emotion("satisfaction") > 0.70
        assert len(loaded.autonomy.goals) >= 1
        assert loaded.autonomy.goals[0].description == "Expand crop harvest"
        db2.close()
    finally:
        try:
            db_path.unlink()
        except OSError:
            pass


def test_acceptance_10_all_previous_functionality_operational():
    """Criteria 10: All previous functionality remaining operational."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)

    try:
        cfg = SimulationConfig(
            random_seed=42,
            initial_population_size=20,
            database_path=db_path,
            checkpoint_interval_ticks=10,
        )
        runner = SimulationRunner(config=cfg)
        runner.initialize()

        # Execute 24 simulation ticks (6 hours)
        runner.run(num_ticks=24)

        assert runner.clock.current_tick == 24
        metrics = runner.metrics.get_summary()
        assert metrics["total_ticks_recorded"] == 24
        assert metrics["average_tick_latency_ms"] < 50.0

        # Inhabitants progressed in activities and navigation
        humans = runner.human_repo.load_all()
        assert len(humans) == 20
        assert any(h.physical_state.current_activity != ActivityType.SLEEP for h in humans)
        runner.db.close()
    finally:
        try:
            db_path.unlink()
        except OSError:
            pass
