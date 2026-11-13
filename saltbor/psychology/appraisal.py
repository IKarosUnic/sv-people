"""OCC-inspired appraisal: the same event is not the same experience.

The engine separates three things that the rest of the simulation must never
conflate:

1. the **event** (what happened, with provenance),
2. the **appraisal** (what it means for *this* individual, given goals,
   expectations, agency, control, values and relationships),
3. the **emotion** and its behavioural consequences.

The appraisal rules follow the structure of the OCC model (Ortony, Clore &
Collins, 1988): desirability of consequences, expectation, agency, certainty
and control select which emotion family is plausible.  The implementation is
native; no OCC library or FAtiMA code is copied.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from saltbor.cognition.emotions.models import EMOTION_DEFAULT_DECAY, EmotionState
from saltbor.core.types import EmotionType, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.psychology.models import AppraisalRecord, PsychologicalState, _clamp


@dataclass(frozen=True)
class EventAppraisalTemplate:
    """Structural affordances of an event type, before individual appraisal."""

    desirability: float = 0.0
    controllability: float = 0.5
    other_agency: float = 0.5       # 0 = self-caused, 1 = other-caused
    loss: float = 0.0               # irreversible loss weight
    social_visibility: float = 0.0
    relationship: float = 0.0
    value_domain: float = 0.0       # moral/value relevance
    relief: float = 0.0
    base_expectedness: float = 0.5
    stress: float = 0.0             # acute stressor weight


# Templates are structural, not emotional destinies.  Desirability only sets
# the sign; the individual's expectation, control, agency, values and history
# determine the emotion and its intensity.
EVENT_TEMPLATES: dict[EventType, EventAppraisalTemplate] = {
    # Social
    EventType.FRIENDSHIP_CREATED: EventAppraisalTemplate(0.8, 0.6, 0.3, 0.0, 0.3, 0.8, 0.2, 0.0, 0.4, 0.02),
    EventType.FRIENDSHIP_ENDED: EventAppraisalTemplate(-0.8, 0.3, 0.5, 0.5, 0.2, 0.9, 0.1, 0.0, 0.4, 0.30),
    EventType.RELATIONSHIP_ENDED: EventAppraisalTemplate(-0.95, 0.2, 0.5, 0.8, 0.3, 1.0, 0.1, 0.0, 0.4, 0.45),
    EventType.TRUST_INCREASED: EventAppraisalTemplate(0.7, 0.4, 0.6, 0.0, 0.2, 0.9, 0.3, 0.0, 0.5, 0.02),
    EventType.TRUST_BROKEN: EventAppraisalTemplate(-0.9, 0.2, 0.9, 0.6, 0.5, 0.9, 0.6, 0.0, 0.3, 0.40),
    EventType.CONFLICT_OCCURRED: EventAppraisalTemplate(-0.7, 0.4, 0.7, 0.2, 0.4, 0.7, 0.2, 0.0, 0.5, 0.30),
    EventType.CONFLICT_RESOLVED: EventAppraisalTemplate(0.7, 0.6, 0.4, 0.0, 0.2, 0.6, 0.3, 0.6, 0.6, 0.02),
    EventType.RECONCILIATION_ACHIEVED: EventAppraisalTemplate(0.9, 0.5, 0.4, 0.0, 0.2, 0.9, 0.3, 1.0, 0.4, 0.02),
    EventType.COOPERATION_OCCURRED: EventAppraisalTemplate(0.6, 0.6, 0.4, 0.0, 0.2, 0.5, 0.2, 0.0, 0.5, 0.01),
    EventType.SOCIAL_REJECTION: EventAppraisalTemplate(-0.9, 0.2, 0.85, 0.3, 0.7, 0.7, 0.5, 0.0, 0.5, 0.40),
    EventType.UNREQUITED_LOVE: EventAppraisalTemplate(-0.85, 0.2, 0.4, 0.6, 0.4, 0.9, 0.4, 0.0, 0.4, 0.35),
    EventType.HEARTBREAK_EXPERIENCED: EventAppraisalTemplate(-1.0, 0.15, 0.5, 0.9, 0.3, 1.0, 0.2, 0.0, 0.3, 0.50),
    EventType.HEARTBREAK_HEALED: EventAppraisalTemplate(0.7, 0.6, 0.2, 0.0, 0.2, 0.8, 0.2, 1.0, 0.5, 0.02),
    EventType.JEALOUSY_EXPERIENCED: EventAppraisalTemplate(-0.8, 0.3, 0.7, 0.4, 0.6, 0.9, 0.5, 0.0, 0.4, 0.35),
    EventType.INFIDELITY_DISCOVERED: EventAppraisalTemplate(-1.0, 0.2, 0.9, 0.8, 0.8, 1.0, 0.8, 0.0, 0.3, 0.55),
    EventType.ROMANTIC_CONFLICT: EventAppraisalTemplate(-0.75, 0.4, 0.7, 0.2, 0.5, 0.8, 0.3, 0.0, 0.5, 0.30),
    EventType.ROMANCE_RECONCILED: EventAppraisalTemplate(0.9, 0.5, 0.4, 0.0, 0.2, 0.9, 0.3, 1.0, 0.4, 0.02),

    # Economic
    EventType.JOB_STARTED: EventAppraisalTemplate(0.85, 0.5, 0.3, 0.0, 0.2, 0.0, 0.1, 0.4, 0.45, 0.02),
    EventType.JOB_LOST: EventAppraisalTemplate(-0.9, 0.2, 0.6, 0.6, 0.2, 0.0, 0.1, 0.0, 0.35, 0.55),
    EventType.JOB_PROMOTION: EventAppraisalTemplate(0.9, 0.6, 0.3, 0.0, 0.3, 0.0, 0.2, 0.0, 0.35, 0.02),
    EventType.JOB_RESIGNED: EventAppraisalTemplate(-0.3, 0.7, 0.2, 0.2, 0.1, 0.0, 0.0, 0.0, 0.5, 0.25),
    EventType.MONEY_EARNED: EventAppraisalTemplate(0.5, 0.6, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 0.01),
    EventType.FINANCIAL_LOSS: EventAppraisalTemplate(-0.85, 0.35, 0.3, 0.4, 0.1, 0.0, 0.0, 0.0, 0.4, 0.45),
    EventType.EVICTION_OCCURRED: EventAppraisalTemplate(-1.0, 0.15, 0.6, 0.8, 0.3, 0.0, 0.0, 0.0, 0.35, 0.60),
    EventType.SHELTER_ENTERED: EventAppraisalTemplate(-0.5, 0.4, 0.5, 0.4, 0.3, 0.0, 0.0, 0.2, 0.5, 0.30),
    EventType.FIADO_CREDIT_GRANTED: EventAppraisalTemplate(0.55, 0.5, 0.4, 0.0, 0.2, 0.2, 0.2, 0.4, 0.5, 0.02),
    EventType.ASSISTANCE_REQUESTED: EventAppraisalTemplate(-0.2, 0.5, 0.2, 0.0, 0.4, 0.3, 0.2, 0.0, 0.5, 0.15),
    EventType.ASSISTANCE_OFFERED: EventAppraisalTemplate(0.8, 0.3, 0.8, 0.0, 0.2, 0.6, 0.4, 0.7, 0.4, 0.01),
    EventType.ASSISTANCE_REJECTED: EventAppraisalTemplate(-0.8, 0.2, 0.9, 0.3, 0.5, 0.6, 0.3, 0.0, 0.4, 0.35),

    # Personal / goals
    EventType.GOAL_CREATED: EventAppraisalTemplate(0.5, 0.6, 0.2, 0.0, 0.0, 0.0, 0.1, 0.0, 0.6, 0.0),
    EventType.GOAL_COMPLETED: EventAppraisalTemplate(0.9, 0.6, 0.2, 0.0, 0.0, 0.0, 0.2, 0.0, 0.4, 0.0),
    EventType.GOAL_ABANDONED: EventAppraisalTemplate(-0.7, 0.4, 0.4, 0.4, 0.0, 0.0, 0.1, 0.0, 0.5, 0.30),
    EventType.GOAL_PROCRASTINATED: EventAppraisalTemplate(-0.5, 0.5, 0.2, 0.2, 0.0, 0.0, 0.3, 0.0, 0.6, 0.20),
    EventType.FAILED_ATTEMPT: EventAppraisalTemplate(-0.7, 0.45, 0.3, 0.3, 0.1, 0.0, 0.2, 0.0, 0.5, 0.30),
    EventType.NEED_CRITICAL: EventAppraisalTemplate(-0.85, 0.35, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0, 0.4, 0.45),
    EventType.NEED_SATISFIED: EventAppraisalTemplate(0.7, 0.5, 0.2, 0.0, 0.0, 0.0, 0.0, 0.8, 0.6, 0.0),
    EventType.ACHIEVEMENT: EventAppraisalTemplate(0.9, 0.6, 0.2, 0.0, 0.1, 0.0, 0.2, 0.0, 0.4, 0.0),
    EventType.PERSONAL_ACHIEVEMENT: EventAppraisalTemplate(0.9, 0.6, 0.2, 0.0, 0.1, 0.0, 0.3, 0.0, 0.4, 0.0),

    # Health / body
    EventType.ILLNESS_CONTRACTED: EventAppraisalTemplate(-0.9, 0.3, 0.1, 0.5, 0.1, 0.0, 0.0, 0.0, 0.35, 0.55),
    EventType.ILLNESS_RECOVERED: EventAppraisalTemplate(0.8, 0.5, 0.1, 0.0, 0.1, 0.0, 0.1, 1.0, 0.5, 0.0),
    EventType.INJURY_SUSTAINED: EventAppraisalTemplate(-0.9, 0.3, 0.3, 0.6, 0.1, 0.0, 0.0, 0.0, 0.35, 0.55),
    EventType.ACCIDENT_OCCURRED: EventAppraisalTemplate(-0.85, 0.35, 0.2, 0.5, 0.2, 0.0, 0.0, 0.0, 0.3, 0.50),
    EventType.HEALTH_TREATMENT_SEEKED: EventAppraisalTemplate(0.2, 0.7, 0.2, 0.0, 0.0, 0.0, 0.1, 0.2, 0.6, 0.05),
    EventType.HEALTH_COMPLICATION: EventAppraisalTemplate(-0.9, 0.2, 0.1, 0.6, 0.1, 0.0, 0.0, 0.0, 0.4, 0.55),
    EventType.BEREAVEMENT_EXPERIENCED: EventAppraisalTemplate(-1.0, 0.1, 0.2, 1.0, 0.5, 1.0, 0.3, 0.0, 0.2, 0.65),
    EventType.DEATH: EventAppraisalTemplate(-1.0, 0.1, 0.2, 1.0, 0.5, 1.0, 0.3, 0.0, 0.2, 0.65),

    # Environment / territory
    EventType.DISASTER_OCCURRED: EventAppraisalTemplate(-0.95, 0.15, 0.1, 0.8, 0.4, 0.0, 0.0, 0.0, 0.30, 0.60),
    EventType.PROPERTY_DAMAGED: EventAppraisalTemplate(-0.9, 0.2, 0.3, 0.7, 0.2, 0.0, 0.0, 0.0, 0.35, 0.50),
    EventType.LOCATION_EXPLORED: EventAppraisalTemplate(0.4, 0.7, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 0.0),
    EventType.ROAD_BLOCKED: EventAppraisalTemplate(-0.6, 0.2, 0.1, 0.2, 0.2, 0.0, 0.0, 0.0, 0.4, 0.25),

    # Perception / epistemic
    EventType.MISUNDERSTANDING_OCCURRED: EventAppraisalTemplate(-0.4, 0.4, 0.3, 0.1, 0.4, 0.3, 0.2, 0.0, 0.6, 0.20),
    EventType.HAZARD_PERCEIVED: EventAppraisalTemplate(-0.6, 0.4, 0.1, 0.2, 0.1, 0.0, 0.0, 0.0, 0.3, 0.30),
    EventType.PERCEPTION_OBTAINED: EventAppraisalTemplate(0.2, 0.4, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 0.0),
}


def _stable_noise(serial: Any, event_id: Any, salt: str = "") -> float:
    """Deterministic noise in [-1, 1] from stable inputs.

    Appraisal must not depend on process-level RNG state: two runs with the
    same seed and the same event must appraise it identically.
    """
    key = f"{serial}|{event_id}|{salt}".encode("utf-8")
    digest = hashlib.blake2b(key, digest_size=8).digest()
    return (int.from_bytes(digest, "big") / (2**64 - 1)) * 2.0 - 1.0


def _goal_context(human: Any) -> dict[str, float]:
    """Summarise active goal pressures without reading more than needed."""
    goals = []
    try:
        goals = human.autonomy.get_active_goals()
    except Exception:
        goals = []
    pressure: dict[str, float] = {}
    for goal in goals[:6]:
        cat = str(getattr(goal, "category", "general"))
        weight = float(getattr(goal, "priority", 0.4))
        pressure[cat] = max(pressure.get(cat, 0.0), weight)
    return pressure


def _relationship_closeness(social: Any, human: Any, target: Any) -> float:
    if social is None or target is None:
        return 0.0
    try:
        rel = social.get_relationship(human.uid, target)
        return _clamp((float(getattr(rel, "trust", 0.0)) + float(getattr(rel, "affinity", 0.0))) / 2.0)
    except Exception:
        return 0.0


class AppraisalEngine:
    """Turns an event into an individual appraisal, then into emotions."""

    def appraise(
        self,
        human: Any,
        event: SimulationEvent,
        psych: PsychologicalState,
        social: Any = None,
        tick: Optional[int] = None,
    ) -> AppraisalRecord:
        tick = int(tick if tick is not None else event.tick)
        template = EVENT_TEMPLATES.get(event.event_type)

        if template is None:
            # Fallback by event category: unknown events are not silently
            # treated as neutral, but they also cannot invent dramatic meaning.
            cat = getattr(event, "category", None)
            cat_name = getattr(cat, "value", str(cat))
            sign = -0.35 if cat_name in ("economic", "environmental") else 0.1
            template = EventAppraisalTemplate(
                desirability=sign,
                controllability=0.4,
                other_agency=0.4,
                base_expectedness=0.5,
                stress=abs(sign) * 0.5,
            )

        p = human.personality.traits
        o = p.effective_value("openness")
        c = p.effective_value("conscientiousness")
        e = p.effective_value("extraversion")
        a = p.effective_value("agreeableness")
        n = p.effective_value("neuroticism")
        risk = p.effective_value("risk_tolerance")

        # --- appraisal variables, individually constructed ---------------
        # Personal meaning can reverse the sign of an event.  Losing a job is
        # not automatically bad for someone who hated it; a separation is not
        # automatically bad for someone already ambivalent.  These modifiers
        # are explicit, bounded and recorded in the appraisal.
        desirability = template.desirability * (0.85 + 0.30 * psych.reactivity)
        prefs = getattr(human, "preferences", {}) or {}
        if event.event_type in (EventType.JOB_LOST, EventType.JOB_RESIGNED):
            satisfaction = float(prefs.get("job_satisfaction", 0.5))
            desirability *= _clamp(1.80 * satisfaction - 0.35, -1.6, 1.6)
        elif event.event_type in (EventType.RELATIONSHIP_ENDED, EventType.HEARTBREAK_EXPERIENCED):
            ambivalence = float(prefs.get("relationship_ambivalence", 0.0))
            desirability *= _clamp(1.0 - 1.55 * ambivalence, -1.5, 1.5)
        elif event.event_type in (EventType.JOB_STARTED, EventType.JOB_PROMOTION):
            satisfaction = float(prefs.get("job_satisfaction", 0.5))
            desirability *= _clamp(0.75 + 0.50 * satisfaction, 0.25, 1.25)

        goal_context = _goal_context(human)
        affected_goals = [cat for cat in goal_context if self._goal_is_affected(cat, event.event_type)]
        goal_congruence = desirability
        if affected_goals:
            goal_congruence *= 1.0 + 0.25 * max(goal_context[cat] for cat in affected_goals)

        # Expectations depend on history and current conditions, not only on
        # the event type.  A job loss is less unexpected for someone already
        # under chronic financial strain.
        expectedness = template.base_expectedness
        if event.event_type in (EventType.JOB_LOST, EventType.FINANCIAL_LOSS, EventType.EVICTION_OCCURRED):
            expectedness = _clamp(0.25 + 0.45 * psych.chronic_stress + 0.20 * psych.uncertainty)
        elif event.event_type in (EventType.ILLNESS_CONTRACTED, EventType.INJURY_SUSTAINED):
            expectedness = _clamp(0.25 + 0.35 * (1.0 - psych.health_buffer) + 0.15 * n)
        elif event.event_type in (EventType.FRIENDSHIP_CREATED, EventType.JOB_STARTED, EventType.ACHIEVEMENT):
            expectedness = _clamp(0.35 + 0.25 * psych.hope)

        # Control: objective controllability filtered through self-control,
        # material buffer and the individual's sense of agency.
        control = _clamp(
            template.controllability
            * (0.55 + 0.45 * psych.self_control)
            * (0.75 + 0.35 * psych.material_buffer)
            * (0.82 + 0.30 * psych.beliefs.get("self_efficacy", 0.5))
        )
        if template.other_agency >= 0.75:
            control *= 0.55

        agency = "self" if template.other_agency < 0.35 else (
            "other" if template.other_agency >= 0.65 else "circumstance"
        )

        certainty = _clamp(0.30 + 0.45 * (1.0 - psych.uncertainty) + 0.15 * c)
        if event.importance >= 0.7:
            certainty = _clamp(certainty + 0.05)

        personal_importance = _clamp(
            event.importance
            * (0.75 + 0.35 * psych.reactivity)
            * (1.0 + 0.40 * template.loss * psych.loss_sensitivity)
        )

        value_congruence = 0.0
        if template.value_domain > 0:
            values = getattr(p, "personal_values", {}) or {}
            security = float(values.get("security", 0.5))
            benevolence = float(values.get("benevolence", 0.5))
            tradition = float(values.get("tradition", 0.5))
            value_congruence = template.value_domain * (
                0.5 * (security - 0.5) + 0.3 * (benevolence - 0.5) + 0.2 * (tradition - 0.5)
            )

        relationship_relevance = template.relationship * _relationship_closeness(
            social, human, getattr(event, "target_human_id", None)
        )

        # --- emotion selection -------------------------------------------
        emotions: dict[str, float] = {}
        imp = max(0.0, personal_importance)
        d = _clamp(desirability, -1.0, 1.0)

        if d > 0:
            surprise = 1.0 - expectedness
            emotions[EmotionType.JOY.value] = 0.55 * d * imp * (0.55 + 0.55 * surprise)
            emotions[EmotionType.SATISFACTION.value] = 0.45 * d * imp * (0.35 + 0.65 * expectedness)
            if agency == "self":
                emotions[EmotionType.PRIDE.value] = 0.35 * d * imp * control
            if template.relief > 0:
                emotions[EmotionType.RELIEF.value] = 0.55 * template.relief * imp
            if expectedness < 0.55 and control < 0.75:
                emotions[EmotionType.HOPE.value] = 0.40 * d * imp * (1.0 - expectedness) * (1.0 - abs(value_congruence))
            if relationship_relevance > 0.2:
                emotions[EmotionType.AFFECTION.value] = 0.45 * d * imp * relationship_relevance
        elif d < 0:
            neg = -d
            loss_weight = 0.45 + 0.55 * template.loss * psych.loss_sensitivity
            emotions[EmotionType.SADNESS.value] = 0.50 * neg * imp * loss_weight * (0.55 + 0.45 * certainty)
            emotions[EmotionType.FEAR.value] = 0.45 * neg * imp * (1.0 - control) * (0.55 + 0.55 * psych.threat_sensitivity) * (1.0 - 0.45 * certainty)
            emotions[EmotionType.ANXIETY.value] = 0.45 * neg * imp * (0.45 + 0.55 * psych.uncertainty) * (1.0 - 0.35 * control)
            if agency == "other":
                blame = 0.55 + 0.45 * (1.0 - a)
                emotions[EmotionType.ANGER.value] = 0.45 * neg * imp * blame * (0.6 + 0.4 * psych.threat_sensitivity)
                if relationship_relevance > 0.25:
                    emotions[EmotionType.RESENTMENT.value] = 0.32 * neg * imp * relationship_relevance
            if expectedness > 0.5:
                emotions[EmotionType.DISAPPOINTMENT.value] = 0.42 * neg * imp * expectedness
            if control < 0.45:
                emotions[EmotionType.FRUSTRATION.value] = 0.40 * neg * imp * (1.0 - control)
            visibility = template.social_visibility
            if agency == "self" and visibility > 0.15:
                shame_gain = 0.42 * neg * imp * visibility * (0.6 + 0.4 * (1.0 - a))
                emotions[EmotionType.SHAME.value] = shame_gain
            if agency == "self" and template.value_domain > 0.2:
                emotions[EmotionType.GUILT.value] = 0.34 * neg * imp * template.value_domain * (0.5 + 0.5 * a)

            if event.event_type in (EventType.SOCIAL_REJECTION, EventType.RELATIONSHIP_ENDED, EventType.HEARTBREAK_EXPERIENCED):
                emotions[EmotionType.LONELINESS.value] = 0.45 * neg * imp * (0.6 + 0.4 * psych.social_sensitivity)
            if event.event_type in (EventType.JEALOUSY_EXPERIENCED, EventType.INFIDELITY_DISCOVERED):
                emotions[EmotionType.JEALOUSY.value] = 0.55 * neg * imp * (0.55 + 0.45 * relationship_relevance)

        # Deterministic individual scatter so two identical agents still differ
        # slightly, but reproducibly for the same identity and event.
        serial = getattr(getattr(human, "identity", None), "serial", 0)
        for key in list(emotions.keys()):
            jitter = 1.0 + 0.08 * _stable_noise(serial, event.event_id, key)
            emotions[key] = round(_clamp(emotions[key] * jitter), 4)

        emotions = {k: v for k, v in emotions.items() if v > 0.015}

        confidence = _clamp(0.35 + 0.35 * certainty + 0.20 * (1.0 - psych.uncertainty) - 0.15 * abs(value_congruence))

        narrative = self._narrative(event, agency, d, emotions, expectedness, control)

        record = AppraisalRecord(
            event_id=str(event.event_id),
            event_type=event.event_type.value,
            tick=tick,
            goal_congruence=round(goal_congruence, 4),
            desirability=round(desirability, 4),
            expectedness=round(expectedness, 4),
            agency=agency,
            certainty=round(certainty, 4),
            control=round(control, 4),
            personal_importance=round(personal_importance, 4),
            value_congruence=round(value_congruence, 4),
            relationship_relevance=round(relationship_relevance, 4),
            emotions=emotions,
            confidence=round(confidence, 4),
            narrative=narrative,
        )
        return record

    # ------------------------------------------------------------------

    @staticmethod
    def _goal_is_affected(goal_category: str, event_type: EventType) -> bool:
        mapping = {
            "financial": {
                EventType.JOB_LOST, EventType.JOB_STARTED, EventType.FINANCIAL_LOSS,
                EventType.MONEY_EARNED, EventType.JOB_PROMOTION, EventType.EVICTION_OCCURRED,
            },
            "biological": {EventType.NEED_CRITICAL, EventType.NEED_SATISFIED, EventType.ILLNESS_CONTRACTED},
            "social": {
                EventType.FRIENDSHIP_CREATED, EventType.SOCIAL_REJECTION,
                EventType.RELATIONSHIP_ENDED, EventType.RECONCILIATION_ACHIEVED,
            },
            "skill": {EventType.SKILL_IMPROVED, EventType.SKILL_ACQUIRED, EventType.FAILED_ATTEMPT},
            "community": {EventType.COMMUNITY_PROJECT_PROPOSED, EventType.FAENA_COMPLETED},
            "health": {EventType.ILLNESS_CONTRACTED, EventType.INJURY_SUSTAINED},
        }
        return event_type in mapping.get(goal_category, set())

    @staticmethod
    def _narrative(
        event: SimulationEvent,
        agency: str,
        desirability: float,
        emotions: dict[str, float],
        expectedness: float,
        control: float,
    ) -> str:
        if not emotions:
            return f"Sin reacción emocional apreciable ante {event.event_type.value}."
        strongest = max(emotions.items(), key=lambda kv: kv[1])[0]
        sign = "positivo" if desirability >= 0 else "negativo"
        agency_txt = {
            "self": "causado por mí mismo",
            "other": "causado por otra persona",
            "circumstance": "fuera de mi control directo",
        }.get(agency, agency)
        surprise = "inesperado" if expectedness < 0.4 else ("esperado" if expectedness > 0.65 else "parcialmente previsto")
        control_txt = "con margen de acción" if control > 0.55 else "con poco margen de acción"
        return (
            f"{event.event_type.value}: resultado {sign}, {agency_txt}, {surprise}, "
            f"{control_txt}; emoción dominante {strongest}."
        )


def apply_appraisal(
    human: Any,
    psych: PsychologicalState,
    record: AppraisalRecord,
    tick: int,
) -> None:
    """Write an appraisal into the emotional profile and the psych substrate.

    This is the single point where appraisal becomes emotion, so the two
    representations cannot drift apart.
    """
    profile = getattr(getattr(human, "emotions", None), "profile", None)
    if profile is None:
        return

    for name, intensity in record.emotions.items():
        try:
            etype = EmotionType(name)
        except ValueError:
            continue
        duration = int(24 + 72 * record.personal_importance)
        if etype in (EmotionType.SADNESS, EmotionType.GRIEF, EmotionType.LONELINESS):
            duration = int(duration * 1.4)
        state = EmotionState(
            emotion_type=etype,
            intensity=_clamp(float(intensity)),
            duration_remaining=max(1, duration),
            decay_rate=EMOTION_DEFAULT_DECAY.get(etype, 0.02),
        )
        profile.add_emotion(state)

    # Integrative substrate.  Negative appraisals raise acute stress in
    # proportion to how little the person can regulate or control them.
    d = record.desirability
    imp = record.personal_importance
    if d < 0:
        load = -d * imp * (0.55 + 0.55 * psych.threat_sensitivity) * (1.0 - 0.35 * psych.regulation_capacity)
        psych.add_acute_stress(load * 0.32)
        psych.fear = _clamp(psych.fear + 0.25 * load * (1.0 - 0.4 * record.control))
        psych.anxiety = _clamp(psych.anxiety + 0.22 * load * (0.5 + 0.5 * psych.uncertainty))
        psych.sadness = _clamp(psych.sadness + 0.22 * load * (1.0 - 0.3 * record.control))
        if record.agency == "other":
            psych.anger = _clamp(psych.anger + 0.20 * load * (1.0 - 0.35 * psych.regulation_capacity))
        psych.frustration = _clamp(psych.frustration + 0.18 * load * (1.0 - record.control))
        psych.hope = _clamp(psych.hope - 0.08 * load)
        psych.trust = _clamp(psych.trust - 0.05 * load * record.relationship_relevance)
    else:
        relief = d * imp
        psych.relieve(relief * 0.18)
        psych.hope = _clamp(psych.hope + 0.07 * relief)
        psych.motivation = _clamp(psych.motivation + 0.05 * relief)
        if record.relationship_relevance > 0.2:
            psych.trust = _clamp(psych.trust + 0.03 * relief * record.relationship_relevance)

    record.consequences.append(
        f"acute_stress={psych.acute_stress:.3f}; regulation={psych.self_control:.3f}"
    )
    psych.record_appraisal(record)
    psych.record_timeline(
        record_timeline_from_appraisal(record)
    )


def record_timeline_from_appraisal(record: AppraisalRecord):
    from saltbor.psychology.models import LifeEventRecord

    return LifeEventRecord(
        tick=record.tick,
        kind="event",
        summary=record.narrative,
        valence=round(record.desirability * record.personal_importance, 4),
        importance=round(record.personal_importance, 4),
        source_event_id=record.event_id,
        source="simulation",
        payload={
            "event_type": record.event_type,
            "agency": record.agency,
            "control": record.control,
            "expectedness": record.expectedness,
            "emotions": dict(record.emotions),
        },
    )
