"""Unit and integration tests for the Phase 1.7 psychological layer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.core.config import SimulationConfig
from saltbor.core.types import RelationshipType
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.psychology.coping import COPING_SPECS, CopingChoice
from saltbor.psychology.engine import PsychologicalEngine
from saltbor.psychology.models import CopingStrategy
from saltbor.psychology.retrieval import AssociativeRetrieval
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.engine import SocialEngine


def make_agent(name: str, serial: int) -> SyntheticHuman:
    agent = SyntheticHuman.create(name=name, age=32, money=80, seed=serial, serial=serial)
    agent.physical_state.current_location_id = "casa_norte_1"
    agent.physical_state.home_location_id = "casa_norte_1"
    return agent


def event(event_type: EventType, human: SyntheticHuman, tick: int, importance: float = 0.8):
    return SimulationEvent(
        event_type=event_type,
        tick=tick,
        source_human_id=human.uid,
        location_id=human.physical_state.current_location_id,
        importance=importance,
    )


def support_network(agent: SyntheticHuman, level: float = 0.7):
    social = SocialEngine()
    partners = []
    for i in range(3):
        partner = make_agent(f"Support {i}", serial=100 + i)
        partner.physical_state.current_location_id = agent.physical_state.current_location_id
        rel = social.get_relationship(agent.uid, partner.uid)
        rel.trust = level
        rel.affinity = level
        rel.familiarity = 0.6
        rel.interaction_count = 8
        rel.relationship_type = RelationshipType.FAMILY if i == 0 else RelationshipType.CLOSE_FRIEND
        partners.append(partner)
    return social, partners


def pop_of(*humans: SyntheticHuman) -> PopulationRegistry:
    registry = PopulationRegistry()
    for human in humans:
        registry.register(human)
    return registry


def test_same_job_loss_can_have_opposite_desirability():
    disliked = make_agent("Disliked", serial=1)
    disliked.preferences["job_satisfaction"] = 0.05
    disliked.personality.personal_values.update({"autonomy": 0.9, "security": 0.2})

    provider = make_agent("Provider", serial=2)
    provider.preferences["job_satisfaction"] = 0.9
    provider.personality.personal_values.update({"security": 0.95, "benevolence": 0.9})

    appraisals = {}
    for name, agent in (("disliked", disliked), ("provider", provider)):
        social, partners = support_network(agent, level=0.6)
        pop = pop_of(agent, *partners)
        engine = PsychologicalEngine(seed=7)
        engine.ensure(agent)
        engine.process_events([event(EventType.JOB_LOST, agent, 1, 0.9)], pop, social)
        appraisals[name] = agent.psychology.recent_appraisals[-1]

    assert appraisals["disliked"].desirability > 0
    assert appraisals["provider"].desirability < 0
    # Traceability: appraisal, emotion, control, confidence, consequences.
    assert appraisals["disliked"].emotions
    assert 0.0 <= appraisals["disliked"].control <= 1.0
    assert appraisals["disliked"].consequences


def test_crisis_has_cause_course_and_end():
    agent = make_agent("Crisis", serial=3)
    social, partners = support_network(agent, level=0.2)
    pop = pop_of(agent, *partners)
    engine = PsychologicalEngine(seed=11)
    psych = engine.ensure(agent)
    psych.chronic_stress = 0.82
    psych.acute_stress = 0.8
    psych.mental_fatigue = 0.6
    psych.self_control = 0.18
    psych.perceived_support = 0.15

    for day in range(30):
        engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)

    assert psych.crisis_history, "sustained pressure should produce a crisis episode"
    episode = psych.crisis_history[0]
    assert episode.causes
    assert episode.triggers
    assert episode.behaviours
    assert episode.peak_severity > 0
    assert not episode.is_active
    assert episode.ended_tick is not None
    assert psych.active_crisis is None
    assert 0.0 <= psych.post_crisis_vulnerability <= 1.0


def test_coping_has_immediate_relief_and_deferred_outcome():
    agent = make_agent("Coping", serial=4)
    social, partners = support_network(agent, level=0.5)
    pop = pop_of(agent, *partners)
    engine = PsychologicalEngine(seed=13)
    psych = engine.ensure(agent)
    psych.chronic_stress = 0.55
    psych.acute_stress = 0.6
    psych.self_control = 0.35
    engine._should_cope = lambda *args, **kwargs: False

    spec = COPING_SPECS[CopingStrategy.PROCRASTINATION]
    episode = engine.coping.execute(
        agent, psych, CopingChoice(spec, 0.5), tick=0,
        support_engine=engine.support, assessment=engine.support.assess(agent, social, None, pop),
        social=social, population=pop,
    )
    assert episode.short_term_relief > 0
    assert episode.start_chronic_stress >= 0
    episode.follow_up_tick = 7
    for day in range(1, 9):
        engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
    assert episode.deferred_applied


def test_memory_is_reconstructed_and_contradictions_are_detected():
    retrieval = AssociativeRetrieval()
    record = EpisodicRecord(
        summary="Discusión con Marta en el mercado por una deuda",
        tick=0,
        importance=0.8,
        emotional_valence=-0.75,
        associated_humans=["marta"],
        context_tags=["conflict"],
    )
    agent = make_agent("Memory", serial=5)
    engine = PsychologicalEngine(seed=17)
    psych = engine.ensure(agent)
    psych.sadness = 0.7
    psych.hope = 0.25
    fresh = retrieval.reconstruct(record, tick=0, psych=psych)
    aged = retrieval.reconstruct(record, tick=96 * 200, psych=psych)
    assert aged.fidelity < fresh.fidelity
    assert aged.age_days > 0

    other = EpisodicRecord(
        summary="Marta me ayudó cuando estaba enfermo",
        tick=50,
        importance=0.7,
        emotional_valence=0.7,
        associated_humans=["marta"],
    )
    assert retrieval.find_contradictions([record, other])


def test_support_is_not_guaranteed_without_a_network():
    agent = make_agent("Isolated", serial=6)
    engine = PsychologicalEngine(seed=19)
    psych = engine.ensure(agent)
    before = psych.loneliness
    outcome = engine.support.request_support(
        agent, psych, need="financial", amount_usd=20.0, tick=1, social=None,
    )
    assert outcome.granted is False
    assert psych.loneliness > before


def test_psychology_persists_across_checkpoint_and_reload():
    db = Path(tempfile.mkdtemp()) / "psych17.db"
    config = SimulationConfig(
        random_seed=23, initial_population_size=12,
        checkpoint_interval_ticks=8, database_path=str(db),
    )
    runner = SimulationRunner(config)
    runner.initialize()
    for _ in range(16):
        runner.step()
    uid = str(runner.population.get_all()[0].uid)
    stress = runner.population.get_all()[0].psychology.chronic_stress
    timeline_rows = runner.db.execute("SELECT COUNT(*) c FROM psychology_timeline").fetchone()["c"]
    # Saving a human must update the row in place: INSERT OR REPLACE would
    # delete it, cascade-delete the timeline, and lose all prior history.
    runner.checkpoint()
    timeline_rows_after = runner.db.execute("SELECT COUNT(*) c FROM psychology_timeline").fetchone()["c"]
    assert timeline_rows_after >= timeline_rows
    runner.db.close()

    reloaded = SimulationRunner(config)
    reloaded.initialize(load_existing=True)
    restored = reloaded.psychology.states[uid]
    assert abs(restored.chronic_stress - stress) < 1e-6
    assert len(reloaded.psychology.states) == 12
    assert timeline_rows > 0
    reloaded.db.close()
