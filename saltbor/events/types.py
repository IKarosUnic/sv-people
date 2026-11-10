"""Event type definitions for the Saltbor simulation."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from saltbor.core.types import EventCategory, EventID, HumanID, LocationID, Tick


class EventType(enum.Enum):
    """Catalog of simulation event types."""

    # --- Social ---
    FRIENDSHIP_CREATED = "friendship_created"
    FRIENDSHIP_ENDED = "friendship_ended"
    RELATIONSHIP_ENDED = "relationship_ended"
    TRUST_INCREASED = "trust_increased"
    TRUST_BROKEN = "trust_broken"
    RELATIONSHIP_CHANGED = "relationship_changed"
    CONVERSATION_HELD = "conversation_held"
    CONFLICT_OCCURRED = "conflict_occurred"
    CONFLICT_RESOLVED = "conflict_resolved"
    RECONCILIATION_ACHIEVED = "reconciliation_achieved"
    COOPERATION_OCCURRED = "cooperation_occurred"
    SOCIAL_REJECTION = "social_rejection"
    GROUP_JOINED = "group_joined"
    GROUP_LEFT = "group_left"

    # --- Economic ---
    JOB_STARTED = "job_started"
    JOB_LOST = "job_lost"
    JOB_PROMOTION = "job_promotion"
    MONEY_EARNED = "money_earned"
    MONEY_SPENT = "money_spent"
    FINANCIAL_LOSS = "financial_loss"
    PURCHASE_MADE = "purchase_made"

    # --- Personal ---
    GOAL_CREATED = "goal_created"
    GOAL_COMPLETED = "goal_completed"
    GOAL_ABANDONED = "goal_abandoned"
    GOAL_MODIFIED = "goal_modified"
    GOAL_PROCRASTINATED = "goal_procrastinated"
    FAILED_ATTEMPT = "failed_attempt"
    NEED_SATISFIED = "need_satisfied"
    NEED_CRITICAL = "need_critical"
    EMOTIONAL_SHIFT = "emotional_shift"
    PERSONALITY_DRIFT = "personality_drift"
    SELF_REFLECTION = "self_reflection"

    # --- Cognitive ---
    SKILL_GAINED = "skill_gained"
    SKILL_ACQUIRED = "skill_acquired"
    SKILL_IMPROVED = "skill_improved"
    SKILL_DECAYED = "skill_decayed"
    KNOWLEDGE_ACQUIRED = "knowledge_acquired"
    MEMORY_FORMED = "memory_formed"
    MEMORY_FORGOTTEN = "memory_forgotten"
    INSIGHT_GAINED = "insight_gained"
    DECISION_MADE = "decision_made"

    # --- Environmental ---
    ARRIVED_AT_LOCATION = "arrived_at_location"
    LEFT_LOCATION = "left_location"
    ACTIVITY_STARTED = "activity_started"
    ACTIVITY_COMPLETED = "activity_completed"
    NEW_OPPORTUNITY = "new_opportunity"
    ACHIEVEMENT = "achievement"
    PERSONAL_ACHIEVEMENT = "personal_achievement"

    # --- System ---
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PAUSED = "simulation_paused"
    DAY_STARTED = "day_started"
    DAY_ENDED = "day_ended"
    CHECKPOINT_SAVED = "checkpoint_saved"

    # --- Biological Lifecycle (Phase 0.4) ---
    PREGNANCY_STARTED = "pregnancy_started"
    BIRTH = "birth"
    DEATH = "death"
    GRIEF_EXPERIENCED = "grief_experienced"
    STAGE_TRANSITION = "stage_transition"

    # --- Economy (Phase 0.4) ---
    TRADE_COMPLETED = "trade_completed"
    PRODUCTION_COMPLETED = "production_completed"
    SHORTAGE_DETECTED = "shortage_detected"

    # --- Social & Institutional (Phase 0.4) ---
    RUMOR_SPREAD = "rumor_spread"
    PROPOSAL_VOTED = "proposal_voted"
    ENCOUNTER_OCCURRED = "encounter_occurred"


# Map each EventType to its category
EVENT_CATEGORIES: dict[EventType, EventCategory] = {
    EventType.FRIENDSHIP_CREATED: EventCategory.SOCIAL,
    EventType.FRIENDSHIP_ENDED: EventCategory.SOCIAL,
    EventType.RELATIONSHIP_ENDED: EventCategory.SOCIAL,
    EventType.TRUST_INCREASED: EventCategory.SOCIAL,
    EventType.TRUST_BROKEN: EventCategory.SOCIAL,
    EventType.RELATIONSHIP_CHANGED: EventCategory.SOCIAL,
    EventType.CONVERSATION_HELD: EventCategory.SOCIAL,
    EventType.CONFLICT_OCCURRED: EventCategory.SOCIAL,
    EventType.CONFLICT_RESOLVED: EventCategory.SOCIAL,
    EventType.RECONCILIATION_ACHIEVED: EventCategory.SOCIAL,
    EventType.COOPERATION_OCCURRED: EventCategory.SOCIAL,
    EventType.SOCIAL_REJECTION: EventCategory.SOCIAL,
    EventType.GROUP_JOINED: EventCategory.SOCIAL,
    EventType.GROUP_LEFT: EventCategory.SOCIAL,
    EventType.JOB_STARTED: EventCategory.ECONOMIC,
    EventType.JOB_LOST: EventCategory.ECONOMIC,
    EventType.JOB_PROMOTION: EventCategory.ECONOMIC,
    EventType.MONEY_EARNED: EventCategory.ECONOMIC,
    EventType.MONEY_SPENT: EventCategory.ECONOMIC,
    EventType.FINANCIAL_LOSS: EventCategory.ECONOMIC,
    EventType.PURCHASE_MADE: EventCategory.ECONOMIC,
    EventType.GOAL_CREATED: EventCategory.PERSONAL,
    EventType.GOAL_COMPLETED: EventCategory.PERSONAL,
    EventType.GOAL_ABANDONED: EventCategory.PERSONAL,
    EventType.GOAL_MODIFIED: EventCategory.PERSONAL,
    EventType.GOAL_PROCRASTINATED: EventCategory.PERSONAL,
    EventType.FAILED_ATTEMPT: EventCategory.PERSONAL,
    EventType.NEED_SATISFIED: EventCategory.PERSONAL,
    EventType.NEED_CRITICAL: EventCategory.PERSONAL,
    EventType.EMOTIONAL_SHIFT: EventCategory.PERSONAL,
    EventType.PERSONALITY_DRIFT: EventCategory.PERSONAL,
    EventType.SELF_REFLECTION: EventCategory.PERSONAL,
    EventType.SKILL_GAINED: EventCategory.COGNITIVE,
    EventType.SKILL_ACQUIRED: EventCategory.COGNITIVE,
    EventType.SKILL_IMPROVED: EventCategory.COGNITIVE,
    EventType.SKILL_DECAYED: EventCategory.COGNITIVE,
    EventType.KNOWLEDGE_ACQUIRED: EventCategory.COGNITIVE,
    EventType.MEMORY_FORMED: EventCategory.COGNITIVE,
    EventType.MEMORY_FORGOTTEN: EventCategory.COGNITIVE,
    EventType.INSIGHT_GAINED: EventCategory.COGNITIVE,
    EventType.DECISION_MADE: EventCategory.COGNITIVE,
    EventType.ARRIVED_AT_LOCATION: EventCategory.ENVIRONMENTAL,
    EventType.LEFT_LOCATION: EventCategory.ENVIRONMENTAL,
    EventType.ACTIVITY_STARTED: EventCategory.ENVIRONMENTAL,
    EventType.ACTIVITY_COMPLETED: EventCategory.ENVIRONMENTAL,
    EventType.NEW_OPPORTUNITY: EventCategory.ENVIRONMENTAL,
    EventType.ACHIEVEMENT: EventCategory.ACHIEVEMENT,
    EventType.PERSONAL_ACHIEVEMENT: EventCategory.ACHIEVEMENT,
    EventType.PREGNANCY_STARTED: EventCategory.PERSONAL,
    EventType.BIRTH: EventCategory.PERSONAL,
    EventType.DEATH: EventCategory.PERSONAL,
    EventType.GRIEF_EXPERIENCED: EventCategory.PERSONAL,
    EventType.STAGE_TRANSITION: EventCategory.PERSONAL,
    EventType.TRADE_COMPLETED: EventCategory.ECONOMIC,
    EventType.PRODUCTION_COMPLETED: EventCategory.ECONOMIC,
    EventType.SHORTAGE_DETECTED: EventCategory.ECONOMIC,
    EventType.RUMOR_SPREAD: EventCategory.SOCIAL,
    EventType.PROPOSAL_VOTED: EventCategory.SOCIAL,
    EventType.ENCOUNTER_OCCURRED: EventCategory.SOCIAL,
}


@dataclass(frozen=True)
class SimulationEvent:
    """An immutable event that occurred in the simulation.

    Events are the primary communication mechanism between modules.
    They are emitted by any system and consumed by handlers that react to them.
    """

    event_id: EventID = field(default_factory=uuid.uuid4)
    event_type: EventType = EventType.SIMULATION_STARTED
    tick: Tick = 0
    timestamp: datetime = field(default_factory=datetime.now)

    # Participants
    source_human_id: Optional[HumanID] = None
    target_human_id: Optional[HumanID] = None
    location_id: Optional[LocationID] = None

    # Payload — flexible key-value data specific to the event type
    data: dict[str, Any] = field(default_factory=dict)

    # Importance for memory formation (0.0 = trivial, 1.0 = life-changing)
    importance: float = 0.5

    # Causal provenance / trace
    cause_event_id: Optional[EventID] = None

    @property
    def category(self) -> EventCategory:
        return EVENT_CATEGORIES.get(self.event_type, EventCategory.PERSONAL)

    def involves(self, human_id: HumanID) -> bool:
        """Check whether a given human is involved in this event."""
        return human_id in (self.source_human_id, self.target_human_id)

    def __str__(self) -> str:
        return (
            f"Event({self.event_type.value}, tick={self.tick}, "
            f"importance={self.importance:.2f})"
        )
