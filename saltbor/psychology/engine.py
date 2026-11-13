"""Integrated psychological engine.

This is the single runtime that connects appraisal, coping, regulation, social
support, memory reconstruction and the existing emotional/personality/memory
engines.  It is intentionally thin at the integration points: state transitions
happen here, but the domain rules live in the sibling modules.

Integration contract
--------------------
* ``SyntheticHuman.psychology`` holds the persistent state (created from the
  Big Five in ``SyntheticHuman.__init__``).
* ``SimulationRunner`` calls :meth:`process_events` after the tick's events are
  emitted and :meth:`step_population` once per tick.
* ``DecisionEngine`` reads the bounded modifiers from
  :meth:`decision_modifiers`.
* ``ExtensionRuntime`` checkpoints :meth:`to_dict`; SQLite keeps the timeline
  in ``psychology_timeline`` for durable observability.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

from saltbor.core.types import ActivityType, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.psychology.appraisal import (
    EVENT_TEMPLATES,
    AppraisalEngine,
    apply_appraisal,
)
from saltbor.psychology.coping import AdaptiveCopingEngine, COPING_SPECS, CopingChoice
from saltbor.psychology.models import (
    CopingStrategy,
    CrisisEpisode,
    LifeEventRecord,
    PsychLOD,
    PsychologicalState,
    _clamp,
)
from saltbor.psychology.regulation import BodySignals, RegulationEngine
from saltbor.psychology.retrieval import AssociativeRetrieval, RetrievalQuery
from saltbor.psychology.support import SupportAssessment, SupportEngine

logger = logging.getLogger(__name__)

# Events worth an appraisal.  Routine activity churn is deliberately excluded:
# appraising every ACTIVITY_STARTED would drown the psychological layer in
# noise and make the timeline unreadable.
PSYCH_RELEVANT_EVENTS: frozenset[EventType] = frozenset(EVENT_TEMPLATES.keys()) | {
    EventType.GRIEF_EXPERIENCED,
    EventType.BEREAVEMENT_EXPERIENCED,
    EventType.MARRIAGE_CELEBRATED,
    EventType.PARTNERSHIP_FORMED,
    EventType.DIVORCE_FINALIZED,
    EventType.RELATIONSHIP_SEPARATED,
    EventType.INFIDELITY_COMMITTED,
    EventType.HOUSEHOLD_EXPENSE_CHARGED,
    EventType.RENT_PAID,
    EventType.EVICTION_OCCURRED,
    EventType.COMMUNITY_AID_DELIVERED,
    EventType.DISASTER_RECOVERY_STARTED,
    EventType.HEALTH_TREATMENT_RECEIVED,
    EventType.HEALTH_TREATMENT_SEEKED,
    EventType.FAENA_COMPLETED,
    EventType.COMMUNITY_MEETING_HELD,
    EventType.COMMUNITY_PROJECT_PROPOSED,
    EventType.SHELTER_ENTERED,
    EventType.SHELTER_LEFT,
    EventType.APPRENTICESHIP_GRADUATED,
    EventType.ASSISTANCE_REQUESTED,
    EventType.ASSISTANCE_OFFERED,
    EventType.ASSISTANCE_REJECTED,
}

# Maximum appraisals per individual per tick, highest importance first.  This
# is the per-agent budget that keeps a busy event bus from becoming O(events ×
# population) work.
MAX_APPRAISALS_PER_TICK = 6

_LOD_INTERVALS = {
    PsychLOD.FULL: 1,
    PsychLOD.ROUTINE: 2,
    PsychLOD.MACRO: 8,
    PsychLOD.DORMANT: 24,
}


class PsychologicalEngine:
    """Owns the psychological states and advances them in the live loop."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = np.random.default_rng(seed)
        self.appraisal = AppraisalEngine()
        self.coping = AdaptiveCopingEngine()
        self.regulation = RegulationEngine()
        self.retrieval = AssociativeRetrieval()
        self.support = SupportEngine(seed=seed)
        self.states: dict[str, PsychologicalState] = {}
        self._support_cache: dict[str, SupportAssessment] = {}
        self._last_daily_tick = -1
        self._last_support_day = -1
        self._last_coping: dict[str, int] = {}
        self._event_cursor = 0
        self._timeline_persisted_until: dict[str, int] = {}
        self._recent_outcomes: list[dict[str, Any]] = []
        self.stats: dict[str, float] = {
            "appraisals": 0,
            "coping_attempts": 0,
            "support_requests": 0,
            "support_grants": 0,
            "crises_started": 0,
            "crises_recovered": 0,
            "relapses": 0,
            "timeline_entries": 0,
        }
        self.default_tick_minutes = 15

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def ensure(self, human: Any) -> PsychologicalState:
        """Return (and if needed create) the individual's persistent state."""
        uid = str(human.uid)
        state = self.states.get(uid)
        if state is not None:
            human.psychology = state
            return state

        traits = human.personality.traits
        values = {
            name: traits.effective_value(name)
            for name in (
                "openness", "conscientiousness", "extraversion",
                "agreeableness", "neuroticism", "risk_tolerance",
                "patience", "persistence",
            )
        }
        state = PsychologicalState.from_personality(
            uid,
            age=float(getattr(human.demographics, "age", 30.0)),
            temperament=str(getattr(traits, "temperament_name", "balanced")),
            personality_values=values,
            money=float(getattr(human.physical_state, "money", 80.0)),
            health=float(getattr(human.physical_state, "health", 1.0)),
        )
        self.states[uid] = state
        human.psychology = state
        return state

    def remove(self, uid: Any) -> None:
        key = str(uid)
        self.states.pop(key, None)
        self._support_cache.pop(key, None)
        self.retrieval.invalidate(key)

    def state_for(self, human: Any) -> PsychologicalState:
        return self.ensure(human)

    # ------------------------------------------------------------------
    # Event appraisal
    # ------------------------------------------------------------------

    def process_events(
        self,
        events: list[SimulationEvent],
        population: Any,
        social: Any = None,
        genealogy: Any = None,
    ) -> int:
        """Appraise only the salient events since the last call.

        The event bus is the integration surface: any engine that emits an
        event is automatically appraised by the people involved, without the
        psychological engine knowing that engine's internals.
        """
        grouped: dict[str, list[SimulationEvent]] = {}
        for event in events:
            if event.event_type not in PSYCH_RELEVANT_EVENTS:
                continue
            if event.importance < 0.18:
                continue
            for attr in ("source_human_id", "target_human_id"):
                human_id = getattr(event, attr, None)
                if human_id is None:
                    continue
                grouped.setdefault(str(human_id), []).append(event)

        processed = 0
        for uid, agent_events in grouped.items():
            human = _resolve_human(population, uid)
            if human is None:
                continue
            psych = self.ensure(human)
            # Highest importance first, budget per tick.
            agent_events.sort(key=lambda e: e.importance, reverse=True)
            for event in agent_events[:MAX_APPRAISALS_PER_TICK]:
                try:
                    record = self.appraisal.appraise(human, event, psych, social, tick=event.tick)
                    apply_appraisal(human, psych, record, event.tick)
                    self._update_beliefs(psych, record)
                    self.retrieval.invalidate(uid)
                    processed += 1
                    self.stats["appraisals"] += 1
                except Exception as ex:  # pragma: no cover - defensive
                    logger.debug("Appraisal failed for %s/%s: %s", uid, event.event_type.value, ex)
        return processed

    @staticmethod
    def _update_beliefs(psych: PsychologicalState, record: Any) -> None:
        """Beliefs change from repeated experience, never from one event.

        Updates are small and bounded; this is the mechanism by which a person
        who keeps failing at work slowly stops believing effort pays off.
        """
        d = record.desirability
        imp = record.personal_importance
        delta = 0.030 * d * imp
        psych.beliefs["world_is_safe"] = _clamp(psych.beliefs.get("world_is_safe", 0.5) + delta)
        psych.beliefs["people_are_reliable"] = _clamp(
            psych.beliefs.get("people_are_reliable", 0.5)
            + 0.035 * d * imp * max(0.2, record.relationship_relevance)
        )
        psych.beliefs["effort_pays_off"] = _clamp(
            psych.beliefs.get("effort_pays_off", 0.5)
            + 0.028 * d * imp * (1.0 if record.agency == "self" else 0.5)
        )
        psych.beliefs["self_efficacy"] = _clamp(
            psych.beliefs.get("self_efficacy", 0.5)
            + 0.032 * d * imp * (1.0 if record.agency == "self" else 0.4) * (0.5 + record.control)
        )

    # ------------------------------------------------------------------
    # Population step
    # ------------------------------------------------------------------

    def step_population(
        self,
        population: Any,
        tick: Tick,
        *,
        social: Any = None,
        genealogy: Any = None,
        event_bus: Any = None,
        lod_manager: Any = None,
        tick_minutes: int = 15,
        force_all: bool = False,
    ) -> dict[str, int]:
        """Advance every living individual with psychological LOD.

        Agents are updated at a cadence set by their load and crisis status.
        Because the dynamics integrate elapsed time analytically, a dormant
        agent does not lose psychological time: it catches up coherently.
        """
        self.default_tick_minutes = tick_minutes
        ticks_per_day = max(1, int(round(24 * 60 / max(1, tick_minutes))))
        day = int(tick) // ticks_per_day
        if day != self._last_support_day:
            self._last_support_day = day
            self._support_cache.clear()

        updated = 0
        crises_started = 0
        crises_recovered = 0
        coping_attempts = 0

        for human in list(population.get_all()):
            psych = self.ensure(human)
            lod = self._lod_for(psych, human, lod_manager)
            psych.lod = lod
            interval = _LOD_INTERVALS[lod]
            elapsed = int(tick) - int(psych.last_update_tick)
            if not force_all and elapsed < interval:
                continue

            body = self._body_signals(human, population)
            support_value = None
            if self._needs_support_refresh(psych, tick, interval):
                assessment = self.support.assess(human, social, genealogy, population)
                self._support_cache[str(human.uid)] = assessment
                psych.network_size = assessment.network_size
                psych.intimate_ties = assessment.intimate_ties
                support_value = assessment.perceived_support
                psych.perceived_support = _clamp(
                    0.65 * psych.perceived_support + 0.35 * assessment.perceived_support
                )
            else:
                assessment = self._support_cache.get(str(human.uid))

            self.regulation.step(
                psych,
                human,
                tick=int(tick),
                elapsed_ticks=max(1, elapsed),
                tick_minutes=tick_minutes,
                body=body,
                support=support_value,
            )

            self._body_consequences(human, psych, max(1, elapsed), tick_minutes)

            evaluation =             self.regulation.evaluate_crisis(
                psych, human, tick=int(tick), elapsed_ticks=max(1, elapsed),
                tick_minutes=tick_minutes,
            )
            if evaluation.started is not None:
                crises_started += 1
                self.stats["crises_started"] += 1
                self._emit_crisis(event_bus, human, evaluation.started, "started", tick)
            if evaluation.relapsed is not None:
                self.stats["relapses"] += 1
                self._emit_crisis(event_bus, human, evaluation.relapsed, "relapsed", tick)
            if evaluation.ended is not None:
                crises_recovered += 1
                self.stats["crises_recovered"] += 1
                self._emit_crisis(event_bus, human, evaluation.ended, "recovered", tick)

            # Coping attempts are throttled: a person does not try a new
            # strategy every 15 minutes.
            if self._should_cope(psych, int(tick), interval, tick_minutes):
                choice = self.coping.choose(human, psych, assessment)
                if choice is not None and choice.utility > -0.05:
                    if self._coping_is_habitual(human, psych, choice):
                        choice.utility += 0.05
                    episode = self.coping.execute(
                        human,
                        psych,
                        choice,
                        tick=int(tick),
                        support_engine=self.support,
                        assessment=assessment,
                        social=social,
                        population=population,
                        genealogy=genealogy,
                    )
                    self._last_coping[str(human.uid)] = int(tick)
                    coping_attempts += 1
                    self.stats["coping_attempts"] += 1
                    if episode.support_provider:
                        self.stats["support_requests"] += 1
                        if episode.support_received > 0:
                            self.stats["support_grants"] += 1
                    self._maybe_form_habit(human, psych, choice)
                    self._emit_coping(event_bus, human, episode, tick, choice)

            # Resolve follow-up outcomes (the trade-off mechanism).
            resolved = self.coping.resolve_due(psych, int(tick))
            for episode in resolved:
                self._recent_outcomes.append(
                    {
                        "uid": str(human.uid),
                        "strategy": episode.strategy.value,
                        "tick": int(tick),
                        "relief": episode.short_term_relief,
                        "long_term_delta": episode.long_term_delta,
                    }
                )
                self._emit_coping_outcome(event_bus, human, episode, tick)
            if len(self._recent_outcomes) > 200:
                self._recent_outcomes = self._recent_outcomes[-200:]

            self._sync_emotions(human, psych, tick)
            psych.last_update_tick = int(tick)
            updated += 1

        if day != self._last_daily_tick:
            self._last_daily_tick = day
            self.daily(population, int(tick), social=social, genealogy=genealogy, tick_minutes=tick_minutes)

        return {
            "updated": updated,
            "crises_started": crises_started,
            "crises_recovered": crises_recovered,
            "coping_attempts": coping_attempts,
        }

    def _lod_for(self, psych: PsychologicalState, human: Any, lod_manager: Any = None) -> PsychLOD:
        # A crisis is always full detail: the point of a crisis is that it
        # changes behaviour now.
        if psych.in_crisis():
            return PsychLOD.FULL
        load = psych.psychological_load
        if load >= 0.52 or psych.acute_stress >= 0.55:
            return PsychLOD.FULL
        if load >= 0.32:
            return PsychLOD.ROUTINE
        if load >= 0.18:
            return PsychLOD.MACRO
        # Respect an external LOD manager when it exists, but never let it
        # hide a person in acute distress.
        if lod_manager is not None:
            try:
                external = lod_manager.get_lod(human)
                if getattr(external, "value", external) in (3, "3"):
                    return PsychLOD.DORMANT
            except Exception:
                pass
        return PsychLOD.DORMANT

    def _body_signals(self, human: Any, population: Any) -> BodySignals:
        ps = human.physical_state
        conditions = list(getattr(human, "active_health_conditions", []))
        illness_load = min(1.0, sum(float(getattr(c, "severity", 0.0)) for c in conditions))
        pain = max((float(getattr(c, "severity", 0.0)) for c in conditions), default=0.0)
        loc = getattr(ps, "current_location_id", None)
        contacts = 0
        if loc is not None:
            try:
                contacts = max(0, len(population.get_at_location(loc)) - 1)
            except Exception:
                contacts = 0
        activity = getattr(ps, "current_activity", None)
        return BodySignals(
            energy=float(getattr(ps, "energy", 1.0)),
            hunger=float(getattr(ps, "hunger", 0.0)),
            health=float(getattr(ps, "health", 1.0)),
            pain=pain,
            illness_load=illness_load,
            sleep_activity=activity in (ActivityType.SLEEP, ActivityType.REST),
            social_contact=contacts,
            money=float(getattr(ps, "money", 0.0)),
        )

    def _body_consequences(
        self,
        human: Any,
        psych: PsychologicalState,
        elapsed_ticks: int,
        tick_minutes: int,
    ) -> None:
        """Mind → body: self-neglect and protection are causal, not decorative.

        Low self-control predicts irregular eating and reduced protective
        behaviour; sustained chronic stress adds a small health cost.  These
        are bounded nudges layered on the existing PhysicalState simulation,
        not a second health model.
        """
        dt = max(0.0, elapsed_ticks * tick_minutes / 1440.0)
        if dt <= 0.0:
            return
        ps = human.physical_state
        neglect = max(0.0, 0.30 - psych.self_control)
        if neglect > 0.0:
            ps.hunger = min(1.0, float(getattr(ps, "hunger", 0.0)) + 0.16 * neglect * dt)
            ps.energy = max(0.0, float(getattr(ps, "energy", 1.0)) - 0.025 * neglect * dt)
            if psych.chronic_stress > 0.66:
                ps.health = max(0.02, float(getattr(ps, "health", 1.0)) - 0.006 * neglect * dt)
        # Protective behaviour: a regulated, hopeful person maintains routines
        # that prevent small deteriorations from accumulating.
        if psych.self_control > 0.62 and psych.hope > 0.55:
            ps.health = min(1.0, float(getattr(ps, "health", 1.0)) + 0.004 * dt)

    def prune(self, living_uids: set[str]) -> int:
        """Drop states of people no longer in the live registry.

        Their timeline rows and episodic memories remain in SQLite, which is
        where historical provenance belongs.
        """
        removed = 0
        for uid in list(self.states.keys()):
            if uid not in living_uids:
                self.states.pop(uid, None)
                self._support_cache.pop(uid, None)
                self.retrieval.invalidate(uid)
                removed += 1
        return removed

    def _needs_support_refresh(self, psych: PsychologicalState, tick: int, interval: int) -> bool:
        assessment = self._support_cache.get(psych.human_uid)
        if assessment is None:
            return True
        if psych.in_crisis():
            return True
        units = (int(tick) - int(psych.last_update_tick)) * max(1, self.default_tick_minutes) / 15.0
        return units >= max(24, interval * 6)

    def _should_cope(self, psych: PsychologicalState, tick: int, interval: int, tick_minutes: int = 15) -> bool:
        uid = psych.human_uid
        last = self._last_coping.get(uid, -10_000)
        cooldown = 6 if psych.in_crisis() else 16
        elapsed_units = (int(tick) - last) * max(1, tick_minutes) / 15.0
        if elapsed_units < cooldown:
            return False
        # No coping without a pressure to cope with.
        return psych.psychological_load > 0.26 or psych.in_crisis() or psych.acute_stress > 0.30

    @staticmethod
    def _coping_is_habitual(human: Any, psych: PsychologicalState, choice: CopingChoice) -> bool:
        for habit in getattr(human, "habits", [])[:24]:
            if str(habit.get("strategy")) == choice.spec.strategy.value and float(habit.get("strength", 0)) > 0.45:
                return True
        return psych.coping.attempts.get(choice.spec.strategy.value, 0) >= 6 and psych.coping.preference(choice.spec.strategy) > 0.62

    @staticmethod
    def _maybe_form_habit(human: Any, psych: PsychologicalState, choice: CopingChoice) -> None:
        """Repeated reinforced coping becomes a habit, but not a cage.

        Habits are stored on the existing ``human.habits`` list, bounded and
        with an explicit strength, so decisions can weight them without the
        individual becoming unable to try something else.
        """
        strategy = choice.spec.strategy.value
        attempts = psych.coping.attempts.get(strategy, 0)
        if attempts < 5:
            return
        preference = psych.coping.preference(choice.spec.strategy)
        if preference < 0.55:
            return
        habits = getattr(human, "habits", None)
        if habits is None:
            human.habits = []
            habits = human.habits
        for habit in habits:
            if str(habit.get("strategy")) == strategy:
                habit["strength"] = round(min(1.0, float(habit.get("strength", 0.3)) + 0.06), 3)
                habit["attempts"] = attempts
                return
        if len(habits) < 12:
            habits.append(
                {
                    "strategy": strategy,
                    "category": choice.spec.category.value,
                    "strength": round(_clamp(0.30 + 0.35 * preference), 3),
                    "attempts": attempts,
                    "formed_tick": psych.last_update_tick,
                }
            )

    # ------------------------------------------------------------------
    # Emotion synchronisation
    # ------------------------------------------------------------------

    def _sync_emotions(self, human: Any, psych: PsychologicalState, tick: int) -> None:
        """Keep the integrative substrate and EmotionState coherent.

        The integrative variables are authoritative for the slow channels.  We
        write them into the emotional profile (not additively) so repeated ticks
        do not inflate intensity, while appraisal-generated emotions keep their
        own faster trajectories.
        """
        profile = getattr(getattr(human, "emotions", None), "profile", None)
        if profile is None:
            return
        from saltbor.cognition.emotions.models import EMOTION_DEFAULT_DECAY, EmotionState
        from saltbor.core.types import EmotionType

        channels = {
            EmotionType.STRESS: psych.acute_stress,
            EmotionType.ANXIETY: psych.anxiety,
            EmotionType.FEAR: psych.fear,
            EmotionType.SADNESS: psych.sadness,
            EmotionType.ANGER: psych.anger,
            EmotionType.FRUSTRATION: psych.frustration,
            EmotionType.LONELINESS: psych.loneliness,
            EmotionType.HOPE: psych.hope,
        }
        for etype, value in channels.items():
            if value < 0.02:
                continue
            existing = profile.active_emotions.get(etype)
            intensity = value if existing is None else max(existing.intensity, value)
            profile.active_emotions[etype] = EmotionState(
                emotion_type=etype,
                intensity=_clamp(intensity),
                duration_remaining=96,
                decay_rate=EMOTION_DEFAULT_DECAY.get(etype, 0.02) * 0.35,
            )

    # ------------------------------------------------------------------
    # Daily consolidation and development
    # ------------------------------------------------------------------

    def daily(
        self,
        population: Any,
        tick: int,
        *,
        social: Any = None,
        genealogy: Any = None,
        tick_minutes: int = 15,
    ) -> None:
        """Daily pass: support refresh, forgetting and slow biographical drift."""
        self.prune({str(h.uid) for h in population.get_all()})
        units_per_day = max(1.0, 1440.0 / max(1, tick_minutes))
        current_day = int(int(tick) / units_per_day)
        for human in list(population.get_all()):
            psych = self.ensure(human)
            assessment = self.support.assess(human, social, genealogy, population)
            self._support_cache[str(human.uid)] = assessment
            psych.network_size = assessment.network_size
            psych.intimate_ties = assessment.intimate_ties
            psych.perceived_support = _clamp(
                0.55 * psych.perceived_support + 0.45 * assessment.perceived_support
            )

            # Forgetting is a slow process; running it every simulated day over
            # a 25-year horizon would dominate the cost of the whole engine.
            last_forget_day = int(psych.stats.get("last_forget_day", -10_000))
            if current_day - last_forget_day >= 14:
                active = human.memory.episodic.get_all(include_dormant=False)
                forgotten = self.retrieval.forgetting_pass(
                    active,
                    tick,
                    archive_callback=human.memory.episodic.remove,
                )
                if forgotten:
                    psych.stats["memories_faded"] = psych.stats.get("memories_faded", 0) + len(forgotten)
                psych.stats["last_forget_day"] = current_day

            self._biographical_drift(human, psych, tick)

    def _biographical_drift(self, human: Any, psych: PsychologicalState, tick: int) -> None:
        """Slow, repeated-condition personality change with an audit trail.

        A single bad day never changes a trait.  The engine accumulates days in
        a condition and applies a very small base shift only after sustained
        exposure.  This is the existing ``evolution_history`` format, so the UI
        and earlier experiments keep working.
        """
        if psych.chronic_stress > 0.62:
            psych.stats["chronic_days"] = psych.stats.get("chronic_days", 0) + 1
        else:
            psych.stats["chronic_days"] = max(0.0, psych.stats.get("chronic_days", 0) - 0.5)

        chronic_days = psych.stats.get("chronic_days", 0)
        # Bounded long-run drift: at most 0.03 of a trait from sustained stress
        # over an entire life.  A single hard year must not rewrite a person.
        if chronic_days >= 30 and int(chronic_days) % 30 == 0:
            traits = human.personality.traits
            trait = traits.get_trait("neuroticism")
            already = float(psych.stats.get("bio_neuroticism_shift", 0.0))
            shift = min(0.0006, max(0.0, 0.03 - already))
            if shift <= 0.0:
                return
            old = trait.base_value
            trait.shift_base(shift)
            psych.stats["bio_neuroticism_shift"] = already + shift
            human.personality.evolution_history.append(
                {
                    "tick": int(tick),
                    "event_type": "sustained_chronic_stress",
                    "trait": "neuroticism",
                    "old_base": round(old, 4),
                    "new_base": round(trait.base_value, 4),
                    "delta": round(trait.base_value - old, 5),
                    "cause": f"{int(chronic_days)} días de estrés crónico sostenido",
                }
            )

        if psych.crisis_count > 0 and not psych.in_crisis():
            psych.stats["days_since_crisis"] = psych.stats.get("days_since_crisis", 0) + 1
            if int(psych.stats["days_since_crisis"]) % 30 == 0 and psych.post_crisis_vulnerability < 0.25:
                trait = human.personality.traits.get_trait("persistence")
                old = trait.base_value
                already = float(psych.stats.get("bio_persistence_shift", 0.0))
                shift = min(0.0004, max(0.0, 0.02 - already))
                if shift <= 0.0:
                    return
                trait.shift_base(shift)
                psych.stats["bio_persistence_shift"] = already + shift
                human.personality.evolution_history.append(
                    {
                        "tick": int(tick),
                        "event_type": "recovery_experience",
                        "trait": "persistence",
                        "old_base": round(old, 4),
                        "new_base": round(trait.base_value, 4),
                        "delta": round(trait.base_value - old, 5),
                        "cause": "recuperación sostenida tras una crisis",
                    }
                )

    # ------------------------------------------------------------------
    # Decision integration
    # ------------------------------------------------------------------

    def decision_modifiers(self, human: Any) -> dict[str, float]:
        return self.regulation.decision_modifiers(self.ensure(human))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _emit_crisis(
        self,
        event_bus: Any,
        human: Any,
        episode: CrisisEpisode,
        phase: str,
        tick: int,
    ) -> None:
        if event_bus is None:
            return
        mapping = {
            "started": EventType.PSYCHOLOGICAL_CRISIS_STARTED,
            "recovered": EventType.PSYCHOLOGICAL_CRISIS_RECOVERED,
            "relapsed": EventType.PSYCHOLOGICAL_RELAPSE,
        }
        event_type = mapping.get(phase)
        if event_type is None:
            return
        event = SimulationEvent(
            event_type=event_type,
            tick=int(tick),
            source_human_id=human.uid,
            location_id=getattr(human.physical_state, "current_location_id", None),
            data={
                "crisis_id": episode.crisis_id,
                "kind": episode.kind.value,
                "severity": round(episode.severity, 4),
                "peak_severity": round(episode.peak_severity, 4),
                "duration_ticks": episode.duration_ticks(int(tick)),
                "causes": dict(episode.causes),
                "triggers": list(episode.triggers),
                "behaviours": list(episode.behaviours),
                "provenance": "psychological_engine_v1",
            },
            importance=0.80 if phase == "started" else 0.55,
        )
        event_bus.emit(event)

    def _emit_coping(
        self,
        event_bus: Any,
        human: Any,
        episode: Any,
        tick: int,
        choice: CopingChoice,
    ) -> None:
        if event_bus is None:
            return
        event_bus.emit(
            SimulationEvent(
                event_type=EventType.COPING_STRATEGY_USED,
                tick=int(tick),
                source_human_id=human.uid,
                location_id=getattr(human.physical_state, "current_location_id", None),
                data={
                    "episode_id": episode.episode_id,
                    "strategy": episode.strategy.value,
                    "category": episode.category.value,
                    "utility": choice.utility,
                    "relief": episode.short_term_relief,
                    "support_received": episode.support_received,
                    "cost": episode.cost_paid,
                    "provenance": "adaptive_coping_v1",
                },
                importance=0.38,
            )
        )

    def _emit_coping_outcome(self, event_bus: Any, human: Any, episode: Any, tick: int) -> None:
        if event_bus is None:
            return
        event_bus.emit(
            SimulationEvent(
                event_type=EventType.COPING_OUTCOME_RECORDED,
                tick=int(tick),
                source_human_id=human.uid,
                data={
                    "episode_id": episode.episode_id,
                    "strategy": episode.strategy.value,
                    "short_term_relief": episode.short_term_relief,
                    "long_term_delta": episode.long_term_delta,
                    "duration_ticks": (episode.resolved_tick or int(tick)) - episode.tick,
                    "provenance": "adaptive_coping_v1",
                },
                importance=0.30,
            )
        )

    # ------------------------------------------------------------------
    # Snapshot / observability
    # ------------------------------------------------------------------

    def snapshot(self, human: Any) -> dict[str, Any]:
        psych = self.ensure(human)
        assessment = self._support_cache.get(str(human.uid))
        if assessment is None:
            assessment = self.support.assess(human, None, None, None)
        active = human.memory.episodic.get_all(include_dormant=False)
        contradictions = self.retrieval.find_contradictions(active)
        contradiction_map: dict[str, list[str]] = {}
        for a, b in contradictions:
            contradiction_map.setdefault(a, []).append(b)
            contradiction_map.setdefault(b, []).append(a)

        recent = sorted(active, key=lambda r: r.tick, reverse=True)[:5]
        reconstructions = []
        for rec in recent:
            recon = self.retrieval.reconstruct(
                rec,
                tick=psych.last_update_tick,
                psych=psych,
                contradiction_ids=contradiction_map.get(str(rec.memory_id), []),
            )
            reconstructions.append(
                {
                    "memory_id": recon.memory_id,
                    "original": recon.original_summary,
                    "reconstructed": recon.reconstructed_summary,
                    "fidelity": recon.fidelity,
                    "confidence": recon.confidence,
                    "distortions": recon.distortions,
                    "contradicts": recon.contradictory_with,
                    "age_days": recon.age_days,
                }
            )

        crisis = psych.active_crisis
        return {
            "human_uid": str(human.uid),
            "name": human.name,
            "lod": psych.lod.name,
            "constitution": {
                "reactivity": psych.reactivity,
                "regulation_capacity": psych.regulation_capacity,
                "resilience": psych.resilience,
                "loss_sensitivity": psych.loss_sensitivity,
                "threat_sensitivity": psych.threat_sensitivity,
                "social_sensitivity": psych.social_sensitivity,
                "impulsivity": psych.impulsivity,
                "self_control_baseline": psych.self_control_baseline,
            },
            "state": {
                "acute_stress": round(psych.acute_stress, 4),
                "chronic_stress": round(psych.chronic_stress, 4),
                "anxiety": round(psych.anxiety, 4),
                "fear": round(psych.fear, 4),
                "sadness": round(psych.sadness, 4),
                "anger": round(psych.anger, 4),
                "loneliness": round(psych.loneliness, 4),
                "frustration": round(psych.frustration, 4),
                "hope": round(psych.hope, 4),
                "trust": round(psych.trust, 4),
                "uncertainty": round(psych.uncertainty, 4),
                "motivation": round(psych.motivation, 4),
                "mental_fatigue": round(psych.mental_fatigue, 4),
                "self_control": round(psych.self_control, 4),
                "perceived_support": round(psych.perceived_support, 4),
                "wellbeing": round(psych.wellbeing, 4),
                "load": round(psych.psychological_load, 4),
            },
            "beliefs": {k: round(v, 3) for k, v in psych.beliefs.items()},
            "support": assessment.as_dict(),
            "crisis": (
                {
                    "crisis_id": crisis.crisis_id,
                    "kind": crisis.kind.value,
                    "start_tick": crisis.start_tick,
                    "severity": crisis.severity,
                    "peak_severity": crisis.peak_severity,
                    "duration_ticks": crisis.duration_ticks(psych.last_update_tick),
                    "causes": crisis.causes,
                    "triggers": crisis.triggers,
                    "behaviours": crisis.behaviours,
                    "recovery_progress": round(crisis.recovery_progress, 3),
                    "is_active": crisis.is_active,
                    "relapsed": crisis.relapsed,
                }
                if crisis is not None
                else None
            ),
            "crisis_history": [
                {
                    "crisis_id": ep.crisis_id,
                    "kind": ep.kind.value,
                    "start_tick": ep.start_tick,
                    "ended_tick": ep.ended_tick,
                    "duration_ticks": ep.duration_ticks(psych.last_update_tick),
                    "peak_severity": ep.peak_severity,
                    "relapsed": ep.relapsed,
                }
                for ep in psych.crisis_history[-8:]
            ],
            "coping": {
                "preferences": dict(sorted(psych.coping.preferences.items(), key=lambda kv: kv[1], reverse=True)[:10]),
                "attempts": dict(psych.coping.attempts),
                "recent": [
                    {
                        "strategy": ep.strategy.value,
                        "category": ep.category.value,
                        "tick": ep.tick,
                        "relief": ep.short_term_relief,
                        "long_term_delta": ep.long_term_delta,
                        "cost": ep.cost_paid,
                        "support": ep.support_received,
                        "note": ep.outcome_note,
                    }
                    for ep in psych.coping_history[-8:]
                ],
            },
            "appraisals": [record.as_dict() for record in psych.recent_appraisals[-5:]],
            "timeline": [record.model_dump(mode="json") for record in psych.timeline[-12:]],
            "memories": reconstructions,
            "habits": list(getattr(human, "habits", []))[:8],
            "decision_modifiers": self.decision_modifiers(human),
        }

    def overview(self) -> dict[str, Any]:
        states = list(self.states.values())
        if not states:
            return {
                "individuals": 0,
                "mean_stress": 0.0,
                "mean_self_control": 0.0,
                "active_crises": 0,
                "crises_total": 0,
                "coping_attempts": 0,
                "support_requests": 0,
                "support_grants": 0,
                "stats": dict(self.stats),
            }
        return {
            "individuals": len(states),
            "mean_stress": round(float(np.mean([s.chronic_stress for s in states])), 4),
            "mean_acute_stress": round(float(np.mean([s.acute_stress for s in states])), 4),
            "mean_self_control": round(float(np.mean([s.self_control for s in states])), 4),
            "mean_hope": round(float(np.mean([s.hope for s in states])), 4),
            "mean_loneliness": round(float(np.mean([s.loneliness for s in states])), 4),
            "active_crises": sum(1 for s in states if s.in_crisis()),
            "crises_total": sum(s.crisis_count for s in states),
            "coping_attempts": sum(s.coping_attempts_total for s in states),
            "support_requests": sum(s.support_requests for s in states),
            "support_grants": sum(s.support_received for s in states),
            "stats": {k: round(float(v), 3) for k, v in self.stats.items()},
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "states": {uid: state.to_compact_dict() for uid, state in self.states.items()},
            "stats": dict(self.stats),
            "last_daily_tick": self._last_daily_tick,
            "last_support_day": self._last_support_day,
            "support": self.support.to_dict(),
            "event_cursor": self._event_cursor,
            "timeline_persisted_until": dict(self._timeline_persisted_until),
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.states = {}
        for uid, payload in dict(data.get("states", {})).items():
            try:
                self.states[str(uid)] = PsychologicalState.from_compact_dict(payload)
            except Exception as ex:
                logger.warning("Discarding invalid psychological state for %s: %s", uid, ex)
        self.stats.update({str(k): float(v) for k, v in dict(data.get("stats", {})).items()})
        self._last_daily_tick = int(data.get("last_daily_tick", -1))
        self._last_support_day = int(data.get("last_support_day", -1))
        self.support.load_dict(dict(data.get("support", {})))
        self._event_cursor = int(data.get("event_cursor", 0))
        self._timeline_persisted_until = {
            str(k): int(v) for k, v in dict(data.get("timeline_persisted_until", {})).items()
        }
        self._support_cache.clear()
        self.retrieval.invalidate()

    def persist_timeline(self, db: Any, limit_per_human: int = 40) -> int:
        """Flush new timeline rows to SQLite, incrementally.

        Only entries after the last persisted tick are written, so checkpoints
        do not rewrite the whole autobiography.  ``INSERT OR REPLACE`` makes
        the operation idempotent if a checkpoint is retried.
        """
        if db is None:
            return 0
        written = 0
        try:
            for uid, state in self.states.items():
                since = self._timeline_persisted_until.get(uid, -1)
                new_entries = [r for r in state.timeline if int(r.tick) > since]
                for record in new_entries[-limit_per_human:]:
                    db.execute(
                        """
                        INSERT OR REPLACE INTO psychology_timeline
                            (human_uid, record_id, tick, kind, summary, valence,
                             importance, location_id, payload_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            uid,
                            record.record_id,
                            int(record.tick),
                            record.kind,
                            record.summary[:500],
                            float(record.valence),
                            float(record.importance),
                            record.location_id,
                            _json_dumps(record.payload),
                        ),
                    )
                    written += 1
                if new_entries:
                    self._timeline_persisted_until[uid] = max(int(r.tick) for r in new_entries)
        except Exception as ex:
            logger.warning("Psychology timeline persistence failed: %s", ex)
        return written


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _resolve_human(population: Any, uid: str) -> Any:
    if population is None:
        return None
    try:
        for human in population.get_all():
            if str(human.uid) == uid:
                return human
    except Exception:
        return None
    return None


def _json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, default=str)
