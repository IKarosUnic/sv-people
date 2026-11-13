"""Phase 1.7 experiments EXP_17_K … EXP_17_T."""

from __future__ import annotations

import gc
import math
import os
import statistics
import tempfile
import time
from typing import Any

from saltbor.core.config import SimulationConfig
from saltbor.core.types import RelationshipType, RomanceStage
from saltbor.events.types import EventType, SimulationEvent
from saltbor.psychology.engine import PsychologicalEngine
from saltbor.psychology.models import CopingStrategy
from saltbor.simulation.experiments.base import ExperimentConfig
from saltbor.simulation.experiments.phase17_common import (
    INCONCLUSIVE,
    REJECTED,
    SUPPORTED,
    Phase17Experiment,
    cohens_d,
    dominant_emotion,
    event,
    make_agent,
    negative_emotions,
    pop_of,
    run_days,
    stress_agent,
    summary,
    support_network,
    tie,
)
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.romance.engine import RomanceEngine
from saltbor.social.romance.models import RomanticDimensions, RomanticRelationship


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3 or len(xs) != len(ys):
        return 0.0
    try:
        return round(statistics.correlation(xs, ys), 3)
    except statistics.StatisticsError:
        return 0.0


def _rss_mb() -> float:
    try:
        import psutil

        return round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
    except Exception:
        return 0.0


# ===========================================================================
# EXP_17_K — Social support
# ===========================================================================

class Experiment17_K_SocialSupport(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_K",
            name="Apoyo social, redes y reciprocidad",
            description="Compara redes ausentes, débiles y fuertes; mide concesiones, rechazo y coste.",
            duration_ticks=90 * 96,
            random_seed=127,
            population_size=3,
        )

    def run(self, runner=None):
        started = time.time()
        seeds = [127, 131, 137]
        arms = {"aislado": 0.0, "debil": 0.35, "fuerte": 0.85}
        rows: dict[str, list[dict[str, float]]] = {a: [] for a in arms}
        for seed in seeds:
            for arm, level in arms.items():
                agent = make_agent(arm, serial=seed * 10 + 8, money=20.0)
                if level > 0:
                    social, partners = support_network(agent, level=level)
                else:
                    social, partners = None, []
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                psych = engine.ensure(agent)
                psych.chronic_stress = 0.62
                psych.acute_stress = 0.55
                psych.self_control = 0.35
                provider_before = {
                    str(p.uid): (round(p.physical_state.money, 2), round(p.physical_state.energy, 2))
                    for p in partners
                }
                grants = 0
                attempts = 0
                for i in range(6):
                    if social is None:
                        refused = True
                        outcome = None
                    else:
                        assessment = engine.support.assess(agent, social, None, pop)
                        outcome = engine.support.request_support(
                            agent, psych, need="financial" if i % 2 == 0 else "emotional",
                            amount_usd=18.0, tick=i * 5, social=social,
                            population=pop, assessment=assessment,
                        )
                        refused = not outcome.granted
                    attempts += 1
                    if outcome is not None and outcome.granted:
                        grants += 1
                    for d in range(i * 5, i * 5 + 5):
                        engine.step_population(pop, d, social=social, tick_minutes=1440, force_all=True)
                provider_costs = 0.0
                for p in partners:
                    before = provider_before.get(str(p.uid), (0.0, 1.0))
                    provider_costs += max(0.0, before[0] - p.physical_state.money)
                    provider_costs += max(0.0, before[1] - p.physical_state.energy) * 10.0
                rows[arm].append(
                    {
                        "grant_rate": grants / max(1, attempts),
                        "support": psych.perceived_support,
                        "loneliness": psych.loneliness,
                        "trust": psych.trust,
                        "stress": psych.chronic_stress,
                        "provider_cost": provider_costs,
                        "network": len(partners),
                    }
                )

        iso = summary([r["grant_rate"] for r in rows["aislado"]])
        strong = summary([r["grant_rate"] for r in rows["fuerte"]])
        d_grant = cohens_d([r["grant_rate"] for r in rows["fuerte"]], [r["grant_rate"] for r in rows["aislado"]])
        hypotheses = [
            self._hyp(
                "H1", "Una red más densa aumenta la probabilidad de recibir apoyo",
                SUPPORTED if strong["mean"] > iso["mean"] + 0.1 else REJECTED,
                "grant rate fuerte vs aislado", f"{strong['mean']} vs {iso['mean']} (d={d_grant})",
            ),
            self._hyp(
                "H2", "El rechazo tiene coste psicológico y el apoyo no está garantizado",
                SUPPORTED
                if summary([r["loneliness"] for r in rows["aislado"]])["mean"]
                > summary([r["loneliness"] for r in rows["fuerte"]])["mean"]
                else INCONCLUSIVE,
                "loneliness aislado vs fuerte",
                f"{summary([r['loneliness'] for r in rows['aislado']])['mean']} vs "
                f"{summary([r['loneliness'] for r in rows['fuerte']])['mean']}",
            ),
            self._hyp(
                "H3", "El apoyo consume recursos del proveedor",
                SUPPORTED
                if summary([r["provider_cost"] for r in rows["fuerte"]])["mean"] > 0
                else REJECTED,
                "provider cost (money + energy·10)", summary([r["provider_cost"] for r in rows["fuerte"]])["mean"],
            ),
        ]
        return self._finish(
            started,
            "EXP_17_K: el apoyo tiene red, coste y rechazo",
            hypotheses,
            {arm: {k: summary([r[k] for r in rows[arm]]) for k in ("grant_rate", "support", "loneliness", "trust", "stress", "provider_cost")} for arm in arms},
        )


