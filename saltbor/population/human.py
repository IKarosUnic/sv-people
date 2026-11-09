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
from saltbor.core.clock import SimulationClock
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import ActivityType, HumanID, LocationID, NeedType, Tick
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

    @property
    def uid(self) -> HumanID:
        return self.identity.uid

    @property
    def name(self) -> str:
        return self.identity.full_name

    def receive_event(self, event: SimulationEvent, event_bus: Optional[EventBus] = None) -> None:
        """Process an incoming event impacting this individual."""
        # 1. Emotional reaction
        states = self.emotions.process_event(event, self.personality.traits)
        impact = self.emotions.get_mood()

        # 2. Memory encoding
        valence = impact
        self.memory.record_event(event, importance=event.importance, emotional_valence=valence)

        # 3. Slow personality adaptation (only for significant events)
        if event.importance >= 0.70:
            self.personality.apply_experience(event, emotional_impact=impact)

        # 4. Extract knowledge
        self.learning.extract_knowledge_from_event(event, self.memory)

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
        # Natural emotional decay
        self.emotions.update(tick)

        # Personality drift towards baseline
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
                self.learning.practice_skill(skill_id, self.memory, duration_ticks=1)

            # Social interactions if socializing with nearby humans
            if act_type == ActivityType.SOCIALIZE and nearby_humans:
                # Pick a random neighbor to converse with
                target_human = nearby_humans[0]
                social_engine.record_interaction(self.uid, target_human, tick, positive=True, intensity=0.3)

            # Check if activity finished
            if self.physical_state.activity_ticks_remaining <= 0:
                completed_act = self.physical_state.current_activity
                self.physical_state.current_activity = None

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
        # 3. Autonomous Goal Generation
        # -------------------------------------------------------------------
        needs = self.physical_state.get_needs()
        self.autonomy.generate_goals_from_needs(needs, self.personality, tick)
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
