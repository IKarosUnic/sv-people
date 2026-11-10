"""Behavioral and scientific experiments for the Saltbor synthetic human simulation.

Validates emergent, individualized cognitive evolution across Phase 0.1 and Phase 0.2:
- EXPERIMENT A: Different personalities responding differently to the identical situation.
- EXPERIMENT B: Emotional state modifying decision-making under identical circumstances.
- EXPERIMENT C: Significant memories influencing future choices while routine memories decay.
- EXPERIMENT D: Long-term personality evolution through repeated significant life experiences.
- EXPERIMENT E: Autonomous skill deficit identification, goal formation, and progressive improvement.
- EXPERIMENT F: Interpersonal relationship dynamics: trust building, conflict, asymmetry, and reconciliation.
- EXPERIMENT G: Bounded rational goal lifecycle, adaptation, procrastination, and abandonment.
- EXPERIMENT H: Individual divergence: identical starting profiles developing substantially different life trajectories.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from saltbor.cognition.autonomy.engine import AutonomyEngine, Goal
from saltbor.cognition.decision.engine import ActionOption, DecisionContext, DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.learning.engine import LearningEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.procedural import Skill
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import ActivityType, EmotionType, NeedType, RelationshipType, SkillCategory
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.social.engine import SocialEngine

logger = logging.getLogger(__name__)


# ===========================================================================
# EXPERIMENT A: Different Personalities in the Same Situation
# ===========================================================================

def experiment_a_different_personalities() -> dict[str, Any]:
    """Experiment A: Expose individuals with different personalities to the same situation.

    Under identical environmental and physical conditions at Plaza Mayor at 11:00 AM:
    - Agent 1 (High Conscientiousness & Openness, Low Extraversion) chooses to STUDY.
    - Agent 2 (High Extraversion & Agreeableness, Low Conscientiousness) chooses to SOCIALIZE.
    """
    decision_eng = DecisionEngine()

    # Agent 1: Conscientious Scholar
    traits_scholar = PersonalityTraits(
        conscientiousness=TraitValue(base_value=0.88, current_value=0.88),
        openness=TraitValue(base_value=0.85, current_value=0.85),
        extraversion=TraitValue(base_value=0.25, current_value=0.25),
        agreeableness=TraitValue(base_value=0.60, current_value=0.60),
        neuroticism=TraitValue(base_value=0.20, current_value=0.20),
    )
    pers_scholar = PersonalityEngine(traits_scholar)
    emot_scholar = EmotionalEngine(profile=EmotionalProfile())

    # Agent 2: Extroverted Socializer
    traits_social = PersonalityTraits(
        conscientiousness=TraitValue(base_value=0.30, current_value=0.30),
        openness=TraitValue(base_value=0.45, current_value=0.45),
        extraversion=TraitValue(base_value=0.92, current_value=0.92),
        agreeableness=TraitValue(base_value=0.85, current_value=0.85),
        neuroticism=TraitValue(base_value=0.25, current_value=0.25),
    )
    pers_social = PersonalityEngine(traits_social)
    emot_social = EmotionalEngine(profile=EmotionalProfile())

    # Identical Decision Context (elective leisure/learning period in plaza)
    context = DecisionContext(
        current_location_id="plaza_central",
        available_activities=[ActivityType.STUDY, ActivityType.SOCIALIZE, ActivityType.RELAX],
        current_needs={NeedType.HUNGER: 0.20, NeedType.REST: 0.20, NeedType.SOCIAL: 0.50},
        current_energy=0.80,
        current_hunger=0.20,
        current_money=50.0,
        is_daytime=True,
        hour_int=15,
        home_location_id="casa_norte_1",
    )

    rng = np.random.default_rng(42)
    choice_scholar = decision_eng.decide(context, pers_scholar, emot_scholar, rng=rng, exploration_noise=0.02)
    choice_social = decision_eng.decide(context, pers_social, emot_social, rng=rng, exploration_noise=0.02)

    return {
        "scholar_choice": choice_scholar.action_type.value,
        "scholar_reasoning": choice_scholar.reasoning,
        "social_choice": choice_social.action_type.value,
        "social_reasoning": choice_social.reasoning,
        "different_decisions_produced": choice_scholar.action_type != choice_social.action_type,
        "success": choice_scholar.action_type == ActivityType.STUDY and choice_social.action_type == ActivityType.SOCIALIZE,
    }


# ===========================================================================
# EXPERIMENT B: Emotional Influence on Decision-Making
# ===========================================================================

def experiment_b_emotional_influence() -> dict[str, Any]:
    """Experiment B: Demonstrate how emotional state modifies decision-making in the same individual.

    Under identical physical conditions and personality:
    - In a state of High Loneliness: prioritizes SOCIALIZE.
    - In a state of High Anxiety / Fear: prioritizes REST / safety.
    - In a state of High Curiosity: prioritizes STUDY.
    """
    decision_eng = DecisionEngine()
    pers = PersonalityEngine(PersonalityTraits(
        openness=TraitValue(base_value=0.60, current_value=0.60),
        conscientiousness=TraitValue(base_value=0.60, current_value=0.60),
        extraversion=TraitValue(base_value=0.60, current_value=0.60),
        neuroticism=TraitValue(base_value=0.40, current_value=0.40),
    ))

    context = DecisionContext(
        current_location_id="plaza_central",
        available_activities=[ActivityType.SOCIALIZE, ActivityType.STUDY, ActivityType.REST, ActivityType.WORK],
        current_needs={NeedType.HUNGER: 0.25, NeedType.REST: 0.35, NeedType.SOCIAL: 0.40},
        current_energy=0.70,
        current_hunger=0.25,
        current_money=50.0,
        is_daytime=True,
        hour_int=14,
        home_location_id="casa_norte_1",
    )

    # 1. High Loneliness
    emot_lonely = EmotionalEngine(profile=EmotionalProfile())
    emot_lonely.induce_emotion(EmotionType.LONELINESS, intensity=0.90)

    # 2. High Anxiety / Fear
    emot_anxious = EmotionalEngine(profile=EmotionalProfile())
    emot_anxious.induce_emotion(EmotionType.ANXIETY, intensity=0.85)
    emot_anxious.induce_emotion(EmotionType.FEAR, intensity=0.75)

    # 3. High Curiosity
    emot_curious = EmotionalEngine(profile=EmotionalProfile())
    emot_curious.induce_emotion(EmotionType.CURIOSITY, intensity=0.90)

    choice_lonely = decision_eng.decide(context, pers, emot_lonely, rng=np.random.default_rng(42), exploration_noise=0.01)
    choice_anxious = decision_eng.decide(context, pers, emot_anxious, rng=np.random.default_rng(42), exploration_noise=0.01)
    choice_curious = decision_eng.decide(context, pers, emot_curious, rng=np.random.default_rng(42), exploration_noise=0.01)

    return {
        "lonely_choice": choice_lonely.action_type.value,
        "anxious_choice": choice_anxious.action_type.value,
        "curious_choice": choice_curious.action_type.value,
        "emotional_modulation_demonstrated": (
            choice_lonely.action_type == ActivityType.SOCIALIZE
            and choice_anxious.action_type == ActivityType.REST
            and choice_curious.action_type == ActivityType.STUDY
        ),
        "success": (
            choice_lonely.action_type != choice_anxious.action_type
            and choice_anxious.action_type != choice_curious.action_type
        ),
    }


# ===========================================================================
# EXPERIMENT C: Memory Retention vs Decay and Behavioral Steering
# ===========================================================================

def experiment_c_memory_influence() -> dict[str, Any]:
    """Experiment C: Important memories guide future choices while routine memories lose accessibility."""
    mem = MemoryEngine()
    decision_eng = DecisionEngine()
    pers = PersonalityEngine(PersonalityTraits.random())
    emot = EmotionalEngine(profile=EmotionalProfile())

    # 1. Encode routine trivial event at Comedor
    routine_evt = SimulationEvent(
        event_type=EventType.ACTIVITY_STARTED,
        tick=10,
        location_id="comedor_dona_maria",
        importance=0.18,
    )
    mem.record_event(routine_evt, importance=0.18, emotional_valence=0.0)

    # 2. Encode severe conflict / traumatic betrayal at Mercado Municipal
    conflict_evt = SimulationEvent(
        event_type=EventType.CONFLICT_OCCURRED,
        tick=12,
        location_id="mercado_municipal",
        importance=0.88,
    )
    mem.record_event(
        conflict_evt,
        importance=0.88,
        emotional_valence=-0.80,
        emotional_charges={"anger": 0.8, "anxiety": 0.7},
    )

    initial_active = mem.episodic.count
    initial_total = mem.episodic.total_stored_count

    # Advance time by 45 simulated days (4320 ticks) and consolidate
    future_tick = 12 + (96 * 45)
    consolidation_stats = mem.consolidate(current_tick=future_tick)

    # Verify: routine memory lost active recall; conflict memory preserved in active recall
    active_memories = mem.episodic.get_all()
    surviving_summaries = [m.summary for m in active_memories]
    all_stored = mem.episodic.get_stored_history()

    # Behavioral steering: individual is hungry and evaluates dining/food locations
    context = DecisionContext(
        current_location_id="plaza_central",
        available_activities=[ActivityType.EAT],
        current_needs={NeedType.HUNGER: 0.70, NeedType.REST: 0.20, NeedType.SOCIAL: 0.30},
        current_energy=0.80,
        current_hunger=0.70,
        current_money=50.0,
        is_daytime=True,
        hour_int=12,
        home_location_id="casa_norte_1",
    )

    # Evaluate options with memory
    options_with_memory = decision_eng.evaluate_options(context, pers, emot, memory=mem)
    mercado_opt = next((o for o in options_with_memory if o.target_location_id == "mercado_municipal"), None)
    comedor_opt = next((o for o in options_with_memory if o.target_location_id == "comedor_dona_maria"), None)

    mercado_assoc = mem.get_location_association("mercado_municipal")

    return {
        "initial_active_memories": initial_active,
        "initial_stored_memories": initial_total,
        "forgotten_active_memories": consolidation_stats["forgotten"],
        "preserved_active_memories": consolidation_stats["preserved"],
        "total_persisted_in_history": len(all_stored),
        "conflict_memory_accessible": any("conflict" in s for s in surviving_summaries),
        "location_aversion_recorded": mercado_assoc.get("valence", 0.0) < -0.5,
        "history_preserved_without_data_loss": len(all_stored) == 2,
        "success": (
            consolidation_stats["forgotten"] >= 1
            and any("conflict" in s for s in surviving_summaries)
            and len(all_stored) == 2
            and mercado_assoc.get("valence", 0.0) < -0.5
        ),
    }


# ===========================================================================
# EXPERIMENT D: Long-Term Personality Evolution
# ===========================================================================

def experiment_d_personality_evolution() -> dict[str, Any]:
    """Experiment D: Repeated significant life experiences measurably shift personality baseline."""
    traits = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.30, current_value=0.30),
        risk_tolerance=TraitValue(base_value=0.65, current_value=0.65),
        agreeableness=TraitValue(base_value=0.70, current_value=0.70),
    )
    pers = PersonalityEngine(traits)

    initial_neuro = pers.get_base_trait("neuroticism")
    initial_risk = pers.get_base_trait("risk_tolerance")
    initial_agree = pers.get_base_trait("agreeableness")

    # Experience repeated severe financial losses and betrayal
    for day in range(1, 6):
        loss_evt = SimulationEvent(
            event_type=EventType.FINANCIAL_LOSS,
            tick=day * 96,
            importance=0.85,
        )
        pers.apply_experience(loss_evt, emotional_impact=-0.80)

        betrayal_evt = SimulationEvent(
            event_type=EventType.TRUST_BROKEN,
            tick=day * 96 + 20,
            importance=0.80,
        )
        pers.apply_experience(betrayal_evt, emotional_impact=-0.75)

    final_neuro = pers.get_base_trait("neuroticism")
    final_risk = pers.get_base_trait("risk_tolerance")
    final_agree = pers.get_base_trait("agreeableness")
    evolution_log = pers.get_evolution_log()

    return {
        "initial_traits": {"neuroticism": initial_neuro, "risk": initial_risk, "agreeableness": initial_agree},
        "final_traits": {"neuroticism": round(final_neuro, 4), "risk": round(final_risk, 4), "agreeableness": round(final_agree, 4)},
        "evolution_events_recorded": len(evolution_log),
        "causal_trace_sample": evolution_log[0] if evolution_log else {},
        "neuroticism_increased": final_neuro > initial_neuro,
        "risk_tolerance_decreased": final_risk < initial_risk,
        "agreeableness_decreased": final_agree < initial_agree,
        "success": final_neuro > initial_neuro and final_risk < initial_risk and len(evolution_log) >= 10,
    }


# ===========================================================================
# EXPERIMENT E: Self-Improvement & Skill Mastery
# ===========================================================================

def experiment_e_self_improvement() -> dict[str, Any]:
    """Experiment E: Autonomous identification of skill deficiency, goal formulation, and improvement."""
    autonomy = AutonomyEngine()
    learning = LearningEngine(learning_rate=1.2)
    mem = MemoryEngine()
    pers = PersonalityEngine(PersonalityTraits(
        openness=TraitValue(base_value=0.85, current_value=0.85),
        persistence=TraitValue(base_value=0.80, current_value=0.80),
        conscientiousness=TraitValue(base_value=0.75, current_value=0.75),
    ))

    # Add a novice skill
    skill_carpentry = Skill(
        skill_id="skill_carpentry",
        name="Ebanistería y Carpintería",
        category=SkillCategory.TECHNICAL,
        level=0.10,
        experience_points=10.0,
    )
    mem.procedural.add_skill(skill_carpentry)

    # 1. Identify deficiency and formulate autonomous goal
    needs = {NeedType.ACHIEVEMENT: 0.75, NeedType.HUNGER: 0.1, NeedType.REST: 0.1}
    generated_goals = autonomy.generate_goals_from_needs(
        needs=needs,
        personality=pers,
        current_tick=10,
        skills=mem.procedural.get_all_skills(),
    )
    skill_goal = next((g for g in generated_goals if g.category == "skill"), None)
    assert skill_goal is not None

    initial_level = skill_carpentry.level

    # 2. Execute practice sessions (deliberate self-improvement)
    level_progression = [initial_level]
    for session in range(1, 5):
        learning.practice_skill("skill_carpentry", mem, duration_ticks=3, current_tick=session * 24)
        skill_goal.advance(0.25)
        level_progression.append(round(mem.procedural.get_skill("skill_carpentry").level, 4))

    final_level = mem.procedural.get_skill("skill_carpentry").level

    return {
        "formulated_goal": skill_goal.description,
        "goal_category": skill_goal.category,
        "initial_skill_level": round(initial_level, 4),
        "final_skill_level": round(final_level, 4),
        "level_progression": level_progression,
        "goal_status": skill_goal.status,
        "goal_completed": skill_goal.status == "completed",
        "proficiency_growth": round(final_level - initial_level, 4),
        "success": skill_goal.status == "completed" and final_level > initial_level * 2,
    }


# ===========================================================================
# EXPERIMENT F: Relationship Arc (Cooperation, Conflict, Directional Asymmetry, Reconciliation)
# ===========================================================================

def experiment_f_relationship_arc() -> dict[str, Any]:
    """Experiment F: Social relationship dynamics across cooperation, conflict, asymmetry, and reconciliation."""
    social = SocialEngine()
    p1 = HumanIdentity().uid
    p2 = HumanIdentity().uid

    # Stage 0: Strangers
    rel_start = social.get_relationship(p1, p2)
    stage_0_type = rel_start.relationship_type.value

    # Stage 1: Cooperative bonding
    for t in range(1, 4):
        social.record_cooperation(p1, p2, tick=t * 10, intensity=0.7)

    rel_bonded = social.get_relationship(p1, p2)
    stage_1_trust = rel_bonded.trust
    stage_1_type = rel_bonded.relationship_type.value

    # Stage 2: Betrayal / Severe conflict
    social.record_conflict(p1, p2, tick=50, intensity=0.9)
    rel_conflict = social.get_relationship(p1, p2)
    stage_2_trust = rel_conflict.trust
    stage_2_type = rel_conflict.relationship_type.value

    # Stage 3: Directional Asymmetry (P1 reaches out; P1's attitude improves faster than skeptical P2)
    social.record_directional_interaction(p1, p2, tick=60, positive=True, intensity=0.6, interaction_type="apology")
    att_p1_to_p2 = social.get_directional_attitude(p1, p2)
    att_p2_to_p1 = social.get_directional_attitude(p2, p1)
    asymmetry_present = att_p1_to_p2.trust > att_p2_to_p1.trust

    # Stage 4: Sincere Reconciliation
    social.record_reconciliation(p1, p2, tick=70, intensity=0.85)
    rel_reconciled = social.get_relationship(p1, p2)
    stage_4_trust = rel_reconciled.trust
    stage_4_type = rel_reconciled.relationship_type.value

    return {
        "stage_0_type": stage_0_type,
        "stage_1_trust": round(stage_1_trust, 3),
        "stage_1_type": stage_1_type,
        "stage_2_trust": round(stage_2_trust, 3),
        "stage_2_type": stage_2_type,
        "p1_to_p2_trust": round(att_p1_to_p2.trust, 3),
        "p2_to_p1_trust": round(att_p2_to_p1.trust, 3),
        "directional_asymmetry_demonstrated": asymmetry_present,
        "stage_4_trust": round(stage_4_trust, 3),
        "stage_4_type": stage_4_type,
        "history_entries": len(rel_reconciled.history),
        "success": (
            stage_1_trust > 0.65
            and stage_2_trust < 0.40
            and asymmetry_present
            and stage_4_trust > 0.55
            and len(rel_reconciled.history) >= 6
        ),
    }


# ===========================================================================
# EXPERIMENT G: Goal Procrastination, Modification, and Abandonment
# ===========================================================================

def experiment_g_goal_abandonment() -> dict[str, Any]:
    """Experiment G: An individual reconsiders, procrastinates, modifies, or abandons an unfeasible goal."""
    autonomy = AutonomyEngine()
    pers_low_persistence = PersonalityEngine(PersonalityTraits(
        persistence=TraitValue(base_value=0.25, current_value=0.25),
        neuroticism=TraitValue(base_value=0.75, current_value=0.75),
    ))
    emot_stressed = EmotionalEngine(profile=EmotionalProfile())
    emot_stressed.induce_emotion(EmotionType.FRUSTRATION, intensity=0.80)
    emot_stressed.induce_emotion(EmotionType.ANXIETY, intensity=0.70)

    # Formulate difficult ambitious goal
    ambitious_goal = Goal(
        description="Launch an independent industrial carpentry export cooperative",
        priority=0.85,
        category="career",
        plan_steps=["acquire_warehouse", "buy_imported_saws", "hire_5_craftsmen"],
        deadline_tick=50,
        created_tick=10,
    )
    autonomy.add_goal(ambitious_goal)

    # Experience repeated obstacles
    ambitious_goal.consecutive_failures = 3

    # Run lifecycle evaluation
    notifications = autonomy.evaluate_and_adapt_goals(
        personality=pers_low_persistence,
        emotions=emot_stressed,
        current_tick=60,
    )

    final_status = ambitious_goal.status

    return {
        "initial_status": "active",
        "consecutive_failures": ambitious_goal.consecutive_failures,
        "final_status": final_status,
        "abandonment_reason": ambitious_goal.reasoning,
        "notifications": notifications,
        "abandoned_or_modified": final_status in ("abandoned", "modified", "procrastinated"),
        "success": final_status == "abandoned",
    }


# ===========================================================================
# EXPERIMENT H: Individual Divergence from Identical Starting Conditions
# ===========================================================================

def experiment_h_individual_divergence() -> dict[str, Any]:
    """Experiment H: Two individuals starting with identical profiles develop substantially divergent trajectories."""
    shared_traits = lambda: PersonalityTraits(
        openness=TraitValue(base_value=0.60, current_value=0.60),
        conscientiousness=TraitValue(base_value=0.60, current_value=0.60),
        extraversion=TraitValue(base_value=0.60, current_value=0.60),
        agreeableness=TraitValue(base_value=0.60, current_value=0.60),
        neuroticism=TraitValue(base_value=0.35, current_value=0.35),
        risk_tolerance=TraitValue(base_value=0.55, current_value=0.55),
    )

    # Create identical twins A and B
    id_a = HumanIdentity(given_name="Mateo", family_name="Rivera", serial=1)
    id_b = HumanIdentity(given_name="Marcos", family_name="Rivera", serial=2)
    demo = Demographics(age=24, gender="male", occupation="Artesano")

    twin_a = SyntheticHuman(
        identity=id_a,
        demographics=demo,
        physical_state=PhysicalState(money=100.0),
        personality=PersonalityEngine(shared_traits()),
        emotions=EmotionalEngine(profile=EmotionalProfile()),
        memory=MemoryEngine(),
    )

    twin_b = SyntheticHuman(
        identity=id_b,
        demographics=demo,
        physical_state=PhysicalState(money=100.0),
        personality=PersonalityEngine(shared_traits()),
        emotions=EmotionalEngine(profile=EmotionalProfile()),
        memory=MemoryEngine(),
    )

    # Subject Twin A to a flourishing life path (achievements, cooperative wins)
    for day in range(1, 5):
        twin_a.receive_event(
            SimulationEvent(
                event_type=EventType.PERSONAL_ACHIEVEMENT,
                tick=day * 96,
                importance=0.85,
            )
        )
        twin_a.receive_event(
            SimulationEvent(
                event_type=EventType.COOPERATION_OCCURRED,
                tick=day * 96 + 20,
                importance=0.75,
            )
        )
        twin_a.learning.practice_skill("skill_craft", twin_a.memory, duration_ticks=4, current_tick=day * 96)

    # Subject Twin B to an adverse life path (financial losses, betrayal, rejection)
    for day in range(1, 5):
        twin_b.receive_event(
            SimulationEvent(
                event_type=EventType.FINANCIAL_LOSS,
                tick=day * 96,
                importance=0.85,
            )
        )
        twin_b.receive_event(
            SimulationEvent(
                event_type=EventType.TRUST_BROKEN,
                tick=day * 96 + 20,
                importance=0.80,
            )
        )
        twin_b.receive_event(
            SimulationEvent(
                event_type=EventType.SOCIAL_REJECTION,
                tick=day * 96 + 40,
                importance=0.70,
            )
        )

    # Consolidate memories
    twin_a.memory.consolidate(current_tick=400)
    twin_b.memory.consolidate(current_tick=400)

    # Formulate goals based on divergent life state
    goals_a = twin_a.autonomy.generate_goals_from_needs(
        needs={NeedType.ACHIEVEMENT: 0.70, NeedType.HUNGER: 0.2},
        personality=twin_a.personality,
        current_tick=400,
        money=twin_a.physical_state.money,
        skills=twin_a.memory.procedural.get_all_skills(),
        emotions=twin_a.emotions,
    )
    goals_b = twin_b.autonomy.generate_goals_from_needs(
        needs={NeedType.HUNGER: 0.2, NeedType.REST: 0.2},
        personality=twin_b.personality,
        current_tick=400,
        money=25.0,  # depleted funds
        skills=twin_b.memory.procedural.get_all_skills(),
        emotions=twin_b.emotions,
    )

    neuro_a = twin_a.personality.get_base_trait("neuroticism")
    neuro_b = twin_b.personality.get_base_trait("neuroticism")
    risk_a = twin_a.personality.get_base_trait("risk_tolerance")
    risk_b = twin_b.personality.get_base_trait("risk_tolerance")
    agree_a = twin_a.personality.get_base_trait("agreeableness")
    agree_b = twin_b.personality.get_base_trait("agreeableness")

    return {
        "twin_a_mood": round(twin_a.emotions.get_mood(), 3),
        "twin_b_mood": round(twin_b.emotions.get_mood(), 3),
        "twin_a_neuroticism": round(neuro_a, 4),
        "twin_b_neuroticism": round(neuro_b, 4),
        "twin_a_risk_tolerance": round(risk_a, 4),
        "twin_b_risk_tolerance": round(risk_b, 4),
        "twin_a_agreeableness": round(agree_a, 4),
        "twin_b_agreeableness": round(agree_b, 4),
        "twin_a_skill_level": round(twin_a.memory.procedural.get_skill("skill_craft").level if twin_a.memory.procedural.get_skill("skill_craft") else 0.0, 4),
        "twin_a_primary_goal": goals_a[0].description if goals_a else "None",
        "twin_b_primary_goal": goals_b[0].description if goals_b else "None",
        "divergence_demonstrated": (
            twin_a.emotions.get_mood() > twin_b.emotions.get_mood()
            and neuro_b > neuro_a
            and risk_a > risk_b
            and agree_a > agree_b
        ),
        "success": (
            twin_a.emotions.get_mood() > 0.0
            and twin_b.emotions.get_mood() < 0.0
            and neuro_b > neuro_a
            and risk_a > risk_b
        ),
    }


# ===========================================================================
# BACKWARDS COMPATIBILITY ALIASES (Phase 0.1 experiment functions)
# ===========================================================================

def experiment_differential_reaction() -> dict[str, Any]:
    """Experiment 1 alias for backward test compatibility."""
    traits_a = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.90, current_value=0.90),
        agreeableness=TraitValue(base_value=0.20, current_value=0.20),
        extraversion=TraitValue(base_value=0.50, current_value=0.50),
    )
    eng_a = EmotionalEngine(profile=EmotionalProfile())

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
    """Experiment 2 alias for backward test compatibility."""
    mem = MemoryEngine()
    skill_id = "carpentry_practice"

    gains = []
    levels = []

    for practice_session in range(1, 6):
        delta = mem.procedural.improve_skill(skill_id, xp_gain=25.0)
        skill = mem.procedural.get_skill(skill_id)
        gains.append(round(delta, 4))
        levels.append(round(skill.level, 4) if skill else 0.0)

    is_diminishing = all(gains[i] >= gains[i + 1] for i in range(len(gains) - 1))

    return {
        "practice_sessions": len(levels),
        "final_level": levels[-1],
        "incremental_gains": gains,
        "levels": levels,
        "diminishing_returns_demonstrated": is_diminishing,
    }


def experiment_autonomous_goal_generation() -> dict[str, Any]:
    """Experiment 3 alias for backward test compatibility."""
    autonomy = AutonomyEngine()
    pers = PersonalityEngine(PersonalityTraits.random())

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
    """Experiment 4 alias for backward test compatibility."""
    mem = MemoryEngine()

    trivial_evt = SimulationEvent(
        event_type=EventType.ACTIVITY_STARTED,
        tick=10,
        importance=0.18,
    )
    mem.record_event(trivial_evt, importance=0.18, emotional_valence=0.0)

    meaningful_evt = SimulationEvent(
        event_type=EventType.FRIENDSHIP_CREATED,
        tick=10,
        importance=0.90,
    )
    mem.record_event(meaningful_evt, importance=0.90, emotional_valence=+0.85)

    assert mem.episodic.count == 2
    initial_count = mem.episodic.count

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
    """Experiment 5 alias for backward test compatibility."""
    social = SocialEngine()
    ident_target = HumanIdentity()
    ident_person1 = HumanIdentity()
    ident_person2 = HumanIdentity()

    for t in range(1, 5):
        social.record_interaction(ident_person1.uid, ident_target.uid, tick=t*10, positive=True, intensity=0.6)

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
    """Experiment 6 alias for backward test compatibility."""
    traits = PersonalityTraits(
        neuroticism=TraitValue(base_value=0.30, current_value=0.30),
        risk_tolerance=TraitValue(base_value=0.70, current_value=0.70),
    )
    pers = PersonalityEngine(traits)

    initial_risk = pers.get_trait("risk_tolerance")
    initial_neuro = pers.get_trait("neuroticism")

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
