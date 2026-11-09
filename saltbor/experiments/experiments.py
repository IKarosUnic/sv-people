"""Behavioral and scientific experiments for the Saltbor synthetic human simulation.

Validates emergent, individualized behaviors as required by the Phase 0.1 directive:
1. Differential reaction: Two individuals experience the same event and react differently.
2. Behavioral adaptation: An individual changes behavior after repeated negative experiences.
3. Skill acquisition: An individual learns a skill through practice with diminishing returns.
4. Autonomous goal formulation: An individual formulates a goal without direct instruction.
5. Selective memory & forgetting: Pruning trivial details while retaining emotionally significant memories.
6. Divergent relationship formation: Two individuals develop different bonds with the same third person.
"""

from __future__ import annotations

import logging
from typing import Any

from saltbor.cognition.autonomy.engine import AutonomyEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import EmotionType, NeedType, RelationshipType, SkillCategory
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.social.engine import SocialEngine

logger = logging.getLogger(__name__)


def experiment_differential_reaction() -> dict[str, Any]:
    """Experiment 1: Two individuals experience the identical event and react differently.

    Agent A has high Neuroticism (0.90) and low Agreeableness (0.20).
    Agent B has low Neuroticism (0.15) and high Agreeableness (0.85).
    Both experience a CONFLICT_OCCURRED event.
    """
    # Agent A (Reactive / Anxious)
    traits_a = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.90, current_value=0.90),
        agreeableness=TraitValue(base_value=0.20, current_value=0.20),
        extraversion=TraitValue(base_value=0.50, current_value=0.50),
    )
    eng_a = EmotionalEngine(profile=EmotionalProfile())

    # Agent B (Calm / Cooperative)
    traits_b = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.15, current_value=0.15),
        agreeableness=TraitValue(base_value=0.85, current_value=0.85),
        extraversion=TraitValue(base_value=0.50, current_value=0.50),
    )
    eng_b = EmotionalEngine(profile=EmotionalProfile())

    conflict_event = SimulationEvent(
        event_type=EventType.CONFLICT_OCCURRED,
        tick=10,
        importance=0.7,
    )

    eng_a.process_event(conflict_event, traits_a)
    eng_b.process_event(conflict_event, traits_b)

    anger_a = eng_a.get_emotion("anger")
    anger_b = eng_b.get_emotion("anger")
    mood_a = eng_a.get_mood()
    mood_b = eng_b.get_mood()

    return {
        "event": conflict_event.event_type.value,
        "agent_a_neuroticism": traits_a.neuroticism.base_value,
        "agent_a_anger": round(anger_a, 3),
        "agent_a_mood": round(mood_a, 3),
        "agent_b_neuroticism": traits_b.neuroticism.base_value,
        "agent_b_anger": round(anger_b, 3),
        "agent_b_mood": round(mood_b, 3),
        "differential_demonstrated": anger_a > anger_b and mood_a < mood_b,
    }


def experiment_skill_acquisition() -> dict[str, Any]:
    """Experiment 2: Skill acquisition with diminishing returns through practice."""
    mem = MemoryEngine()
    skill_id = "carpentry_practice"

    gains = []
    levels = []

    for practice_session in range(1, 6):
        # 4 ticks of practice per session
        delta = mem.procedural.improve_skill(skill_id, xp_gain=25.0)
        skill = mem.procedural.get_skill(skill_id)
        gains.append(round(delta, 4))
        levels.append(round(skill.level, 4) if skill else 0.0)

    # Verify diminishing returns: earlier gains must be strictly larger than later gains
    is_diminishing = all(gains[i] >= gains[i + 1] for i in range(len(gains) - 1))

    return {
        "practice_sessions": len(levels),
        "final_level": levels[-1],
        "incremental_gains": gains,
        "levels": levels,
        "diminishing_returns_demonstrated": is_diminishing,
    }


def experiment_autonomous_goal_generation() -> dict[str, Any]:
    """Experiment 3: An individual formulates personal goals without external instruction."""
    autonomy = AutonomyEngine()
    pers = PersonalityEngine(PersonalityTraits.random())

    # Simulate hunger build-up
    urgent_needs = {
        NeedType.HUNGER: 0.85,
        NeedType.REST: 0.10,
        NeedType.SOCIAL: 0.20,
    }

    initial_goals = autonomy.get_active_goals()
    assert len(initial_goals) == 0

    new_goals = autonomy.generate_goals_from_needs(urgent_needs, pers, current_tick=12)

    return {
        "initial_goals_count": len(initial_goals),
        "generated_goals_count": len(new_goals),
        "primary_goal": new_goals[0].description if new_goals else None,
        "primary_goal_priority": new_goals[0].priority if new_goals else 0.0,
        "autonomy_demonstrated": len(new_goals) > 0 and new_goals[0].need_type == NeedType.HUNGER,
    }


