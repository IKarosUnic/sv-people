"""Self-regulation, psychological breakdown and recovery.

Breakdown is modelled as a *continuous risk process*, not three magic
thresholds.  Two people at the same stress level can react differently because
the onset condition combines:

* intensity (acute and chronic stress, fatigue, loneliness),
* duration (ticks spent above their own danger line),
* constitution (neuroticism, conscientiousness, agreeableness, resilience),
* regulation capacity and current self-control,
* material and social resources,
* prior crises (sensitisation) and residual vulnerability.

A crisis is an episode with causes, a course, consequences and an end.  It is
never written into the person as a permanent trait.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

from saltbor.psychology.models import (
    CopingStrategy,
    CrisisEpisode,
    CrisisKind,
    PsychologicalState,
    _approach,
    _clamp,
)


@dataclass
class BodySignals:
    """Physical inputs that modulate the psychological trajectory."""

    energy: float = 1.0
    hunger: float = 0.0
    health: float = 1.0
    pain: float = 0.0
    illness_load: float = 0.0
    sleep_activity: bool = False
    social_contact: int = 0
    money: float = 80.0
    is_daytime: bool = True


@dataclass
class CrisisEvaluation:
    started: Optional[CrisisEpisode] = None
    ended: Optional[CrisisEpisode] = None
    relapsed: Optional[CrisisEpisode] = None
    risk: float = 0.0
    pressure: float = 0.0
    resistance: float = 0.0
    threshold: float = 1.0
    behaviours: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.behaviours is None:
            self.behaviours = []


class RegulationEngine:
    """Advances the causal psychological state and manages crisis episodes."""

    # ------------------------------------------------------------------
    # Continuous dynamics
    # ------------------------------------------------------------------

    def step(
        self,
        psych: PsychologicalState,
        human: Any,
        *,
        tick: int,
        elapsed_ticks: int,
        tick_minutes: int = 15,
        body: Optional[BodySignals] = None,
        support: Optional[float] = None,
    ) -> None:
        body = body or BodySignals()
        # Convert ticks to days; cognitive LOD may deliver several days at once.
        dt = max(0.0, elapsed_ticks * tick_minutes / 1440.0)
        if dt <= 0.0:
            return

        # Body buffers are read, never overwritten, so PhysicalState remains
        # the single source of truth for the body.
        psych.health_buffer = _clamp(body.health)
        psych.material_buffer = _clamp(body.money / 240.0)
        if support is not None:
            psych.perceived_support = _clamp(
                _approach(psych.perceived_support, support, 0.35, dt)
            )

        illness = _clamp(body.illness_load)
        sleep_debt = _clamp(max(0.0, 0.72 - body.energy))
        deprivation = _clamp(0.45 * body.hunger + 0.30 * sleep_debt + 0.25 * (1.0 - body.health) + 0.20 * illness)

        vulnerability = _clamp(
            0.45 * human.personality.effective_value("neuroticism")
            + 0.25 * (1.0 - human.personality.effective_value("conscientiousness"))
            + 0.15 * (1.0 - human.personality.effective_value("agreeableness"))
            + 0.15 * (1.0 - psych.resilience)
        )

        # --- acute stress ------------------------------------------------
        acute_target = _clamp(
            0.55 * psych.chronic_stress
            + 0.30 * deprivation
            + 0.15 * illness
            - 0.10 * psych.perceived_support
        )
        # Fast rise, slower recovery: the asymmetry is the point.
        acute_rate = 2.2 if acute_target > psych.acute_stress else 1.1
        psych.acute_stress = _approach(psych.acute_stress, acute_target, acute_rate, dt)

        # --- chronic stress ---------------------------------------------
        chronic_target = _clamp(
            0.12
            + 0.62 * psych.acute_stress
            + 0.22 * psych.loneliness
            + 0.14 * (1.0 - psych.perceived_support)
            - 0.10 * psych.hope
        )
        if chronic_target > psych.chronic_stress:
            rate = 0.24 * (0.55 + 0.90 * vulnerability)
        else:
            recovery = 0.055 * (0.45 + 0.90 * psych.resilience + 0.55 * psych.perceived_support)
            rate = max(0.012, recovery)
        psych.chronic_stress = _approach(psych.chronic_stress, chronic_target, rate, dt)

        # --- fatigue ------------------------------------------------------
        fatigue_target = _clamp(
            0.30 * psych.chronic_stress
            + 0.28 * psych.acute_stress
            + 0.42 * sleep_debt
            + 0.22 * illness
            + 0.10 * body.pain
        )
        fatigue_rate = 0.60 if fatigue_target > psych.mental_fatigue else (0.32 if not body.sleep_activity else 0.55)
        psych.mental_fatigue = _approach(psych.mental_fatigue, fatigue_target, fatigue_rate, dt)

        # --- self-control ------------------------------------------------
        control_target = _clamp(
            psych.self_control_baseline
            * (
                1.0
                - 0.50 * psych.chronic_stress
                - 0.34 * psych.mental_fatigue
                + 0.18 * psych.perceived_support
                + 0.10 * psych.hope
            )
            + 0.08 * (1.0 - psych.chronic_stress)
        )
        control_rate = 1.35 if control_target < psych.self_control else 0.30
        psych.self_control = _approach(psych.self_control, control_target, control_rate, dt)

        # --- anxiety / fear ----------------------------------------------
        anxiety_target = _clamp(
            0.34 * psych.acute_stress
            + 0.28 * psych.uncertainty
            + 0.22 * psych.fear
            + 0.16 * psych.threat_sensitivity * psych.chronic_stress
        )
        psych.anxiety = _approach(psych.anxiety, anxiety_target, 0.55, dt)

        fear_target = _clamp(0.04 + 0.30 * psych.acute_stress + 0.10 * psych.threat_sensitivity)
        psych.fear = _approach(psych.fear, fear_target, 0.90, dt)

        # --- sadness / anger / frustration -------------------------------
        sadness_target = _clamp(
            0.28 * psych.loneliness
            + 0.34 * max(0.0, psych.chronic_stress - 0.35)
            + 0.22 * (1.0 - psych.hope)
            + 0.10 * psych.loss_sensitivity
        )
        psych.sadness = _approach(psych.sadness, sadness_target, 0.20, dt)

        anger_target = _clamp(
            0.28 * psych.frustration
            + 0.22 * max(0.0, psych.chronic_stress - 0.45)
            + 0.10 * (1.0 - psych.regulation_capacity)
        )
        psych.anger = _approach(psych.anger, anger_target, 0.55, dt)

        frustration_target = _clamp(
            0.30 * psych.acute_stress
            + 0.22 * psych.chronic_stress
            + 0.16 * (1.0 - psych.self_control)
        )
        psych.frustration = _approach(psych.frustration, frustration_target, 0.85, dt)

        # --- loneliness ---------------------------------------------------
        contact_norm = _clamp(body.social_contact / 3.0)
        loneliness_target = _clamp(
            0.12
            + 0.55 * (1.0 - psych.perceived_support)
            + 0.20 * (1.0 - contact_norm)
            + 0.10 * psych.social_sensitivity
        )
        psych.loneliness = _approach(psych.loneliness, loneliness_target, 0.13, dt)

        # --- hope ---------------------------------------------------------
        hope_target = _clamp(
            0.18
            + 0.28 * (1.0 - psych.chronic_stress)
            + 0.20 * psych.perceived_support
            + 0.16 * (1.0 - psych.mental_fatigue)
            + 0.12 * psych.trust
            + 0.06 * psych.regulation_capacity
        )
        hope_rate = 0.11 if hope_target > psych.hope else 0.055
        psych.hope = _approach(psych.hope, hope_target, hope_rate, dt)

        # --- uncertainty ---------------------------------------------------
        uncertainty_target = _clamp(
            0.12
            + 0.36 * (1.0 - psych.self_control)
            + 0.24 * psych.acute_stress
            + 0.18 * (1.0 - psych.perceived_support)
        )
        psych.uncertainty = _approach(psych.uncertainty, uncertainty_target, 0.22, dt)

        # --- motivation ----------------------------------------------------
        motivation_target = _clamp(
            0.18 * psych.hope
            + 0.24 * body.energy
            + 0.22 * psych.self_control
            + 0.18 * (1.0 - psych.mental_fatigue)
            + 0.18 * (1.0 - psych.chronic_stress)
            - 0.05
        )
        psych.motivation = _approach(psych.motivation, motivation_target, 0.45, dt)

        # Trust moves very slowly; only relationships and betrayal should move
        # it quickly, and those arrive through appraisal.
        psych.trust = _clamp(psych.trust + (0.5 - psych.trust) * min(0.02 * dt, 0.02))

        # Residual crisis vulnerability fades over days but is not erased.
        psych.post_crisis_vulnerability = max(
            0.0, psych.post_crisis_vulnerability - 0.010 * dt
        )
        psych.last_update_tick = int(tick)

    # ------------------------------------------------------------------
    # Crisis risk
    # ------------------------------------------------------------------

    def risk_components(self, psych: PsychologicalState) -> tuple[float, float, float]:
        """Return (pressure, resistance, risk ratio)."""
        pressure = _clamp(
            0.34 * psych.chronic_stress
            + 0.22 * psych.acute_stress
            + 0.16 * psych.mental_fatigue
            + 0.14 * psych.loneliness
            + 0.14 * (1.0 - psych.self_control)
        )
        resistance = _clamp(
            0.30 * psych.resilience
            + 0.22 * psych.perceived_support
            + 0.20 * psych.self_control
            + 0.14 * psych.hope
            + 0.14 * psych.material_buffer
        )
        risk = pressure / max(0.18, resistance + 0.22)
        return pressure, resistance, risk

    def evaluate_crisis(
        self,
        psych: PsychologicalState,
        human: Any,
        *,
        tick: int,
        elapsed_ticks: int,
        tick_minutes: int = 15,
        support: Optional[float] = None,
    ) -> CrisisEvaluation:
        # Crisis clocks are expressed in 15-minute units regardless of the
        # caller's tick length.  Without this, a daily macro-step experiment
        # would produce crises in one day of simulated time while a 15-minute
        # run would need weeks, and the two would not be comparable.
        units = max(1, int(round(elapsed_ticks * max(1, tick_minutes) / 15.0)))
        pressure, resistance, risk = self.risk_components(psych)
        n = human.personality.effective_value("neuroticism")
        c = human.personality.effective_value("conscientiousness")
        a = human.personality.effective_value("agreeableness")
        e = human.personality.effective_value("extraversion")

        vulnerability = _clamp(0.42 * n + 0.22 * (1.0 - c) + 0.18 * (1.0 - a) + 0.18 * (1.0 - psych.resilience))

        # Threshold is individual, not universal.  Prior crises sensitise the
        # system (lower threshold); residual vulnerability opens a relapse
        # window.  A floor prevents the threshold from collapsing to zero.
        threshold = 1.00 + 0.10 * vulnerability - 0.06 * psych.resilience
        threshold -= 0.035 * min(4, psych.crisis_count)      # sensitisation
        threshold -= 0.18 * psych.post_crisis_vulnerability   # relapse window
        threshold = max(0.55, threshold)

        required = int(8 + 44 * (1.0 - vulnerability))
        required = max(6, required)

        if risk > threshold:
            psych.ticks_in_danger += units
        else:
            psych.ticks_in_danger = max(0, psych.ticks_in_danger - units * 2)

        evaluation = CrisisEvaluation(
            risk=round(risk, 4),
            pressure=round(pressure, 4),
            resistance=round(resistance, 4),
            threshold=round(threshold, 4),
        )

        if psych.active_crisis is None or not psych.active_crisis.is_active:
            if psych.ticks_in_danger >= required and risk > threshold:
                kind = self._select_kind(psych, human, n=n, c=c, a=a, e=e)
                severity = _clamp(risk - threshold + 0.10)
                episode = CrisisEpisode(
                    kind=kind,
                    start_tick=int(tick),
                    peak_tick=int(tick),
                    peak_severity=round(severity, 4),
                    severity=round(severity, 4),
                    causes={
                        "chronic_stress": round(psych.chronic_stress, 3),
                        "acute_stress": round(psych.acute_stress, 3),
                        "mental_fatigue": round(psych.mental_fatigue, 3),
                        "loneliness": round(psych.loneliness, 3),
                        "low_self_control": round(1.0 - psych.self_control, 3),
                        "perceived_support": round(psych.perceived_support, 3),
                    },
                    triggers=[
                        f"presión={pressure:.2f}",
                        f"resistencia={resistance:.2f}",
                        f"riesgo={risk:.2f} > umbral={threshold:.2f}",
                        f"duración={psych.ticks_in_danger} ticks",
                    ],
                    behaviours=self._behaviours(kind),
                )
                episode.relapsed = psych.post_crisis_vulnerability >= 0.12
                psych.active_crisis = episode
                psych.crisis_history.append(episode)
                if len(psych.crisis_history) > 20:
                    psych.crisis_history = psych.crisis_history[-20:]
                psych.crisis_count += 1
                psych.stats["crises"] = psych.stats.get("crises", 0) + 1
                evaluation.started = episode
                evaluation.relapsed = episode if episode.relapsed else None
                evaluation.behaviours = list(episode.behaviours)
                psych.recovery_ticks = 0
                return evaluation

        active = psych.active_crisis
        if active is None or not active.is_active:
            return evaluation

        # --- course of an active episode ---------------------------------
        active.severity = round(
            _clamp(0.55 * active.severity + 0.45 * _clamp(risk - threshold + 0.10)), 4
        )
        if active.severity >= active.peak_severity:
            active.peak_severity = active.severity
            active.peak_tick = int(tick)

        # Recovery needs sustained relief, not a single good tick.
        relief_condition = risk < (threshold - 0.04) and psych.self_control > 0.28
        if relief_condition:
            psych.recovery_ticks += units
            active.recovery_progress = _clamp(
                active.recovery_progress
                + (0.012 + 0.010 * psych.resilience + 0.008 * psych.perceived_support)
                * units / 8.0
            )
        else:
            psych.recovery_ticks = max(0, psych.recovery_ticks - units // 2)
            active.recovery_progress = max(0.0, active.recovery_progress - 0.006 * units / 8.0)

        # No crisis is permanent: after a maximum span the episode closes even
        # if the underlying conditions remain, and residual vulnerability keeps
        # the possibility of relapse honest.
        duration = int((int(tick) - active.start_tick) * units)
        max_duration = int(96 + 240 * active.peak_severity)
        if active.recovery_progress >= 1.0 or duration >= max_duration:
            active.is_active = False
            active.ended_tick = int(tick)
            active.recovery_progress = 1.0 if active.recovery_progress >= 1.0 else 0.6
            active.residual_vulnerability = round(
                _clamp(0.20 + 0.45 * active.peak_severity * (1.0 - psych.resilience)), 4
            )
            psych.post_crisis_vulnerability = max(
                psych.post_crisis_vulnerability, active.residual_vulnerability
            )
            psych.recovery_ticks = 0
            psych.ticks_in_danger = 0
            psych.active_crisis = None
            evaluation.ended = active
            evaluation.behaviours = []

        return evaluation

    # ------------------------------------------------------------------
    # Crisis phenomenology (modelled behaviours)
    # ------------------------------------------------------------------

    @staticmethod
    def _select_kind(
        psych: PsychologicalState,
        human: Any,
        *,
        n: float,
        c: float,
        a: float,
        e: float,
    ) -> CrisisKind:
        if psych.anger > 0.35 and a < 0.45:
            return CrisisKind.DEFENSIVE_HOSTILITY
        if psych.loneliness > 0.55 and e < 0.45:
            return CrisisKind.WITHDRAWAL
        if psych.impulsivity > 0.60 and c < 0.55:
            return CrisisKind.IMPULSIVE_COLLAPSE
        if c >= 0.60 and psych.mental_fatigue > 0.55:
            return CrisisKind.DISORGANIZATION
        if psych.self_control < 0.25:
            return CrisisKind.AVOIDANT_DISENGAGEMENT
        return CrisisKind.ACUTE_OVERLOAD

    @staticmethod
    def _behaviours(kind: CrisisKind) -> list[str]:
        mapping = {
            CrisisKind.ACUTE_OVERLOAD: [
                "concentración intermitente",
                "decisiones evitadas",
                "irritabilidad",
            ],
            CrisisKind.WITHDRAWAL: [
                "aislamiento",
                "abandono de actividades sociales",
                "silencio prolongado",
            ],
            CrisisKind.IMPULSIVE_COLLAPSE: [
                "decisiones precipitadas",
                "búsqueda compulsiva de alivio",
                "gasto impulsivo",
            ],
            CrisisKind.DISORGANIZATION: [
                "desorganización de objetivos",
                "procrastinación",
                "pérdida temporal de concentración",
            ],
            CrisisKind.AVOIDANT_DISENGAGEMENT: [
                "conducta evitativa",
                "abandono de responsabilidades",
                "evitación de problemas financieros",
            ],
            CrisisKind.DEFENSIVE_HOSTILITY: [
                "reacciones defensivas",
                "conflictos interpersonales",
                "respuestas agresivas",
            ],
        }
        return mapping.get(kind, [])

    # ------------------------------------------------------------------
    # Decision modulation
    # ------------------------------------------------------------------

    def decision_modifiers(self, psych: PsychologicalState) -> dict[str, float]:
        """Bounded modifiers consumed by the decision engine.

        Under load the agent does not become irrational: it changes the weights
        of its options (rest, withdrawal, risk, planning horizon).  All values
        are small enough that a strong goal can still override them.
        """
        load = psych.psychological_load
        crisis = psych.active_crisis
        severity = crisis.severity if crisis is not None and crisis.is_active else 0.0
        kind = crisis.kind.value if crisis is not None and crisis.is_active else ""

        fatigue = psych.mental_fatigue
        return {
            "psychological_load": round(load, 4),
            "rest_weight": round(0.35 * fatigue + 0.25 * psych.acute_stress + 0.20 * severity, 4),
            "social_weight": round(
                0.30 * psych.loneliness - 0.35 * severity * (1.0 if kind == "withdrawal" else 0.4),
                4,
            ),
            "work_weight": round(
                0.22 * psych.motivation - 0.28 * fatigue - 0.18 * psych.chronic_stress, 4
            ),
            "planning_horizon": round(
                _clamp(0.55 + 0.25 * psych.hope + 0.15 * psych.self_control - 0.35 * severity, 0.10, 1.0),
                4,
            ),
            "risk_perception": round(
                _clamp(0.45 + 0.30 * psych.threat_sensitivity + 0.25 * psych.chronic_stress + 0.15 * severity, 0.0, 1.0),
                4,
            ),
            "help_seeking": round(
                _clamp(0.20 + 0.35 * psych.perceived_support + 0.25 * psych.hope - 0.30 * psych.self_control * (1.0 - psych.perceived_support), 0.0, 1.0),
                4,
            ),
            "avoidance": round(
                _clamp(0.35 * (1.0 - psych.self_control) + 0.30 * severity + 0.12 * psych.mental_fatigue, 0.0, 1.0),
                4,
            ),
            "impulsivity": round(
                _clamp(psych.impulsivity + 0.30 * severity * (1.0 - psych.self_control), 0.0, 1.0),
                4,
            ),
            "crisis_severity": round(severity, 4),
            "crisis_kind": kind,
            "coping_preference_problem": round(
                psych.coping.preference(CopingStrategy.SEEK_WORK), 4
            ),
        }


__all__ = ["BodySignals", "CrisisEvaluation", "RegulationEngine"]
