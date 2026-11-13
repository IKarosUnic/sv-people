"""Adaptive coping: strategies with conditions, costs, benefits and learning.

The design follows two ideas rather than copying an implementation:

* FAtiMA-style appraisal/coping separation — an emotional reaction and the
  attempt to cope with it are distinct processes.
* OCC's consequence/agency structure — a coping option is chosen because it is
  expected to change a specific appraisal or condition, not because a strategy
  is labelled "good" or "bad".

Every strategy can relieve stress immediately and still worsen the situation
later.  ``CopingEpisode`` therefore stores both the immediate relief and a
follow-up outcome, and the individual learns preferences from realised results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.types import Tick
from saltbor.psychology.models import (
    CopingCategory,
    CopingEpisode,
    CopingStrategy,
    PsychologicalState,
    _clamp,
)
from saltbor.psychology.support import SupportAssessment, SupportEngine


@dataclass(frozen=True)
class CopingSpec:
    strategy: CopingStrategy
    category: CopingCategory
    label: str
    relief: float
    chronic_effect: float = 0.0       # per use; negative improves, positive worsens
    control_effect: float = 0.0
    hope_effect: float = 0.0
    loneliness_effect: float = 0.0
    fatigue_effect: float = 0.0
    money_delta: float = 0.0
    energy_delta: float = 0.0
    support_effect: float = 0.0
    risk: float = 0.0
    social_channel: str = ""          # "" | emotional | financial | material
    follow_up_ticks: int = 48
    cost_label: str = ""


TRAIT_AFFINITY: dict[CopingStrategy, dict[str, float]] = {
    CopingStrategy.SEEK_WORK: {"conscientiousness": 0.30, "persistence": 0.25, "openness": 0.05},
    CopingStrategy.REQUEST_FINANCIAL_HELP: {"agreeableness": 0.20, "extraversion": 0.15, "neuroticism": 0.10},
    CopingStrategy.NEGOTIATE_DEBT: {"conscientiousness": 0.25, "agreeableness": 0.15},
    CopingStrategy.ASK_FIADO: {"extraversion": 0.20, "agreeableness": 0.15},
    CopingStrategy.SEEK_COMMUNITY_SUPPORT: {"extraversion": 0.20, "agreeableness": 0.25},
    CopingStrategy.REDUCE_EXPENSES: {"conscientiousness": 0.30, "patience": 0.15},
    CopingStrategy.SELL_BELONGINGS: {"conscientiousness": 0.15, "risk_tolerance": -0.10},
    CopingStrategy.SEEK_MEDICAL_TREATMENT: {"conscientiousness": 0.25, "neuroticism": 0.15},
    CopingStrategy.RESOLVE_CONFLICT: {"agreeableness": 0.30, "patience": 0.15},
    CopingStrategy.LEARN_SKILL: {"openness": 0.30, "persistence": 0.20, "conscientiousness": 0.10},
    CopingStrategy.SEEK_COMPANY: {"extraversion": 0.35, "agreeableness": 0.15},
    CopingStrategy.TALK_TO_FAMILY: {"agreeableness": 0.25, "extraversion": 0.15},
    CopingStrategy.SEEK_CONSOLATION: {"agreeableness": 0.25, "neuroticism": 0.15},
    CopingStrategy.WITHDRAW_TEMPORARILY: {"extraversion": -0.30, "neuroticism": 0.15},
    CopingStrategy.REST: {"conscientiousness": 0.10, "neuroticism": 0.10},
    CopingStrategy.RECREATION: {"extraversion": 0.20, "openness": 0.15},
    CopingStrategy.SPIRITUAL_SUPPORT: {"agreeableness": 0.15, "openness": 0.10},
    CopingStrategy.EXPRESS_SADNESS: {"neuroticism": 0.20, "extraversion": 0.05},
    CopingStrategy.TEMPORARY_AVOIDANCE: {"neuroticism": 0.20, "conscientiousness": -0.15},
    CopingStrategy.DENIAL: {"neuroticism": 0.25, "conscientiousness": -0.25},
    CopingStrategy.PROCRASTINATION: {"conscientiousness": -0.30, "patience": -0.10},
    CopingStrategy.PROLONGED_ISOLATION: {"extraversion": -0.35, "neuroticism": 0.20},
    CopingStrategy.ABANDON_RESPONSIBILITIES: {"conscientiousness": -0.35, "persistence": -0.20},
    CopingStrategy.AGGRESSIVE_REACTION: {"agreeableness": -0.30, "neuroticism": 0.20},
    CopingStrategy.RASH_DECISION: {"risk_tolerance": 0.30, "patience": -0.20},
    CopingStrategy.FINANCIAL_AVOIDANCE: {"conscientiousness": -0.25, "neuroticism": 0.15},
}


COPING_SPECS: dict[CopingStrategy, CopingSpec] = {
    # ---------------- problem-focused ----------------
    CopingStrategy.SEEK_WORK: CopingSpec(
        CopingStrategy.SEEK_WORK, CopingCategory.PROBLEM_FOCUSED, "Buscar empleo",
        relief=0.20, chronic_effect=-0.035, control_effect=0.035, hope_effect=0.025,
        money_delta=-1.0, energy_delta=-0.05, fatigue_effect=0.02, risk=0.20,
        follow_up_ticks=96, cost_label="tiempo y pasaje",
    ),
    CopingStrategy.REQUEST_FINANCIAL_HELP: CopingSpec(
        CopingStrategy.REQUEST_FINANCIAL_HELP, CopingCategory.PROBLEM_FOCUSED, "Solicitar ayuda económica",
        relief=0.24, chronic_effect=-0.045, control_effect=0.02, hope_effect=0.03,
        support_effect=0.04, risk=0.30, social_channel="financial",
        follow_up_ticks=72, cost_label="capital social / reciprocidad",
    ),
    CopingStrategy.NEGOTIATE_DEBT: CopingSpec(
        CopingStrategy.NEGOTIATE_DEBT, CopingCategory.PROBLEM_FOCUSED, "Negociar una deuda",
        relief=0.18, chronic_effect=-0.05, control_effect=0.03, hope_effect=0.02,
        energy_delta=-0.03, risk=0.15, follow_up_ticks=72, cost_label="tiempo y desgaste",
    ),
    CopingStrategy.ASK_FIADO: CopingSpec(
        CopingStrategy.ASK_FIADO, CopingCategory.PROBLEM_FOCUSED, "Pedir fiado",
        relief=0.16, chronic_effect=-0.015, control_effect=0.01, hope_effect=0.01,
        money_delta=6.0, support_effect=-0.02, risk=0.30, social_channel="material",
        follow_up_ticks=96, cost_label="obligación y deuda",
    ),
    CopingStrategy.SEEK_COMMUNITY_SUPPORT: CopingSpec(
        CopingStrategy.SEEK_COMMUNITY_SUPPORT, CopingCategory.PROBLEM_FOCUSED, "Buscar apoyo comunitario",
        relief=0.24, chronic_effect=-0.05, hope_effect=0.03, support_effect=0.08,
        energy_delta=-0.04, risk=0.20, social_channel="material",
        follow_up_ticks=96, cost_label="tiempo y exposición pública",
    ),
    CopingStrategy.REDUCE_EXPENSES: CopingSpec(
        CopingStrategy.REDUCE_EXPENSES, CopingCategory.PROBLEM_FOCUSED, "Reducir gastos",
        relief=0.12, chronic_effect=-0.04, control_effect=0.025, hope_effect=0.01,
        money_delta=2.0, risk=0.05, follow_up_ticks=72, cost_label="renuncia a consumo",
    ),
    CopingStrategy.SELL_BELONGINGS: CopingSpec(
        CopingStrategy.SELL_BELONGINGS, CopingCategory.PROBLEM_FOCUSED, "Vender pertenencias",
        relief=0.20, chronic_effect=-0.02, control_effect=0.01, hope_effect=-0.01,
        money_delta=12.0, risk=0.20, follow_up_ticks=96, cost_label="pérdida material",
    ),
    CopingStrategy.SEEK_MEDICAL_TREATMENT: CopingSpec(
        CopingStrategy.SEEK_MEDICAL_TREATMENT, CopingCategory.PROBLEM_FOCUSED, "Buscar tratamiento médico",
        relief=0.22, chronic_effect=-0.06, hope_effect=0.04,
        money_delta=-6.0, energy_delta=-0.04, risk=0.05, follow_up_ticks=72,
        cost_label="cuota y tiempo",
    ),
    CopingStrategy.RESOLVE_CONFLICT: CopingSpec(
        CopingStrategy.RESOLVE_CONFLICT, CopingCategory.PROBLEM_FOCUSED, "Resolver un conflicto",
        relief=0.22, chronic_effect=-0.05, control_effect=0.03, hope_effect=0.02,
        energy_delta=-0.04, risk=0.20, social_channel="emotional",
        follow_up_ticks=72, cost_label="tiempo y exposición",
    ),
    CopingStrategy.LEARN_SKILL: CopingSpec(
        CopingStrategy.LEARN_SKILL, CopingCategory.PROBLEM_FOCUSED, "Aprender una habilidad",
        relief=0.10, chronic_effect=-0.03, control_effect=0.04, hope_effect=0.035,
        money_delta=-2.0, energy_delta=-0.06, fatigue_effect=0.03, risk=0.10,
        follow_up_ticks=192, cost_label="tiempo y esfuerzo",
    ),
    # ---------------- emotion-focused ----------------
    CopingStrategy.SEEK_COMPANY: CopingSpec(
        CopingStrategy.SEEK_COMPANY, CopingCategory.EMOTION_FOCUSED, "Buscar compañía",
        relief=0.22, chronic_effect=-0.02, loneliness_effect=-0.12, hope_effect=0.02,
        support_effect=0.03, energy_delta=-0.03, risk=0.05, social_channel="emotional",
        follow_up_ticks=24, cost_label="tiempo",
    ),
    CopingStrategy.TALK_TO_FAMILY: CopingSpec(
        CopingStrategy.TALK_TO_FAMILY, CopingCategory.EMOTION_FOCUSED, "Conversar con familiares",
        relief=0.26, chronic_effect=-0.03, loneliness_effect=-0.15, hope_effect=0.03,
        support_effect=0.05, energy_delta=-0.03, risk=0.02, social_channel="emotional",
        follow_up_ticks=24, cost_label="tiempo",
    ),
    CopingStrategy.SEEK_CONSOLATION: CopingSpec(
        CopingStrategy.SEEK_CONSOLATION, CopingCategory.EMOTION_FOCUSED, "Buscar consuelo",
        relief=0.28, chronic_effect=-0.02, loneliness_effect=-0.10, hope_effect=0.02,
        support_effect=0.05, risk=0.04, social_channel="emotional",
        follow_up_ticks=24, cost_label="tiempo y vulnerabilidad",
    ),
    CopingStrategy.WITHDRAW_TEMPORARILY: CopingSpec(
        CopingStrategy.WITHDRAW_TEMPORARILY, CopingCategory.EMOTION_FOCUSED, "Aislarse temporalmente",
        relief=0.14, chronic_effect=0.025, loneliness_effect=0.05,
        energy_delta=0.02, risk=0.20, follow_up_ticks=48, cost_label="aislamiento",
    ),
    CopingStrategy.REST: CopingSpec(
        CopingStrategy.REST, CopingCategory.EMOTION_FOCUSED, "Descansar",
        relief=0.20, chronic_effect=-0.025, fatigue_effect=-0.10,
        energy_delta=0.08, risk=0.03, follow_up_ticks=24, cost_label="tiempo",
    ),
    CopingStrategy.RECREATION: CopingSpec(
        CopingStrategy.RECREATION, CopingCategory.EMOTION_FOCUSED, "Actividad recreativa",
        relief=0.24, chronic_effect=-0.02, hope_effect=0.02,
        money_delta=-3.0, energy_delta=-0.03, risk=0.03, follow_up_ticks=24,
        cost_label="dinero y tiempo",
    ),
    CopingStrategy.SPIRITUAL_SUPPORT: CopingSpec(
        CopingStrategy.SPIRITUAL_SUPPORT, CopingCategory.EMOTION_FOCUSED, "Apoyo espiritual",
        relief=0.20, chronic_effect=-0.02, hope_effect=0.04, loneliness_effect=-0.05,
        risk=0.02, follow_up_ticks=24, cost_label="tiempo",
    ),
    CopingStrategy.EXPRESS_SADNESS: CopingSpec(
        CopingStrategy.EXPRESS_SADNESS, CopingCategory.EMOTION_FOCUSED, "Expresar tristeza",
        relief=0.12, chronic_effect=-0.015, risk=0.05, follow_up_ticks=24,
        cost_label="exposición emocional",
    ),
    CopingStrategy.TEMPORARY_AVOIDANCE: CopingSpec(
        CopingStrategy.TEMPORARY_AVOIDANCE, CopingCategory.EMOTION_FOCUSED, "Evitar temporalmente",
        relief=0.14, chronic_effect=0.02, loneliness_effect=0.02,
        risk=0.25, follow_up_ticks=48, cost_label="postergación",
    ),
    # ---------------- avoidant / dysregulated ----------------
    CopingStrategy.DENIAL: CopingSpec(
        CopingStrategy.DENIAL, CopingCategory.AVOIDANT, "Negación",
        relief=0.12, chronic_effect=0.05, control_effect=-0.03, hope_effect=-0.02,
        risk=0.40, follow_up_ticks=72, cost_label="problema no atendido",
    ),
    CopingStrategy.PROCRASTINATION: CopingSpec(
        CopingStrategy.PROCRASTINATION, CopingCategory.AVOIDANT, "Procrastinación",
        relief=0.10, chronic_effect=0.04, control_effect=-0.03,
        risk=0.35, follow_up_ticks=72, cost_label="acumulación de pendientes",
    ),
    CopingStrategy.PROLONGED_ISOLATION: CopingSpec(
        CopingStrategy.PROLONGED_ISOLATION, CopingCategory.AVOIDANT, "Aislamiento prolongado",
        relief=0.08, chronic_effect=0.06, loneliness_effect=0.15, support_effect=-0.06,
        risk=0.45, follow_up_ticks=96, cost_label="deterioro de vínculos",
    ),
    CopingStrategy.ABANDON_RESPONSIBILITIES: CopingSpec(
        CopingStrategy.ABANDON_RESPONSIBILITIES, CopingCategory.AVOIDANT, "Abandonar responsabilidades",
        relief=0.12, chronic_effect=0.07, control_effect=-0.05, support_effect=-0.05,
        risk=0.50, follow_up_ticks=96, cost_label="consecuencias diferidas",
    ),
    CopingStrategy.AGGRESSIVE_REACTION: CopingSpec(
        CopingStrategy.AGGRESSIVE_REACTION, CopingCategory.AVOIDANT, "Reacción agresiva",
        relief=0.10, chronic_effect=0.08, support_effect=-0.10, risk=0.55,
        social_channel="emotional", follow_up_ticks=72,
        cost_label="ruptura de vínculos y reputación",
    ),
    CopingStrategy.RASH_DECISION: CopingSpec(
        CopingStrategy.RASH_DECISION, CopingCategory.AVOIDANT, "Decisión precipitada",
        relief=0.08, chronic_effect=0.09, control_effect=-0.04,
        money_delta=-8.0, risk=0.55, follow_up_ticks=96, cost_label="pérdida material",
    ),
    CopingStrategy.FINANCIAL_AVOIDANCE: CopingSpec(
        CopingStrategy.FINANCIAL_AVOIDANCE, CopingCategory.AVOIDANT, "Evitar los problemas financieros",
        relief=0.10, chronic_effect=0.06, control_effect=-0.04, hope_effect=-0.02,
        risk=0.40, follow_up_ticks=96, cost_label="deuda y mora",
    ),
}


@dataclass
class CopingContext:
    stress: float
    chronic_stress: float
    self_control: float
    hope: float
    loneliness: float
    sadness: float
    anger: float
    mental_fatigue: float
    support: float
    money: float
    energy: float
    health: float
    impulsivity: float
    has_close_tie: bool = False
    has_family_tie: bool = False
    has_partner: bool = False
    is_employed: bool = True
    has_debt: bool = False
    has_dependents: bool = False
    tradition_value: float = 0.5
    traits: dict[str, float] = field(default_factory=dict)


@dataclass
class CopingChoice:
    spec: CopingSpec
    utility: float
    reasons: list[str] = field(default_factory=list)


class AdaptiveCopingEngine:
    """Selects, executes and evaluates coping strategies."""

    def build_context(
        self,
        human: Any,
        psych: PsychologicalState,
        assessment: Optional[SupportAssessment] = None,
    ) -> CopingContext:
        traits = human.personality.traits
        values = getattr(traits, "personal_values", {}) or {}
        employment = getattr(human, "employment_status", None)
        employed = str(getattr(employment, "value", employment)) not in ("unemployed", "None", "")
        assessment = assessment or SupportAssessment()
        return CopingContext(
            stress=psych.acute_stress,
            chronic_stress=psych.chronic_stress,
            self_control=psych.self_control,
            hope=psych.hope,
            loneliness=psych.loneliness,
            sadness=psych.sadness,
            anger=psych.anger,
            mental_fatigue=psych.mental_fatigue,
            support=assessment.perceived_support,
            money=float(getattr(human.physical_state, "money", 0.0)),
            energy=float(getattr(human.physical_state, "energy", 1.0)),
            health=float(getattr(human.physical_state, "health", 1.0)),
            impulsivity=psych.impulsivity,
            has_close_tie=assessment.intimate_ties > 0,
            has_family_tie=assessment.family_ties > 0,
            has_partner=assessment.partner_tie > 0.05,
            is_employed=employed,
            has_debt=bool(getattr(human, "has_pending_loan", False)),
            has_dependents=bool(
                getattr(human, "dependent_children_ids", [])
                or getattr(human, "elderly_dependents_ids", [])
            ),
            tradition_value=float(values.get("tradition", 0.5)),
            traits={
                name: traits.effective_value(name)
                for name in (
                    "openness", "conscientiousness", "extraversion", "agreeableness",
                    "neuroticism", "risk_tolerance", "patience", "persistence",
                )
            },
        )

    # ------------------------------------------------------------------
    # Feasibility and salience
    # ------------------------------------------------------------------

    def is_feasible(self, spec: CopingSpec, ctx: CopingContext) -> tuple[bool, str]:
        s = spec.strategy
        if ctx.energy < 0.12:
            return False, "sin energía"
        if spec.money_delta < 0 and ctx.money + spec.money_delta < 0:
            return False, "sin dinero suficiente"
        if s == CopingStrategy.SEEK_WORK and ctx.is_employed:
            return False, "ya tiene empleo"
        if s == CopingStrategy.SEEK_MEDICAL_TREATMENT and ctx.health >= 0.82:
            return False, "sin necesidad médica"
        if s in (
            CopingStrategy.REQUEST_FINANCIAL_HELP,
            CopingStrategy.TALK_TO_FAMILY,
            CopingStrategy.SEEK_CONSOLATION,
            CopingStrategy.SEEK_COMPANY,
        ) and not ctx.has_close_tie:
            return False, "sin vínculo disponible"
        if s == CopingStrategy.TALK_TO_FAMILY and not ctx.has_family_tie:
            return False, "sin familiares en la red"
        if s == CopingStrategy.SEEK_COMMUNITY_SUPPORT and ctx.support < 0.18:
            return False, "sin red comunitaria"
        if s == CopingStrategy.SPIRITUAL_SUPPORT and ctx.tradition_value < 0.30:
            return False, "no corresponde a sus valores"
        if s == CopingStrategy.RESOLVE_CONFLICT and ctx.anger < 0.12:
            return False, "sin conflicto activo"
        if s == CopingStrategy.NEGOTIATE_DEBT and not (ctx.has_debt or ctx.money < 45):
            return False, "sin deuda relevante"
        if s == CopingStrategy.FINANCIAL_AVOIDANCE and ctx.money > 60:
            return False, "sin presión financiera"
        if s in (CopingStrategy.AGGRESSIVE_REACTION, CopingStrategy.RASH_DECISION) and ctx.self_control > 0.55:
            return False, "regulación suficiente"
        if s == CopingStrategy.ABANDON_RESPONSIBILITIES and not (ctx.has_dependents or ctx.chronic_stress > 0.55):
            return False, "sin responsabilidades críticas"
        return True, ""

    def category_salience(self, category: CopingCategory, ctx: CopingContext) -> float:
        if category == CopingCategory.PROBLEM_FOCUSED:
            return _clamp(
                0.30 * ctx.stress
                + 0.28 * ctx.chronic_stress
                + 0.22 * (0.5 + 0.5 * ctx.self_control)
                + 0.10 * min(1.0, ctx.money / 80.0)
                + 0.10 * (0.4 + 0.6 * ctx.hope)
            )
        if category == CopingCategory.EMOTION_FOCUSED:
            return _clamp(
                0.30 * ctx.sadness
                + 0.30 * ctx.loneliness
                + 0.22 * ctx.stress
                + 0.18 * (1.0 - ctx.self_control)
            )
        return _clamp(
            0.34 * (1.0 - ctx.self_control)
            + 0.26 * ctx.chronic_stress
            + 0.20 * ctx.mental_fatigue
            + 0.20 * ctx.impulsivity
        )

    def choose(
        self,
        human: Any,
        psych: PsychologicalState,
        assessment: Optional[SupportAssessment] = None,
    ) -> Optional[CopingChoice]:
        """Rank feasible strategies and return the best one."""
        ctx = self.build_context(human, psych, assessment)
        salience = {
            cat: self.category_salience(cat, ctx) for cat in CopingCategory
        }
        best: Optional[CopingChoice] = None
        for spec in COPING_SPECS.values():
            ok, reason = self.is_feasible(spec, ctx)
            if not ok:
                continue
            affinity = 0.0
            for trait, weight in TRAIT_AFFINITY.get(spec.strategy, {}).items():
                value = ctx.traits.get(trait, 0.5)
                affinity += weight * (value - 0.5) * 2.0
            preference = psych.coping.preference(spec.strategy)
            cost = abs(spec.money_delta) / 60.0 + abs(spec.energy_delta) + spec.fatigue_effect
            expected_long = -spec.chronic_effect * 3.0
            utility = (
                0.55 * salience[spec.category]
                + 0.45 * spec.relief * (0.55 + 0.9 * preference)
                + 0.20 * expected_long
                + 0.16 * affinity
                - 0.22 * spec.risk * (0.4 + 0.6 * (1.0 - ctx.self_control))
                - 0.12 * cost
            )
            # Stable tie-breaking jitter (same person + tick + strategy).
            utility += 0.005 * _stable_unit(
                getattr(human.identity, "serial", 0), psych.last_update_tick, spec.strategy.value
            )
            if best is None or utility > best.utility:
                best = CopingChoice(spec, round(utility, 5), [reason] if reason else [])
        return best

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        human: Any,
        psych: PsychologicalState,
        choice: CopingChoice,
        *,
        tick: Tick,
        support_engine: Optional[SupportEngine] = None,
        assessment: Optional[SupportAssessment] = None,
        social: Any = None,
        population: Any = None,
        genealogy: Any = None,
    ) -> CopingEpisode:
        spec = choice.spec
        ctx = self.build_context(human, psych, assessment)
        support_received = 0.0
        provider: Optional[str] = None
        note = spec.label

        # Social channel: the strategy is only a request until someone answers.
        if spec.social_channel and support_engine is not None:
            need = spec.social_channel
            amount = max(4.0, 24.0 * (1.0 - min(1.0, ctx.money / 60.0))) if need == "financial" else 0.0
            outcome = support_engine.request_support(
                human,
                psych,
                need="financial" if need == "financial" else "emotional",
                amount_usd=amount,
                tick=tick,
                social=social,
                population=population,
                genealogy=genealogy,
                assessment=assessment,
            )
            if outcome.granted:
                support_received = outcome.emotional_relief
                provider = outcome.provider_uid
                if outcome.amount_usd:
                    note += f": recibió ${outcome.amount_usd:.2f} de {outcome.provider_uid} (provenance: support)"
                else:
                    note += f": apoyo de {outcome.provider_uid}"
            else:
                # A refused request still costs the attempt and does not grant
                # the expected relief.  It can also make the avoidant loop worse.
                support_received = 0.0
                note += f": rechazado ({outcome.reason})"

        # Relief efficacy is reduced when the attempt failed to obtain what it
        # needed (a refused loan does not reduce financial strain).
        relief = spec.relief
        if spec.social_channel == "financial" and support_received == 0.0:
            relief *= 0.35
        elif spec.social_channel and support_received == 0.0:
            relief *= 0.55
        relief *= 0.85 + 0.30 * psych.regulation_capacity

        # Apply state effects.
        psych.relieve(relief)
        psych.chronic_stress = _clamp(psych.chronic_stress + spec.chronic_effect)
        psych.self_control = _clamp(psych.self_control + spec.control_effect)
        psych.hope = _clamp(psych.hope + spec.hope_effect)
        psych.loneliness = _clamp(psych.loneliness + spec.loneliness_effect)
        psych.mental_fatigue = _clamp(psych.mental_fatigue + spec.fatigue_effect)
        if spec.support_effect:
            psych.perceived_support = _clamp(psych.perceived_support + spec.support_effect)

        # Material and physical costs are applied to the actual states.
        money_before = float(getattr(human.physical_state, "money", 0.0))
        if spec.money_delta:
            human.physical_state.money = max(0.0, money_before + spec.money_delta)
        if spec.energy_delta:
            human.physical_state.energy = _clamp(
                getattr(human.physical_state, "energy", 1.0) + spec.energy_delta
            )

        cost_paid = abs(human.physical_state.money - money_before) + abs(spec.energy_delta)

        episode = CopingEpisode(
            strategy=spec.strategy,
            category=spec.category,
            tick=int(tick),
            trigger_stress=round(ctx.stress, 4),
            expected_relief=round(spec.relief, 4),
            short_term_relief=round(relief, 4),
            start_chronic_stress=round(psych.chronic_stress - spec.chronic_effect, 4),
            follow_up_tick=int(tick) + int(spec.follow_up_ticks),
            support_received=round(support_received, 4),
            support_provider=provider,
            cost_paid=round(cost_paid, 4),
            outcome_note=note,
        )
        psych.record_coping(episode)
        psych.record_timeline(
            _coping_timeline(episode, tick)
        )
        return episode

    # ------------------------------------------------------------------
    # Deferred outcome resolution
    # ------------------------------------------------------------------

    def resolve_due(
        self,
        psych: PsychologicalState,
        tick: int,
    ) -> list[CopingEpisode]:
        """Close coping episodes whose follow-up window has elapsed.

        The realised long-term change is measured against the chronic stress at
        the moment of the attempt.  A strategy that gave relief but raised
        chronic stress ends with a negative long-term delta, which lowers its
        learned preference.
        """
        resolved: list[CopingEpisode] = []
        by_id = {ep.episode_id: ep for ep in psych.coping_history}
        remaining: list[str] = []
        for episode_id in psych.unresolved_coping:
            episode = by_id.get(episode_id)
            if episode is None:
                continue
            if tick < episode.follow_up_tick:
                remaining.append(episode_id)
                continue
            delta = episode.start_chronic_stress - psych.chronic_stress
            episode.long_term_delta = round(delta, 4)
            episode.resolved_tick = int(tick)
            episode.deferred_applied = True
            observed = _clamp(
                0.55 * _clamp(episode.short_term_relief)
                + 0.45 * _clamp(0.5 + delta * 2.5)
            )
            psych.coping.record(episode.strategy, observed, tick)
            resolved.append(episode)
        psych.unresolved_coping = remaining
        return resolved


def _coping_timeline(episode: CopingEpisode, tick: int):
    from saltbor.psychology.models import LifeEventRecord

    return LifeEventRecord(
        tick=int(tick),
        kind="coping",
        summary=f"Afrontamiento: {episode.strategy.value} ({episode.category.value})",
        valence=round(episode.short_term_relief - 0.25, 4),
        importance=0.35,
        payload={
            "strategy": episode.strategy.value,
            "category": episode.category.value,
            "relief": episode.short_term_relief,
            "support": episode.support_received,
            "cost": episode.cost_paid,
        },
    )


def _stable_unit(serial: Any, tick: Any, salt: str) -> float:
    import hashlib

    key = f"{serial}|{tick}|{salt}".encode("utf-8")
    digest = hashlib.blake2b(key, digest_size=8).digest()
    return int.from_bytes(digest, "big") / (2**64 - 1)
