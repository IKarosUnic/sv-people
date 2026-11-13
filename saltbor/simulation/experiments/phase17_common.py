"""Shared harness for the Phase 1.7 psychological experiments.

Scientific hygiene rules:

* Every experiment states its hypotheses before running.
* Where a comparison is possible, a control arm is included.
* Multiple seeds are used for stochastic components (support, tie-breaking).
* Effect sizes and confidence intervals are reported, not only p-values or
  means.
* A supported hypothesis means "the mechanism behaved as stated under these
  conditions", never "the psychological claim is proven".
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

from saltbor.core.types import ActivityType, EmotionType, RelationshipType
from saltbor.events.types import EventType, SimulationEvent
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.psychology.engine import PsychologicalEngine
from saltbor.psychology.models import CopingCategory, CopingStrategy, PsychologicalState
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.social.engine import SocialEngine

SUPPORTED = "HYPOTHESIS_SUPPORTED"
REJECTED = "HYPOTHESIS_REJECTED"
INCONCLUSIVE = "INCONCLUSIVE"
ERROR = "EXPERIMENT_ERROR"


def make_agent(
    name: str = "Sujeto",
    *,
    serial: int = 1,
    age: float = 32.0,
    money: float = 80.0,
    health: float = 1.0,
    energy: float = 1.0,
    hunger: float = 0.1,
    traits: Optional[dict[str, float]] = None,
    partner: Optional[str] = None,
) -> SyntheticHuman:
    human = SyntheticHuman.create(
        name=name,
        age=age,
        money=money,
        seed=serial,
        serial=serial,
    )
    human.physical_state.health = health
    human.physical_state.energy = energy
    human.physical_state.hunger = hunger
    if partner:
        human.romantic_partner_id = partner
    for trait, value in (traits or {}).items():
        tv = getattr(human.personality.traits, trait, None)
        if tv is not None:
            tv.base_value = float(value)
            tv.current_value = float(value)
            tv.temperament_value = float(value)
    return human


def pop_of(*humans: SyntheticHuman) -> PopulationRegistry:
    registry = PopulationRegistry()
    for human in humans:
        registry.register(human)
    return registry


def event(
    event_type: EventType,
    human: SyntheticHuman,
    tick: int,
    *,
    importance: float = 0.8,
    target: Optional[SyntheticHuman] = None,
    data: Optional[dict[str, Any]] = None,
) -> SimulationEvent:
    return SimulationEvent(
        event_type=event_type,
        tick=int(tick),
        source_human_id=human.uid,
        target_human_id=target.uid if target is not None else None,
        location_id=getattr(human.physical_state, "current_location_id", None),
        data=data or {},
        importance=importance,
    )


def run_days(
    engine: PsychologicalEngine,
    population: PopulationRegistry,
    days: int,
    *,
    start_tick: int = 0,
    events_by_day: Optional[dict[int, list[SimulationEvent]]] = None,
    social: Optional[SocialEngine] = None,
    day_minutes: int = 1440,
    on_day: Optional[Callable[[int, PsychologicalEngine], None]] = None,
) -> int:
    """Advance by whole simulated days with one psychological macro-step/day.

    The engine integrates elapsed time analytically, so one call per day is
    equivalent to 96 calls of 15 minutes for the continuous variables.  Crisis
    and recovery clocks are normalised to 15-minute units inside the engine.
    """
    events_by_day = events_by_day or {}
    tick = start_tick
    for d in range(days):
        tick = start_tick + d
        for evt in events_by_day.get(d, []):
            engine.process_events([evt], population, social=social)
        engine.step_population(
            population,
            tick,
            social=social,
            tick_minutes=day_minutes,
            force_all=True,
        )
        if on_day is not None:
            on_day(d, engine)
    return tick


def support_network(
    agent: SyntheticHuman,
    *,
    level: float = 0.75,
    family: bool = True,
    serial_base: int = 50_000,
) -> tuple[SocialEngine, list[SyntheticHuman]]:
    """Create a small, explicit support network for an experiment arm.

    The network is real ``SocialEngine`` state, so the support assessment and
    request paths read the same structures they use in a full simulation.
    """
    social = SocialEngine()
    partners = []
    for i, name in enumerate(("Apoyo A", "Apoyo B", "Apoyo C")):
        partner = make_agent(name, serial=serial_base + i, money=120.0, traits={"agreeableness": level})
        partner.physical_state.home_location_id = agent.physical_state.home_location_id
        partner.physical_state.current_location_id = agent.physical_state.current_location_id
        tie(
            social,
            agent,
            partner,
            trust=level,
            affinity=level,
            familiarity=0.6,
            kind=RelationshipType.FAMILY if family and i == 0 else RelationshipType.CLOSE_FRIEND,
        )
        partners.append(partner)
    if partners:
        agent.romantic_partner_id = str(partners[0].uid)
    return social, partners


def tie(
    social: SocialEngine,
    a: SyntheticHuman,
    b: SyntheticHuman,
    *,
    trust: float = 0.7,
    affinity: float = 0.7,
    familiarity: float = 0.5,
    kind: RelationshipType = RelationshipType.FRIEND,
) -> None:
    rel = social.get_relationship(a.uid, b.uid)
    rel.trust = trust
    rel.affinity = affinity
    rel.familiarity = familiarity
    rel.relationship_type = kind
    rel.interaction_count = 8


def summary(values: list[float]) -> dict[str, float]:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return {"mean": 0.0, "sd": 0.0, "ci95": 0.0, "n": 0, "min": 0.0, "max": 0.0}
    n = len(clean)
    mean = statistics.fmean(clean)
    sd = statistics.stdev(clean) if n > 1 else 0.0
    ci = 1.96 * sd / math.sqrt(n) if n > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "ci95": round(ci, 4),
        "n": n,
        "min": round(min(clean), 4),
        "max": round(max(clean), 4),
    }


def cohens_d(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    mean_a, mean_b = statistics.fmean(a), statistics.fmean(b)
    var_a = statistics.variance(a)
    var_b = statistics.variance(b)
    pooled = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    if pooled == 0.0:
        return 0.0
    return round((mean_a - mean_b) / pooled, 3)


def stress_agent(
    engine: PsychologicalEngine,
    human: SyntheticHuman,
    *,
    chronic: Optional[float] = None,
    acute: Optional[float] = None,
    fatigue: Optional[float] = None,
    control: Optional[float] = None,
    loneliness: Optional[float] = None,
    support: Optional[float] = None,
) -> None:
    """Directly set a state for an experimental arm.

    Direct state injection is used only to establish initial conditions; the
    measurements always come from the subsequent dynamics, never from the
    injected value.
    """
    psych = engine.ensure(human)
    if chronic is not None:
        psych.chronic_stress = max(0.0, min(1.0, chronic))
    if acute is not None:
        psych.acute_stress = max(0.0, min(1.0, acute))
    if fatigue is not None:
        psych.mental_fatigue = max(0.0, min(1.0, fatigue))
    if control is not None:
        psych.self_control = max(0.0, min(1.0, control))
    if loneliness is not None:
        psych.loneliness = max(0.0, min(1.0, loneliness))
    if support is not None:
        psych.perceived_support = max(0.0, min(1.0, support))


def chronic_series(
    engine: PsychologicalEngine,
    human: SyntheticHuman,
    days: int,
    *,
    events_by_day: Optional[dict[int, list[SimulationEvent]]] = None,
    social: Optional[SocialEngine] = None,
) -> list[float]:
    pop = pop_of(human)
    series: list[float] = []
    for d in range(days):
        for evt in (events_by_day or {}).get(d, []):
            engine.process_events([evt], pop, social=social)
        engine.step_population(pop, d, social=social, tick_minutes=1440, force_all=True)
        series.append(round(human.psychology.chronic_stress, 4))
    return series


def dominant_emotion(engine: PsychologicalEngine, human: SyntheticHuman) -> str:
    profile = human.emotions.profile
    if not profile.active_emotions:
        return "quiescent"
    etype = max(profile.active_emotions.values(), key=lambda s: s.intensity).emotion_type
    return etype.value


def positive_emotions(human: SyntheticHuman) -> float:
    from saltbor.cognition.emotions.models import EMOTION_VALENCE

    return round(
        sum(
            max(0.0, EMOTION_VALENCE.get(state.emotion_type, 0.0)) * state.intensity
            for state in human.emotions.profile.active_emotions.values()
        ),
        4,
    )


def negative_emotions(human: SyntheticHuman) -> float:
    from saltbor.cognition.emotions.models import EMOTION_VALENCE

    return round(
        sum(
            max(0.0, -EMOTION_VALENCE.get(state.emotion_type, 0.0)) * state.intensity
            for state in human.emotions.profile.active_emotions.values()
        ),
        4,
    )


class Phase17Experiment(BaseExperiment):
    """Result plumbing shared by the 20 Phase 1.7 experiments."""

    def _hyp(
        self,
        hid: str,
        statement: str,
        status: str,
        metric: str = "",
        value: Any = None,
        detail: str = "",
    ) -> dict[str, Any]:
        return {
            "id": hid,
            "statement": statement,
            "status": status,
            "metric": metric,
            "value": value,
            "detail": detail,
        }

    def _finish(
        self,
        started: float,
        summary_text: str,
        hypotheses: list[dict[str, Any]],
        metrics: dict[str, Any],
        anomalies: Optional[list[str]] = None,
        design_valid: bool = True,
    ) -> ExperimentResult:
        duration = round(time.time() - started, 3)
        supported = sum(1 for h in hypotheses if h["status"] == SUPPORTED)
        rejected = sum(1 for h in hypotheses if h["status"] == REJECTED)
        inconclusive = sum(1 for h in hypotheses if h["status"] == INCONCLUSIVE)
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=design_valid,
            summary=summary_text,
            hypotheses=hypotheses,
            metrics={
                **metrics,
                "hypotheses_supported": supported,
                "hypotheses_rejected": rejected,
                "hypotheses_inconclusive": inconclusive,
                "duration_seconds": duration,
                "seeds": self.config.random_seed,
                "population_size": self.config.population_size,
            },
            observed_anomalies=anomalies or [],
            duration_seconds=duration,
            report_markdown=self._report(summary_text, hypotheses, metrics),
            raw_data={"hypotheses": hypotheses, "metrics": metrics},
        )

    @staticmethod
    def _report(summary_text: str, hypotheses: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
        lines = [f"## {summary_text}", "", "| Hypothesis | Status | Metric | Value |", "| --- | --- | --- | --- |"]
        for h in hypotheses:
            lines.append(f"| {h['id']}: {h['statement']} | {h['status']} | {h['metric']} | {h['value']} |")
        lines.append("")
        lines.append("Metrics: " + ", ".join(f"{k}={v}" for k, v in metrics.items()))
        return "\n".join(lines)
