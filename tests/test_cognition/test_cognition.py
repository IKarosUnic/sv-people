"""Tests for cognitive engines: personality, emotions, memory, learning, and autonomy."""

import numpy as np

from saltbor.cognition.autonomy.engine import AutonomyEngine
from saltbor.cognition.decision.engine import DecisionContext, DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.types import ActivityType, EmotionType, NeedType
from saltbor.events.types import EventType, SimulationEvent


def test_memory_creation_and_consolidation():
    mem = MemoryEngine()
    evt = SimulationEvent(
        event_type=EventType.FRIENDSHIP_CREATED,
        tick=10,
        importance=0.85,
    )
    mem.record_event(evt, importance=0.85, emotional_valence=0.7)

    assert mem.working.count == 1
    assert mem.episodic.count == 1

    # Trivial memory
    trivial = SimulationEvent(
        event_type=EventType.ACTIVITY_STARTED,
        tick=10,
        importance=0.18,
    )
    mem.record_event(trivial, importance=0.18, emotional_valence=0.0)
    assert mem.episodic.count == 2

    # Consolidate 40 days later: trivial should decay away, friendship persists
    result = mem.consolidate(current_tick=10 + (96 * 40))
    assert result["forgotten"] >= 1
    assert mem.episodic.count == 1


def test_emotional_response_and_personality():
    traits_calm = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.1, current_value=0.1),
        agreeableness=TraitValue(base_value=0.9, current_value=0.9),
    )
    traits_anxious = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.9, current_value=0.9),
        agreeableness=TraitValue(base_value=0.2, current_value=0.2),
    )

    eng_calm = EmotionalEngine(profile=EmotionalProfile())
    eng_anxious = EmotionalEngine(profile=EmotionalProfile())

    evt = SimulationEvent(event_type=EventType.CONFLICT_OCCURRED, tick=1, importance=0.8)

    eng_calm.process_event(evt, traits_calm)
    eng_anxious.process_event(evt, traits_anxious)

    assert eng_anxious.get_emotion("anger") > eng_calm.get_emotion("anger")


def test_autonomous_goal_generation():
    autonomy = AutonomyEngine()
    pers = PersonalityEngine(PersonalityTraits.random())

    needs = {NeedType.HUNGER: 0.90, NeedType.REST: 0.20}
    goals = autonomy.generate_goals_from_needs(needs, pers, current_tick=5)

    assert len(goals) >= 1
    primary = autonomy.current_primary_goal()
    assert primary is not None
    assert primary.need_type == NeedType.HUNGER


def test_decision_making_context():
    decision_eng = DecisionEngine()
    pers = PersonalityEngine(PersonalityTraits.random())
    emot = EmotionalEngine(profile=EmotionalProfile())

    # Starving and late at night
    context = DecisionContext(
        current_location_id="casa_norte_1",
        available_activities=[ActivityType.SLEEP, ActivityType.EAT, ActivityType.WORK],
        current_needs={NeedType.HUNGER: 0.95, NeedType.REST: 0.85},
        current_energy=0.15,
        current_hunger=0.95,
        current_money=50.0,
        is_daytime=False,
        hour_int=23,
        home_location_id="casa_norte_1",
    )

    action = decision_eng.decide(context, pers, emot, rng=np.random.default_rng(42))
    # Must choose to Eat or Sleep (not Work in the middle of the night while exhausted)
    assert action.action_type in (ActivityType.EAT, ActivityType.COOK, ActivityType.SLEEP)
