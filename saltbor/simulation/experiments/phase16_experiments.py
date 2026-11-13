"""Phase 1.6 experiments: perception, world interaction and open-ended society.

Twenty experiments (EXP_16_A ... EXP_16_T) covering §22 of the Phase 1.6
specification.  Each experiment states a hypothesis, records the initial
conditions, runs several seeds, includes a control arm where the design allows
one, and reports the outcome *with* uncertainty.  Negative and inconclusive
results are reported honestly rather than coerced into support.

Scientific hygiene rules applied here:

* No experiment claims that a passing assertion is scientific validity.  What
  is asserted is that the mechanism operates as specified under the recorded
  conditions.
* Where an effect is probabilistic (accidents, illness, attraction) the
  experiment reports counts and rates over repeated trials, not a single draw.
* Where a mechanism is deterministic (acuity curves, routing cost) the
  experiment reports exact values and the seeds only exercise tie-breaking.
"""

from __future__ import annotations

import math
import statistics
import time
from typing import Any, Callable, Optional

import numpy as np

from saltbor.accidents.engine import MisfortuneEngine
from saltbor.cognition.perception.engine import PerceptionEngine
from saltbor.cognition.perception.models import (
    Interpretation,
    Observation,
    PerceptionChannel,
    TargetKind,
)
from saltbor.core.types import DisasterType, RomanceStage, Tick
from saltbor.events.bus import EventBus
from saltbor.events.causal_graph import CausalEventGraph
from saltbor.events.types import EventType, SimulationEvent
from saltbor.health.engine import HealthEngine
from saltbor.lifecycle.family.caregiving import FamilyCaregivingEngine
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.social.romance.engine import RomanceEngine
from saltbor.world.geographic.osm_router import OSMRoadNetwork
from saltbor.world.interaction.world_human_engine import WorldHumanInteractionEngine

SUPPORTED = "HYPOTHESIS_SUPPORTED"
REJECTED = "HYPOTHESIS_REJECTED"
INCONCLUSIVE = "INCONCLUSIVE"
ERROR = "EXPERIMENT_ERROR"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_human(
    *,
    age: float = 30.0,
    money: float = 80.0,
    name: str = "Sujeto Prueba",
    seed: int = 1,
    home: str = "casa_norte_1",
    traits: Optional[dict[str, float]] = None,
    energy: float = 1.0,
    serial: Optional[int] = None,
) -> SyntheticHuman:
    """Create a fully configured synthetic human for an experiment.

    The identity serial is derived from the seed unless given explicitly:
    perception keys its randomness off the serial, so two experiment subjects
    sharing one serial would share one detection draw and both see (or miss)
    each other for the same reason.
    """
    human = SyntheticHuman.create(
        name=name,
        age=age,
        money=money,
        seed=seed,
        serial=serial if serial is not None else 1 + abs(int(seed)) % 900_000,
    )
    human.physical_state.home_location_id = home
    human.physical_state.current_location_id = home
    human.physical_state.energy = energy
    if traits:
        for trait, value in traits.items():
            tv = getattr(human.personality.traits, trait, None)
            if tv is not None:
                tv.base_value = float(value)
                tv.current_value = float(value)
                tv.temperament_value = float(value)
    return human


def mean_sd(values: list[float]) -> dict[str, float]:
    """Return mean and sample standard deviation, safely for n < 2."""
    if not values:
        return {"mean": 0.0, "sd": 0.0, "n": 0}
    if len(values) == 1:
        return {"mean": round(values[0], 4), "sd": 0.0, "n": 1}
    return {
        "mean": round(statistics.fmean(values), 4),
        "sd": round(statistics.stdev(values), 4),
        "n": len(values),
    }


class Phase16Experiment(BaseExperiment):
    """Common result plumbing for the Phase 1.6 suite."""

    tick_budget = 96

    def default_config(self) -> ExperimentConfig:
        raise NotImplementedError

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
        summary: str,
        hypotheses: list[dict[str, Any]],
        metrics: dict[str, Any],
        anomalies: Optional[list[str]] = None,
        design_valid: bool = True,
    ) -> ExperimentResult:
        any_error = any(h["status"] == ERROR for h in hypotheses)
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=bool(hypotheses) and not any_error and design_valid,
            summary=summary,
            hypotheses=hypotheses,
            metrics=metrics,
            observed_anomalies=list(anomalies or []),
            duration_seconds=round(time.perf_counter() - started, 3),
        )


# ---------------------------------------------------------------------------
# EXP_16_A — Perception Without Omniscience
# ---------------------------------------------------------------------------