# ===========================================================================
# EXP_17_L — Romantic crisis
# ===========================================================================

class Experiment17_L_RelationshipCrisis(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_L",
            name="Crisis de pareja, infidelidad y reconciliación",
            description="No impone un desenlace: mide confianza, separación y reconciliación posibles.",
            duration_ticks=200 * 96,
            random_seed=139,
            population_size=4,
        )

    def run(self, runner=None):
        started = time.time()
        seeds = [139, 149, 151, 157]
        rows: list[dict[str, Any]] = []
        for seed in seeds:
            for index, persona in enumerate(("celoso", "confiado", "ambivalente", "pragmatico")):
                a = make_agent("A", serial=seed * 10 + 1, traits={"agreeableness": 0.6, "extraversion": 0.7})
                b = make_agent("B", serial=seed * 10 + 2, traits={"agreeableness": 0.55, "extraversion": 0.6})
                third = make_agent("Tercero", serial=seed * 10 + 3, traits={"agreeableness": 0.8, "openness": 0.85, "extraversion": 0.9})
                engine = RomanceEngine(seed=seed + index * 7)
                rel = RomanticRelationship(
                    relationship_id=f"rel_{seed}_{persona}",
                    partner_a_id=str(a.uid),
                    partner_b_id=str(b.uid),
                    stage=RomanceStage.DATING,
                    dims_a=RomanticDimensions(
                        attraction=0.8, affection=0.75, trust=0.82, commitment=0.78,
                        compatibility=0.7, communication_quality=0.65,
                        jealousy=0.2 if persona == "confiado" else (0.8 if persona == "celoso" else 0.5),
                        conflict_level=0.15,
                    ),
                    dims_b=RomanticDimensions(
                        attraction=0.75, affection=0.72, trust=0.8, commitment=0.7,
                        compatibility={"confiado": 0.9, "celoso": 0.35, "ambivalente": 0.55, "pragmatico": 0.2}[persona],
                        communication_quality={"confiado": 0.9, "celoso": 0.35, "ambivalente": 0.7, "pragmatico": 0.2}[persona],
                        jealousy=0.6, conflict_level=0.2,
                    ),
                    start_tick=0,
                    is_active=True,
                )
                engine._relationships[rel.relationship_id] = rel
                a.romantic_partner_id = str(b.uid)
                b.romantic_partner_id = str(a.uid)
                before_trust = (rel.dims_a.trust + rel.dims_b.trust) / 2.0

                # Make the vulnerability explicit, then let the engine decide
                # whether an incident and a discovery actually occur.
                rel.dims_a.commitment = 0.18 if persona in ("ambivalente", "pragmatico") else 0.35
                rel.dims_a.conflict_level = 0.82
                discovered = None
                for attempt in range(40):
                    engine.evaluate_jealousy_and_infidelity(a, third, attempt)
                    discovered = engine.evaluate_infidelity_discovery(rel.relationship_id, attempt + 1)
                    if discovered is not None:
                        break
                after_trust = (rel.dims_a.trust + rel.dims_b.trust) / 2.0
                outcome = discovered.get("outcome") if discovered else "no_discovery"
                separated = not rel.is_active
                reconciled = False
                if separated:
                    # One decision, not repeated attempts until success.
                    reconciled = engine.evaluate_reconciliation(rel.relationship_id, 100)
                rows.append(
                    {
                        "seed": seed,
                        "persona": persona,
                        "trust_before": round(before_trust, 3),
                        "trust_after": round(after_trust, 3),
                        "outcome": outcome,
                        "separated": separated,
                        "reconciled": reconciled,
                        "active": rel.is_active,
                        "stage": rel.stage.value,
                    }
                )

        discovered_rows = [r for r in rows if r["outcome"] != "no_discovery"]
        trust_before = summary([r["trust_before"] for r in discovered_rows])
        trust_after = summary([r["trust_after"] for r in discovered_rows])
        outcomes = sorted({r["outcome"] for r in rows})
        separations = sum(1 for r in rows if r["separated"])
        reconciliations = sum(1 for r in rows if r["reconciled"])
        hypotheses = [
            self._hyp(
                "H1", "El descubrimiento de infidelidad reduce la confianza",
                SUPPORTED if trust_after["mean"] < trust_before["mean"] - 0.05 else REJECTED,
                "mean trust before/after", f"{trust_before['mean']} → {trust_after['mean']}",
            ),
            self._hyp(
                "H2", "El desenlace no es uniforme entre personas y semillas",
                SUPPORTED if len(outcomes) >= 2 else INCONCLUSIVE,
                "distinct outcomes", outcomes,
            ),
            self._hyp(
                "H3", "La reconciliación es posible, pero no automática",
                SUPPORTED if 0 < reconciliations < max(1, separations) else INCONCLUSIVE,
                "reconciliations / separations", f"{reconciliations} / {separations}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_L: confianza, ruptura y reconciliación sin guion",
            hypotheses,
            {
                "rows": rows,
                "distinct_outcomes": outcomes,
                "separations": separations,
                "reconciliations": reconciliations,
                "trust_before": trust_before,
                "trust_after": trust_after,
            },
        )


# ===========================================================================
# EXP_17_M — Longitudinal development
# ===========================================================================

class Experiment17_M_LongitudinalDevelopment(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_M",
            name="Desarrollo psicológico longitudinal",
            description="Trayectorias de 1, 5, 10 y 25 años con condiciones repetidas.",
            duration_ticks=25 * 365 * 96,
            random_seed=163,
            population_size=2,
        )

    def run(self, runner=None):
        started = time.time()
        personas = {
            "sensible": {"neuroticism": 0.8, "conscientiousness": 0.4, "agreeableness": 0.5},
            "resistente": {"neuroticism": 0.25, "conscientiousness": 0.8, "agreeableness": 0.7},
        }
        support_levels = {"sensible": 0.35, "resistente": 0.8}
        horizons = {1: 365, 5: 1825, 10: 3650, 25: 9125}
        results: dict[str, dict[int, dict[str, Any]]] = {p: {} for p in personas}
        for name, traits in personas.items():
            agent = make_agent(name, serial=100 + list(personas).index(name), traits=traits)
            social, partners = support_network(agent, level=support_levels[name])
            pop = pop_of(agent, *partners)
            engine = PsychologicalEngine(seed=163)
            engine.ensure(agent)
            checkpoints = set(horizons.values())
            biography: dict[int, dict[str, Any]] = {}
            for day in range(1, 9126):
                if day % 90 == 0:
                    ev_type = (EventType.JOB_LOST, EventType.FINANCIAL_LOSS, EventType.CONFLICT_OCCURRED, EventType.ASSISTANCE_REJECTED)[(day // 90) % 4]
                    engine.process_events([event(ev_type, agent, day, importance=0.65)], pop, social)
                engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                if day in checkpoints:
                    trait = agent.personality.traits.get_trait("neuroticism")
                    biography[day] = {
                        "neuroticism_base": round(trait.base_value, 4),
                        "chronic": round(agent.psychology.chronic_stress, 4),
                        "control": round(agent.psychology.self_control, 4),
                        "hope": round(agent.psychology.hope, 4),
                        "crises": len(agent.psychology.crisis_history),
                        "beliefs": {k: round(v, 3) for k, v in agent.psychology.beliefs.items()},
                        "coping_top": max(agent.psychology.coping.preferences.items(), key=lambda kv: kv[1], default=("none", 0.5))[0],
                    }
            for years, day in horizons.items():
                results[name][years] = biography.get(day, {})

        shifts = []
        for name, horizons_data in results.items():
            initial = horizons_data.get(1, {}).get("neuroticism_base", 0.0)
            final = horizons_data.get(25, {}).get("neuroticism_base", 0.0)
            shifts.append(abs(final - initial))
        distinct_25 = len({round(results[p][25]["chronic"], 2) for p in personas})
        any_coping_change = any(
            results[p][1].get("coping_top") != results[p][25].get("coping_top") for p in personas
        )
        hypotheses = [
            self._hyp(
                "H1", "La personalidad cambia de forma lenta y acotada, no por un solo evento",
                SUPPORTED if all(s <= 0.031 for s in shifts) else REJECTED,
                "max |neuroticism base change| over 25 years", round(max(shifts), 4),
            ),
            self._hyp(
                "H2", "Las trayectorias divergen entre individuos bajo el mismo entorno",
                SUPPORTED if distinct_25 >= 2 else INCONCLUSIVE,
                "distinct chronic stress at 25 years", distinct_25,
            ),
            self._hyp(
                "H3", "El aprendizaje de afrontamiento puede cambiar con la experiencia",
                SUPPORTED if any_coping_change else INCONCLUSIVE,
                "coping preference changed", any_coping_change,
            ),
        ]
        return self._finish(
            started,
            "EXP_17_M: 1, 5, 10 y 25 años de biografía",
            hypotheses,
            {"results": results, "neuroticism_shift_max": round(max(shifts), 4), "any_coping_change": any_coping_change},
        )


# ===========================================================================
# EXP_17_N — Behavioral diversity
# ===========================================================================

class Experiment17_N_BehavioralDiversity(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_N",
            name="Diversidad conductual explicable",
            description="Mide divergencia de actividad y su relación con rasgos, no con ruido.",
            duration_ticks=96,
            random_seed=167,
            population_size=20,
        )

    def _run(self, seed: int) -> dict[str, Any]:
        path = os.path.join(tempfile.mkdtemp(), f"diversity_{seed}.db")
        cfg = SimulationConfig(
            random_seed=seed,
            initial_population_size=20,
            checkpoint_interval_ticks=100_000,
            database_path=path,
        )
        runner = SimulationRunner(cfg)
        runner.initialize()
        activity_counts: dict[str, int] = {}
        per_agent: dict[str, set[str]] = {}
        for tick in range(96):
            runner.step()
            if tick % 8 == 0:
                for human in runner.population.get_all():
                    act = getattr(human.physical_state.current_activity, "value", "idle")
                    activity_counts[act] = activity_counts.get(act, 0) + 1
                    per_agent.setdefault(str(human.uid), set()).add(act)
        rows = []
        for human in runner.population.get_all():
            acts = per_agent.get(str(human.uid), set())
            rows.append(
                {
                    "uid": str(human.uid),
                    "neuroticism": human.personality.effective_value("neuroticism"),
                    "conscientiousness": human.personality.effective_value("conscientiousness"),
                    "extraversion": human.personality.effective_value("extraversion"),
                    "chronic": human.psychology.chronic_stress,
                    "activities": len(acts),
                }
            )
        total = sum(activity_counts.values()) or 1
        entropy = -sum((count / total) * math.log(count / total) for count in activity_counts.values() if count)
        normalized_entropy = round(entropy / math.log(max(2, len(activity_counts))), 4)
        overview = runner.psychology.overview()
        runner.db.close()
        return {
            "activity_counts": activity_counts,
            "entropy": normalized_entropy,
            "rows": rows,
            "overview": overview,
        }

    def run(self, runner=None):
        started = time.time()
        first = self._run(167)
        third = self._run(173)
        fourth = self._run(179)
        pooled = first["rows"] + third["rows"] + fourth["rows"]
        corr = _pearson([r["neuroticism"] for r in pooled], [r["chronic"] for r in pooled])
        act_corr = _pearson([r["extraversion"] for r in pooled], [float(r["activities"]) for r in pooled])
        entropies = [first["entropy"], third["entropy"], fourth["entropy"]]
        stable_diversity = min(entropies) > 0.2 and (max(entropies) - min(entropies)) < 0.10
        hypotheses = [
            self._hyp(
                "H1", "La población muestra diversidad conductual medible",
                SUPPORTED if first["entropy"] > 0.2 and len(first["activity_counts"]) >= 3 else REJECTED,
                "normalized activity entropy", first["entropy"],
            ),
            self._hyp(
                "H2", "Parte de la divergencia se asocia a rasgos y estado, no solo a azar",
                SUPPORTED if abs(corr) >= 0.3 or abs(act_corr) >= 0.3 else INCONCLUSIVE,
                "corr(neuroticism, chronic) / corr(extraversion, #activities)",
                f"{corr} / {act_corr}",
            ),
            self._hyp(
                "H3", "La diversidad agregada se mantiene al cambiar la semilla",
                SUPPORTED if stable_diversity else REJECTED,
                "normalized entropy across seeds 167/173/179", entropies,
            ),
        ]
        return self._finish(
            started,
            "EXP_17_N: divergencia conductual con causas",
            hypotheses,
            {
                "entropy": first["entropy"],
                "activity_counts": first["activity_counts"],
                "corr_neuroticism_chronic": corr,
                "corr_extraversion_activities": act_corr,
                "entropy_by_seed": entropies,
                "seeds_pooled": [167, 173, 179],
                "pooled_observations": len(pooled),
            },
        )


# ===========================================================================
# EXP_17_O — Adversarial conditions
# ===========================================================================

class Experiment17_O_AdversarialConditions(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_O",
            name="Condiciones adversarias y crisis múltiples",
            description="Crisis simultáneas, prolongadas y contradictorias.",
            duration_ticks=240 * 96,
            random_seed=179,
            population_size=3,
        )

    def run(self, runner=None):
        started = time.time()
        seeds = [179, 181, 191]
        arms = {
            "unica": [(0, EventType.JOB_LOST, 0.95)],
            "compuesta": [
                (0, EventType.JOB_LOST, 0.95),
                (1, EventType.ILLNESS_CONTRACTED, 0.9),
                (2, EventType.RELATIONSHIP_ENDED, 0.9),
                (3, EventType.DISASTER_OCCURRED, 0.9),
                (4, EventType.FINANCIAL_LOSS, 0.9),
                (30, EventType.EVICTION_OCCURRED, 0.9),
                (60, EventType.ACCIDENT_OCCURRED, 0.85),
                (120, EventType.FINANCIAL_LOSS, 0.85),
            ],
            "contradictoria": [
                (0, EventType.JOB_LOST, 0.9),
                (1, EventType.RECONCILIATION_ACHIEVED, 0.85),
                (2, EventType.TRUST_BROKEN, 0.9),
                (3, EventType.ASSISTANCE_OFFERED, 0.8),
                (4, EventType.ASSISTANCE_REJECTED, 0.85),
                (30, EventType.JOB_STARTED, 0.8),
                (60, EventType.FINANCIAL_LOSS, 0.85),
                (120, EventType.TRUST_BROKEN, 0.85),
            ],
        }
        rows: dict[str, list[dict[str, float]]] = {a: [] for a in arms}
        for seed in seeds:
            for arm, schedule in arms.items():
                agent = make_agent(arm, serial=seed * 10 + 9, traits={"neuroticism": 0.7, "conscientiousness": 0.45})
                social, partners = support_network(agent, level=0.35)
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                stress_agent(
                    engine, agent, chronic=0.72, acute=0.62, fatigue=0.55,
                    control=0.24, loneliness=0.62, support=0.20,
                )
                # Exposure arm: coping is held off so that the comparison
                # measures the cumulative adversity itself, not how quickly
                # one particular agent finds relief.
                engine._should_cope = lambda *args, **kwargs: False  # type: ignore[assignment]
                residual_peak = 0.0
                for day in range(240):
                    for ev_day, ev_type, imp in schedule:
                        if day == ev_day:
                            engine.process_events([event(ev_type, agent, day, importance=imp)], pop, social)
                    engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                    residual_peak = max(residual_peak, agent.psychology.post_crisis_vulnerability)
                rows[arm].append(
                    {
                        "crises": float(len(agent.psychology.crisis_history)),
                        "peak": max((ep.peak_severity for ep in agent.psychology.crisis_history), default=0.0),
                        "residual": residual_peak,
                        "belief_safety": agent.psychology.beliefs.get("world_is_safe", 0.5),
                        "belief_reliable": agent.psychology.beliefs.get("people_are_reliable", 0.5),
                        "chronic": agent.psychology.chronic_stress,
                    }
                )

        def m(arm: str, key: str) -> float:
            return summary([r[key] for r in rows[arm]])["mean"]

        hypotheses = [
            self._hyp(
                "H1", "Las crisis compuestas producen mayor carga que una crisis única",
                SUPPORTED
                if m("compuesta", "peak") > 0
                and m("compuesta", "peak") > m("unica", "peak") + 0.01
                else REJECTED,
                "peak/chronic compuesta vs única",
                f"{m('compuesta', 'peak')}/{m('compuesta', 'chronic')} vs {m('unica', 'peak')}/{m('unica', 'chronic')}",
            ),
            self._hyp(
                "H2", "Los desenlaces no son homogéneos entre individuos y secuencias",
                SUPPORTED if len({round(r["peak"], 2) for rows_ in rows.values() for r in rows_}) >= 2 else INCONCLUSIVE,
                "distinct peak severities", len({round(r["peak"], 2) for rows_ in rows.values() for r in rows_}),
            ),
            self._hyp(
                "H3", "Quedan consecuencias residuales tras las crisis",
                SUPPORTED if any(r["residual"] > 0.01 or r["belief_safety"] < 0.48 for rows_ in rows.values() for r in rows_) else INCONCLUSIVE,
                "residual vulnerability / belief change",
                f"residual_max={max(r['residual'] for rows_ in rows.values() for r in rows_):.3f}, "
                f"belief_min={min(r['belief_safety'] for rows_ in rows.values() for r in rows_):.3f}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_O: adversidad múltiple y contradictoria",
            hypotheses,
            {arm: {k: summary([r[k] for r in rows[arm]]) for k in ("crises", "peak", "residual", "belief_safety", "chronic")} for arm in arms},
        )


# ===========================================================================
# EXP_17_P — Recovery and relapse
# ===========================================================================

class Experiment17_P_RecoveryRelapse(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_P",
            name="Recuperación, recaída y secuelas",
            description="Una crisis, alivio sostenido y una nueva exposición.",
            duration_ticks=300 * 96,
            random_seed=193,
            population_size=1,
        )

    def run(self, runner=None):
        started = time.time()
        seeds = [193, 197, 199]
        rows: list[dict[str, Any]] = []
        for seed in seeds:
            agent = make_agent("Sobreviviente", serial=seed * 10 + 10)
            social, partners = support_network(agent, level=0.35)
            pop = pop_of(agent, *partners)
            engine = PsychologicalEngine(seed=seed)
            psych = engine.ensure(agent)
            stress_agent(engine, agent, chronic=0.82, acute=0.8, fatigue=0.7, control=0.12, loneliness=0.7, support=0.15)
            recovered_at = None
            residual_after = 0.0
            for day in range(20):
                engine.process_events([event(EventType.FINANCIAL_LOSS, agent, day, importance=0.75)], pop, social)
                engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                if psych.crisis_history and not psych.in_crisis() and recovered_at is None:
                    recovered_at = psych.crisis_history[-1].ended_tick
                    residual_after = max(residual_after, psych.post_crisis_vulnerability)
            first_crisis = len(psych.crisis_history)
            peak = max((ep.peak_severity for ep in psych.crisis_history), default=0.0)
            # Sustained relief: support, rest, income, control.
            psych.chronic_stress = 0.18
            psych.acute_stress = 0.10
            psych.mental_fatigue = 0.15
            psych.self_control = 0.72
            psych.perceived_support = 0.82
            psych.hope = 0.82
            for day in range(20, 140):
                engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                if psych.crisis_history and not psych.in_crisis():
                    residual_after = max(residual_after, psych.post_crisis_vulnerability)
                    if recovered_at is None:
                        recovered_at = psych.crisis_history[-1].ended_tick
            # Re-exposure under residual vulnerability.
            stress_agent(engine, agent, chronic=0.78, acute=0.76, fatigue=0.6, control=0.16, loneliness=0.65, support=0.2)
            for day in range(140, 260):
                if day % 5 == 0:
                    engine.process_events([event(EventType.FINANCIAL_LOSS, agent, day, importance=0.8)], pop, social)
                engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
            new_episodes = psych.crisis_history[first_crisis:]
            relapse = any(ep.relapsed for ep in new_episodes) or len(new_episodes) > 0
            rows.append(
                {
                    "first_crisis": first_crisis,
                    "peak": peak,
                    "recovered_at": recovered_at,
                    "recovered": recovered_at is not None,
                    "crises_total": len(psych.crisis_history),
                    "relapse": relapse,
                    "residual": round(residual_after, 4),
                    "residual_end": psych.post_crisis_vulnerability,
                    "control_end": psych.self_control,
                    "trust_end": psych.trust,
                }
            )

        recovered = sum(1 for r in rows if r["recovered"])
        relapses = sum(1 for r in rows if r["relapse"])
        hypotheses = [
            self._hyp(
                "H1", "La crisis puede resolverse cuando las condiciones cambian",
                SUPPORTED if recovered >= 2 else INCONCLUSIVE,
                "recovered within 120 days", f"{recovered}/{len(rows)}",
            ),
            self._hyp(
                "H2", "La recaída es posible tras una recuperación",
                SUPPORTED if relapses > 0 else INCONCLUSIVE,
                "relapses observed", f"{relapses}/{len(rows)}",
            ),
            self._hyp(
                "H3", "Quedan secuelas medibles después de la recuperación",
                SUPPORTED if any(r["residual"] > 0.05 for r in rows) else INCONCLUSIVE,
                "max residual vulnerability", round(max(r["residual"] for r in rows), 4),
            ),
        ]
        return self._finish(
            started,
            "EXP_17_P: recuperarse no es volver al punto de partida",
            hypotheses,
            {"rows": rows, "recovered": recovered, "relapses": relapses},
        )


# ===========================================================================
# EXP_17_Q — Causal ablation
# ===========================================================================

class Experiment17_Q_CausalAblation(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_Q",
            name="Ablación causal de mecanismos",
            description="Desactiva evaluación, afrontamiento y apoyo para ver qué cambia.",
            duration_ticks=150 * 96,
            random_seed=211,
            population_size=4,
        )

    def run(self, runner=None):
        started = time.time()
        seeds = [211, 223, 227]
        arms = ["completo", "sin_evaluacion", "sin_afrontamiento", "sin_apoyo"]
        rows: dict[str, list[dict[str, float]]] = {a: [] for a in arms}
        for seed in seeds:
            for arm in arms:
                agent = make_agent(arm, serial=seed * 10 + 11, traits={"neuroticism": 0.6, "conscientiousness": 0.5})
                if arm == "sin_apoyo":
                    social, partners = None, []
                else:
                    social, partners = support_network(agent, level=0.6)
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                psych = engine.ensure(agent)
                psych.chronic_stress = 0.55
                psych.acute_stress = 0.55
                psych.self_control = 0.40
                if arm == "sin_afrontamiento":
                    engine._should_cope = lambda *args, **kwargs: False  # type: ignore[assignment]
                for day in range(150):
                    if arm != "sin_evaluacion" and day % 10 == 0:
                        engine.process_events(
                            [event(EventType.FINANCIAL_LOSS, agent, day, importance=0.65)], pop, social
                        )
                    engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                rows[arm].append(
                    {
                        "chronic": psych.chronic_stress,
                        "crises": float(len(psych.crisis_history)),
                        "hope": psych.hope,
                        "negative": negative_emotions(agent),
                        "coping": float(psych.coping_attempts_total),
                        "control": psych.self_control,
                    }
                )

        def m(arm: str, key: str) -> float:
            return summary([r[key] for r in rows[arm]])["mean"]

        hypotheses = [
            self._hyp(
                "H1", "Desactivar la evaluación cambia la respuesta emocional y acumulativa",
                SUPPORTED if abs(m("sin_evaluacion", "negative") - m("completo", "negative")) > 0.02 or abs(m("sin_evaluacion", "chronic") - m("completo", "chronic")) > 0.02 else INCONCLUSIVE,
                "negative/chronic sin_evaluación vs completo",
                f"{m('sin_evaluacion', 'negative')}/{m('sin_evaluacion', 'chronic')} vs "
                f"{m('completo', 'negative')}/{m('completo', 'chronic')}",
            ),
            self._hyp(
                "H2", "Desactivar el afrontamiento cambia el curso del estrés",
                SUPPORTED if abs(m("sin_afrontamiento", "chronic") - m("completo", "chronic")) > 0.02 else INCONCLUSIVE,
                "chronic sin_afrontamiento vs completo",
                f"{m('sin_afrontamiento', 'chronic')} vs {m('completo', 'chronic')}",
            ),
            self._hyp(
                "H3", "Desactivar el apoyo cambia la recuperación y la esperanza",
                SUPPORTED if abs(m("sin_apoyo", "hope") - m("completo", "hope")) > 0.02 else INCONCLUSIVE,
                "hope sin_apoyo vs completo",
                f"{m('sin_apoyo', 'hope')} vs {m('completo', 'hope')}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_Q: qué cambia cuando se apaga cada mecanismo",
            hypotheses,
            {arm: {k: summary([r[k] for r in rows[arm]]) for k in ("chronic", "crises", "hope", "negative", "coping", "control")} for arm in arms},
        )


# ===========================================================================
# EXP_17_R — Deterministic reproducibility
# ===========================================================================

class Experiment17_R_DeterministicReproducibility(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_R",
            name="Reproducibilidad determinista",
            description="Mismas condiciones y semilla, mismos resultados; condiciones distintas, trayectorias distintas.",
            duration_ticks=90 * 96,
            random_seed=229,
            population_size=2,
        )

    @staticmethod
    def _trajectory(seed: int, neuroticism: float) -> dict[str, Any]:
        agent = make_agent("Det", serial=7001, traits={"neuroticism": neuroticism})
        social, partners = support_network(agent, level=0.5)
        pop = pop_of(agent, *partners)
        engine = PsychologicalEngine(seed=seed)
        engine.ensure(agent)
        for day in range(90):
            if day % 15 == 0:
                engine.process_events([event(EventType.FINANCIAL_LOSS, agent, day, importance=0.6)], pop, social)
            engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
        psych = agent.psychology
        return {
            "chronic": round(psych.chronic_stress, 6),
            "control": round(psych.self_control, 6),
            "hope": round(psych.hope, 6),
            "crises": len(psych.crisis_history),
            "coping": psych.coping_attempts_total,
            "timeline_len": len(psych.timeline),
            "prefs": {k: round(v, 5) for k, v in sorted(psych.coping.preferences.items())},
        }

    def run(self, runner=None):
        started = time.time()
        a = self._trajectory(229, 0.65)
        b = self._trajectory(229, 0.65)
        c = self._trajectory(229, 0.15)
        d = self._trajectory(233, 0.65)
        same = a == b
        different_conditions = a != c
        different_seed = a != d
        hypotheses = [
            self._hyp(
                "H1", "La misma semilla y las mismas condiciones reproducen la trayectoria",
                SUPPORTED if same else REJECTED,
                "state signatures equal", same,
            ),
            self._hyp(
                "H2", "Cambiar una condición individual cambia la trayectoria",
                SUPPORTED if different_conditions else REJECTED,
                "neuroticism 0.65 vs 0.15 differs", different_conditions,
            ),
            self._hyp(
                "H3", "La semilla sólo importa en los mecanismos estocásticos",
                SUPPORTED if different_seed or a["coping"] == 0 else INCONCLUSIVE,
                "seed 229 vs 233 differs / coping attempts", f"{different_seed} / {a['coping']}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_R: determinismo cuando se exige",
            hypotheses,
            {"a": a, "b": b, "c": c, "d": d, "same_seed_equal": same},
        )


# ===========================================================================
# EXP_17_S — Sustained population benchmark
# ===========================================================================

class Experiment17_S_PopulationBenchmark(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_S",
            name="Rendimiento sostenido por población",
            description="Mide ms/tick, ms/individuo, RSS y tamaño de checkpoint psicológico.",
            duration_ticks=6,
            random_seed=239,
            population_size=1000,
        )

    def run(self, runner=None):
        started = time.time()
        populations = [20, 100, 500, 1000]
        rows: list[dict[str, Any]] = []
        gc.collect()
        baseline_rss = _rss_mb()
        for size in populations:
            agents = [make_agent(f"P{i}", serial=i + 1) for i in range(size)]
            pop = pop_of(*agents)
            engine = PsychologicalEngine(seed=239)
            for human in agents:
                engine.ensure(human)
            # Warm-up one tick (state creation, LOD classification).
            engine.step_population(pop, 0, tick_minutes=15, force_all=True)
            timings = []
            for tick in range(1, 6):
                t0 = time.perf_counter()
                engine.step_population(pop, tick, tick_minutes=15)
                timings.append((time.perf_counter() - t0) * 1000.0)
            payload = len(str(engine.to_dict()))
            rows.append(
                {
                    "population": size,
                    "mean_ms_tick": round(statistics.fmean(timings), 2),
                    "p95_ms_tick": round(sorted(timings)[max(0, int(len(timings) * 0.95) - 1)], 2),
                    "ms_per_agent": round(statistics.fmean(timings) / size, 4),
                    "rss_mb": _rss_mb(),
                    "state_payload_chars": payload,
                    "active_crises": sum(1 for s in engine.states.values() if s.in_crisis()),
                }
            )
            del agents, pop, engine
            gc.collect()

        slopes = []
        for prev, nxt in zip(rows, rows[1:]):
            if prev["ms_per_agent"] > 0 and nxt["ms_per_agent"] > 0:
                slopes.append(nxt["ms_per_agent"] / prev["ms_per_agent"])
        hypotheses = [
            self._hyp(
                "H1", "El coste por individuo no crece linealmente con la población (LOD)",
                SUPPORTED if rows[-1]["ms_per_agent"] <= rows[0]["ms_per_agent"] * 1.5 else INCONCLUSIVE,
                "ms/agent 20 → 1000",
                f"{rows[0]['ms_per_agent']} → {rows[-1]['ms_per_agent']}",
            ),
            self._hyp(
                "H2", "1000 individuos se actualizan sin fallo ni crecimiento descontrolado",
                SUPPORTED if rows[-1]["population"] == 1000 and rows[-1]["rss_mb"] < 4096 else REJECTED,
                "RSS at 1000", f"{rows[-1]['rss_mb']} MB",
            ),
            self._hyp(
                "H3", "El checkpoint psicológico escala de forma manejable",
                SUPPORTED if rows[-1]["state_payload_chars"] < 12_000_000 else INCONCLUSIVE,
                "checkpoint chars at 1000", rows[-1]["state_payload_chars"],
            ),
        ]
        return self._finish(
            started,
            "EXP_17_S: rendimiento sostenido 20–1000",
            hypotheses,
            {"rows": rows, "baseline_rss_mb": baseline_rss, "rss_after_mb": _rss_mb(), "slopes": slopes},
        )


# ===========================================================================
# EXP_17_T — Integrated simulation
# ===========================================================================

class Experiment17_T_IntegratedSimulation(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_T",
            name="Integración en la simulación completa",
            description="Verifica que el sistema psicológico participa en SimulationRunner y persiste.",
            duration_ticks=192,
            random_seed=241,
            population_size=20,
        )

    def run(self, runner=None):
        started = time.time()
        path = os.path.join(tempfile.mkdtemp(), "integrated17.db")
        cfg = SimulationConfig(
            random_seed=241,
            initial_population_size=20,
            checkpoint_interval_ticks=96,
            database_path=path,
        )
        sim = SimulationRunner(cfg)
        sim.initialize()
        decision_hits = 0
        for tick in range(192):
            if tick in (20, 60, 100, 140):
                for human in sim.population.get_all()[:10]:
                    sim.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.JOB_LOST,
                            tick=tick,
                            source_human_id=human.uid,
                            location_id=getattr(human.physical_state, "current_location_id", None),
                            data={"origin": "exp_17_t", "provenance": "experiment"},
                            importance=0.85,
                        )
                    )
            sim.step()
            for human in sim.population.get_all():
                trace = human.decision.get_last_trace()
                if trace and any("Psychological load" in str(f) for f in trace.dominant_factors):
                    decision_hits += 1
        overview = sim.psychology.overview()
        snapshots = [sim.psychology.snapshot(h) for h in sim.population.get_all()[:5]]
        timeline_rows = sim.db.execute("SELECT COUNT(*) c FROM psychology_timeline").fetchone()["c"]
        sim.db.close()

        reload = SimulationRunner(cfg)
        reload.initialize(load_existing=True)
        restored_states = len(reload.psychology.states)
        restored_population = reload.population.count
        reload_samples = [
            {
                "uid": str(h.uid),
                "chronic": round(h.psychology.chronic_stress, 4),
                "control": round(h.psychology.self_control, 4),
            }
            for h in reload.population.get_all()[:5]
        ]
        reload.step()
        reload.db.close()

        hypotheses = [
            self._hyp(
                "H1", "La capa psicológica participa en el flujo real y produce cambios observables",
                SUPPORTED if overview["stats"].get("appraisals", 0) > 0 and overview["coping_attempts"] >= 0 else REJECTED,
                "appraisals / coping attempts",
                f"{overview['stats'].get('appraisals', 0)} / {overview['coping_attempts']}",
            ),
            self._hyp(
                "H2", "El estado psicológico aparece en decisiones y en la observabilidad",
                SUPPORTED if decision_hits > 0 and all("state" in s for s in snapshots) else REJECTED,
                "decision traces with psych factor / snapshots",
                f"{decision_hits} / {len(snapshots)}",
            ),
            self._hyp(
                "H3", "El estado y la línea de tiempo sobreviven a un checkpoint y recarga",
                SUPPORTED if restored_states == restored_population and timeline_rows > 0 else REJECTED,
                "restored states / population / timeline rows",
                f"{restored_states} / {restored_population} / {timeline_rows}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_T: la psicología dentro de SimulationRunner",
            hypotheses,
            {
                "overview": overview,
                "decision_traces_with_psych": decision_hits,
                "timeline_rows": timeline_rows,
                "restored_states": restored_states,
                "restored_population": restored_population,
                "reload_samples": reload_samples,
                "snapshot_sample": snapshots[0] if snapshots else {},
            },
        )
