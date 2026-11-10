"""SyntheticHuman — the central aggregate root representing an autonomous individual.

Composes cognitive, emotional, mnemic, physical, and autonomous engines into
a coherent, evolving synthetic individual.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

from saltbor.cognition.autonomy.engine import AutonomyEngine
from saltbor.cognition.cognitive.engine import CognitiveEngine
from saltbor.cognition.decision.engine import DecisionContext, DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.learning.engine import LearningEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.reasoning.engine import AdvancedReasoningEngine
from saltbor.cognition.problem_solving.engine import ProblemSolvingEngine
from saltbor.cognition.metacognition.engine import MetacognitionEngine
from saltbor.cognition.creativity.engine import CreativeCombinationEngine
from saltbor.cognition.curiosity.engine import CuriosityEngine
from saltbor.cognition.architecture.brain import CognitiveBrainArchitecture
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.core.clock import SimulationClock
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import ActivityType, Gender, HumanID, LocationID, NeedType, Tick
from saltbor.events.bus import EventBus
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.demographics import Demographics
from saltbor.population.physical_state import PhysicalState
from saltbor.social.engine import SocialEngine
from saltbor.world.activities.catalog import ActivityCatalog
from saltbor.world.locations.registry import LocationRegistry

logger = logging.getLogger(__name__)


class SyntheticHuman:
    """An autonomous synthetic human in the Saltbor simulation."""

    def __init__(
        self,
        identity: HumanIdentity,
        demographics: Demographics,
        physical_state: PhysicalState,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        memory: MemoryEngine,
        cognition: Optional[CognitiveEngine] = None,
        learning: Optional[LearningEngine] = None,
        autonomy: Optional[AutonomyEngine] = None,
        decision: Optional[DecisionEngine] = None,
        rng: Optional[np.random.Generator] = None,
        knowledge_graph: Optional[IndividualKnowledgeGraph] = None,
        epistemic: Optional[EpistemicInterface] = None,
        reasoning: Optional[AdvancedReasoningEngine] = None,
        problem_solver: Optional[ProblemSolvingEngine] = None,
        metacognition: Optional[MetacognitionEngine] = None,
        creativity: Optional[CreativeCombinationEngine] = None,
        curiosity: Optional[CuriosityEngine] = None,
        brain: Optional[CognitiveBrainArchitecture] = None,
    ) -> None:
        self.identity = identity
        self.demographics = demographics
        self.physical_state = physical_state
        self.personality = personality
        self.emotions = emotions
        self.memory = memory

        self.cognition = cognition or CognitiveEngine()
        self.learning = learning or LearningEngine()
        self.autonomy = autonomy or AutonomyEngine()
        self.decision = decision or DecisionEngine()
        self._rng = rng or np.random.default_rng()

        # Phase 0.7 Advanced Cognitive, Epistemic, and Reasoning Architecture
        self.knowledge_graph = knowledge_graph or IndividualKnowledgeGraph(human_uid=str(self.identity.uid))
        self.epistemic = epistemic or EpistemicInterface(
            human_uid=str(self.identity.uid),
            knowledge_graph=self.knowledge_graph,
            memory=self.memory,
        )
        self.reasoning = reasoning or AdvancedReasoningEngine()
        self.problem_solver = problem_solver or ProblemSolvingEngine(reasoning=self.reasoning)
        self.metacognition = metacognition or MetacognitionEngine()
        self.creativity = creativity or CreativeCombinationEngine()
        self.curiosity = curiosity or CuriosityEngine()
        self.brain = brain or CognitiveBrainArchitecture(
            human_uid=str(self.identity.uid),
            personality=self.personality,
            emotions=self.emotions,
            memory=self.memory,
            autonomy=self.autonomy,
            knowledge_graph=self.knowledge_graph,
            epistemic=self.epistemic,
            reasoning=self.reasoning,
            problem_solver=self.problem_solver,
        )

    @property
    def uid(self) -> HumanID:
        return self.identity.uid

    @property
    def id(self) -> str:
        return str(self.identity.uid)

    @property
    def name(self) -> str:
        return self.identity.full_name

    @property
    def economy(self) -> PhysicalState:
        return self.physical_state

    @classmethod
    def create(
        cls,
        name: str = "Test Person",
        serial: int = 1,
        age: float = 30.0,
        money: float = 100.0,
        seed: int = 42,
        gender: Gender = Gender.MALE,
    ) -> SyntheticHuman:
        """Convenience factory for generating a fully configured test agent."""
        from uuid import uuid4
        from saltbor.lifecycle.demographics.stages import get_stage_for_age
        from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
        parts = name.split(maxsplit=1)
        given = parts[0]
        family = parts[1] if len(parts) > 1 else "Smith"
        stage = get_stage_for_age(age)
        traits = PersonalityTraits(
            openness=TraitValue(base_value=0.5, current_value=0.5),
            agreeableness=TraitValue(base_value=0.5, current_value=0.5),
            conscientiousness=TraitValue(base_value=0.5, current_value=0.5),
        )
        return cls(
            identity=HumanIdentity(uid=uuid4(), serial=serial, given_name=given, family_name=family),
            demographics=Demographics(age=int(age), gender=gender, stage=stage),
            physical_state=PhysicalState(money=money, health=1.0, home_location_id="casa_residencial_1"),
            personality=PersonalityEngine(traits),
            emotions=EmotionalEngine(),
            memory=MemoryEngine(),
            rng=np.random.default_rng(seed),
        )

    def receive_event(self, event: SimulationEvent, event_bus: Optional[EventBus] = None) -> None:
        """Process an incoming event impacting this individual."""
        # 1. Emotional reaction
        states = self.emotions.process_event(event, self.personality.traits)
        impact = self.emotions.get_mood()
        charges = {s.emotion_type.value: s.intensity for s in states}

        # 2. Memory encoding with emotional associations
        self.memory.record_event(
            event,
            importance=event.importance,
            emotional_valence=impact,
            emotional_charges=charges,
        )

        # 3. Personality adaptation (for significant life events >= 0.65 importance)
        if event.importance >= 0.65:
            self.personality.apply_experience(event, emotional_impact=impact)

        # 4. Extract reusable semantic knowledge
        self.learning.extract_knowledge_from_event(event, self.memory)

        # 5. Cognitive reflection on salient events (Cognitive LOD: importance >= 0.65)
        if event.importance >= 0.65:
            self.metacognition.reflect_on_outcome(
                target_event=event.event_type.value,
                action_attempted=event.event_type.value,
                motivating_reason="environmental_or_social_experience",
                actual_outcome=str(event.data),
                was_successful=(impact >= 0),
                epistemic=self.epistemic,
                tick=event.tick,
            )

    def update(
        self,
        tick: Tick,
        clock: SimulationClock,
        event_bus: EventBus,
        location_registry: LocationRegistry,
        activity_catalog: ActivityCatalog,
        social_engine: SocialEngine,
        nearby_humans: list[HumanID],
    ) -> None:
        """Main per-tick update loop for this individual."""
        # Natural emotional decay with individual regulation
        self.emotions.update(tick)

        # Personality drift towards baseline and stress relief
        self.personality.update(tick, events=[])

        # -------------------------------------------------------------------
        # 1. If currently executing an activity, advance it
        # -------------------------------------------------------------------
        if self.physical_state.current_activity is not None and self.physical_state.activity_ticks_remaining > 0:
            act_type = self.physical_state.current_activity
            self.physical_state.activity_ticks_remaining -= 1

            # Apply per-tick effects
            defn = activity_catalog.get(act_type)
            eff = defn.effects_per_tick

            self.physical_state.energy = max(0.0, min(1.0, self.physical_state.energy + eff.energy_delta))
            self.physical_state.hunger = max(0.0, min(1.0, self.physical_state.hunger + eff.hunger_delta))
            self.physical_state.money = max(0.0, self.physical_state.money + eff.money_delta)

            # Skill practice if activity grants it
            if eff.skill_category:
                skill_id = f"skill_{eff.skill_category.value}"
                self.learning.practice_skill(skill_id, self.memory, duration_ticks=1, current_tick=tick)

            # Social interactions if socializing with nearby humans
            if act_type == ActivityType.SOCIALIZE and nearby_humans:
                target_human = nearby_humans[0]
                social_engine.record_interaction(
                    self.uid,
                    target_human,
                    tick,
                    positive=True,
                    intensity=0.3,
                    interaction_type="socialize",
                )

            # Check if activity finished
            if self.physical_state.activity_ticks_remaining <= 0:
                completed_act = self.physical_state.current_activity
                self.physical_state.current_activity = None

                # Advance matching goals in autonomy lifecycle
                for goal in self.autonomy.get_active_goals():
                    if goal.category == "biological":
                        if completed_act in (ActivityType.EAT, ActivityType.COOK) and goal.need_type == NeedType.HUNGER:
                            goal.advance(0.50)
                        elif completed_act in (ActivityType.SLEEP, ActivityType.REST) and goal.need_type == NeedType.REST:
                            goal.advance(0.50)
                    elif goal.category == "financial" and completed_act == ActivityType.WORK:
                        goal.advance(0.35)
                    elif goal.category == "skill" and completed_act == ActivityType.STUDY:
                        goal.advance(0.35)
                    elif goal.category == "social" and completed_act == ActivityType.SOCIALIZE:
                        goal.advance(0.40)

                    if goal.status == "completed":
                        event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.GOAL_COMPLETED,
                                tick=tick,
                                source_human_id=self.uid,
                                location_id=self.physical_state.current_location_id,
                                data={"goal_id": str(goal.goal_id), "description": goal.description},
                                importance=0.65,
                            )
                        )

                # Emit completion event
                evt = SimulationEvent(
                    event_type=EventType.ACTIVITY_COMPLETED,
                    tick=tick,
                    source_human_id=self.uid,
                    location_id=self.physical_state.current_location_id,
                    data={"activity": completed_act.value if completed_act else "none"},
                    importance=0.2,
                )
                event_bus.emit(evt)
            return

        # -------------------------------------------------------------------
        # 2. No active activity: apply baseline biological degradation
        # -------------------------------------------------------------------
        self.physical_state.update(clock.config.tick_duration_minutes)

        # -------------------------------------------------------------------
        # 3. Autonomous Goal Generation & Lifecycle Adaptation
        # -------------------------------------------------------------------
        needs = self.physical_state.get_needs()
        self.autonomy.generate_goals_from_needs(
            needs=needs,
            personality=self.personality,
            current_tick=tick,
            money=self.physical_state.money,
            skills=self.memory.procedural.get_all_skills(),
            emotions=self.emotions,
        )
        self.autonomy.evaluate_and_adapt_goals(self.personality, self.emotions, tick)
        self.autonomy.cleanup_completed_or_stale(tick)

        # -------------------------------------------------------------------
        # 4. Deliberation and Decision Making
        # -------------------------------------------------------------------
        current_loc = (
            location_registry.get_optional(self.physical_state.current_location_id)
            if self.physical_state.current_location_id
            else None
        )
        available_acts = current_loc.available_activities if current_loc else [ActivityType.REST]

        context = DecisionContext(
            current_location_id=self.physical_state.current_location_id,
            available_activities=available_acts,
            current_needs=needs,
            current_energy=self.physical_state.energy,
            current_hunger=self.physical_state.hunger,
            current_money=self.physical_state.money,
            is_daytime=clock.is_daytime,
            hour_int=clock.current_hour_int,
            active_goals=self.autonomy.get_active_goals(),
            nearby_humans=nearby_humans,
            home_location_id=self.physical_state.home_location_id,
            work_location_id=self.physical_state.work_location_id,
        )

        chosen = self.decision.decide(
            context=context,
            personality=self.personality,
            emotions=self.emotions,
            memory=self.memory,
            rng=self._rng,
            brain=getattr(self, "brain", None),
        )

        # -------------------------------------------------------------------
        # 5. Execute Decision (Travel or Activity Initiation)
        # -------------------------------------------------------------------
        target_loc_id = chosen.target_location_id or self.physical_state.current_location_id

        # If chosen action requires being at another location, initiate TRAVEL first
        if target_loc_id and target_loc_id != self.physical_state.current_location_id:
            old_loc = self.physical_state.current_location_id
            self.physical_state.current_activity = ActivityType.TRAVEL
            self.physical_state.activity_ticks_remaining = 1
            self.physical_state.current_location_id = target_loc_id

            event_bus.emit(
                SimulationEvent(
                    event_type=EventType.ARRIVED_AT_LOCATION,
                    tick=tick,
                    source_human_id=self.uid,
                    location_id=target_loc_id,
                    data={"from": old_loc, "to": target_loc_id},
                    importance=0.15,
                )
            )
        else:
            # Begin activity at current location
            act_type = chosen.action_type
            defn = activity_catalog.get(act_type)

            # Cap duration reasonably
            duration = min(8, defn.default_duration_ticks)
            self.physical_state.current_activity = act_type
            self.physical_state.activity_ticks_remaining = duration

            event_bus.emit(
                SimulationEvent(
                    event_type=EventType.ACTIVITY_STARTED,
                    tick=tick,
                    source_human_id=self.uid,
                    location_id=self.physical_state.current_location_id,
                    data={"activity": act_type.value, "reason": chosen.reasoning},
                    importance=0.2,
                )
            )

        # -------------------------------------------------------------------
        # 6. Periodic Memory Consolidation (Once every 96 ticks / 1 simulated day)
        # -------------------------------------------------------------------
        if clock.tick_of_day == 0 and tick > 0:
            self.memory.consolidate(tick)

    def get_status_summary(self) -> dict[str, Any]:
        """Compact status overview for inspection and visualization."""
        primary_goal = self.autonomy.current_primary_goal()
        return {
            "uid": str(self.uid),
            "serial": self.identity.serial,
            "name": self.name,
            "age": self.demographics.age,
            "occupation": self.demographics.occupation,
            "energy": round(self.physical_state.energy, 2),
            "hunger": round(self.physical_state.hunger, 2),
            "money": round(self.physical_state.money, 2),
            "location": self.physical_state.current_location_id,
            "activity": self.physical_state.current_activity.value if self.physical_state.current_activity else "idle",
            "mood": round(self.emotions.get_mood(), 2),
            "dominant_emotion": (
                self.emotions.profile.get_dominant_emotion().value
                if hasattr(self.emotions, "profile") and self.emotions.profile.get_dominant_emotion() is not None
                else "quiescent"
            ),
            "primary_goal": primary_goal.description if primary_goal else "None",
            "memory_items": self.memory.episodic.count,
        }
