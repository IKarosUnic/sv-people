"""Persistent psychological state for a synthetic individual.

This module is deliberately *not* a second emotion system.  It is the
integrative layer that gives the existing :class:`EmotionalProfile` a
longitudinal, causally connected substrate:

* stable individual parameters derived from Big Five + biography,
* slow state variables (chronic stress, fatigue, self-control, hope, trust,
  loneliness, uncertainty, motivation, resilience),
* appraisal records and their behavioural consequences,
* coping attempts with realised short- and long-term outcomes,
* crisis episodes with a beginning, a course, an end and a history.

All numbers are simulation constructs.  Nothing here is a clinical claim or a
diagnosis; the vocabulary (stress, anxiety, crisis) names modelled variables,
not validated medical entities.
"""

from __future__ import annotations

import math
import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from saltbor.core.types import Tick


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp with NaN protection, because a destabilised variable poisons a run."""
    if value is None or not math.isfinite(float(value)):
        return low
    return max(low, min(high, float(value)))


def _approach(current: float, target: float, rate: float, dt: float) -> float:
    """Exponential approach that cannot overshoot the target.

    ``rate`` is per simulated day.  For ``dt`` days the gap closes by
    ``1 - exp(-rate*dt)``.  This is stable for any dt, which matters because
    cognitive LOD skips ticks: a dormant agent integrates the same trajectory
    analytically instead of losing time.
    """
    if dt <= 0.0:
        return current
    if rate <= 0.0:
        return current
    factor = 1.0 - math.exp(-rate * dt)
    return current + (target - current) * factor


class CopingCategory(str, Enum):
    PROBLEM_FOCUSED = "problem_focused"
    EMOTION_FOCUSED = "emotion_focused"
    AVOIDANT = "avoidant"


class CopingStrategy(str, Enum):
    # Problem-focused
    SEEK_WORK = "seek_work"
    REQUEST_FINANCIAL_HELP = "request_financial_help"
    NEGOTIATE_DEBT = "negotiate_debt"
    ASK_FIADO = "ask_fiado"
    SEEK_COMMUNITY_SUPPORT = "seek_community_support"
    REDUCE_EXPENSES = "reduce_expenses"
    SELL_BELONGINGS = "sell_belongings"
    SEEK_MEDICAL_TREATMENT = "seek_medical_treatment"
    RESOLVE_CONFLICT = "resolve_conflict"
    LEARN_SKILL = "learn_skill"
    # Emotion-focused
    SEEK_COMPANY = "seek_company"
    TALK_TO_FAMILY = "talk_to_family"
    SEEK_CONSOLATION = "seek_consolation"
    WITHDRAW_TEMPORARILY = "withdraw_temporarily"
    REST = "rest"
    RECREATION = "recreation"
    SPIRITUAL_SUPPORT = "spiritual_support"
    EXPRESS_SADNESS = "express_sadness"
    TEMPORARY_AVOIDANCE = "temporary_avoidance"
    # Avoidant / dysregulated
    DENIAL = "denial"
    PROCRASTINATION = "procrastination"
    PROLONGED_ISOLATION = "prolonged_isolation"
    ABANDON_RESPONSIBILITIES = "abandon_responsibilities"
    AGGRESSIVE_REACTION = "aggressive_reaction"
    RASH_DECISION = "rash_decision"
    FINANCIAL_AVOIDANCE = "financial_avoidance"


class CrisisKind(str, Enum):
    ACUTE_OVERLOAD = "acute_overload"
    WITHDRAWAL = "withdrawal"
    IMPULSIVE_COLLAPSE = "impulsive_collapse"
    DISORGANIZATION = "disorganization"
    AVOIDANT_DISENGAGEMENT = "avoidant_disengagement"
    DEFENSIVE_HOSTILITY = "defensive_hostility"


class PsychLOD(int, Enum):
    FULL = 0
    ROUTINE = 1
    MACRO = 2
    DORMANT = 3


class AppraisalRecord(BaseModel):
    """OCC-style appraisal of one event as seen by one individual.

    The original event is referenced by id; this record is the individual's
    *interpretation*, which is allowed to diverge from the event payload.
    """

    appraisal_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    event_id: Optional[str] = None
    event_type: str = ""
    tick: int = 0
    goal_congruence: float = 0.0
    desirability: float = 0.0
    expectedness: float = 0.5
    agency: str = "circumstance"  # self | other | circumstance
    certainty: float = 0.5
    control: float = 0.5
    personal_importance: float = 0.5
    value_congruence: float = 0.0
    relationship_relevance: float = 0.0
    emotions: dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.5
    narrative: str = ""
    consequences: list[str] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class CopingEpisode(BaseModel):
    """One coping attempt and its *observed* outcome.

    ``short_term_relief`` is recorded at execution; ``long_term_delta`` is
    filled in when the follow-up window closes, which is what makes
    trade-offs (relief now, worse later) measurable rather than asserted.
    """

    episode_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    strategy: CopingStrategy
    category: CopingCategory
    tick: int = 0
    trigger_stress: float = 0.0
    expected_relief: float = 0.0
    short_term_relief: float = 0.0
    long_term_delta: float = 0.0
    resolved_tick: Optional[int] = None
    follow_up_tick: int = 0
    deferred_applied: bool = False
    start_chronic_stress: float = 0.0
    was_available: bool = True
    outcome_note: str = ""
    support_received: float = 0.0
    support_provider: Optional[str] = None
    cost_paid: float = 0.0


class CrisisEpisode(BaseModel):
    """A bounded episode of lost self-regulation.

    It is never a permanent label: the episode has a start, a severity
    trajectory, consequences and either a recovery or an open end.
    """

    crisis_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    kind: CrisisKind
    start_tick: int
    ended_tick: Optional[int] = None
    peak_tick: int
    peak_severity: float = 0.0
    severity: float = 0.0
    triggers: list[str] = Field(default_factory=list)
    causes: dict[str, float] = Field(default_factory=dict)
    consequences: list[str] = Field(default_factory=list)
    behaviours: list[str] = Field(default_factory=list)
    recovery_progress: float = 0.0
    is_active: bool = True
    relapsed: bool = False
    residual_vulnerability: float = 0.0

    def duration_ticks(self, current_tick: int) -> int:
        end = self.ended_tick if self.ended_tick is not None else current_tick
        return max(0, end - self.start_tick)


class LifeEventRecord(BaseModel):
    """Autobiographical timeline entry (the durable, interpreted history)."""

    record_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    tick: int = 0
    kind: str = "event"
    summary: str = ""
    valence: float = 0.0
    importance: float = 0.5
    location_id: Optional[str] = None
    related_humans: list[str] = Field(default_factory=list)
    source_event_id: Optional[str] = None
    source: str = "simulation"  # simulation | recollection | testimony
    payload: dict[str, Any] = Field(default_factory=dict)


class CopingProfile(BaseModel):
    """Learned coping preferences, not a fixed typology."""

    preferences: dict[str, float] = Field(default_factory=dict)
    attempts: dict[str, int] = Field(default_factory=dict)
    successes: dict[str, int] = Field(default_factory=dict)
    last_used: dict[str, int] = Field(default_factory=dict)

    def preference(self, strategy: CopingStrategy) -> float:
        return float(self.preferences.get(strategy.value, 0.5))

    def record(
        self,
        strategy: CopingStrategy,
        outcome: float,
        tick: int,
        learning_rate: float = 0.18,
    ) -> None:
        """Update preference toward the realised outcome (bounded EMA)."""
        key = strategy.value
        current = float(self.preferences.get(key, 0.5))
        updated = _clamp(current + learning_rate * (_clamp(outcome) - current), 0.05, 0.95)
        self.preferences[key] = round(updated, 4)
        self.attempts[key] = int(self.attempts.get(key, 0)) + 1
        self.last_used[key] = tick
        if outcome >= 0.55:
            self.successes[key] = int(self.successes.get(key, 0)) + 1


class PsychologicalState(BaseModel):
    """Integrated, persistent psychological state of one individual.

    The fields split into four groups:

    1. **Constitution** (stable): reactivity, regulation capacity, resilience,
       sensitivities.  These change only through slow biographical processes.
    2. **Slow state**: chronic stress, mental fatigue, self-control, hope,
       trust, loneliness, uncertainty, motivation, perceived support.
    3. **Acute state**: acute stress, anxiety, fear, sadness, anger, frustration.
       These are additionally represented as emotions in ``EmotionalProfile``;
       the values here are the *integrative* substrate used for causal coupling
       and are kept consistent by :class:`PsychologicalEngine`.
    4. **History**: appraisals, coping episodes, crises and the timeline.
    """

    human_uid: str

    # --- 1. constitution -------------------------------------------------
    reactivity: float = 0.5
    regulation_capacity: float = 0.5
    resilience: float = 0.5
    self_control_baseline: float = 0.55
    loss_sensitivity: float = 0.5
    threat_sensitivity: float = 0.5
    social_sensitivity: float = 0.5
    impulsivity: float = 0.5

    # --- 2. slow state ----------------------------------------------------
    chronic_stress: float = 0.08
    mental_fatigue: float = 0.10
    self_control: float = 0.60
    hope: float = 0.55
    trust: float = 0.50
    loneliness: float = 0.25
    uncertainty: float = 0.35
    motivation: float = 0.55
    perceived_support: float = 0.40
    material_buffer: float = 0.40
    health_buffer: float = 1.00

    # --- 3. acute state ---------------------------------------------------
    acute_stress: float = 0.10
    anxiety: float = 0.10
    fear: float = 0.05
    sadness: float = 0.05
    anger: float = 0.03
    frustration: float = 0.05

    # --- dynamics bookkeeping --------------------------------------------
    last_update_tick: int = 0
    ticks_in_danger: int = 0
    recovery_ticks: int = 0
    post_crisis_vulnerability: float = 0.0
    crisis_count: int = 0
    coping_attempts_total: int = 0
    social_contacts: int = 0
    intimate_ties: int = 0
    network_size: int = 0
    support_requests: int = 0
    support_refusals: int = 0
    support_received: int = 0
    support_given: int = 0

    # --- acquired beliefs (slow, evidence-dependent) -----------------------
    beliefs: dict[str, float] = Field(
        default_factory=lambda: {
            "world_is_safe": 0.5,
            "people_are_reliable": 0.5,
            "effort_pays_off": 0.5,
            "self_efficacy": 0.5,
        }
    )

    # --- history ----------------------------------------------------------
    active_crisis: Optional[CrisisEpisode] = None
    crisis_history: list[CrisisEpisode] = Field(default_factory=list)
    coping_history: list[CopingEpisode] = Field(default_factory=list)
    coping: CopingProfile = Field(default_factory=CopingProfile)
    recent_appraisals: list[AppraisalRecord] = Field(default_factory=list)
    timeline: list[LifeEventRecord] = Field(default_factory=list)
    unresolved_coping: list[str] = Field(default_factory=list)

    # --- observability ----------------------------------------------------
    lod: PsychLOD = PsychLOD.FULL
    stats: dict[str, float] = Field(default_factory=dict)

    # ==================================================================
    # Construction
    # ==================================================================

    @classmethod
    def from_personality(
        cls,
        human_uid: str,
        *,
        age: float = 30.0,
        temperament: str = "balanced",
        personality_values: Optional[dict[str, float]] = None,
        money: float = 80.0,
        health: float = 1.0,
        social_support: float = 0.40,
    ) -> "PsychologicalState":
        """Derive the constitution from Big Five values.

        The mapping is explicit and inspectable rather than learned: high
        neuroticism raises threat/loss sensitivity; high conscientiousness
        supports self-control; agreeableness and extraversion support the
        social channels of regulation.  ``temperament`` gives a small additional
        offset so two people with equal trait vectors are not identical.
        """
        p = personality_values or {}
        o = float(p.get("openness", 0.5))
        c = float(p.get("conscientiousness", 0.5))
        e = float(p.get("extraversion", 0.5))
        a = float(p.get("agreeableness", 0.5))
        n = float(p.get("neuroticism", 0.5))
        risk = float(p.get("risk_tolerance", 0.5))
        patience = float(p.get("patience", 0.5))
        persistence = float(p.get("persistence", 0.5))

        temperament_offsets = {
            "balanced": 0.0,
            "sanguine": 0.04,
            "choleric": -0.02,
            "melancholic": -0.04,
            "phlegmatic": 0.02,
        }
        offset = temperament_offsets.get(str(temperament).lower(), 0.0)

        reactivity = _clamp(0.25 + 0.45 * n + 0.10 * e + offset * 0.5)
        regulation = _clamp(0.30 + 0.30 * c + 0.18 * a + 0.12 * (1.0 - n) + offset)
        resilience = _clamp(0.20 + 0.25 * c + 0.20 * persistence + 0.15 * (1.0 - n) + 0.10 * e + offset)
        self_control_base = _clamp(0.25 + 0.40 * c + 0.18 * patience + 0.12 * (1.0 - n) + offset)
        loss_sensitivity = _clamp(0.20 + 0.45 * n + 0.20 * a + 0.10 * (1.0 - c))
        threat_sensitivity = _clamp(0.15 + 0.55 * n + 0.15 * (1.0 - risk) + 0.08 * (1.0 - e))
        social_sensitivity = _clamp(0.20 + 0.40 * a + 0.30 * e + 0.08 * n)
        impulsivity = _clamp(0.20 + 0.40 * risk + 0.25 * (1.0 - c) + 0.15 * (1.0 - patience))

        buffer = _clamp(money / 240.0)
        return cls(
            human_uid=human_uid,
            reactivity=round(reactivity, 4),
            regulation_capacity=round(regulation, 4),
            resilience=round(resilience, 4),
            self_control_baseline=round(self_control_base, 4),
            loss_sensitivity=round(loss_sensitivity, 4),
            threat_sensitivity=round(threat_sensitivity, 4),
            social_sensitivity=round(social_sensitivity, 4),
            impulsivity=round(impulsivity, 4),
            self_control=round(_clamp(0.55 + 0.30 * self_control_base), 4),
            hope=round(_clamp(0.42 + 0.22 * (1.0 - n) + 0.10 * e + offset), 4),
            trust=round(_clamp(0.35 + 0.25 * a + 0.10 * (1.0 - n)), 4),
            loneliness=round(_clamp(0.15 + 0.22 * (1.0 - e) + 0.12 * n), 4),
            uncertainty=round(_clamp(0.25 + 0.25 * (1.0 - c) + 0.10 * n), 4),
            motivation=round(_clamp(0.40 + 0.30 * persistence + 0.14 * c), 4),
            perceived_support=round(_clamp(social_support), 4),
            material_buffer=round(buffer, 4),
            health_buffer=round(_clamp(health), 4),
            chronic_stress=round(_clamp(0.05 + 0.12 * n), 4),
            acute_stress=round(_clamp(0.08 + 0.10 * n), 4),
            anxiety=round(_clamp(0.08 + 0.14 * n), 4),
            # Age is a mild modifier, never a destiny: older adults have
            # accumulated regulation but also accumulated load.
            mental_fatigue=round(_clamp(0.08 + max(0.0, age - 55.0) / 300.0), 4),
        )

    # ==================================================================
    # Queries used by the rest of the simulation
    # ==================================================================

    @property
    def psychological_load(self) -> float:
        """Composite load in [0, 1] used for LOD and decision modulation."""
        return _clamp(
            0.34 * self.chronic_stress
            + 0.22 * self.acute_stress
            + 0.16 * self.mental_fatigue
            + 0.14 * self.loneliness
            + 0.14 * (1.0 - self.self_control)
        )

    @property
    def wellbeing(self) -> float:
        """A descriptive composite, not a clinical score."""
        return _clamp(
            0.40 * self.hope
            + 0.20 * self.self_control
            + 0.15 * self.perceived_support
            + 0.15 * (1.0 - self.chronic_stress)
            + 0.10 * (1.0 - self.loneliness)
        )

    def in_crisis(self) -> bool:
        return self.active_crisis is not None and self.active_crisis.is_active

    def dominant_pressure(self) -> str:
        """Name the largest modelled contributor; used in explanations."""
        components = {
            "chronic_stress": 0.34 * self.chronic_stress,
            "acute_stress": 0.22 * self.acute_stress,
            "mental_fatigue": 0.16 * self.mental_fatigue,
            "loneliness": 0.14 * self.loneliness,
            "low_self_control": 0.14 * (1.0 - self.self_control),
        }
        return max(components, key=components.get)

    # ==================================================================
    # Mutation primitives
    # ==================================================================

    def add_acute_stress(self, amount: float, cap: float = 1.0) -> None:
        """Inject a stressor.  Repeated small stressors accumulate sublinearly."""
        amount = max(0.0, float(amount))
        if amount <= 0.0:
            return
        # Diminishing returns protect against a burst of events saturating the
        # variable in a single tick (the anti-oscillation requirement).
        gain = amount * (1.0 - 0.45 * self.acute_stress)
        self.acute_stress = _clamp(self.acute_stress + gain, 0.0, cap)

    def relieve(self, amount: float) -> None:
        """Immediate relief reduces acute stress and raises hope slightly."""
        amount = max(0.0, float(amount))
        self.acute_stress = _clamp(self.acute_stress - amount)
        self.hope = _clamp(self.hope + amount * 0.20)

    def record_appraisal(self, record: AppraisalRecord, limit: int = 60) -> None:
        self.recent_appraisals.append(record)
        if len(self.recent_appraisals) > limit:
            self.recent_appraisals = self.recent_appraisals[-limit:]

    def record_coping(self, episode: CopingEpisode, limit: int = 80) -> None:
        self.coping_history.append(episode)
        if len(self.coping_history) > limit:
            self.coping_history = self.coping_history[-limit:]
        self.coping_attempts_total += 1
        if episode.episode_id not in self.unresolved_coping:
            self.unresolved_coping.append(episode.episode_id)
        if len(self.unresolved_coping) > 32:
            self.unresolved_coping = self.unresolved_coping[-32:]
        self.coping.record(episode.strategy, episode.short_term_relief, episode.tick)

    def record_timeline(self, record: LifeEventRecord, limit: int = 240) -> None:
        self.timeline.append(record)
        if len(self.timeline) > limit:
            self.timeline = self.timeline[-limit:]

    # ==================================================================
    # Serialisation
    # ==================================================================

    def to_compact_dict(self) -> dict[str, Any]:
        """Checkpoint payload.

        History lists are bounded at append time, so this document has a
        known maximum size per individual and cannot grow without limit.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_compact_dict(cls, data: dict[str, Any]) -> "PsychologicalState":
        return cls.model_validate(data)