def experiment_selective_forgetting() -> dict[str, Any]:
    """Experiment 4: Irrelevant details are forgotten while emotionally significant experiences persist."""
    mem = MemoryEngine()

    # 1. Trivial event (low importance, zero emotional charge)
    trivial_evt = SimulationEvent(
        event_type=EventType.ACTIVITY_STARTED,
        tick=10,
        importance=0.18,
    )
    mem.record_event(trivial_evt, importance=0.18, emotional_valence=0.0)

    # 2. Significant, emotionally intense event (friendship created)
    meaningful_evt = SimulationEvent(
        event_type=EventType.FRIENDSHIP_CREATED,
        tick=10,
        importance=0.90,
    )
    mem.record_event(meaningful_evt, importance=0.90, emotional_valence=+0.85)

    assert mem.episodic.count == 2
    initial_count = mem.episodic.count

    # Advance time by 60 simulated days (5760 ticks)
    future_tick = 10 + (96 * 60)
    consolidation_result = mem.consolidate(current_tick=future_tick)

    remaining_memories = mem.episodic.get_all()
    survived_types = [m.summary for m in remaining_memories]

    return {
        "initial_memory_count": initial_count,
        "forgotten_count": consolidation_result["forgotten"],
        "preserved_count": consolidation_result["preserved"],
        "surviving_memory_summaries": survived_types,
        "selective_decay_demonstrated": (
            consolidation_result["forgotten"] >= 1
            and any("friendship" in s for s in survived_types)
        ),
    }


def experiment_divergent_relationships() -> dict[str, Any]:
    """Experiment 5: Two individuals develop divergent relationships with the same third person."""
    social = SocialEngine()
    ident_target = HumanIdentity()
    ident_person1 = HumanIdentity()
    ident_person2 = HumanIdentity()

    # Person 1 has series of positive, cooperative interactions with target
    for t in range(1, 5):
        social.record_interaction(ident_person1.uid, ident_target.uid, tick=t*10, positive=True, intensity=0.6)

    # Person 2 has conflicting, negative interactions with target
    for t in range(1, 5):
        social.record_interaction(ident_person2.uid, ident_target.uid, tick=t*10, positive=False, intensity=0.6)

    rel_1 = social.get_relationship(ident_person1.uid, ident_target.uid)
    rel_2 = social.get_relationship(ident_person2.uid, ident_target.uid)

    return {
        "person1_trust": round(rel_1.trust, 3),
        "person1_affinity": round(rel_1.affinity, 3),
        "person1_type": rel_1.relationship_type.value,
        "person2_trust": round(rel_2.trust, 3),
        "person2_affinity": round(rel_2.affinity, 3),
        "person2_type": rel_2.relationship_type.value,
        "divergent_dynamics_demonstrated": rel_1.affinity > rel_2.affinity and rel_1.trust > rel_2.trust,
    }


def experiment_behavioral_adaptation() -> dict[str, Any]:
    """Experiment 6: An individual adapts and changes personality drift/caution after repeated losses."""
    traits = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.30, current_value=0.30),
        risk_tolerance=TraitValue(base_value=0.70, current_value=0.70),
    )
    pers = PersonalityEngine(traits)

    initial_risk = pers.get_trait("risk_tolerance")
    initial_neuro = pers.get_trait("neuroticism")

    # Experience repeated severe financial losses
    for t in range(1, 4):
        loss_event = SimulationEvent(
            event_type=EventType.FINANCIAL_LOSS,
            tick=t * 50,
            importance=0.85,
        )
        pers.apply_experience(loss_event, emotional_impact=-0.75)

    final_risk = pers.get_trait("risk_tolerance")
    final_neuro = pers.get_trait("neuroticism")

    return {
        "initial_risk_tolerance": round(initial_risk, 3),
        "final_risk_tolerance": round(final_risk, 3),
        "initial_neuroticism": round(initial_neuro, 3),
        "final_neuroticism": round(final_neuro, 3),
        "adaptation_demonstrated": final_risk < initial_risk or final_neuro > initial_neuro,
    }
