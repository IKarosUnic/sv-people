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

    # --- Psychological realism (Phase 1.7) ---
    APPRAISAL_FORMED = "appraisal_formed"
    COPING_STRATEGY_USED = "coping_strategy_used"
    COPING_OUTCOME_RECORDED = "coping_outcome_recorded"
    PSYCHOLOGICAL_CRISIS_STARTED = "psychological_crisis_started"
    PSYCHOLOGICAL_CRISIS_RECOVERED = "psychological_crisis_recovered"
    PSYCHOLOGICAL_RELAPSE = "psychological_relapse"
    SOCIAL_SUPPORT_REQUESTED = "social_support_requested"
    SOCIAL_SUPPORT_GRANTED = "social_support_granted"
    SOCIAL_SUPPORT_REFUSED = "social_support_refused"

    # --- Perception & Epistemic (Phase 1.6) ---
    PERCEPTION_OBTAINED = "perception_obtained"
    HAZARD_PERCEIVED = "hazard_perceived"
    MISUNDERSTANDING_OCCURRED = "misunderstanding_occurred"
    INFORMATION_REPORTED = "information_reported"
    IDENTITY_RECOGNISED = "identity_recognised"

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

    # --- Phase 1.4 Civilization Integration Events ---
    COMMUNITY_MEETING_HELD = "community_meeting_held"
    COMMUNITY_PROJECT_PROPOSED = "community_project_proposed"
    FAENA_COMPLETED = "faena_completed"
    CUCHUBAL_TURN_EXECUTED = "cuchubal_turn_executed"
    DISPUTE_FILED = "dispute_filed"
    HEARING_HELD = "hearing_held"
    VERDICT_RENDERED = "verdict_rendered"
    RESTITUTION_ENFORCED = "restitution_enforced"
    COMMERCE_TRANSACTION = "commerce_transaction"
    FIADO_CREDIT_GRANTED = "fiado_credit_granted"
    FIADO_CREDIT_SETTLED = "fiado_credit_settled"
    REMITTANCE_RECEIVED = "remittance_received"
    APPRENTICESHIP_STARTED = "apprenticeship_started"
    APPRENTICESHIP_GRADUATED = "apprenticeship_graduated"
    SCIENTIFIC_EXPERIMENT_CONDUCTED = "scientific_experiment_conducted"
    HYPOTHESIS_CONFIRMED = "hypothesis_confirmed"
    HYPOTHESIS_REFUTED = "hypothesis_refuted"
    DIALOGUE_OCCURRED = "dialogue_occurred"
    SCENARIO_PROFILE_LOADED = "scenario_profile_loaded"
    INTERVENTION_EXECUTED = "intervention_executed"

    # --- Phase 1.5 Everyday Life, Labor Market, Housing & Socioeconomic Events ---
    WINDOW_SHOPPING_DONE = "window_shopping_done"
    STORE_BROWSED = "store_browsed"
    PRICES_COMPARED = "prices_compared"
    GOODS_PURCHASED = "goods_purchased"
    DINED_OUT = "dined_out"
    ENTERTAINMENT_ATTENDED = "entertainment_attended"
    PARK_VISITED = "park_visited"
    FRIEND_VISITED = "friend_visited"
    RELATIVE_VISITED = "relative_visited"
    EVENT_ATTENDED = "event_attended"
    JOB_SEARCHED = "job_searched"
    JOB_APPLIED = "job_applied"
    INTERVIEW_ATTENDED = "interview_attended"
    SALARY_NEGOTIATED = "salary_negotiated"
    JOB_OFFER_ACCEPTED = "job_offer_accepted"
    JOB_OFFER_REJECTED = "job_offer_rejected"
    JOB_RESIGNED = "job_resigned"
    BUSINESS_STARTED = "business_started"
    BUSINESS_CLOSED = "business_closed"
    HOUSING_SEARCHED = "housing_searched"
    HOUSING_LEASED = "housing_leased"
    SHELTER_ENTERED = "shelter_entered"
    SHELTER_LEFT = "shelter_left"
    EVICTION_OCCURRED = "eviction_occurred"
    ASSISTANCE_REQUESTED = "assistance_requested"
    ASSISTANCE_OFFERED = "assistance_offered"
    ASSISTANCE_REJECTED = "assistance_rejected"
    HOBBY_PRACTICED = "hobby_practiced"
    SPORT_PLAYED = "sport_played"
    LOCATION_EXPLORED = "location_explored"
    SOCIAL_INVITATION_SENT = "social_invitation_sent"
    SOCIAL_INVITATION_ACCEPTED = "social_invitation_accepted"
    SOCIAL_INVITATION_REJECTED = "social_invitation_rejected"
    HOUSEHOLD_EXPENSE_CHARGED = "household_expense_charged"
    RENT_PAID = "rent_paid"

    # --- Phase 1.5 Extension: Health, Accidents, Romance, Family & Environment ---
    ILLNESS_CONTRACTED = "illness_contracted"
    ILLNESS_RECOVERED = "illness_recovered"
    HEALTH_TREATMENT_SEEKED = "health_treatment_seeked"
    HEALTH_TREATMENT_RECEIVED = "health_treatment_received"
    HEALTH_COMPLICATION = "health_complication"
    DISEASE_TRANSMITTED = "disease_transmitted"
    ACCIDENT_OCCURRED = "accident_occurred"
    DISASTER_OCCURRED = "disaster_occurred"
    INJURY_SUSTAINED = "injury_sustained"
    PROPERTY_DAMAGED = "property_damaged"
    DISASTER_RECOVERY_STARTED = "disaster_recovery_started"
    COMMUNITY_AID_DELIVERED = "community_aid_delivered"
    ROMANTIC_ATTRACTION_FORMED = "romantic_attraction_formed"
    DATING_STARTED = "dating_started"
    PARTNERSHIP_FORMED = "partnership_formed"
    MARRIAGE_CELEBRATED = "marriage_celebrated"
    JEALOUSY_EXPERIENCED = "jealousy_experienced"
    INFIDELITY_COMMITTED = "infidelity_committed"
    INFIDELITY_DISCOVERED = "infidelity_discovered"
    RELATIONSHIP_SEPARATED = "relationship_separated"
    DIVORCE_FINALIZED = "divorce_finalized"
    ROMANCE_RECONCILED = "romance_reconciled"
    ROMANTIC_CONFLICT = "romantic_conflict"
    UNREQUITED_LOVE = "unrequited_love"
    HEARTBREAK_EXPERIENCED = "heartbreak_experienced"
    HEARTBREAK_HEALED = "heartbreak_healed"
    CHILDCARE_PROVIDED = "childcare_provided"
    ELDER_CARE_PROVIDED = "elder_care_provided"
    BEREAVEMENT_EXPERIENCED = "bereavement_experienced"
    INHERITANCE_PASSED = "inheritance_passed"
    WATER_SOURCE_POLLUTED = "water_source_polluted"
    WATER_SOURCE_CLEANED = "water_source_cleaned"
    INFRASTRUCTURE_DAMAGED = "infrastructure_damaged"
    ROAD_BLOCKED = "road_blocked"
    ROAD_REOPENED = "road_reopened"
    ENVIRONMENTAL_DEGRADATION = "environmental_degradation"
    RESOURCES_DEPLETED = "resources_depleted"


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
    EventType.COMMUNITY_MEETING_HELD: EventCategory.SOCIAL,
    EventType.COMMUNITY_PROJECT_PROPOSED: EventCategory.SOCIAL,
    EventType.FAENA_COMPLETED: EventCategory.SOCIAL,
    EventType.CUCHUBAL_TURN_EXECUTED: EventCategory.ECONOMIC,
    EventType.DISPUTE_FILED: EventCategory.SOCIAL,
    EventType.HEARING_HELD: EventCategory.SOCIAL,
    EventType.VERDICT_RENDERED: EventCategory.SOCIAL,
    EventType.RESTITUTION_ENFORCED: EventCategory.ECONOMIC,
    EventType.COMMERCE_TRANSACTION: EventCategory.ECONOMIC,
    EventType.FIADO_CREDIT_GRANTED: EventCategory.ECONOMIC,
    EventType.FIADO_CREDIT_SETTLED: EventCategory.ECONOMIC,
    EventType.REMITTANCE_RECEIVED: EventCategory.ECONOMIC,
    EventType.APPRENTICESHIP_STARTED: EventCategory.COGNITIVE,
    EventType.APPRENTICESHIP_GRADUATED: EventCategory.COGNITIVE,
    EventType.SCIENTIFIC_EXPERIMENT_CONDUCTED: EventCategory.COGNITIVE,
    EventType.HYPOTHESIS_CONFIRMED: EventCategory.COGNITIVE,
    EventType.HYPOTHESIS_REFUTED: EventCategory.COGNITIVE,
    EventType.DIALOGUE_OCCURRED: EventCategory.SOCIAL,
    EventType.SCENARIO_PROFILE_LOADED: EventCategory.ENVIRONMENTAL,
    EventType.INTERVENTION_EXECUTED: EventCategory.ENVIRONMENTAL,

    # Phase 1.5 Event Mappings
    EventType.WINDOW_SHOPPING_DONE: EventCategory.ECONOMIC,
    EventType.STORE_BROWSED: EventCategory.ECONOMIC,
    EventType.PRICES_COMPARED: EventCategory.ECONOMIC,
    EventType.GOODS_PURCHASED: EventCategory.ECONOMIC,
    EventType.DINED_OUT: EventCategory.PERSONAL,
    EventType.ENTERTAINMENT_ATTENDED: EventCategory.PERSONAL,
    EventType.PARK_VISITED: EventCategory.PERSONAL,
    EventType.FRIEND_VISITED: EventCategory.SOCIAL,
    EventType.RELATIVE_VISITED: EventCategory.SOCIAL,
    EventType.EVENT_ATTENDED: EventCategory.SOCIAL,
    EventType.JOB_SEARCHED: EventCategory.ECONOMIC,
    EventType.JOB_APPLIED: EventCategory.ECONOMIC,
    EventType.INTERVIEW_ATTENDED: EventCategory.ECONOMIC,
    EventType.SALARY_NEGOTIATED: EventCategory.ECONOMIC,
    EventType.JOB_OFFER_ACCEPTED: EventCategory.ECONOMIC,
    EventType.JOB_OFFER_REJECTED: EventCategory.ECONOMIC,
    EventType.JOB_RESIGNED: EventCategory.ECONOMIC,
    EventType.BUSINESS_STARTED: EventCategory.ECONOMIC,
    EventType.BUSINESS_CLOSED: EventCategory.ECONOMIC,
    EventType.HOUSING_SEARCHED: EventCategory.ECONOMIC,
    EventType.HOUSING_LEASED: EventCategory.ECONOMIC,
    EventType.SHELTER_ENTERED: EventCategory.PERSONAL,
    EventType.SHELTER_LEFT: EventCategory.PERSONAL,
    EventType.EVICTION_OCCURRED: EventCategory.ECONOMIC,
    EventType.ASSISTANCE_REQUESTED: EventCategory.SOCIAL,
    EventType.ASSISTANCE_OFFERED: EventCategory.SOCIAL,
    EventType.ASSISTANCE_REJECTED: EventCategory.SOCIAL,
    EventType.HOBBY_PRACTICED: EventCategory.PERSONAL,
    EventType.SPORT_PLAYED: EventCategory.PERSONAL,
    EventType.LOCATION_EXPLORED: EventCategory.PERSONAL,
    EventType.SOCIAL_INVITATION_SENT: EventCategory.SOCIAL,
    EventType.SOCIAL_INVITATION_ACCEPTED: EventCategory.SOCIAL,
    EventType.SOCIAL_INVITATION_REJECTED: EventCategory.SOCIAL,
    EventType.HOUSEHOLD_EXPENSE_CHARGED: EventCategory.ECONOMIC,
    EventType.RENT_PAID: EventCategory.ECONOMIC,
    # Phase 1.5 Extension Categories
    EventType.ILLNESS_CONTRACTED: EventCategory.PERSONAL,
    EventType.ILLNESS_RECOVERED: EventCategory.PERSONAL,
    EventType.HEALTH_TREATMENT_SEEKED: EventCategory.PERSONAL,
    EventType.HEALTH_TREATMENT_RECEIVED: EventCategory.PERSONAL,
    EventType.HEALTH_COMPLICATION: EventCategory.PERSONAL,
    EventType.DISEASE_TRANSMITTED: EventCategory.SOCIAL,
    EventType.ACCIDENT_OCCURRED: EventCategory.ENVIRONMENTAL,
    EventType.DISASTER_OCCURRED: EventCategory.ENVIRONMENTAL,
    EventType.INJURY_SUSTAINED: EventCategory.PERSONAL,
    EventType.PROPERTY_DAMAGED: EventCategory.ECONOMIC,
    EventType.DISASTER_RECOVERY_STARTED: EventCategory.SOCIAL,
    EventType.COMMUNITY_AID_DELIVERED: EventCategory.SOCIAL,
    EventType.ROMANTIC_ATTRACTION_FORMED: EventCategory.SOCIAL,
    EventType.DATING_STARTED: EventCategory.SOCIAL,
    EventType.PARTNERSHIP_FORMED: EventCategory.SOCIAL,
    EventType.MARRIAGE_CELEBRATED: EventCategory.SOCIAL,
    EventType.JEALOUSY_EXPERIENCED: EventCategory.PERSONAL,
    EventType.INFIDELITY_COMMITTED: EventCategory.SOCIAL,
    EventType.INFIDELITY_DISCOVERED: EventCategory.SOCIAL,
    EventType.RELATIONSHIP_SEPARATED: EventCategory.SOCIAL,
    EventType.DIVORCE_FINALIZED: EventCategory.SOCIAL,
    EventType.APPRAISAL_FORMED: EventCategory.PERSONAL,
    EventType.COPING_STRATEGY_USED: EventCategory.PERSONAL,
    EventType.COPING_OUTCOME_RECORDED: EventCategory.PERSONAL,
    EventType.PSYCHOLOGICAL_CRISIS_STARTED: EventCategory.PERSONAL,
    EventType.PSYCHOLOGICAL_CRISIS_RECOVERED: EventCategory.PERSONAL,
    EventType.PSYCHOLOGICAL_RELAPSE: EventCategory.PERSONAL,
    EventType.SOCIAL_SUPPORT_REQUESTED: EventCategory.SOCIAL,
    EventType.SOCIAL_SUPPORT_GRANTED: EventCategory.SOCIAL,
    EventType.SOCIAL_SUPPORT_REFUSED: EventCategory.SOCIAL,
    EventType.PERCEPTION_OBTAINED: EventCategory.COGNITIVE,
    EventType.HAZARD_PERCEIVED: EventCategory.COGNITIVE,
    EventType.MISUNDERSTANDING_OCCURRED: EventCategory.COGNITIVE,
    EventType.INFORMATION_REPORTED: EventCategory.SOCIAL,
    EventType.IDENTITY_RECOGNISED: EventCategory.COGNITIVE,
    EventType.ROMANCE_RECONCILED: EventCategory.SOCIAL,
    EventType.ROMANTIC_CONFLICT: EventCategory.SOCIAL,
    EventType.UNREQUITED_LOVE: EventCategory.PERSONAL,
    EventType.HEARTBREAK_EXPERIENCED: EventCategory.PERSONAL,
    EventType.HEARTBREAK_HEALED: EventCategory.PERSONAL,
    EventType.CHILDCARE_PROVIDED: EventCategory.SOCIAL,
    EventType.ELDER_CARE_PROVIDED: EventCategory.SOCIAL,
    EventType.BEREAVEMENT_EXPERIENCED: EventCategory.PERSONAL,
    EventType.INHERITANCE_PASSED: EventCategory.ECONOMIC,
    EventType.WATER_SOURCE_POLLUTED: EventCategory.ENVIRONMENTAL,
    EventType.WATER_SOURCE_CLEANED: EventCategory.ENVIRONMENTAL,
    EventType.INFRASTRUCTURE_DAMAGED: EventCategory.ENVIRONMENTAL,
    EventType.ROAD_BLOCKED: EventCategory.ENVIRONMENTAL,
    EventType.ROAD_REOPENED: EventCategory.ENVIRONMENTAL,
    EventType.ENVIRONMENTAL_DEGRADATION: EventCategory.ENVIRONMENTAL,
    EventType.RESOURCES_DEPLETED: EventCategory.ENVIRONMENTAL,
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
    coordinates: Optional[tuple[float, float]] = None

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
