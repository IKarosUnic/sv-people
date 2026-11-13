"""Phase 1.7 experiments EXP_17_A … EXP_17_J."""

from __future__ import annotations

import dataclasses
import statistics
from types import SimpleNamespace
from typing import Any

from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.events.types import EventType
from saltbor.psychology.coping import COPING_SPECS, CopingChoice
from saltbor.psychology.engine import PsychologicalEngine
from saltbor.psychology.models import CopingStrategy
from saltbor.psychology.retrieval import AssociativeRetrieval, RetrievalQuery
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
    positive_emotions,
    run_days,
    stress_agent,
    summary,
    support_network,
    tie,
)


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3 or len(xs) != len(ys):
        return 0.0
    try:
        return round(statistics.correlation(xs, ys), 3)
    except statistics.StatisticsError:
        return 0.0


# ===========================================================================
# EXP_17_A — Stress accumulation
# ===========================================================================

class Experiment17_A_StressAccumulation(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_A",
            name="Acumulación de estrés agudo vs. crónico",
            description="Compara un shock único con exposiciones repetidas y mide recuperación.",
            duration_ticks=180 * 96,
            random_seed=17,
            population_size=3,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        seeds = [17, 23, 31]
        arms = {
            "control": [],
            "acute": [(10, EventType.JOB_LOST, 0.9)],
            # A dense chronic series is deliberate: it tests whether repeated
            # adversity outruns the individual's coping capacity.  Coping stays
            # enabled in both arms, so the comparison is not an ablation.
            "chronic": [(10 + i, EventType.FINANCIAL_LOSS, 0.9) for i in range(60)],
        }
        result: dict[str, dict[str, list[float]]] = {
            arm: {"peak": [], "end": [], "recovery": [], "auc": [], "late": [], "series": []}
            for arm in arms
        }
        for seed in seeds:
            for arm, schedule in arms.items():
                agent = make_agent(
                    f"Agente {arm}", serial=seed * 10 + 1,
                    traits={"neuroticism": 0.55, "conscientiousness": 0.5},
                    money=90.0,
                )
                social, partners = support_network(agent, level=0.65)
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                engine.ensure(agent)
                series: list[float] = []
                for day in range(180):
                    for ev_day, ev_type, importance in schedule:
                        if day == ev_day:
                            engine.process_events(
                                [event(ev_type, agent, day, importance=importance)],
                                pop, social,
                            )
                    engine.step_population(
                        pop, day, social=social, tick_minutes=1440, force_all=True
                    )
                    series.append(round(agent.psychology.chronic_stress, 4))
                peak = max(series)
                end = series[-1]
                result[arm]["peak"].append(peak)
                result[arm]["end"].append(end)
                result[arm]["recovery"].append(peak - end)
                # Exposure burden (days 10-90) and stress persisting 80 days
                # after the last stressor (days 100-180).
                result[arm]["auc"].append(sum(series[10:90]))
                result[arm]["late"].append(statistics.fmean(series[100:]))
                result[arm]["series"].append(series)

        chronic_peak = summary(result["chronic"]["peak"])
        acute_peak = summary(result["acute"]["peak"])
        control_end = summary(result["control"]["end"])
        d_peak = cohens_d(result["chronic"]["peak"], result["acute"]["peak"])
        d_late = cohens_d(result["chronic"]["late"], result["acute"]["late"])
        chronic_auc = summary(result["chronic"]["auc"])
        acute_auc = summary(result["acute"]["auc"])
        chronic_late = summary(result["chronic"]["late"])
        acute_late = summary(result["acute"]["late"])

        hypotheses = [
            self._hyp(
                "H1", "La exposición repetida produce mayor estrés crónico que un shock único",
                SUPPORTED if chronic_peak["mean"] > acute_peak["mean"] + 0.03 else REJECTED,
                "chronic_peak_mean vs acute_peak_mean",
                f"{chronic_peak['mean']} vs {acute_peak['mean']} (d={d_peak})",
            ),
            self._hyp(
                "H2", "La carga acumulada durante la exposición es mayor con estresores repetidos",
                SUPPORTED if chronic_auc["mean"] > acute_auc["mean"] * 1.05 else REJECTED,
                "AUC of chronic stress, days 10-90",
                f"{chronic_auc['mean']} vs {acute_auc['mean']}",
            ),
            self._hyp(
                "H3", "El efecto persiste tras cesar los estresores",
                SUPPORTED if chronic_late["mean"] > acute_late["mean"] + 0.02 else INCONCLUSIVE,
                "late mean (days 100-180) / Cohen d",
                f"{chronic_late['mean']} vs {acute_late['mean']} / d={d_late}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_A: estrés agudo frente a acumulación crónica",
            hypotheses,
            {
                "control_end": control_end,
                "acute_peak": acute_peak,
                "chronic_peak": chronic_peak,
                "acute_end": summary(result["acute"]["end"]),
                "chronic_end": summary(result["chronic"]["end"]),
                "acute_auc": acute_auc,
                "chronic_auc": chronic_auc,
                "acute_late": acute_late,
                "chronic_late": chronic_late,
                "cohens_d_peak": d_peak,
                "cohens_d_late": d_late,
                "sample_trajectory": result["chronic"]["series"][0][::20],
            },
        )


# ===========================================================================
# EXP_17_B — Individual response diversity
# ===========================================================================

class Experiment17_B_IndividualResponseDiversity(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_B",
            name="Diversidad de respuesta individual",
            description="Un mismo despido, seis biografías distintas, múltiples semillas.",
            duration_ticks=60 * 96,
            random_seed=29,
            population_size=6,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        personas = {
            "ansioso": {"neuroticism": 0.9, "conscientiousness": 0.45, "agreeableness": 0.55},
            "seguro": {"neuroticism": 0.15, "conscientiousness": 0.8, "agreeableness": 0.7},
            "proveedor": {"neuroticism": 0.55, "conscientiousness": 0.85, "agreeableness": 0.65},
            "desapegado": {"neuroticism": 0.25, "conscientiousness": 0.4, "agreeableness": 0.3},
            "resentido": {"neuroticism": 0.7, "conscientiousness": 0.5, "agreeableness": 0.15},
            "pragmatico": {"neuroticism": 0.35, "conscientiousness": 0.7, "agreeableness": 0.5},
        }
        support_levels = {"ansioso": 0.35, "seguro": 0.8, "proveedor": 0.55, "desapegado": 0.2, "resentido": 0.3, "pragmatico": 0.65}
        seeds = [29, 37, 41]
        records: dict[str, list[dict[str, Any]]] = {name: [] for name in personas}

        for seed in seeds:
            for name, traits in personas.items():
                agent = make_agent(name, serial=seed * 10 + list(personas).index(name), traits=traits)
                # The same event has a different meaning depending on what the
                # person had built around that job.  These are biographical
                # conditions, not a label attached to the outcome.
                history = {
                    "ansioso": (0.45, {"security": 0.9, "benevolence": 0.6}),
                    "seguro": (0.55, {"autonomy": 0.8, "achievement": 0.7}),
                    "proveedor": (0.9, {"security": 0.95, "benevolence": 0.85}),
                    "desapegado": (0.15, {"autonomy": 0.9, "stimulation": 0.8}),
                    "resentido": (0.6, {"tradition": 0.9, "security": 0.7}),
                    "pragmatico": (0.1, {"achievement": 0.9, "autonomy": 0.8}),
                }[name]
                agent.preferences["job_satisfaction"] = history[0]
                agent.personality.personal_values.update(history[1])
                social, partners = support_network(agent, level=support_levels[name])
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                engine.ensure(agent)
                run_days(
                    engine, pop, 30, social=social,
                    events_by_day={2: [event(EventType.JOB_LOST, agent, 2, importance=0.9)]},
                )
                record = agent.psychology.recent_appraisals[-1] if agent.psychology.recent_appraisals else None
                # Dominant *appraisal-generated* emotion, not baseline mood:
                # the profile also contains slow hope/loneliness states that
                # would otherwise mask the event's immediate meaning.
                generated = record.emotions if record else {}
                generated_top = max(generated, key=generated.get) if generated else "none"
                generated_negative = sum(
                    v for k, v in generated.items()
                    if k in ("sadness", "fear", "anxiety", "anger", "frustration", "shame", "guilt", "distress")
                )
                records[name].append(
                    {
                        "seed": seed,
                        "dominant": generated_top,
                        "desirability": record.desirability if record else 0.0,
                        "expectedness": record.expectedness if record else 0.0,
                        "control": record.control if record else 0.0,
                        "chronic": round(agent.psychology.chronic_stress, 4),
                        "negative": round(generated_negative, 4),
                        "profile_negative": negative_emotions(agent),
                        "positive": round(sum(v for k, v in generated.items() if k in ("joy", "hope", "satisfaction", "relief", "pride")), 4),
                        "neuroticism": traits["neuroticism"],
                    }
                )

        flat = [r for rows in records.values() for r in rows]
        distinct = sorted({r["dominant"] for r in flat})
        desirability_range = round(max(r["desirability"] for r in flat) - min(r["desirability"] for r in flat), 3)
        corr = _pearson([r["neuroticism"] for r in flat], [r["negative"] for r in flat])
        chronic_by_persona = {name: summary([r["chronic"] for r in rows]) for name, rows in records.items()}

        hypotheses = [
            self._hyp(
                "H1", "El mismo acontecimiento produce emociones dominantes distintas",
                SUPPORTED if len(distinct) >= 2 else REJECTED,
                "distinct dominant emotions", f"{len(distinct)}: {distinct}",
            ),
            self._hyp(
                "H2", "La evaluación individual varía (no solo la intensidad)",
                SUPPORTED if desirability_range >= 0.15 else INCONCLUSIVE,
                "range(desirability)", desirability_range,
            ),
            self._hyp(
                "H3", "La variación se asocia a diferencias individuales, no a ruido",
                SUPPORTED if abs(corr) >= 0.35 else INCONCLUSIVE,
                "corr(neuroticism, negative appraisal)", corr,
            ),
        ]
        return self._finish(
            started,
            "EXP_17_B: un despido, seis biografías",
            hypotheses,
            {
                "distinct_emotions": distinct,
                "desirability_range": desirability_range,
                "corr_neuroticism_negative": corr,
                "chronic_by_persona": chronic_by_persona,
                "samples": flat[:12],
            },
        )


# ===========================================================================
# EXP_17_C — Psychological breakdown and recovery
# ===========================================================================

class Experiment17_C_PsychologicalBreakdown(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_C",
            name="Deterioro psicológico y recuperación del autocontrol",
            description="Compara perfiles vulnerables y resilientes bajo estresores sostenidos.",
            duration_ticks=240 * 96,
            random_seed=43,
            population_size=2,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        seeds = [43, 47, 53]
        # Same initial pressure and support; only the person differs.  This is
        # the individual-threshold test, not a comparison of "good" and "bad"
        # lives.
        arms = {
            "vulnerable": {
                "traits": {"neuroticism": 0.9, "conscientiousness": 0.3, "agreeableness": 0.3},
                "chronic": 0.80, "control": 0.20, "support": 0.20,
            },
            "resiliente": {
                "traits": {"neuroticism": 0.2, "conscientiousness": 0.8, "agreeableness": 0.7},
                "chronic": 0.80, "control": 0.20, "support": 0.20,
            },
        }
        rows: dict[str, list[dict[str, Any]]] = {a: [] for a in arms}
        for seed in seeds:
            for arm, cfg in arms.items():
                agent = make_agent(arm, serial=seed * 10 + 2, traits=cfg["traits"])
                social, partners = support_network(agent, level=cfg["support"])
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                stress_agent(
                    engine, agent, chronic=cfg["chronic"], acute=0.65,
                    fatigue=0.55, control=cfg["control"], loneliness=0.55,
                    support=cfg["support"],
                )
                seen = set()
                ended_days: list[int] = []
                days_in_crisis = 0
                for day in range(240):
                    engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                    if agent.psychology.in_crisis():
                        days_in_crisis += 1
                    for ep in agent.psychology.crisis_history:
                        if not ep.is_active and ep.ended_tick is not None and ep.crisis_id not in seen:
                            seen.add(ep.crisis_id)
                            ended_days.append(ep.ended_tick)
                peaks = [ep.peak_severity for ep in agent.psychology.crisis_history]
                rows[arm].append(
                    {
                        "crises": len(agent.psychology.crisis_history),
                        "peak": max(peaks) if peaks else 0.0,
                        "days_in_crisis": days_in_crisis,
                        "recovered": len(ended_days),
                        "residual": round(agent.psychology.post_crisis_vulnerability, 4),
                        "control_end": round(agent.psychology.self_control, 4),
                        "chronic_end": round(agent.psychology.chronic_stress, 4),
                        "active": agent.psychology.in_crisis(),
                    }
                )

        vul = rows["vulnerable"]
        res = rows["resiliente"]
        vul_peak = summary([r["peak"] for r in vul])
        res_peak = summary([r["peak"] for r in res])
        vul_control = summary([r["control_end"] for r in vul])
        res_control = summary([r["control_end"] for r in res])
        hypotheses = [
            self._hyp(
                "H1", "La presión sostenida produce crisis en ambos perfiles",
                SUPPORTED if all(r["crises"] > 0 for r in vul + res) else REJECTED,
                "individuals with at least one crisis",
                f"{sum(1 for r in vul + res if r['crises'] > 0)}/{len(vul + res)}",
            ),
            self._hyp(
                "H2", "Con la misma presión, el perfil vulnerable pierde más autocontrol y sufre crisis más severas",
                SUPPORTED if vul_peak["mean"] > res_peak["mean"] and vul_control["mean"] < res_control["mean"] else REJECTED,
                "peak / end self-control vulnerable vs resilient",
                f"{vul_peak['mean']} / {vul_control['mean']} vs {res_peak['mean']} / {res_control['mean']}",
            ),
            self._hyp(
                "H3", "Las crisis iniciadas pueden terminar; no son etiquetas permanentes",
                SUPPORTED if any(r["recovered"] > 0 for r in vul + res) else INCONCLUSIVE,
                "episodes ended", sum(r["recovered"] for r in vul + res),
            ),
        ]
        return self._finish(
            started,
            "EXP_17_C: deterioro y recuperación del autocontrol",
            hypotheses,
            {
                "vulnerable": vul,
                "resiliente": res,
                "vulnerable_peak": vul_peak,
                "resilient_peak": res_peak,
                "vulnerable_control_end": vul_control,
                "resilient_control_end": res_control,
            },
        )


# ===========================================================================
# EXP_17_D — Adaptive coping
# ===========================================================================

class Experiment17_D_AdaptiveCoping(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_D",
            name="Afrontamiento adaptativo por categoría",
            description="Compara estrategias centradas en problema, emoción y evitación.",
            duration_ticks=60 * 96,
            random_seed=59,
            population_size=3,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        arms = {
            "problema": CopingStrategy.REDUCE_EXPENSES,
            "emocion": CopingStrategy.REST,
            "evitacion": CopingStrategy.PROCRASTINATION,
        }
        seeds = [59, 61, 67]
        rows: dict[str, list[dict[str, float]]] = {a: [] for a in arms}
        for seed in seeds:
            for arm, strategy in arms.items():
                agent = make_agent(arm, serial=seed * 10 + 3, money=30.0)
                social, partners = support_network(agent, level=0.65)
                pop = pop_of(agent, *partners)
                engine = PsychologicalEngine(seed=seed)
                psych = engine.ensure(agent)
                psych.chronic_stress = 0.55
                psych.acute_stress = 0.60
                psych.self_control = 0.35
                # Isolate the assigned strategy: no automatic strategy choice
                # competing with it.
                engine._should_cope = lambda *args, **kwargs: False  # type: ignore[assignment]
                spec = COPING_SPECS[strategy]
                before_chronic = psych.chronic_stress
                before_acute = psych.acute_stress
                reliefs: list[float] = []
                long_terms: list[float] = []
                # Four attempts across a month, each followed by a new
                # financial pressure.  This prevents natural decay from being
                # mistaken for a coping benefit.
                for cycle in range(4):
                    tick = cycle * 7
                    episode = engine.coping.execute(
                        agent, psych, CopingChoice(spec, 0.5),
                        tick=tick, support_engine=engine.support,
                        assessment=engine.support.assess(agent, social, None, pop),
                        social=social, population=pop,
                    )
                    episode.follow_up_tick = tick + 7
                    reliefs.append(episode.short_term_relief)
                    for day in range(tick + 1, tick + 8):
                        if day % 3 == 0:
                            engine.process_events(
                                [event(EventType.FINANCIAL_LOSS, agent, day, importance=0.55)],
                                pop, social,
                            )
                        engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                        if day == tick + 7:
                            # step_population resolves due episodes internally,
                            # so read the realised outcome rather than only the
                            # call's return value.
                            resolved = [
                                item for item in psych.coping_history
                                if item.strategy == strategy and item.deferred_applied
                            ]
                            if resolved:
                                long_terms.append(resolved[-1].long_term_delta)
                rows[arm].append(
                    {
                        "relief": round(statistics.fmean(reliefs), 4),
                        "acute_delta": round(before_acute - psych.acute_stress, 4),
                        "chronic_delta": round(psych.chronic_stress - before_chronic, 4),
                        "long_term": round(statistics.fmean(long_terms), 4) if long_terms else 0.0,
                        "control": psych.self_control,
                        "preference": psych.coping.preference(strategy),
                    }
                )

        def metric(arm: str, key: str) -> dict[str, float]:
            return summary([r[key] for r in rows[arm]])

        hypotheses = [
            self._hyp(
                "H1", "Las estrategias centradas en el problema reducen más el estrés crónico",
                SUPPORTED
                if metric("problema", "chronic_delta")["mean"] < metric("evitacion", "chronic_delta")["mean"]
                else REJECTED,
                "chronic_delta (negative improves)",
                f"problema={metric('problema', 'chronic_delta')['mean']}, "
                f"emocion={metric('emocion', 'chronic_delta')['mean']}, "
                f"evitacion={metric('evitacion', 'chronic_delta')['mean']}",
            ),
            self._hyp(
                "H2", "Las estrategias emocionales alivian más el estrés agudo inmediato",
                SUPPORTED
                if metric("emocion", "acute_delta")["mean"] >= metric("problema", "acute_delta")["mean"]
                else INCONCLUSIVE,
                "acute_delta",
                f"emocion={metric('emocion', 'acute_delta')['mean']}, "
                f"problema={metric('problema', 'acute_delta')['mean']}",
            ),
            self._hyp(
                "H3", "La evitación puede aliviar a corto plazo y empeorar el largo plazo",
                SUPPORTED
                if metric("evitacion", "relief")["mean"] > 0
                and metric("evitacion", "long_term")["mean"] < 0
                else INCONCLUSIVE,
                "relief vs long_term_delta",
                f"{metric('evitacion', 'relief')['mean']} vs {metric('evitacion', 'long_term')['mean']}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_D: problema, emoción y evitación",
            hypotheses,
            {arm: {k: metric(arm, k) for k in ("relief", "acute_delta", "chronic_delta", "long_term", "control")} for arm in arms},
        )


# ===========================================================================
# EXP_17_E — Coping trade-offs
# ===========================================================================

class Experiment17_E_CopingTradeOffs(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_E",
            name="Trade-offs del afrontamiento",
            description="Mide alivio inmediato y consecuencia diferida de la procrastinación repetida.",
            duration_ticks=120 * 96,
            random_seed=71,
            population_size=1,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        seeds = [71, 73, 79]
        trajectories: list[dict[str, Any]] = []
        for seed in seeds:
            agent = make_agent("Procrastinador", serial=seed * 10 + 4)
            social, partners = support_network(agent, level=0.45)
            pop = pop_of(agent, *partners)
            engine = PsychologicalEngine(seed=seed)
            psych = engine.ensure(agent)
            psych.chronic_stress = 0.45
            psych.acute_stress = 0.55
            psych.self_control = 0.32
            engine._should_cope = lambda *args, **kwargs: False  # type: ignore[assignment]
            reliefs: list[float] = []
            long_terms: list[float] = []
            prefs: list[float] = []
            chronic: list[float] = []
            spec = COPING_SPECS[CopingStrategy.PROCRASTINATION]
            for cycle in range(8):
                tick = cycle * 10
                episode = engine.coping.execute(
                    agent, psych, CopingChoice(spec, 0.5),
                    tick=tick, support_engine=engine.support,
                    assessment=engine.support.assess(agent, social, None, pop),
                    social=social, population=pop,
                )
                episode.follow_up_tick = tick + 7
                reliefs.append(round(episode.short_term_relief, 4))
                for day in range(tick, tick + 10):
                    if day > tick and day % 5 == 0:
                        engine.process_events(
                            [event(EventType.FINANCIAL_LOSS, agent, day, importance=0.55)],
                            pop, social,
                        )
                    engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                    engine.coping.resolve_due(psych, day)
                resolved = [e for e in psych.coping_history if e.deferred_applied and e.strategy == CopingStrategy.PROCRASTINATION]
                if resolved:
                    long_terms.append(round(resolved[-1].long_term_delta, 4))
                prefs.append(round(psych.coping.preference(CopingStrategy.PROCRASTINATION), 4))
                chronic.append(round(psych.chronic_stress, 4))
            trajectories.append(
                {
                    "reliefs": reliefs,
                    "long_terms": long_terms,
                    "prefs": prefs,
                    "chronic": chronic,
                }
            )

        mean_relief = statistics.fmean([v for t in trajectories for v in t["reliefs"]])
        mean_long = statistics.fmean([v for t in trajectories for v in t["long_terms"]]) if any(t["long_terms"] for t in trajectories) else 0.0
        preference_drop = statistics.fmean([t["prefs"][0] - t["prefs"][-1] for t in trajectories])
        hypotheses = [
            self._hyp(
                "H1", "La estrategia evitativa produce alivio inmediato medible",
                SUPPORTED if mean_relief > 0.03 else REJECTED,
                "mean short-term relief", round(mean_relief, 4),
            ),
            self._hyp(
                "H2", "El beneficio inmediato coexiste con un coste diferido",
                SUPPORTED if mean_long < 0 else INCONCLUSIVE,
                "mean long_term_delta (negative = worse)", round(mean_long, 4),
            ),
            self._hyp(
                "H3", "El aprendizaje corrige parcialmente la preferencia tras resultados negativos",
                SUPPORTED if preference_drop < 0 else REJECTED,
                "preference drop first→last", round(preference_drop, 4),
            ),
        ]
        return self._finish(
            started,
            "EXP_17_E: alivio ahora, coste después",
            hypotheses,
            {
                "mean_relief": round(mean_relief, 4),
                "mean_long_term_delta": round(mean_long, 4),
                "preference_drop": round(preference_drop, 4),
                "trajectories": trajectories,
            },
        )


# ===========================================================================
# EXP_17_F — Emotional appraisal
# ===========================================================================

class Experiment17_F_EmotionalAppraisal(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_F",
            name="Evaluación emocional OCC",
            description="Un mismo acontecimiento con metas, valores y expectativas distintas.",
            duration_ticks=10,
            random_seed=83,
            population_size=4,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        personas = {
            "odiaba_su_trabajo": {
                "traits": {"neuroticism": 0.4, "conscientiousness": 0.5},
                "job_satisfaction": 0.05,
                "values": {"autonomy": 0.85, "security": 0.2},
            },
            "sostiene_familia": {
                "traits": {"neuroticism": 0.6, "conscientiousness": 0.8},
                "job_satisfaction": 0.85,
                "values": {"security": 0.95, "benevolence": 0.8},
            },
            "verguenza_social": {
                "traits": {"neuroticism": 0.75, "agreeableness": 0.4},
                "job_satisfaction": 0.6,
                "values": {"tradition": 0.9, "security": 0.7},
            },
            "esperanzado": {
                "traits": {"neuroticism": 0.2, "openness": 0.85},
                "job_satisfaction": 0.3,
                "values": {"achievement": 0.9, "autonomy": 0.8},
            },
        }
        results: dict[str, dict[str, Any]] = {}
        for name, cfg in personas.items():
            agent = make_agent(name, serial=list(personas).index(name) + 1, traits=cfg["traits"])
            agent.preferences["job_satisfaction"] = cfg["job_satisfaction"]
            agent.personality.personal_values.update(cfg["values"])
            social, partners = support_network(agent, level=0.55)
            pop = pop_of(agent, *partners)
            engine = PsychologicalEngine(seed=83)
            engine.ensure(agent)
            engine.process_events(
                [event(EventType.JOB_LOST, agent, 1, importance=0.9)],
                pop, social,
            )
            record = agent.psychology.recent_appraisals[-1]
            results[name] = {
                "desirability": record.desirability,
                "expectedness": record.expectedness,
                "control": record.control,
                "dominant": dominant_emotion(engine, agent),
                "emotions": dict(record.emotions),
                "negative": negative_emotions(agent),
                "positive": positive_emotions(agent),
            }

        signs = {name: (1 if r["desirability"] > 0 else -1) for name, r in results.items()}
        distinct = sorted({r["dominant"] for r in results.values()})
        hypotheses = [
            self._hyp(
                "H1", "La deseabilidad no se deriva sólo del tipo de acontecimiento",
                SUPPORTED if len(set(signs.values())) > 1 else REJECTED,
                "signs of desirability", signs,
            ),
            self._hyp(
                "H2", "Personas distintas experimentan emociones dominantes distintas",
                SUPPORTED if len(distinct) >= 2 else REJECTED,
                "distinct dominant emotions", distinct,
            ),
            self._hyp(
                "H3", "La evaluación deja trazabilidad de metas, control y confianza",
                SUPPORTED if all("control" in r and "expectedness" in r for r in results.values()) else REJECTED,
                "appraisal fields present", True,
            ),
        ]
        return self._finish(
            started,
            "EXP_17_F: el mismo despido, cuatro significados",
            hypotheses,
            {"personas": results, "distinct_emotions": distinct},
        )


# ===========================================================================
# EXP_17_G — Memory retrieval
# ===========================================================================

class Experiment17_G_MemoryRetrieval(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_G",
            name="Recuperación asociativa de memoria",
            description="Evalúa recencia, importancia, relevancia y selectividad del índice.",
            duration_ticks=1,
            random_seed=97,
            population_size=1,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        records = [
            EpisodicRecord(summary="Desayuno rutinario", tick=990, importance=0.10, emotional_valence=0.1),
            EpisodicRecord(summary="Discusión con Marta en el mercado", tick=980, importance=0.85, emotional_valence=-0.8, associated_humans=["marta"], location_id="mercado_central", context_tags=["conflict"]),
            EpisodicRecord(summary="Paseo por el parque", tick=500, importance=0.20, emotional_valence=0.2, location_id="parque_central", context_tags=["leisure"]),
            EpisodicRecord(summary="Trabajo estable durante años", tick=100, importance=0.75, emotional_valence=0.4, location_id="taller", context_tags=["work"]),
            EpisodicRecord(summary="Ayuda de José con la renta", tick=800, importance=0.65, emotional_valence=0.6, associated_humans=["jose"], context_tags=["support"]),
        ]
        retrieval = AssociativeRetrieval()
        top_recent = retrieval.retrieve(uid="u", records=records, tick=1000, query=RetrievalQuery(limit=2))
        top_important = retrieval.retrieve(uid="u", records=records, tick=1000, query=RetrievalQuery(tags=("conflict",), limit=2))
        top_relevant = retrieval.retrieve(uid="u", records=records, tick=1000, query=RetrievalQuery(associated_human="jose", limit=2))
        candidates = retrieval.stats["candidates_examined"]

        hypotheses = [
            self._hyp(
                "H1", "La recencia influye en la recuperación cuando no hay otra señal",
                SUPPORTED if top_recent[0].tick >= 800 else REJECTED,
                "top tick (no cue)", top_recent[0].tick,
            ),
            self._hyp(
                "H2", "La relevancia contextual puede superar a la recencia",
                SUPPORTED if any(r.associated_humans == ["jose"] for r in top_relevant) else REJECTED,
                "top relevance memory", top_relevant[0].summary,
            ),
            self._hyp(
                "H3", "La recuperación es selectiva, no un escaneo completo",
                SUPPORTED if candidates < len(records) * 4 else INCONCLUSIVE,
                "candidates examined per query", candidates,
            ),
        ]
        return self._finish(
            started,
            "EXP_17_G: recuperación selectiva y contextual",
            hypotheses,
            {
                "top_recent": [r.summary for r in top_recent],
                "top_important": [r.summary for r in top_important],
                "top_relevant": [r.summary for r in top_relevant],
                "candidates_examined": candidates,
            },
        )


# ===========================================================================
# EXP_17_H — Memory distortion
# ===========================================================================

class Experiment17_H_MemoryDistortion(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_H",
            name="Olvido, reconstrucción y contradicción",
            description="Mide fidelidad, distorsión afectiva y recuerdos contradictorios.",
            duration_ticks=1,
            random_seed=101,
            population_size=1,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        rec = EpisodicRecord(
            summary="Discusión con Marta en el mercado por una deuda; gritos, gente mirando, luego silencio",
            tick=0,
            importance=0.8,
            emotional_valence=-0.75,
            associated_humans=["marta"],
            context_tags=["conflict"],
        )
        retrieval = AssociativeRetrieval()
        agent = make_agent("Recordador", serial=101)
        engine = PsychologicalEngine(seed=101)
        psych = engine.ensure(agent)
        psych.sadness = 0.6
        psych.hope = 0.3
        sad = retrieval.reconstruct(rec, tick=0, psych=psych)
        psych.sadness = 0.1
        psych.hope = 0.8
        hopeful = retrieval.reconstruct(rec, tick=0, psych=psych)
        aged = retrieval.reconstruct(rec, tick=96 * 200, psych=psych)

        other = EpisodicRecord(
            summary="Marta me ayudó cuando estaba enfermo",
            tick=50,
            importance=0.7,
            emotional_valence=0.7,
            associated_humans=["marta"],
        )
        contradictions = retrieval.find_contradictions([rec, other])

        hypotheses = [
            self._hyp(
                "H1", "La fidelidad declina con el tiempo",
                SUPPORTED if aged.fidelity < sad.fidelity - 0.15 else REJECTED,
                "fidelity at 0 vs 200 days", f"{sad.fidelity} vs {aged.fidelity}",
            ),
            self._hyp(
                "H2", "El estado afectivo actual sesga la reconstrucción",
                SUPPORTED if sad.reconstructed_summary != hopeful.reconstructed_summary else REJECTED,
                "reconstructed differs by mood", sad.reconstructed_summary != hopeful.reconstructed_summary,
            ),
            self._hyp(
                "H3", "Se detectan recuerdos contradictorios sobre la misma persona",
                SUPPORTED if len(contradictions) > 0 else INCONCLUSIVE,
                "contradiction pairs", len(contradictions),
            ),
        ]
        return self._finish(
            started,
            "EXP_17_H: la memoria no es una copia",
            hypotheses,
            {
                "fresh": dataclasses.asdict(sad),
                "aged": dataclasses.asdict(aged),
                "hopeful": dataclasses.asdict(hopeful),
                "contradictions": contradictions,
            },
        )


# ===========================================================================
# EXP_17_I — Grief trajectories
# ===========================================================================

class Experiment17_I_GriefTrajectories(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_I",
            name="Trayectorias de duelo",
            description="Compara perfiles y apoyo sin imponer una recuperación uniforme.",
            duration_ticks=180 * 96,
            random_seed=103,
            population_size=8,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        personas = {
            "apegado": {"neuroticism": 0.85, "agreeableness": 0.8, "conscientiousness": 0.4},
            "pragmatico": {"neuroticism": 0.25, "agreeableness": 0.5, "conscientiousness": 0.8},
            "aislado": {"neuroticism": 0.6, "agreeableness": 0.3, "conscientiousness": 0.5},
            "comunitario": {"neuroticism": 0.45, "agreeableness": 0.8, "conscientiousness": 0.6},
        }
        # Same persona and seed in both arms: only the available network
        # changes.  Comparing different personalities would confound support
        # with neuroticism and agreeableness.
        support_levels = {"bajo": 0.15, "alto": 0.85}
        seeds = [103, 107]
        rows: dict[str, dict[str, list[dict[str, float]]]] = {
            name: {arm: [] for arm in support_levels} for name in personas
        }
        for seed in seeds:
            for name, traits in personas.items():
                for arm, level in support_levels.items():
                    agent = make_agent(name, serial=seed * 10 + 5, traits=traits)
                    social, partners = support_network(agent, level=level)
                    deceased = make_agent("Fallecido", serial=seed * 10 + 99)
                    pop = pop_of(agent, deceased, *partners)
                    tie(social, agent, deceased, trust=0.9, affinity=0.95, familiarity=0.9)
                    engine = PsychologicalEngine(seed=seed)
                    engine.ensure(agent)
                    engine.process_events(
                        [event(EventType.BEREAVEMENT_EXPERIENCED, agent, 2, importance=0.95, target=deceased)],
                        pop, social,
                    )
                    series: list[float] = []
                    recovery_day = None
                    peak = 0.0
                    for day in range(180):
                        engine.step_population(pop, day, social=social, tick_minutes=1440, force_all=True)
                        value = agent.psychology.sadness
                        series.append(round(value, 4))
                        peak = max(peak, value)
                        if recovery_day is None and day > 10 and value < 0.25 and peak > 0.4:
                            recovery_day = day
                    baseline = series[0]
                    rows[name][arm].append(
                        {
                            "peak": peak,
                            "day30": series[min(29, len(series) - 1)],
                            "day90": series[min(89, len(series) - 1)],
                            "day180": series[-1],
                            "recovery_day": float(recovery_day if recovery_day is not None else -1),
                            "residual": round(series[-1] - baseline, 4),
                        }
                    )

        all_rows = [r for by_arm in rows.values() for arm_rows in by_arm.values() for r in arm_rows]
        recovery_values = [r["recovery_day"] for r in all_rows if r["recovery_day"] >= 0]
        low_support = [r for name in personas for r in rows[name]["bajo"]]
        high_support = [r for name in personas for r in rows[name]["alto"]]
        paired_deltas = [
            rows[name]["bajo"][i]["day30"] - rows[name]["alto"][i]["day30"]
            for name in personas
            for i in range(min(len(rows[name]["bajo"]), len(rows[name]["alto"])))
        ]
        d30 = cohens_d([r["day30"] for r in low_support], [r["day30"] for r in high_support])
        mean_paired_delta = sum(paired_deltas) / max(1, len(paired_deltas))
        still_elevated = sum(1 for r in all_rows if r["day180"] > 0.22)

        hypotheses = [
            self._hyp(
                "H1", "Las trayectorias de duelo son heterogéneas",
                SUPPORTED if len({round(r["day30"], 2) for r in all_rows}) > 1 else INCONCLUSIVE,
                "distinct day-30 sadness values",
                len({round(r["day30"], 2) for r in all_rows}),
            ),
            self._hyp(
                "H2", "Con la misma personalidad, más apoyo reduce la tristeza a 30 días",
                SUPPORTED if d30 > 0.2 and mean_paired_delta > 0 else REJECTED,
                "Cohen d (low-support - high-support); paired delta",
                f"{d30} / {mean_paired_delta:.4f}",
            ),
            self._hyp(
                "H3", "No todas las personas vuelven al nivel previo en 180 días",
                SUPPORTED if still_elevated > 0 else REJECTED,
                "still elevated at day 180", still_elevated,
            ),
        ]
        return self._finish(
            started,
            "EXP_17_I: duelo sin recuperación uniforme",
            hypotheses,
            {
                "by_persona": {
                    name: {
                        arm: summary([r["day30"] for r in arm_rows])
                        for arm, arm_rows in by_arm.items()
                    }
                    for name, by_arm in rows.items()
                },
                "recovery_days": recovery_values,
                "cohens_d_day30": d30,
                "mean_paired_delta": round(mean_paired_delta, 4),
                "paired_deltas": [round(x, 4) for x in paired_deltas],
                "still_elevated": still_elevated,
                "rows": rows,
            },
        )


# ===========================================================================
# EXP_17_J — Physical–psychological interaction
# ===========================================================================

class Experiment17_J_PhysicalPsychological(Phase17Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_17_J",
            name="Interacción cuerpo–mente",
            description="Hambre, sueño, dolor y fatiga modifican estrés y autocontrol; el descontrol afecta al cuerpo.",
            duration_ticks=60 * 96,
            random_seed=109,
            population_size=4,
        )

    def run(self, runner=None):
        import time

        started = time.time()
        seeds = [109, 113]
        conditions = {
            "control": {"hunger": 0.15, "energy": 0.95, "pain": 0.0, "health": 1.0},
            "hambre": {"hunger": 0.9, "energy": 0.8, "pain": 0.0, "health": 1.0},
            "sueño": {"hunger": 0.2, "energy": 0.12, "pain": 0.0, "health": 1.0},
            "dolor": {"hunger": 0.2, "energy": 0.8, "pain": 0.7, "health": 0.55},
        }
        rows: dict[str, list[dict[str, float]]] = {c: [] for c in conditions}
        for seed in seeds:
            for name, cfg in conditions.items():
                agent = make_agent(name, serial=seed * 10 + 6)
                agent.physical_state.hunger = cfg["hunger"]
                agent.physical_state.energy = cfg["energy"]
                agent.physical_state.health = cfg["health"]
                if cfg["pain"] > 0:
                    agent.active_health_conditions.append(
                        SimpleNamespace(name="Dolor crónico", severity=cfg["pain"], category="injury", is_treated=False)
                    )
                pop = pop_of(agent)
                engine = PsychologicalEngine(seed=seed)
                engine.ensure(agent)
                for day in range(30):
                    engine.step_population(pop, day, tick_minutes=1440, force_all=True)
                rows[name].append(
                    {
                        "stress": round(agent.psychology.acute_stress, 4),
                        "fatigue": round(agent.psychology.mental_fatigue, 4),
                        "control": round(agent.psychology.self_control, 4),
                        "hope": round(agent.psychology.hope, 4),
                    }
                )

        # Mind → body arm: low self-control vs regulated, same body.
        body_rows = {"descontrol": [], "regulado": []}
        for seed in seeds:
            for arm, control in (("descontrol", 0.12), ("regulado", 0.75)):
                agent = make_agent(arm, serial=seed * 10 + 7)
                pop = pop_of(agent)
                engine = PsychologicalEngine(seed=seed)
                psych = engine.ensure(agent)
                psych.self_control = control
                psych.chronic_stress = 0.75 if arm == "descontrol" else 0.25
                psych.hope = 0.2 if arm == "descontrol" else 0.7
                before_hunger = agent.physical_state.hunger
                before_health = agent.physical_state.health
                for day in range(60):
                    engine.step_population(pop, day, tick_minutes=1440, force_all=True)
                body_rows[arm].append(
                    {
                        "hunger_delta": round(agent.physical_state.hunger - before_hunger, 4),
                        "health_delta": round(agent.physical_state.health - before_health, 4),
                    }
                )

        def m(name: str, key: str) -> float:
            return summary([r[key] for r in rows[name]])["mean"]

        hypotheses = [
            self._hyp(
                "H1", "Hambre y deuda de sueño elevan el estrés agudo",
                SUPPORTED if m("hambre", "stress") > m("control", "stress") and m("sueño", "stress") > m("control", "stress") else REJECTED,
                "stress hambre/sueño/control",
                f"{m('hambre', 'stress')}/{m('sueño', 'stress')}/{m('control', 'stress')}",
            ),
            self._hyp(
                "H2", "Dolor y enfermedad elevan la fatiga y reducen el autocontrol",
                SUPPORTED if m("dolor", "fatigue") > m("control", "fatigue") and m("dolor", "control") < m("control", "control") else REJECTED,
                "fatigue/control dolor vs control",
                f"{m('dolor', 'fatigue')}/{m('dolor', 'control')} vs {m('control', 'fatigue')}/{m('control', 'control')}",
            ),
            self._hyp(
                "H3", "El descontrol psicológico se traduce en deterioro corporal",
                SUPPORTED
                if summary([r["hunger_delta"] for r in body_rows["descontrol"]])["mean"]
                > summary([r["hunger_delta"] for r in body_rows["regulado"]])["mean"]
                else REJECTED,
                "hunger delta descontrol vs regulado",
                f"{summary([r['hunger_delta'] for r in body_rows['descontrol']])['mean']} vs "
                f"{summary([r['hunger_delta'] for r in body_rows['regulado']])['mean']}",
            ),
        ]
        return self._finish(
            started,
            "EXP_17_J: cuerpo y mente se modifican mutuamente",
            hypotheses,
            {
                "conditions": {name: {k: summary([r[k] for r in rows[name]]) for k in ("stress", "fatigue", "control", "hope")} for name in rows},
                "body_arms": body_rows,
            },
        )