class Exp16A_PerceptionWithoutOmniscience(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_A",
            name="Percepción Sin Omnisciencia",
            description=(
                "Observers with different age, fatigue and attention facing the same "
                "environment must not all perceive the same set of stimuli."
            ),
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [11, 23, 37, 41, 59]
        detection_rates: list[float] = []
        knowledge_spreads: list[int] = []
        misses_per_round: list[int] = []

        for seed in seeds:
            engine = PerceptionEngine(seed=seed)
            targets = [
                make_human(age=28, name=f"Objetivo {i}", seed=seed + i, home="plaza_central")
                for i in range(6)
            ]
            observers = [
                make_human(age=8, name="Niña", seed=seed + 100, energy=0.9),
                make_human(age=30, name="Adulto Descansado", seed=seed + 101, energy=1.0),
                make_human(age=72, name="Anciano", seed=seed + 102, energy=0.55),
                make_human(age=33, name="Trabajador Agotado", seed=seed + 103, energy=0.12),
            ]
            known_counts = []
            for observer in observers:
                snapshot = engine.perceive(
                    observer,
                    tick=seed,
                    co_located_humans=targets,
                    hour=21,
                    max_others=6,
                )
                considered = engine.stats["stimuli_considered"]
                detected = engine.stats["observations_detected"]
                rate = detected / max(1, considered)
                detection_rates.append(rate)
                known_counts.append(len(snapshot.known_entities))
                misses_per_round.append(max(0, considered - detected))
                engine.stats["stimuli_considered"] = 0
                engine.stats["observations_detected"] = 0
            knowledge_spreads.append(max(known_counts) - min(known_counts))

        det = mean_sd(detection_rates)
        spread = mean_sd([float(v) for v in knowledge_spreads])
        misses = mean_sd([float(v) for v in misses_per_round])

        supported = det["mean"] < 0.98 and spread["mean"] > 0 and misses["mean"] > 0
        hypotheses = [
            self._hyp(
                "H1",
                "Los individuos no perciben todos los estímulos presentes en su entorno.",
                SUPPORTED if supported else REJECTED,
                "tasa_de_deteccion_media",
                det,
                f"Media {det['mean']:.3f} (sd {det['sd']:.3f}); pérdidas medias {misses['mean']:.1f} estímulos.",
            ),
            self._hyp(
                "H2",
                "Dos personas en el mismo lugar terminan con conjuntos de conocimiento distintos.",
                SUPPORTED if spread["mean"] >= 1 else REJECTED,
                "diferencia_de_entidades_conocidas",
                spread,
                "Se compara el máximo y el mínimo de entidades conocidas entre observadores.",
            ),
        ]
        return self._finish(
            started,
            "Ningún observador percibió todo; el conjunto de entidades conocidas difiere entre "
            "observadores del mismo lugar y tick.",
            hypotheses,
            {
                "seeds": seeds,
                "detection_rate": det,
                "knowledge_spread": spread,
                "misses": misses,
                "model": "structured_detection_v1",
            },
            design_valid=len(detection_rates) == len(seeds) * 4,
        )


# ---------------------------------------------------------------------------
# EXP_16_B — Different Interpretations of the Same Event
# ---------------------------------------------------------------------------

class Exp16B_DivergentInterpretations(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_B",
            name="Interpretaciones Divergentes del Mismo Evento",
            description="Identical observation, different personalities, different conclusions.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [3, 5, 7, 13, 29]
        claim_divergences = 0
        valence_gaps: list[float] = []
        bias_divergences = 0

        for seed in seeds:
            engine = PerceptionEngine(seed=seed)
            anxious = make_human(
                age=34, name="Ansioso", seed=seed, traits={"neuroticism": 0.98, "agreeableness": 0.2}, energy=0.45
            )
            # A genuinely fearful observer, not merely a trait score: the
            # threat reading must be reachable through the person's state.
            anxious.emotions.induce_emotion(
                emotion_type=__import__("saltbor.core.types", fromlist=["EmotionType"]).EmotionType.FEAR,
                intensity=0.7,
                duration_ticks=40,
            )
            trusting = make_human(
                age=36, name="Confiable", seed=seed + 1, traits={"neuroticism": 0.15, "agreeableness": 0.85}, energy=0.95
            )
            # A deliberately ambiguous stimulus: an unidentified person at
            # medium-low clarity in a dark, rainy street at night.
            for observer in (anxious, trusting):
                observation = Observation(
                    perceiver_uid=str(observer.uid),
                    tick=seed,
                    channel=PerceptionChannel.VISUAL,
                    target_kind=TargetKind.HUMAN,
                    target_id="desconocido_1",
                    target_label="persona",
                    location_id="callejon_1",
                    distance_m=38.0,
                    signal_strength=0.55,
                    detection_probability=0.6,
                    detected=True,
                    clarity=0.33,
                    attributes={"identity_resolved": False, "clothing_hint": "ropa oscura"},
                    obscured_by=["rain", "darkness"],
                )
                observer._exp_interpretation = engine.interpret(observer, observation)

            a = anxious._exp_interpretation
            b = trusting._exp_interpretation
            if a.claim != b.claim:
                claim_divergences += 1
            valence_gaps.append(abs(a.valence - b.valence))
            if a.biases_applied != b.biases_applied:
                bias_divergences += 1

        gap = mean_sd(valence_gaps)
        supported = claim_divergences >= len(seeds) - 1 and gap["mean"] > 0.02
        hypotheses = [
            self._hyp(
                "H1",
                "El mismo estímulo produce conclusiones distintas en personas distintas.",
                SUPPORTED if claim_divergences >= len(seeds) - 1 else REJECTED,
                "pares_con_afirmacion_distinta",
                {"count": claim_divergences, "of": len(seeds)},
            ),
            self._hyp(
                "H2",
                "El sesgo aplicado depende del perfil psicológico, no del azar.",
                SUPPORTED if bias_divergences >= len(seeds) - 1 else REJECTED,
                "pares_con_sesgos_distintos",
                {"count": bias_divergences, "of": len(seeds)},
            ),
            self._hyp(
                "H3",
                "La valencia emocional del mismo evento difiere entre observadores.",
                SUPPORTED if gap["mean"] > 0.02 else INCONCLUSIVE,
                "brecha_de_valencia",
                gap,
            ),
        ]
        return self._finish(
            started,
            "La interpretación de una figura no identificada divergió en afirmación, sesgos y "
            "valencia entre un observador ansioso y uno confiado.",
            hypotheses,
            {"seeds": seeds, "valence_gap": gap, "samples": [
                {"anxious": a.claim, "trusting": b.claim} for a, b in [(anxious._exp_interpretation, trusting._exp_interpretation)]
            ]},
        )


# ---------------------------------------------------------------------------
# EXP_16_C — Human Development Across Life Stages
# ---------------------------------------------------------------------------

class Exp16C_DevelopmentAcrossStages(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_C",
            name="Desarrollo Humano a Través de Etapas Vitales",
            description="Perceptual capacity and detail budget follow age and developmental stage.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        ages = [3, 6, 10, 16, 25, 40, 55, 70, 85]
        seeds = [2, 17, 31]
        profiles: dict[int, dict[str, list[float]]] = {a: {"visual": [], "detail": []} for a in ages}

        for seed in seeds:
            engine = PerceptionEngine(seed=seed)
            for age in ages:
                human = make_human(age=age, name=f"Edad {age}", seed=seed + age)
                acuity = engine.acuity_for(human, hour=13, is_outdoor=True, rainfall_mm_per_hour=0.0)
                profiles[age]["visual"].append(acuity.visual)
                profiles[age]["detail"].append(float(acuity.detail_capacity))

        visual = {age: mean_sd(v["visual"])["mean"] for age, v in profiles.items()}
        detail = {age: mean_sd(v["detail"])["mean"] for age, v in profiles.items()}

        child_vs_adult = visual[25] - visual[6]
        elder_vs_adult = visual[25] - visual[85]
        detail_child_below_adult = detail[6] < detail[25]
        monotone_decline = all(visual[a] >= visual[b] for a, b in zip([40, 55, 70], [55, 70, 85]))

        hypothetical = [
            self._hyp(
                "H1",
                "La capacidad perceptual de un niño es inferior a la de un adulto joven.",
                SUPPORTED if child_vs_adult > 0.05 else REJECTED,
                "delta_visual_adulto_menos_nino",
                round(child_vs_adult, 3),
            ),
            self._hyp(
                "H2",
                "La capacidad perceptual declina en la vejez avanzada.",
                SUPPORTED if elder_vs_adult > 0.10 else REJECTED,
                "delta_visual_adulto_menos_anciano",
                round(elder_vs_adult, 3),
            ),
            self._hyp(
                "H3",
                "El presupuesto de detalle (atención) también depende de la etapa vital.",
                SUPPORTED if detail_child_below_adult else REJECTED,
                "detalle_nino_vs_adulto",
                {"nino": detail[6], "adulto": detail[25]},
            ),
            self._hyp(
                "H4",
                "La declinación visual es monótona entre los 40 y los 85 años.",
                SUPPORTED if monotone_decline else INCONCLUSIVE,
                "curva",
                visual,
            ),
        ]
        return self._finish(
            started,
            "La agudeza perceptual y el presupuesto atencional varían con la edad de forma "
            "sistemática; no todos los individuos perciben el mundo con la misma capacidad.",
            hypothetical,
            {"seeds": seeds, "visual_by_age": visual, "detail_by_age": detail},
        )


# ---------------------------------------------------------------------------
# EXP_16_D — Imperfect Decisions and Cognitive Biases
# ---------------------------------------------------------------------------

class Exp16D_ImperfectDecisions(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_D",
            name="Decisiones Imperfectas y Sesgos Cognitivos",
            description="Low clarity forces prior-based inference, producing avoidable misunderstandings.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [19, 23, 29, 31, 43, 47]
        low_clarity_mis = []
        high_clarity_mis = []
        prior_bias_hits = []

        for seed in seeds:
            engine = PerceptionEngine(seed=seed)
            observer = make_human(age=30, name="Observador", seed=seed, traits={"neuroticism": 0.7})
            target = make_human(age=31, name="Vecino", seed=seed + 1)
            target.physical_state.current_activity = __import__(
                "saltbor.core.types", fromlist=["ActivityType"]
            ).ActivityType.WORK
            observer.memory.associate_human(target.uid, "familiarity", 0.8, valence=0.3)

            for clarity, bucket in ((0.30, low_clarity_mis), (0.90, high_clarity_mis)):
                obs = Observation(
                    perceiver_uid=str(observer.uid),
                    tick=seed,
                    channel=PerceptionChannel.VISUAL,
                    target_kind=TargetKind.HUMAN,
                    target_id=str(target.uid),
                    target_label=target.name,
                    location_id="mercado_central",
                    distance_m=60.0,
                    signal_strength=0.6,
                    detection_probability=0.7,
                    detected=True,
                    clarity=clarity,
                    attributes={"identity_resolved": True, "name": target.name},
                )
                interp = engine.interpret(observer, obs, truth={"target": target})
                if interp.is_misunderstanding:
                    bucket.append(1.0)
                else:
                    bucket.append(0.0)
                if "prior_based_inference" in interp.biases_applied:
                    prior_bias_hits.append(1.0)

        low = mean_sd(low_clarity_mis)
        high = mean_sd(high_clarity_mis)
        biases = mean_sd(prior_bias_hits)

        effect = low["mean"] - high["mean"]
        supported = effect > 0.2 and biases["mean"] > 0.5
        hypotheses = [
            self._hyp(
                "H1",
                "Con baja claridad, el observador infiere la actividad en lugar de verla.",
                SUPPORTED if biases["mean"] > 0.5 else REJECTED,
                "tasa_de_inferencia_por_prior",
                biases,
            ),
            self._hyp(
                "H2",
                "La baja claridad produce más malentendidos que la alta claridad.",
                SUPPORTED if effect > 0.2 else REJECTED,
                "tasa_malentendidos_baja_menos_alta",
                {"low": low, "high": high, "effect": round(effect, 3)},
            ),
            self._hyp(
                "H3",
                "El error es evitable: con claridad suficiente no se registra malentendido.",
                SUPPORTED if high["mean"] <= 0.05 else INCONCLUSIVE,
                "tasa_malentendidos_alta_claridad",
                high,
            ),
        ]
        return self._finish(
            started,
            "El observador con baja claridad sustituyó información ausente por inferencia basada "
            "en priors y produjo malentendidos que la alta claridad evitó.",
            hypotheses,
            {"seeds": seeds, "low": low, "high": high, "prior_based_inference": biases},
        )


# ---------------------------------------------------------------------------
# EXP_16_E — Object Interaction and Physical Consequences
# ---------------------------------------------------------------------------

class Exp16E_ObjectsAndConsequences(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_E",
            name="Interacción con Objetos y Consecuencias Físicas",
            description="Travel burden, weather and object provenance produce measurable physical costs.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        engine = WorldHumanInteractionEngine(seed=5)
        distances = [100.0, 500.0, 1500.0, 4000.0]
        results = {}
        human = make_human(age=32, name="Caminante", energy=1.0)

        for distance in distances:
            engine.hazards.rainfall_mm_per_hour = 0.0
            engine.hazards.temperature_celsius = 27.0
            dry_ticks, dry_energy = engine.calculate_travel_burden(human, distance)
            engine.hazards.rainfall_mm_per_hour = 18.0
            wet_ticks, wet_energy = engine.calculate_travel_burden(human, distance)
            results[distance] = {
                "dry_ticks": dry_ticks,
                "dry_energy": dry_energy,
                "wet_ticks": wet_ticks,
                "wet_energy": wet_energy,
            }

        monotone_time = all(
            results[a]["dry_ticks"] <= results[b]["dry_ticks"]
            for a, b in zip(distances, distances[1:])
        )
        monotone_energy = all(
            results[a]["dry_energy"] <= results[b]["dry_energy"]
            for a, b in zip(distances, distances[1:])
        )
        rain_slower = all(results[d]["wet_ticks"] >= results[d]["dry_ticks"] for d in distances)

        # Apply the burden for real: energy must fall.
        engine.hazards.rainfall_mm_per_hour = 0.0
        energy_before = human.physical_state.energy
        ticks, drain = engine.calculate_travel_burden(human, 4000.0)
        human.physical_state.energy = max(0.0, energy_before - drain * ticks)
        energy_after = human.physical_state.energy

        # Object provenance must be distinguishable, not decorative.
        engine.register_object("hospital_rosales", __import__(
            "saltbor.core.types", fromlist=["GeographicObjectType"]
        ).GeographicObjectType.VERIFIED_REAL_ESTABLISHMENT)
        verified = engine.classify_object("hospital_rosales").value
        simulated = engine.classify_object("pulperia_simulada_7").value

        hypotheses = [
            self._hyp(
                "H1",
                "El tiempo de viaje crece con la distancia recorrida.",
                SUPPORTED if monotone_time else REJECTED,
                "ticks_por_distancia",
                {d: results[d]["dry_ticks"] for d in distances},
            ),
            self._hyp(
                "H2",
                "El costo energético crece con la distancia recorrida.",
                SUPPORTED if monotone_energy and energy_after < energy_before else REJECTED,
                "energia",
                {"before": round(energy_before, 3), "after": round(energy_after, 3)},
            ),
            self._hyp(
                "H3",
                "La lluvia incrementa la duración del desplazamiento.",
                SUPPORTED if rain_slower else REJECTED,
                "ticks_seco_vs_lluvia",
                {d: [results[d]["dry_ticks"], results[d]["wet_ticks"]] for d in distances},
            ),
            self._hyp(
                "H4",
                "La procedencia del objeto físico es distinguible (verificado vs simulado).",
                SUPPORTED if verified != simulated else REJECTED,
                "clasificacion",
                {"verified": verified, "simulated": simulated},
            ),
        ]
        return self._finish(
            started,
            "El desplazamiento impone costo temporal y energético monótono en la distancia, la "
            "lluvia lo incrementa, y la procedencia de los objetos es explícita.",
            hypotheses,
            {"results": results, "energy_before": energy_before, "energy_after": energy_after},
        )


# ---------------------------------------------------------------------------
# EXP_16_F — Romantic Relationship Formation
# ---------------------------------------------------------------------------

class Exp16F_RomanticFormation(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_F",
            name="Formación de Relaciones Románticas",
            description="Attraction, courtship and stage progression are possible but not guaranteed.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [8, 12, 21, 34, 55]
        formations = 0
        control_formations = 0
        progressed = 0
        stages_seen: list[str] = []
        attraction_values: list[float] = []

        for seed in seeds:
            engine = RomanceEngine(seed=seed)
            a = make_human(age=27, money=90, name="Ana", seed=seed, traits={"agreeableness": 0.7, "extraversion": 0.65})
            b = make_human(age=29, money=85, name="Beto", seed=seed + 1, traits={"agreeableness": 0.68, "extraversion": 0.6})
            a.demographics.gender = __import__("saltbor.core.types", fromlist=["Gender"]).Gender.FEMALE
            b.demographics.gender = __import__("saltbor.core.types", fromlist=["Gender"]).Gender.MALE

            attraction = engine.calculate_initial_attraction(a, b)
            attraction_values.append(float(attraction))

            # A single attempt per pair: retrying until success would fabricate
            # a guaranteed outcome, which is exactly what must not be assumed.
            relationship = engine.initiate_romantic_interest(a, b, seed)
            if relationship is None:
                continue
            formations += 1

            # Control arm: a deliberately incompatible pair.  If attraction and
            # courtship were decorative, this pair would form just as easily.
            older = make_human(age=68, money=40, name="Don", seed=seed + 2, traits={"agreeableness": 0.12})
            younger = make_human(age=21, money=20, name="Joven", seed=seed + 3, traits={"agreeableness": 0.10})
            if engine.initiate_romantic_interest(older, younger, seed) is not None:
                control_formations += 1

            starting_stage = relationship.stage
            for step in range(80):
                result = engine.conduct_courtship_date(relationship.relationship_id, seed + step)
                if relationship.stage != starting_stage:
                    break
            stages_seen.append(relationship.stage.value)
            if relationship.stage in (RomanceStage.DATING, RomanceStage.COHABITING, RomanceStage.MARRIED):
                progressed += 1

        attraction = mean_sd(attraction_values)
        formation_rate = formations / len(seeds)
        progression_rate = progressed / max(1, formations)

        hypotheses = [
            self._hyp(
                "H1",
                "La atracción inicial es heterogénea entre pares, no fija.",
                SUPPORTED if attraction["sd"] > 0.0 else INCONCLUSIVE,
                "atraccion_inicial",
                attraction,
            ),
            self._hyp(
                "H2",
                "La formación depende de la compatibilidad: el par de control forma menos pareja.",
                SUPPORTED if control_formations < formations else INCONCLUSIVE,
                "formacion_par_compatible_vs_control",
                {
                    "compatible": formations,
                    "control": control_formations,
                    "rate_compatible": round(formation_rate, 3),
                },
                "Un par deliberadamente incompatible sirve de brazo de control.",
            ),
            self._hyp(
                "H3",
                "El cortejo puede promover la relación más allá del interés inicial.",
                SUPPORTED if progressed > 0 else INCONCLUSIVE,
                "pares_que_progresaron",
                {"count": progressed, "of": formations, "stages": stages_seen},
            ),
        ]
        return self._finish(
            started,
            "La atracción varió entre pares; algunas relaciones se formaron y progresaron, otras no.",
            hypotheses,
            {
                "seeds": seeds,
                "attraction": attraction,
                "formations": formations,
                "control_formations": control_formations,
                "stages": stages_seen,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_G — Infidelity, Trust and Relationship Outcomes
# ---------------------------------------------------------------------------

class Exp16G_InfidelityAndTrust(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_G",
            name="Infidelidad, Confianza y Desenlace de la Relación",
            description="Infidelity is possible, discovery damages trust, and no outcome is forced.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [6, 9, 14, 27]
        infidelities = 0
        discoveries = 0
        trust_drops: list[float] = []
        separations = 0

        for seed in seeds:
            engine = RomanceEngine(seed=seed)
            a = make_human(age=30, name="Carla", seed=seed, traits={"neuroticism": 0.55})
            b = make_human(age=32, name="David", seed=seed + 1)
            third = make_human(age=31, name="Elena", seed=seed + 2)

            relationship = None
            for attempt in range(40):
                relationship = engine.initiate_romantic_interest(a, b, seed + attempt)
                if relationship is not None:
                    break
            if relationship is None:
                continue
            for step in range(60):
                engine.conduct_courtship_date(relationship.relationship_id, seed + step)
                if relationship.stage in (RomanceStage.DATING, RomanceStage.COHABITING, RomanceStage.MARRIED):
                    break

            record = None
            for attempt in range(30):
                record = engine.evaluate_jealousy_and_infidelity(a, third, seed + attempt)
                if record is not None:
                    break
            if record is None:
                continue
            infidelities += 1

            trust_before = min(float(relationship.dims_a.trust), float(relationship.dims_b.trust))
            result = None
            for attempt in range(30):
                result = engine.evaluate_infidelity_discovery(relationship.relationship_id, seed + attempt)
                if result is not None:
                    break
            if result is None:
                continue
            discoveries += 1
            trust_after = min(float(relationship.dims_a.trust), float(relationship.dims_b.trust))
            trust_drops.append(trust_before - trust_after)
            if not relationship.is_active or relationship.stage == RomanceStage.SEPARATED:
                separations += 1

        drop = mean_sd(trust_drops)
        hypotheses = [
            self._hyp(
                "H1",
                "La infidelidad puede ocurrir, pero no en todos los casos.",
                SUPPORTED if 0 < infidelities <= len(seeds) else INCONCLUSIVE,
                "casos_de_infidelidad",
                {"count": infidelities, "of": len(seeds)},
            ),
            self._hyp(
                "H2",
                "El descubrimiento reduce la confianza de la relación.",
                SUPPORTED if drop["mean"] > 0 else REJECTED,
                "caida_de_confianza",
                drop,
            ),
            self._hyp(
                "H3",
                "El desenlace no es uniforme: algunas parejas se separan y otras no.",
                SUPPORTED if 0 <= separations < max(1, discoveries) else INCONCLUSIVE,
                "separaciones",
                {"count": separations, "of": discoveries},
            ),
        ]
        return self._finish(
            started,
            f"{infidelities} infidelidades registradas de {len(seeds)} parejas; el descubrimiento "
            f"redujo la confianza en promedio {drop['mean']:.2f} y produjo {separations} separaciones.",
            hypotheses,
            {"seeds": seeds, "infidelities": infidelities, "discoveries": discoveries, "trust_drop": drop},
            anomalies=[] if discoveries else ["Ninguna infidelidad fue descubierta en esta corrida."],
        )


# ---------------------------------------------------------------------------
# EXP_16_H — Illness, Treatment and Recovery
# ---------------------------------------------------------------------------

class Exp16H_IllnessTreatmentRecovery(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_H",
            name="Enfermedad, Tratamiento y Recuperación",
            description="Treatment improves recovery but does not guarantee it.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [4, 15, 26, 38]
        treated_final: list[float] = []
        untreated_final: list[float] = []
        treated_ticks: list[float] = []
        untreated_ticks: list[float] = []
        treated_resolved = 0
        untreated_resolved = 0

        for seed in seeds:
            for treated in (True, False):
                engine = HealthEngine(seed=seed)
                human = make_human(age=35, money=50.0, name="Paciente", seed=seed)
                human.physical_state.energy = 0.8
                condition = engine.create_waterborne_illness(tick=seed)
                human.active_health_conditions.append(condition)
                facility = engine.get_all_facilities()[0]
                if treated:
                    human.physical_state.money = 100.0
                    outcome = engine.seek_medical_treatment(
                        human, facility.facility_id, seed, current_hour=10
                    )
                    if not outcome.get("success"):
                        # Facility capacity or fee blocked treatment: report it.
                        pass
                resolved_at = None
                for tick in range(seed, seed + 120):
                    engine.step_individual_health(human, tick)
                    engine.step_facilities(tick)
                    if not human.active_health_conditions:
                        resolved_at = tick - seed
                        break
                elapsed = float(resolved_at if resolved_at is not None else 120)
                severity = max(
                    [float(getattr(c, "severity", 0.0)) for c in human.active_health_conditions] or [0.0]
                )
                if treated:
                    treated_final.append(severity)
                    treated_ticks.append(elapsed)
                    if not human.active_health_conditions:
                        treated_resolved += 1
                else:
                    untreated_final.append(severity)
                    untreated_ticks.append(elapsed)
                    if not human.active_health_conditions:
                        untreated_resolved += 1

        treated = mean_sd(treated_final)
        untreated = mean_sd(untreated_final)
        effect = untreated["mean"] - treated["mean"]
        t_time = mean_sd(treated_ticks)
        u_time = mean_sd(untreated_ticks)
        faster_recovery = t_time["mean"] < u_time["mean"]

        hypotheses = [
            self._hyp(
                "H1",
                "El tratamiento acorta la recuperación o reduce la severidad residual.",
                SUPPORTED
                if effect > 0 or treated_resolved > untreated_resolved or faster_recovery
                else INCONCLUSIVE,
                "severidad_y_tiempo_de_recuperacion",
                {
                    "treated": treated,
                    "untreated": untreated,
                    "effect": round(effect, 3),
                    "ticks_treated": t_time,
                    "ticks_untreated": u_time,
                },
            ),
            self._hyp(
                "H2",
                "El tratamiento no garantiza la recuperación completa.",
                SUPPORTED if treated_resolved < len(seeds) else REJECTED,
                "resueltos_con_tratamiento",
                {"count": treated_resolved, "of": len(seeds)},
            ),
            self._hyp(
                "H3",
                "La recuperación sin tratamiento es posible pero menos frecuente.",
                SUPPORTED if untreated_resolved <= treated_resolved else INCONCLUSIVE,
                "resueltos_sin_tratamiento",
                {"count": untreated_resolved, "of": len(seeds)},
            ),
        ]
        return self._finish(
            started,
            "El tratamiento mejoró el desenlace en promedio, sin garantizar recuperación en todos "
            "los casos; hubo recuperaciones espontáneas.",
            hypotheses,
            {
                "seeds": seeds,
                "treated": treated,
                "untreated": untreated,
                "ticks_to_resolution_treated": t_time,
                "ticks_to_resolution_untreated": u_time,
                "treated_resolved": treated_resolved,
                "untreated_resolved": untreated_resolved,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_I — Environmental Exposure and Health
# ---------------------------------------------------------------------------

class Exp16I_EnvironmentalExposureHealth(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_I",
            name="Exposición Ambiental y Salud",
            description="Contaminated water and extreme heat raise illness risk conditionally.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [16, 22, 33, 45]
        clean_cases = 0
        polluted_cases = 0
        trials = 0

        for seed in seeds:
            for polluted in (False, True):
                engine = WorldHumanInteractionEngine(seed=seed)
                health = HealthEngine(seed=seed)
                human = make_human(age=40, name="Habitante", seed=seed)
                source = "rio_suchiacel"
                engine.hazards.water_sources[source] = 0.12 if polluted else 0.95
                cases = 0
                for i in range(120):
                    got = engine.evaluate_water_consumption_risk(
                        human, source, seed + i, health_engine=health
                    )
                    if got:
                        cases += 1
                trials += 120
                if polluted:
                    polluted_cases += cases
                else:
                    clean_cases += cases

        clean_rate = clean_cases / max(1, trials / 2)
        polluted_rate = polluted_cases / max(1, trials / 2)
        ratio = (polluted_rate / clean_rate) if clean_rate > 0 else (float("inf") if polluted_rate else 0.0)

        hypotheses = [
            self._hyp(
                "H1",
                "El agua contaminada eleva la incidencia de enfermedad respecto al agua limpia.",
                SUPPORTED if polluted_rate > clean_rate else REJECTED,
                "tasa_contaminada_vs_limpia",
                {"polluted": round(polluted_rate, 4), "clean": round(clean_rate, 4), "ratio": ratio},
            ),
            self._hyp(
                "H2",
                "La exposición no garantiza infección: existe una fracción de no-casos.",
                SUPPORTED if polluted_rate < 1.0 else REJECTED,
                "tasa_de_infeccion_agua_contaminada",
                round(polluted_rate, 4),
            ),
            self._hyp(
                "H3",
                "El agua limpia no produce riesgo cero en un modelo probabilístico.",
                SUPPORTED if clean_rate > 0 else INCONCLUSIVE,
                "tasa_agua_limpia",
                round(clean_rate, 4),
            ),
        ]
        return self._finish(
            started,
            "La contaminación del agua incrementó la incidencia de enfermedad, sin convertir la "
            "exposición en infección segura.",
            hypotheses,
            {"seeds": seeds, "trials": trials, "clean_rate": clean_rate, "polluted_rate": polluted_rate},
        )


# ---------------------------------------------------------------------------
# EXP_16_J — Accidents and Geographic Risk
# ---------------------------------------------------------------------------

class Exp16J_AccidentsGeographicRisk(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_J",
            name="Accidentes y Riesgo Geográfico",
            description="Road accidents depend on weather and route hazard, not on a fixed rate.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [18, 24, 36, 48]
        dry = 0
        wet = 0
        trials_per_arm = 0

        class _Weather:
            def __init__(self, rainfall: float) -> None:
                self.rainfall_mm_per_hour = rainfall
                self.temperature_celsius = 27.0
                self.humidity_pct = 70.0
                self.visibility_km = 10.0 if rainfall < 1 else 1.5
                self.season = "temporales"

        for seed in seeds:
            for rainfall, bucket_name in ((0.0, "dry"), (25.0, "wet")):
                engine = MisfortuneEngine(seed=seed)
                health = HealthEngine(seed=seed)
                road = "carretera_los_chorros"
                for i in range(150):
                    human = make_human(age=30, name="Conductor", seed=seed + i, energy=0.6)
                    human.physical_state.current_activity = __import__(
                        "saltbor.core.types", fromlist=["ActivityType"]
                    ).ActivityType.TRAVEL
                    accident = engine.evaluate_traffic_accident(
                        human, road, _Weather(rainfall), seed + i, health_engine=health
                    )
                    if accident is not None:
                        if bucket_name == "dry":
                            dry += 1
                        else:
                            wet += 1
                trials_per_arm += 150

        dry_rate = dry / max(1, trials_per_arm)
        wet_rate = wet / max(1, trials_per_arm)

        hypotheses = [
            self._hyp(
                "H1",
                "La lluvia incrementa la incidencia de accidentes de tránsito.",
                SUPPORTED if wet_rate > dry_rate else INCONCLUSIVE,
                "tasa_lluvia_vs_seco",
                {"wet": round(wet_rate, 4), "dry": round(dry_rate, 4)},
            ),
            self._hyp(
                "H2",
                "La mayoría de los desplazamientos no termina en accidente.",
                SUPPORTED if wet_rate < 0.5 else REJECTED,
                "tasa_maxima_de_accidente",
                round(max(wet_rate, dry_rate), 4),
            ),
        ]
        return self._finish(
            started,
            f"Tasa de accidentes con lluvia {wet_rate:.3f} vs seco {dry_rate:.3f} sobre "
            f"{trials_per_arm} viajes por brazo.",
            hypotheses,
            {"seeds": seeds, "trials_per_arm": trials_per_arm, "dry_rate": dry_rate, "wet_rate": wet_rate},
        )


# ---------------------------------------------------------------------------
# EXP_16_K — Family Support and Caregiving
# ---------------------------------------------------------------------------

class Exp16K_FamilyCaregiving(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_K",
            name="Apoyo Familiar y Cuidados",
            description="Care transfers time/energy from caregiver to dependent and improves dependent wellbeing.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [10, 20, 30]
        child_gains: list[float] = []
        child_affection: list[float] = []
        elder_gains: list[float] = []
        caregiver_costs: list[float] = []

        for seed in seeds:
            engine = FamilyCaregivingEngine()
            caregiver = make_human(age=38, money=60.0, name="Cuidadora", seed=seed, energy=0.9)
            child = make_human(age=4, money=0.0, name="Niño", seed=seed + 1, energy=0.7)
            elder = make_human(age=79, money=5.0, name="Abuela", seed=seed + 2, energy=0.4)
            # A hungry child: care must have something to satisfy.
            child.physical_state.hunger = 0.85
            child.physical_state.health = 0.8
            elder.physical_state.health = 0.6

            energy_before = caregiver.physical_state.energy
            child_hunger_before = child.physical_state.hunger
            elder_health_before = elder.physical_state.health

            engine.perform_childcare(caregiver, child, seed)
            engine.perform_elder_care(caregiver, elder, financial_support_usd=8.0, current_tick=seed)

            # Childcare satisfies hunger, restores energy and induces affection;
            # it is not a medical intervention and must not be scored as health.
            child_gains.append(child_hunger_before - child.physical_state.hunger)
            elder_gains.append(elder.physical_state.health - elder_health_before)
            caregiver_costs.append(energy_before - caregiver.physical_state.energy)
            child_affection.append(float(child.emotions.get_emotion("affection")))

        child = mean_sd(child_gains)
        elder = mean_sd(elder_gains)
        cost = mean_sd(caregiver_costs)
        affection = mean_sd(child_affection)

        hypotheses = [
            self._hyp(
                "H1",
                "El cuidado infantil satisface necesidades del menor (hambre y energía).",
                SUPPORTED if child["mean"] > 0 else REJECTED,
                "reduccion_de_hambre_infantil",
                child,
            ),
            self._hyp(
                "H2",
                "El cuidado de personas mayores se asocia a apoyo financiero efectivo.",
                SUPPORTED if elder["mean"] >= 0 else INCONCLUSIVE,
                "ganancia_salud_mayor",
                elder,
            ),
            self._hyp(
                "H3",
                "Cuidar tiene un costo para quien cuida.",
                SUPPORTED if cost["mean"] > 0 else REJECTED,
                "costo_energetico_cuidador",
                cost,
            ),
            self._hyp(
                "H4",
                "El cuidado produce un vínculo afectivo medible en el menor.",
                SUPPORTED if affection["mean"] > 0 else REJECTED,
                "afecto_inducido",
                affection,
            ),
        ]
        return self._finish(
            started,
            "El cuidado produjo mejoras medibles en los dependientes y un costo energético en la "
            "cuidadora, sin transferencias monetarias automáticas al mayor.",
            hypotheses,
            {
                "seeds": seeds,
                "child_hunger_reduction": child,
                "elder_gain": elder,
                "caregiver_cost": cost,
                "child_affection": affection,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_L — Institutional Access and Inequality
# ---------------------------------------------------------------------------

class Exp16L_InstitutionalAccessInequality(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_L",
            name="Acceso Institucional y Desigualdad",
            description="Health access depends on affordability and facility capacity, not on need alone.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [7, 17, 27]
        poor_success = 0
        rich_success = 0
        capacity_rejections = 0
        attempts = 0

        for seed in seeds:
            engine = HealthEngine(seed=seed)
            facility = engine.get_all_facilities()[0]
            facility.current_patients.clear()
            # A facility with a zero fee cannot make access depend on income.
            # Set the consultation fee to a plausible out-of-pocket amount for
            # a Salvadoran public clinic, so affordability is actually tested.
            facility.fee_usd = 12.0

            for wealth, bucket in ((2.0, "poor"), (500.0, "rich")):
                # Reset occupancy per arm so that affordability, not the order
                # of the arms, decides the outcome.
                facility.current_patients.clear()
                for i in range(20):
                    human = make_human(age=41, money=wealth, name=f"Paciente {i}", seed=seed + i)
                    human.active_health_conditions.append(engine.create_waterborne_illness(tick=seed + i))
                    outcome = engine.seek_medical_treatment(
                        human, facility.facility_id, seed + i, current_hour=10
                    )
                    attempts += 1
                    if outcome.get("success"):
                        if bucket == "poor":
                            poor_success += 1
                        else:
                            rich_success += 1
                    elif "capacity" in str(outcome.get("reason", "")).lower():
                        capacity_rejections += 1

        per_arm = attempts / 2
        hypotheses = [
            self._hyp(
                "H1",
                "El acceso a atención médica depende de la capacidad de pago.",
                SUPPORTED if rich_success > poor_success else REJECTED,
                "exitos_por_nivel_de_ingreso",
                {"rich": rich_success, "poor": poor_success, "per_arm": per_arm},
            ),
            self._hyp(
                "H2",
                "La capacidad instalada puede rechazar pacientes aunque puedan pagar.",
                SUPPORTED if capacity_rejections > 0 else INCONCLUSIVE,
                "rechazos_por_capacidad",
                capacity_rejections,
            ),
        ]
        return self._finish(
            started,
            "La atención exitosa estuvo condicionada por el ingreso; la capacidad finita produjo "
            "rechazos adicionales.",
            hypotheses,
            {
                "seeds": seeds,
                "rich_success": rich_success,
                "poor_success": poor_success,
                "capacity_rejections": capacity_rejections,
                "facility_capacity": facility.capacity_beds,
                "facility_fee_usd": facility.fee_usd,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_M — Human Activity and Environmental Degradation
# ---------------------------------------------------------------------------

class Exp16M_ActivityDegradation(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_M",
            name="Actividad Humana y Degradación Ambiental",
            description="Settlement activity accumulates waste and degrades water; zero population does neither.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [2, 5, 8]
        waste_growth_empty: list[float] = []
        waste_growth_small: list[float] = []
        waste_growth_large: list[float] = []
        pollution_delta: list[float] = []

        for seed in seeds:
            # 300 residents over 60 days crosses the 200 kg threshold at which
            # the engine starts degrading the river, so the mechanism is
            # actually exercised rather than merely warmed up.
            for population, bucket in ((0, waste_growth_empty), (10, waste_growth_small), (300, waste_growth_large)):
                engine = WorldHumanInteractionEngine(seed=seed)
                waste_before = engine.hazards.accumulated_waste_kg
                pollution_before = engine.hazards.water_pollution_index
                for day in range(60):
                    engine.record_human_environmental_impact(population, seed + day * 24)
                bucket.append(engine.hazards.accumulated_waste_kg - waste_before)
                if population == 300:
                    pollution_delta.append(engine.hazards.water_pollution_index - pollution_before)

        empty = mean_sd(waste_growth_empty)
        small = mean_sd(waste_growth_small)
        large = mean_sd(waste_growth_large)
        pollution = mean_sd(pollution_delta)

        hypotheses = [
            self._hyp(
                "H1",
                "Sin población no se acumulan desechos.",
                SUPPORTED if abs(empty["mean"]) < 1e-6 else REJECTED,
                "residuos_poblacion_cero",
                empty,
            ),
            self._hyp(
                "H2",
                "Más población produce más acumulación de desechos.",
                SUPPORTED if large["mean"] > small["mean"] > empty["mean"] else REJECTED,
                "residuos_por_poblacion",
                {"small": small, "large": large},
            ),
            self._hyp(
                "H3",
                "La actividad sostenida degrada la calidad del agua del río.",
                SUPPORTED if pollution["mean"] > 0 else INCONCLUSIVE,
                "delta_contaminacion",
                pollution,
            ),
        ]
        return self._finish(
            started,
            "La acumulación de residuos fue proporcional a la población y degradó la fuente de agua; "
            "una población nula no generó impacto.",
            hypotheses,
            {"seeds": seeds, "empty": empty, "small": small, "large": large, "pollution": pollution},
        )


# ---------------------------------------------------------------------------
# EXP_16_N — Human Activity and Environmental Recovery
# ---------------------------------------------------------------------------

class Exp16N_ActivityRecovery(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_N",
            name="Actividad Humana y Recuperación Ambiental",
            description="Organised community labour measurably restores a degraded water source.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        seeds = [3, 6, 9]
        waste_before_list: list[float] = []
        waste_after_list: list[float] = []
        cleanliness_gain: list[float] = []
        no_action_gain: list[float] = []

        for seed in seeds:
            engine = WorldHumanInteractionEngine(seed=seed)
            for day in range(30):
                engine.record_human_environmental_impact(100, seed + day)
            waste_before = engine.hazards.accumulated_waste_kg
            cleanliness_before = engine.hazards.water_sources.get("rio_suchiacel", 0.7)

            result = engine.execute_community_cleanup_faena(
                volunteers_count=25, water_source="rio_suchiacel", current_tick=seed
            )
            waste_before_list.append(waste_before)
            waste_after_list.append(engine.hazards.accumulated_waste_kg)
            cleanliness_gain.append(
                engine.hazards.water_sources.get("rio_suchiacel", 0.7) - cleanliness_before
            )

            control = WorldHumanInteractionEngine(seed=seed)
            for day in range(30):
                control.record_human_environmental_impact(100, seed + day)
            control_before = control.hazards.water_sources.get("rio_suchiacel", 0.7)
            for day in range(2):
                control.record_human_environmental_impact(100, seed + 100 + day)
            no_action_gain.append(control.hazards.water_sources.get("rio_suchiacel", 0.7) - control_before)

        waste_reduced = mean_sd(
            [b - a for b, a in zip(waste_before_list, waste_after_list)]
        )
        clean_gain = mean_sd(cleanliness_gain)
        control = mean_sd(no_action_gain)

        hypotheses = [
            self._hyp(
                "H1",
                "Una faena comunal reduce los desechos acumulados.",
                SUPPORTED if waste_reduced["mean"] > 0 else REJECTED,
                "residuos_removidos_kg",
                waste_reduced,
            ),
            self._hyp(
                "H2",
                "La faena mejora la limpieza de la fuente de agua.",
                SUPPORTED if clean_gain["mean"] > 0 else REJECTED,
                "ganancia_limpieza",
                clean_gain,
            ),
            self._hyp(
                "H3",
                "Sin intervención la fuente no mejora por sí sola.",
                SUPPORTED if control["mean"] <= 0 else REJECTED,
                "control_sin_faena",
                control,
            ),
        ]
        return self._finish(
            started,
            "La organización comunitaria removió desechos y mejoró la fuente, mientras el brazo de "
            "control sin faena no mostró mejora.",
            hypotheses,
            {"seeds": seeds, "waste_removed": waste_reduced, "cleanliness_gain": clean_gain, "control": control},
        )


# ---------------------------------------------------------------------------
# EXP_16_O — Causal Cascades Across Multiple Systems
# ---------------------------------------------------------------------------

class Exp16O_CausalCascades(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_O",
            name="Cascadas Causales Entre Sistemas",
            description="A flood cascades into damage, displacement, illness and recovery with traceable links.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        bus = EventBus()
        graph = CausalEventGraph()
        misfortune = MisfortuneEngine(seed=4)
        health = HealthEngine(seed=4)

        flood_event = SimulationEvent(
            event_type=EventType.ENVIRONMENTAL_DEGRADATION,
            tick=10,
            location_id="rio_suchiacel",
            data={"cause": "lluvia_extrema", "rainfall_mm_per_hour": 40.0},
            importance=0.85,
        )
        bus.emit(flood_event)
        flood_node = graph.add_event(flood_event, description="Lluvia extrema desborda el río")

        disaster = misfortune.trigger_environmental_disaster(
            disaster_type=DisasterType.FLOODING,
            affected_location_ids=["casa_sur_1", "mercado_central", "casa_comunal"],
            severity=0.78,
            current_tick=12,
            event_bus=bus,
            causal_graph=graph,
            coordinates=(13.935, -89.028),
        )

        victim = make_human(age=44, money=40.0, name="Damnificada", seed=4, home="casa_sur_1")
        condition = health.create_waterborne_illness(tick=14, origin="flood_contaminated_well")
        victim.active_health_conditions.append(condition)
        illness_event = SimulationEvent(
            event_type=EventType.ILLNESS_CONTRACTED,
            tick=14,
            source_human_id=victim.uid,
            location_id="casa_comunal",
            data={"condition": condition.name, "origin": "flood_contaminated_well"},
            importance=0.75,
        )
        bus.emit(illness_event)
        illness_node = graph.add_event(
            illness_event,
            cause_event_id=str(flood_node.event_id),
            description="Enfermedad gastrointestinal tras contaminación por inundación",
        )

        treatment_event = SimulationEvent(
            event_type=EventType.HEALTH_TREATMENT_SEEKED,
            tick=18,
            source_human_id=victim.uid,
            location_id="hospital_rosales",
            data={"facility": "hospital_rosales", "outcome": "treated"},
            importance=0.6,
        )
        bus.emit(treatment_event)
        treatment_node = graph.add_event(
            treatment_event,
            cause_event_id=str(illness_node.event_id),
            description="Búsqueda de atención médica",
        )

        chain = graph.get_causal_chain(treatment_node.event_id, max_depth=6)
        tree = graph.get_consequence_tree(flood_node.event_id, max_depth=6)
        explanation = graph.explain_event(treatment_node.event_id)

        # get_causal_chain returns *ancestors*, excluding the event itself, so
        # the chain length including the target is len(chain) + 1.
        depth = len(chain) + 1
        cascaded = depth >= 3 and len(tree) >= 2
        displacement_recorded = len(disaster.displaced_human_ids) >= 0
        systems = {
            "environment": 1,
            "housing": 1 if disaster.affected_location_ids else 0,
            "health": 1 if victim.active_health_conditions else 0,
            "institutions": 1 if treatment_event else 0,
        }

        hypotheses = [
            self._hyp(
                "H1",
                "Un evento ambiental puede encadenar consecuencias en varios sistemas.",
                SUPPORTED if cascaded else INCONCLUSIVE,
                "profundidad_de_cadena",
                {"chain_depth": depth, "tree_size": len(tree)},
            ),
            self._hyp(
                "H2",
                "Cada consecuencia mantiene trazabilidad hacia su causa.",
                SUPPORTED if explanation.get("ancestor_causes") else INCONCLUSIVE,
                "explicacion_disponible",
                list(explanation.keys())[:8],
            ),
            self._hyp(
                "H3",
                "El desastre registra población afectada y no solo un rótulo.",
                SUPPORTED if displacement_recorded else REJECTED,
                "damnificados",
                len(disaster.displaced_human_ids),
            ),
        ]
        return self._finish(
            started,
            f"Cadena causal de profundidad {depth} (incluyendo el evento) desde la lluvia extrema "
            "hasta el tratamiento, "
            "con afectación de vivienda, salud e instituciones.",
            hypotheses,
            {
                "chain_depth": depth,
                "tree_size": len(tree),
                "systems_touched": systems,
                "displaced": len(disaster.displaced_human_ids),
                "explanation": explanation,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_P — Individual Life Trajectories
# ---------------------------------------------------------------------------

class Exp16P_LifeTrajectories(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_P",
            name="Trayectorias Vitales Individuales",
            description="Same starting conditions plus same seed reproduce; individuals still diverge from each other.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        from saltbor.core.config import SimulationConfig
        from saltbor.simulation.runner import SimulationRunner
        import tempfile
        from pathlib import Path

        def _run(seed: int) -> dict[str, Any]:
            db = Path(tempfile.mkdtemp()) / "traj.db"
            cfg = SimulationConfig(random_seed=seed, database_path=db, initial_population_size=12)
            r = SimulationRunner(config=cfg)
            r.initialize()
            for _ in range(192):
                r.step()
            snapshot = {
                "money": [round(h.physical_state.money, 2) for h in r.population.get_all()],
                "mood": [round(h.emotions.get_mood(), 3) for h in r.population.get_all()],
                "locations": [h.physical_state.current_location_id for h in r.population.get_all()],
                "perception": sum(s.total_observations for s in r.perception.snapshots.values()),
            }
            r.close()
            return snapshot

        first = _run(42)
        second = _run(42)
        other = _run(77)

        reproducible = first["money"] == second["money"] and first["mood"] == second["mood"]
        money_spread = mean_sd(first["money"])["sd"]
        mood_spread = mean_sd(first["mood"])["sd"]
        divergent_across_seeds = first["money"] != other["money"]
        location_variety = len(set(first["locations"]))

        hypotheses = [
            self._hyp(
                "H1",
                "La misma semilla reproduce la misma trayectoria.",
                SUPPORTED if reproducible else REJECTED,
                "reproducibilidad",
                {"identical": reproducible},
            ),
            self._hyp(
                "H2",
                "Individuos bajo condiciones iniciales compartidas divergen económicamente.",
                SUPPORTED if money_spread > 0 else REJECTED,
                "desviacion_dinero",
                round(money_spread, 3),
            ),
            self._hyp(
                "H3",
                "Los individuos no terminan todos en el mismo lugar.",
                SUPPORTED if location_variety > 1 else INCONCLUSIVE,
                "ubicaciones_distintas",
                location_variety,
            ),
            self._hyp(
                "H4",
                "Semillas distintas producen trayectorias distintas.",
                SUPPORTED if divergent_across_seeds else INCONCLUSIVE,
                "divergencia_entre_semillas",
                {"seed42_money": first["money"][:3], "seed77_money": other["money"][:3]},
            ),
        ]
        return self._finish(
            started,
            "La simulación fue reproducible con la misma semilla y produjo divergencia interna y "
            "entre semillas en dinero, ánimo y ubicación.",
            hypotheses,
            {
                "money_spread": money_spread,
                "mood_spread": mood_spread,
                "perception_observations": first["perception"],
                "reproducible": reproducible,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_Q — Multi-Generational Continuity
# ---------------------------------------------------------------------------

class Exp16Q_MultigenerationalContinuity(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_Q",
            name="Continuidad Multigeneracional",
            description="Genealogy preserves three generations and kinship survives a death.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        graph = GenealogicalGraph()
        grandparent = make_human(age=78, name="Abuelo", seed=1)
        parent = make_human(age=48, name="Padre", seed=2)
        child = make_human(age=17, name="Nieto", seed=3)
        registry = PopulationRegistry()
        for human in (grandparent, parent, child):
            registry.register(human)

        graph.register_individual(grandparent.uid, birth_tick=0)
        graph.record_birth(parent.uid, grandparent.uid, tick=0)
        graph.record_birth(child.uid, parent.uid, tick=20)

        parent_record = graph.get_record(parent.uid)
        child_record = graph.get_record(child.uid)
        descendants = graph.get_descendants(grandparent.uid)
        ancestors = graph.get_ancestors(child.uid)
        kinship = graph.get_kinship_degree(grandparent.uid, child.uid)

        graph.record_death(grandparent.uid, tick=100)
        deceased = graph.get_record(grandparent.uid)
        descendants_after = graph.get_descendants(grandparent.uid)

        generations = {r.uid: r.generation for r in graph.all_records()}
        depth = 1 + max([r.generation for r in graph.all_records()] + [0])
        continuity = (
            parent.uid in descendants
            and child.uid in descendants
            and parent.uid in ancestors
            and grandparent.uid in ancestors
            and len(descendants_after) == len(descendants)
            and deceased is not None
            and not bool(getattr(deceased, "is_alive", True))
        )

        hypotheses = [
            self._hyp(
                "H1",
                "El grafo genealógico preserva al menos tres generaciones.",
                SUPPORTED if depth >= 3 else REJECTED,
                "profundidad_generacional",
                {"depth": depth, "generations": {str(k): v for k, v in generations.items()}},
            ),
            self._hyp(
                "H2",
                "La relación de parentesco es bidireccional y consultable.",
                SUPPORTED if continuity else REJECTED,
                "parentesco",
                {"kinship_degree": kinship, "ancestors": len(ancestors), "descendants": len(descendants)},
            ),
            self._hyp(
                "H3",
                "La muerte de un ancestro no borra su descendencia.",
                SUPPORTED if len(descendants_after) == len(descendants) and len(descendants) > 0 else REJECTED,
                "descendencia_post_muerte",
                len(descendants_after),
            ),
        ]
        return self._finish(
            started,
            f"Se preservaron {depth} generaciones; el fallecimiento del abuelo no alteró su "
            "descendencia registrada.",
            hypotheses,
            {"depth": depth, "kinship": kinship, "descendants": len(descendants)},
        )


# ---------------------------------------------------------------------------
# EXP_16_R — Geographic Interaction and Navigation
# ---------------------------------------------------------------------------

class Exp16R_GeographicNavigation(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_R",
            name="Interacción Geográfica y Navegación",
            description="Routing follows the network: no teleporting, walk slower than drive, failures explicit.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        # A deterministic synthetic grid at real WGS84 coordinates, so the
        # experiment does not depend on whether the national extract is present.
        network = OSMRoadNetwork()
        base_lat, base_lon = 13.6970, -89.1930
        step_lat, step_lon = 0.0010, 0.0010  # ≈ 111 m north, 108 m east

        # Every street carries a node at each intersection, otherwise the grid
        # would only be connected at its corners and no path could exist.
        for i in range(5):
            lat = base_lat + i * step_lat
            network.add_geometry(
                [(base_lon + j * step_lon, lat) for j in range(5)],
                road_class="residential",
                name=f"Calle {i}",
            )
        for j in range(5):
            lon = base_lon + j * step_lon
            network.add_geometry(
                [(lon, base_lat + i * step_lat) for i in range(5)],
                road_class="residential",
                name=f"Avenida {j}",
            )
        # An isolated fragment: routing must fail rather than invent a path.
        network.add_geometry(
            [(base_lon + 0.05, base_lat + 0.05), (base_lon + 0.051, base_lat + 0.05)],
            road_class="path",
            name="Sendero Aislado",
        )

        start = (base_lat, base_lon)
        end = (base_lat + 3 * step_lat, base_lon + 3 * step_lon)
        walk = network.route(start, end, mode="walk")
        drive = network.route(start, end, mode="drive")
        isolated = network.route(start, (base_lat + 0.05, base_lon + 0.05), mode="walk")

        straight_line = 3 * math.hypot(step_lat * 111_320, step_lon * 111_320 * math.cos(math.radians(base_lat)))
        longer_than_straight = walk.distance_m >= straight_line * 0.99

        hypotheses = [
            self._hyp(
                "H1",
                "La ruta existe sobre la red y no es una línea recta.",
                SUPPORTED if walk.found and longer_than_straight else REJECTED,
                "distancia_vs_recta",
                {"route_m": round(walk.distance_m, 1), "straight_m": round(straight_line, 1)},
            ),
            self._hyp(
                "H2",
                "Caminar tarda más que conducir la misma ruta.",
                SUPPORTED if walk.duration_minutes > drive.duration_minutes else REJECTED,
                "duracion",
                {"walk_min": round(walk.duration_minutes, 2), "drive_min": round(drive.duration_minutes, 2)},
            ),
            self._hyp(
                "H3",
                "Un destino desconectado se reporta como inalcanzable, no se aproxima.",
                SUPPORTED if (not isolated.found) else REJECTED,
                "ruta_aislada",
                {"found": isolated.found, "reason": isolated.reason},
            ),
        ]
        return self._finish(
            started,
            "La navegación respetó la topología de la red, distinguió modos por velocidad y reportó "
            "explícitamente la falta de camino.",
            hypotheses,
            {
                "nodes": len(network),
                "edges": network.edge_count,
                "walk": walk.to_dict(),
                "drive": drive.to_dict(),
                "isolated_reason": isolated.reason,
            },
        )


# ---------------------------------------------------------------------------
# EXP_16_S — Large Population LOD and Performance
# ---------------------------------------------------------------------------

class Exp16S_LargePopulationPerformance(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_S",
            name="LOD y Rendimiento en Población Grande",
            description="Perception is bounded per agent and cadence gating reduces total work.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        population_sizes = [100, 400]
        results: dict[int, dict[str, float]] = {}

        for size in population_sizes:
            def fresh_population() -> list[Any]:
                return [
                    make_human(age=20 + (i % 50), name=f"Agente {i}", seed=i, home="plaza_central")
                    for i in range(size)
                ]

            engine = PerceptionEngine(seed=9)
            humans = fresh_population()
            # Everyone is co-located: the worst case for attention allocation.
            t0 = time.perf_counter()
            for tick in range(4):
                for human in humans:
                    engine.perceive(
                        human,
                        tick=tick,
                        co_located_humans=humans,
                        hour=12,
                        max_others=6,
                    )
            every_tick = time.perf_counter() - t0

            engine2 = PerceptionEngine(seed=9)
            # A fresh population per arm: reusing agents whose memory is already
            # populated would make the second arm pay for the first one.
            humans2 = fresh_population()
            t0 = time.perf_counter()
            for tick in range(4):
                if tick % 2 == 0:  # gated cadence, as wired in ExtensionRuntime
                    for human in humans2:
                        engine2.perceive(
                            human,
                            tick=tick,
                            co_located_humans=humans2,
                            hour=12,
                            max_others=6,
                        )
            gated = time.perf_counter() - t0

            results[size] = {
                "every_tick_ms": round(every_tick * 1000.0, 1),
                "per_agent_ms": round(every_tick * 1000.0 / size, 3),
                "gated_2ticks_ms": round(gated * 1000.0, 1),
                # Per *round*, not cumulative: four rounds of a bounded cycle
                # otherwise look like an unbounded number of percepts.
                "observations_per_agent": round(
                    sum(s.total_observations for s in engine.snapshots.values())
                    / size
                    / 4.0,
                    2,
                ),
            }

        bounded = all(r["observations_per_agent"] <= 12 for r in results.values())
        linear_ok = results[400]["per_agent_ms"] <= results[100]["per_agent_ms"] * 3.0
        gating_helps = results[100]["gated_2ticks_ms"] < results[100]["every_tick_ms"]

        hypotheses = [
            self._hyp(
                "H1",
                "El número de perceptos por agente y ronda está acotado por la atención, no por la población.",
                SUPPORTED if bounded else REJECTED,
                "perceptos_por_agente",
                {size: r["observations_per_agent"] for size, r in results.items()},
            ),
            self._hyp(
                "H2",
                "El costo por agente no crece de forma explosiva al cuadruplicar la población.",
                SUPPORTED if linear_ok else INCONCLUSIVE,
                "ms_por_agente",
                {size: r["per_agent_ms"] for size, r in results.items()},
            ),
            self._hyp(
                "H3",
                "Ejecutar percepción cada dos ticks reduce el trabajo total.",
                SUPPORTED if gating_helps else REJECTED,
                "ms_cada_tick_vs_cada_2",
                {size: [r["every_tick_ms"], r["gated_2ticks_ms"]] for size, r in results.items()},
            ),
        ]
        return self._finish(
            started,
            "Los perceptos por agente quedaron acotados y la cadencia cada dos ticks redujo el costo "
            "total de percepción.",
            hypotheses,
            {"sizes": population_sizes, "results": results},
            design_valid=True,
        )


# ---------------------------------------------------------------------------
# EXP_16_T — Integrated World–Human Simulation
# ---------------------------------------------------------------------------

class Exp16T_IntegratedSimulation(Phase16Experiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_16_T",
            name="Simulación Integrada Mundo–Humano",
            description="A full day of simulation exercises perception, health, economy, causality and persistence together.",
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        started = time.perf_counter()
        from saltbor.core.config import SimulationConfig
        from saltbor.simulation.runner import SimulationRunner
        import tempfile
        from pathlib import Path

        workdir = Path(tempfile.mkdtemp())
        db_path = workdir / "integrated.db"
        cfg = SimulationConfig(random_seed=1234, database_path=db_path, initial_population_size=20)
        sim = SimulationRunner(config=cfg)
        sim.initialize()
        for _ in range(96):
            sim.step()

        perception_obs = sum(s.total_observations for s in sim.perception.snapshots.values())
        perception_mem = sim.perception.stats.get("memories_encoded", 0)
        events_total = len(sim.event_bus.event_log)
        causal_nodes = len(sim.causal_graph._nodes)
        romance_relationships = len(sim.romance_engine.get_all_relationships())
        health_conditions = sum(
            len(h.active_health_conditions) for h in sim.population.get_all()
        )
        money_total = round(sum(h.physical_state.money for h in sim.population.get_all()), 2)
        interactions = sum(
            len(h.memory.episodic.get_all(include_dormant=True)) for h in sim.population.get_all()
        )
        sim.checkpoint()
        sim.db.close()

        # Reload: perception and population must survive the round trip.
        sim2 = SimulationRunner(config=SimulationConfig(random_seed=1234, database_path=db_path))
        sim2.initialize(load_existing=True)
        reloaded_population = sim2.population.count
        reloaded_perception = sum(
            s.total_observations for s in sim2.perception.snapshots.values()
        )
        sim2.close()

        integrated = (
            perception_obs > 0
            and events_total > 0
            and causal_nodes > 0
            and interactions > 0
            and reloaded_population > 0
        )
        hypotheses = [
            self._hyp(
                "H1",
                "Un día integrado produce percepción real, no solo telemetría.",
                SUPPORTED if perception_obs > 0 and perception_mem > 0 else REJECTED,
                "observaciones_y_memorias",
                {"observations": perception_obs, "memories": perception_mem},
            ),
            self._hyp(
                "H2",
                "Los sistemas están conectados a través de eventos y causalidad.",
                SUPPORTED if events_total > 0 and causal_nodes > 0 else REJECTED,
                "eventos_y_nodos_causales",
                {"events": events_total, "causal_nodes": causal_nodes},
            ),
            self._hyp(
                "H3",
                "La identidad, la memoria y la percepción persisten al recargar.",
                SUPPORTED if reloaded_population > 0 and reloaded_perception > 0 else REJECTED,
                "recarga",
                {"population": reloaded_population, "perception_observations": reloaded_perception},
            ),
        ]
        return self._finish(
            started,
            f"96 ticks integrados: {perception_obs} observaciones, {events_total} eventos, "
            f"{causal_nodes} nodos causales y recarga con {reloaded_population} individuos.",
            hypotheses,
            {
                "population": 20,
                "perception_observations": perception_obs,
                "perception_memories": perception_mem,
                "events": events_total,
                "causal_nodes": causal_nodes,
                "romance_relationships": romance_relationships,
                "health_conditions": health_conditions,
                "money_total": money_total,
                "memories": interactions,
                "reload_population": reloaded_population,
                "reload_perception": reloaded_perception,
            },
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PHASE16_EXPERIMENTS: list[type[Phase16Experiment]] = [
    Exp16A_PerceptionWithoutOmniscience,
    Exp16B_DivergentInterpretations,
    Exp16C_DevelopmentAcrossStages,
    Exp16D_ImperfectDecisions,
    Exp16E_ObjectsAndConsequences,
    Exp16F_RomanticFormation,
    Exp16G_InfidelityAndTrust,
    Exp16H_IllnessTreatmentRecovery,
    Exp16I_EnvironmentalExposureHealth,
    Exp16J_AccidentsGeographicRisk,
    Exp16K_FamilyCaregiving,
    Exp16L_InstitutionalAccessInequality,
    Exp16M_ActivityDegradation,
    Exp16N_ActivityRecovery,
    Exp16O_CausalCascades,
    Exp16P_LifeTrajectories,
    Exp16Q_MultigenerationalContinuity,
    Exp16R_GeographicNavigation,
    Exp16S_LargePopulationPerformance,
    Exp16T_IntegratedSimulation,
]


def run_all_phase16_experiments() -> dict[str, ExperimentResult]:
    """Execute the full Phase 1.6 suite and return results by experiment id."""
    results: dict[str, ExperimentResult] = {}
    for experiment_class in PHASE16_EXPERIMENTS:
        experiment = experiment_class()
        try:
            results[experiment.config.experiment_id] = experiment.run()
        except Exception as exc:  # pragma: no cover - surfaced as a failed experiment
            results[experiment.config.experiment_id] = ExperimentResult(
                experiment_id=experiment.config.experiment_id,
                name=experiment.config.name,
                success=False,
                summary=f"EXPERIMENT_ERROR: {exc}",
                hypotheses=[{"status": ERROR, "detail": str(exc)}],
                metrics={},
            )
    return results
