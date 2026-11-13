"""Human perception engine (Phase 1.6 §5).

Connects the world to individual cognition without granting omniscience.

The engine answers one question per individual per tick: *given where this
person is, what they can see and hear, how tired, how old, how attentive and
how predisposed they are, what did they actually notice — and what did they
make of it?*

Design notes
------------
* **Structured, not visual.**  There is no rendering and no image model.  Each
  potential stimulus is described structurally (a person, a hazard, a
  location feature) with an objective ``signal_strength``; observation is a
  detection model over that structure.
* **Channels.**  Visual and auditory accessibility are computed separately and
  are affected differently by walls, night and rain, so "I heard shouting but
  could not see who it was" is representable.
* **Clarity gates detail.**  Only attributes supported by the achieved clarity
  are stored.  A blurry figure at 80 m does not yield a name.
* **Interpretation is separate from observation.**  The same observation can
  produce a benign or a threatening reading depending on personality, mood,
  prior beliefs and the relationship with the target.
* **Determinism.**  Per-individual, per-tick random streams are derived from a
  stable hash of (seed, uid, tick), so results are reproducible and do not
  depend on iteration order or the shared master RNG.
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Any, Iterable, Optional

import numpy as np

from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.cognition.memory.working import WorkingMemoryItem
from saltbor.cognition.perception.models import (
    AcuityProfile,
    Interpretation,
    Observation,
    PerceptionChannel,
    PerceptionSnapshot,
    TargetKind,
)
from saltbor.core.types import ActivityType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Physical constants of the perceptual model.  These are explicit modelling
# assumptions, not measured human factors; see
# SALTBOR_PHASE_1_6_ASSUMPTIONS.md.
# ---------------------------------------------------------------------------
VISUAL_SCALE_INDOOR_DAY = 38.0     # metres, e-folding distance
VISUAL_SCALE_OUTDOOR_DAY = 130.0
VISUAL_SCALE_OUTDOOR_NIGHT = 28.0
AUDITORY_SCALE_INDOOR = 30.0
AUDITORY_SCALE_OUTDOOR = 110.0
RAIN_VISUAL_PENALTY = 0.55
RAIN_AUDITORY_PENALTY = 0.45
WALL_BLOCK = 0.02
MICRO_POSITION_RADIUS_M = 22.0

_ACTIVITY_LABELS_ES: dict[str, str] = {
    "sleep": "durmiendo",
    "eat": "comiendo",
    "work": "trabajando",
    "study": "estudiando",
    "shop": "comprando",
    "cook": "cocinando",
    "socialize": "conversando",
    "exercise": "haciendo ejercicio",
    "relax": "descansando",
    "travel": "desplazándose",
    "rest": "descansando",
    "community_meeting": "en reunión comunitaria",
    "commerce_buy": "comprando",
    "commerce_sell": "vendiendo",
    "search_employment": "buscando trabajo",
    "seek_medical_care": "buscando atención médica",
    "community_cleanup": "en faena de limpieza",
    "play_sport": "jugando fútbol",
    "visit_park": "paseando",
}

_HAZARD_LABELS_ES: dict[str, str] = {
    "flood": "crecida o inundación",
    "landslide": "deslizamiento de tierra",
    "heat": "calor extremo",
    "pollution": "contaminación del agua",
    "rain": "lluvia intensa",
}

_NIGHT_HOURS = range(19, 24)
_EARLY_NIGHT = range(0, 6)


class PerceptionEngine:
    """Per-individual structured perception with explicit epistemic limits."""

    def __init__(self, seed: Optional[int] = 42, max_observations_per_tick: int = 12) -> None:
        self.seed = seed
        self.max_observations_per_tick = max_observations_per_tick
        self.snapshots: dict[str, PerceptionSnapshot] = {}
        self.stats: dict[str, int] = {
            "ticks_processed": 0,
            "stimuli_considered": 0,
            "observations_detected": 0,
            "observations_missed": 0,
            "attended": 0,
            "suppressed_by_attention": 0,
            "misunderstandings": 0,
            "memories_encoded": 0,
            "reports_received": 0,
        }

    # ------------------------------------------------------------------
    # Deterministic randomness
    # ------------------------------------------------------------------
    @staticmethod
    def _stable_id(entity: Any) -> str:
        """Reproducible identity key used to derive per-entity randomness.

        Human UUIDs are generated with ``uuid4`` at creation time, so seeding
        randomness from them would make the same seed produce different
        perceptions on every process run.  The identity *serial* is assigned
        deterministically by the population order, so it is used whenever it is
        available; anything else (locations, hazards, raw ids) falls back to its
        string form.
        """
        serial = getattr(getattr(entity, "identity", None), "serial", None)
        if serial is not None:
            return f"serial:{serial}"
        uid = getattr(entity, "uid", None)
        if uid is not None:
            return f"uid:{uid}"
        return str(entity)

    def _rng(self, *parts: Any) -> np.random.Generator:
        token = "|".join(str(p) for p in parts).encode("utf-8")
        digest = hashlib.blake2b(token, digest_size=8).digest()
        entropy = int.from_bytes(digest, "big") ^ (self.seed or 0)
        return np.random.default_rng(entropy & 0xFFFFFFFFFFFFFFFF)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def get_snapshot(self, human_uid: str) -> PerceptionSnapshot:
        snap = self.snapshots.get(str(human_uid))
        if snap is None:
            snap = PerceptionSnapshot(human_uid=str(human_uid))
            self.snapshots[str(human_uid)] = snap
        return snap

    def has_perceived(self, human_uid: str, entity_id: str) -> bool:
        return self.get_snapshot(str(human_uid)).has_perceived(str(entity_id))

    def summary_for(self, human_uid: str) -> dict[str, Any]:
        return self.get_snapshot(str(human_uid)).summary()

    # ------------------------------------------------------------------
    # Acuity
    # ------------------------------------------------------------------
    @staticmethod
    def _trait(human: Any, name: str) -> float:
        try:
            return float(human.personality.get_trait(name))
        except Exception:
            return 0.5

    @staticmethod
    def _emotion(human: Any, name: str) -> float:
        try:
            return float(human.emotions.get_emotion(name))
        except Exception:
            return 0.0

    def acuity_for(
        self,
        human: Any,
        *,
        hour: int,
        is_outdoor: bool,
        rainfall_mm_per_hour: float = 0.0,
    ) -> AcuityProfile:
        """Compute this individual's effective perceptual capacity right now."""
        age = float(getattr(human.demographics, "age", 30))
        energy = float(getattr(human.physical_state, "energy", 1.0))
        stress = max(
            self._emotion(human, "stress"),
            self._emotion(human, "anxiety"),
            self._emotion(human, "fear"),
        )

        # Age: visual and auditory acuity peak in early adulthood.
        if age < 4:
            age_factor = 0.45
        elif age < 8:
            age_factor = 0.70
        elif age < 14:
            age_factor = 0.88
        elif age <= 40:
            age_factor = 1.0
        elif age <= 55:
            age_factor = 0.94
        elif age <= 68:
            age_factor = 0.84
        elif age <= 78:
            age_factor = 0.72
        else:
            age_factor = 0.60

        # Fatigue degrades sustained attention and contrast sensitivity.
        fatigue_factor = 0.62 + 0.38 * max(0.0, min(1.0, energy))

        # Active illness reduces capacity (fever, pain, medication).
        health_factor = 1.0
        for condition in getattr(human, "active_health_conditions", []) or []:
            severity = float(getattr(condition, "severity", 0.2) or 0.2)
            health_factor *= 1.0 - min(0.40, 0.35 * severity)
        health_factor = max(0.35, health_factor)

        # Stress narrows the attentional field.
        attention = max(0.25, 1.0 - 0.45 * stress)

        # Waking vs sleeping: a sleeping person perceives almost nothing.
        activity = getattr(human.physical_state, "current_activity", None)
        if activity in (ActivityType.SLEEP,):
            attention *= 0.12

        # Environmental modifiers.
        is_night = hour in _NIGHT_HOURS or hour in _EARLY_NIGHT
        env_factor = 1.0
        if is_night and is_outdoor:
            env_factor = 0.42
        elif is_night:
            env_factor = 0.70  # indoor lighting
        if rainfall_mm_per_hour > 0.5:
            env_factor *= 1.0 - min(0.45, rainfall_mm_per_hour / 40.0)

        visual = max(0.05, age_factor * env_factor)
        auditory = max(0.10, age_factor * (1.0 - 0.25 * stress))
        olfactory = max(0.10, 0.85 * health_factor)

        # Detail capacity: how many stimuli can be held in attention at once.
        base_capacity = 7
        if age < 7:
            base_capacity = 4
        elif age < 12:
            base_capacity = 5
        elif age > 75:
            base_capacity = 5
        if stress > 0.5:
            base_capacity -= 1
        if self._trait(human, "openness") > 0.65:
            base_capacity += 1
        detail_capacity = max(3, min(9, base_capacity))

        return AcuityProfile(
            visual=visual,
            auditory=auditory,
            olfactory=olfactory,
            attention=attention,
            fatigue_factor=fatigue_factor,
            age_factor=age_factor,
            health_factor=health_factor,
            environmental_factor=env_factor,
            detail_capacity=detail_capacity,
            provenance={
                "hour": hour,
                "is_outdoor": is_outdoor,
                "rainfall_mm_per_hour": round(rainfall_mm_per_hour, 2),
                "is_night": is_night,
                "model": "structured_detection_v1",
            },
        )

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    @staticmethod
    def _distance_between(
        human: Any,
        target_position: tuple[float, float],
        locations: Any,
    ) -> tuple[float, bool]:
        """Return (distance in metres, same_location) from a human to a point."""
        loc_id = getattr(human.physical_state, "current_location_id", None)
        if not loc_id or locations is None:
            return (0.0, True)
        loc = locations.get_optional(loc_id) if hasattr(locations, "get_optional") else None
        if loc is None:
            return (0.0, True)
        dx = float(loc.position[0]) - float(target_position[0])
        dy = float(loc.position[1]) - float(target_position[1])
        return (math.hypot(dx, dy), dx == 0.0 and dy == 0.0)

    def _micro_distance(self, perceiver_uid: Any, target_uid: Any) -> float:
        """Deterministic approximate separation inside one location.

        SALTBOR tracks location occupancy, not centimetre positions.  When two
        people share a location their separation is drawn deterministically
        from ``[1, MICRO_POSITION_RADIUS_M]``; the value is marked
        ``approximate_micro_position`` in observation provenance.
        """
        rng = self._rng("micro", perceiver_uid, target_uid)
        return float(1.0 + rng.random() * (MICRO_POSITION_RADIUS_M - 1.0))

    # ------------------------------------------------------------------
    # Stimulus construction
    # ------------------------------------------------------------------
    def _stimulus(self, kind: TargetKind, target_id: str, label: str, signal: float) -> dict[str, Any]:
        return {
            "target_kind": kind,
            "target_id": str(target_id),
            "target_label": label,
            "signal": max(0.02, min(1.0, signal)),
        }

    def _attention_weight(self, human: Any, stimulus: dict[str, Any], clarity: float) -> float:
        """Personal relevance of a detected stimulus (attention allocation)."""
        kind = stimulus["target_kind"]
        neuroticism = self._trait(human, "neuroticism")
        extraversion = self._trait(human, "extraversion")
        openness = self._trait(human, "openness")
        conscientiousness = self._trait(human, "conscientiousness")
        fear = self._emotion(human, "fear")
        loneliness = self._emotion(human, "loneliness")
        curiosity = self._emotion(human, "curiosity")

        weight = 0.5
        if kind == TargetKind.HUMAN:
            weight += 0.35 * extraversion + 0.25 * loneliness
            # Familiar people are recognised and attended to faster.
            if stimulus.get("familiar"):
                weight += 0.20
        elif kind == TargetKind.HAZARD:
            weight += 0.55 * neuroticism + 0.45 * fear
        elif kind == TargetKind.ENVIRONMENT:
            weight += 0.30 * openness + 0.25 * curiosity
        elif kind == TargetKind.LOCATION:
            weight += 0.15 * openness
        elif kind == TargetKind.EVENT:
            weight += 0.20 * neuroticism + 0.15 * conscientiousness
        elif kind == TargetKind.ACTIVITY:
            weight += 0.15 * conscientiousness

        weight *= 0.55 + 0.45 * clarity
        return max(0.02, min(1.5, weight))

    # ------------------------------------------------------------------
    # Detail resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _coarse_age_band(age: float) -> str:
        if age < 5:
            return "bebé"
        if age < 13:
            return "niño/a"
        if age < 18:
            return "adolescente"
        if age < 30:
            return "joven"
        if age < 50:
            return "adulto/a"
        if age < 70:
            return "persona mayor"
        return "persona anciana"

    def _resolve_human_attributes(
        self,
        human: Any,
        target: Any,
        clarity: float,
        distances_known: bool,
    ) -> dict[str, Any]:
        """Return only the attributes this level of clarity actually supports."""
        attrs: dict[str, Any] = {}
        if target is None:
            return {"identity_resolved": False, "description": "una figura"}
        target_uid = str(getattr(target, "uid", ""))

        # A person already known to the observer resolves identity at much
        # lower clarity than a stranger.
        familiarity = 0.0
        try:
            familiarity = float(
                human.memory.get_human_association(target_uid).get("intensity", 0.0)
            )
        except Exception:
            familiarity = 0.0
        known = familiarity > 0.0

        # A stranger is never "identity resolved": the observer may register a
        # face, build and clothing, but not a name.  Only people already known
        # to the observer resolve to an identity.
        if not known and clarity >= 0.55:
            rng = self._rng("build", self._stable_id(human), self._stable_id(target))
            attrs["build"] = ["contextura delgada", "contextura media", "contextura robusta"][
                int(rng.integers(0, 3))
            ]
            attrs["description"] = "una persona no identificada"

        identity_threshold = 0.30 if known else 1.01
        if clarity < 0.22:
            attrs["description"] = "una figura"
            attrs["identity_resolved"] = False
            return attrs

        attrs["description"] = "una persona"
        attrs["approximate_age_band"] = self._coarse_age_band(
            float(getattr(target.demographics, "age", 30))
        )

        if clarity < identity_threshold:
            attrs["identity_resolved"] = False
            # A witness can still retain coarse cues, deterministically drawn.
            rng = self._rng("cues", self._stable_id(human), self._stable_id(target), clarity)
            attrs["clothing_hint"] = ["ropa clara", "ropa oscura", "ropa de color"][
                int(rng.integers(0, 3))
            ]
            attrs["carrying"] = bool(rng.random() < 0.35)
            return attrs

        attrs["identity_resolved"] = True
        attrs["name"] = getattr(target, "name", "")
        attrs["occupation"] = getattr(getattr(target, "demographics", None), "occupation", None)

        activity = getattr(target.physical_state, "current_activity", None)
        if activity is not None:
            attrs["activity_observed"] = getattr(activity, "value", str(activity))
            if clarity >= 0.55:
                attrs["activity_label"] = _ACTIVITY_LABELS_ES.get(
                    getattr(activity, "value", str(activity)), "activo/a"
                )
        if clarity >= 0.72:
            attrs["emotional_expression"] = (
                "tenso/a"
                if self._emotion(target, "stress") > 0.5
                else "tranquilo/a"
            )
            attrs["posture"] = "de pie" if activity not in (ActivityType.REST, ActivityType.SLEEP) else "descansando"
        if clarity >= 0.85:
            attrs["carrying"] = bool(getattr(target.physical_state, "carrying_weight_kg", 0.0))
        attrs["distance_known"] = distances_known
        return attrs

    # ------------------------------------------------------------------
    # Core observation
    # ------------------------------------------------------------------
    def observe_stimulus(
        self,
        human: Any,
        stimulus: dict[str, Any],
        *,
        tick: int,
        acuity: AcuityProfile,
        distance_m: float,
        same_location: bool,
        is_outdoor: bool,
        rain: float,
        location_id: Optional[str],
        coordinates: Optional[tuple[float, float]] = None,
        channel: PerceptionChannel = PerceptionChannel.VISUAL,
        ground_truth: Optional[dict[str, Any]] = None,
    ) -> Observation:
        """Apply the detection model to one stimulus for one observer."""
        rng = self._rng(
            "detect",
            self._stable_id(human),
            stimulus.get("detect_key", stimulus["target_id"]),
            tick,
            channel.value,
        )

        if channel == PerceptionChannel.VISUAL:
            if is_outdoor:
                scale = VISUAL_SCALE_OUTDOOR_DAY
                if acuity.provenance.get("is_night"):
                    scale = VISUAL_SCALE_OUTDOOR_NIGHT
            else:
                scale = VISUAL_SCALE_INDOOR_DAY
            if rain > 0.5:
                scale *= RAIN_VISUAL_PENALTY
            blocked = (not same_location) and (not is_outdoor) and distance_m > 12.0
        else:
            scale = AUDITORY_SCALE_INDOOR if not is_outdoor else AUDITORY_SCALE_OUTDOOR
            if rain > 0.5:
                scale *= RAIN_AUDITORY_PENALTY
            blocked = False

        attenuation = math.exp(-max(0.0, distance_m) / max(6.0, scale))
        if blocked or (not same_location and is_outdoor and distance_m > 6.0 * scale):
            wall_factor = WALL_BLOCK
        else:
            wall_factor = 1.0

        acuity_channel = acuity.channel(channel)
        probability = acuity_channel * stimulus["signal"] * attenuation * (
            0.45 + 0.55 * acuity.attention
        ) * wall_factor
        probability = max(0.0, min(1.0, probability))

        detected = bool(rng.random() < probability)
        # Clarity: how much detail resolved, conditional on detection.
        noise = float(rng.normal(0.0, 0.08))
        clarity = 0.0
        if detected:
            clarity = max(
                0.05,
                min(
                    1.0,
                    0.25
                    + 0.55 * probability
                    + 0.20 * acuity.visual
                    - 0.10 * max(0.0, rain) / 20.0
                    + noise,
                ),
            )
        if detected and stimulus["target_kind"] == TargetKind.HUMAN:
            target_obj = (ground_truth or {}).get("target")
            attrs = self._resolve_human_attributes(
                human, target_obj, clarity, same_location
            )
        elif detected:
            attrs = dict(ground_truth.get("attributes", {}) if ground_truth else {})
        else:
            attrs = {}

        obscured: list[str] = []
        if blocked:
            obscured.append("walls")
        if rain > 0.5:
            obscured.append("rain")
        if acuity.provenance.get("is_night") and is_outdoor:
            obscured.append("darkness")
        if getattr(human.physical_state, "current_activity", None) == ActivityType.SLEEP:
            obscured.append("sleeping")

        return Observation(
            perceiver_uid=str(human.uid),
            tick=tick,
            channel=channel,
            target_kind=stimulus["target_kind"],
            target_id=stimulus["target_id"],
            target_label=stimulus["target_label"],
            location_id=location_id,
            coordinates=coordinates,
            distance_m=distance_m,
            signal_strength=stimulus["signal"],
            detection_probability=probability,
            detected=detected,
            clarity=clarity,
            attributes=attrs,
            obscured_by=obscured,
            provenance={
                "model": "structured_detection_v1",
                "same_location": same_location,
                "micro_position": "approximate_micro_position" if same_location else "location_centroid",
                "channel_scale_m": round(scale, 1),
                "familiar": bool(stimulus.get("familiar")),
            },
        )

    # ------------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------------
    def interpret(
        self,
        human: Any,
        observation: Observation,
        *,
        truth: Optional[dict[str, Any]] = None,
        social_engine: Any = None,
    ) -> Interpretation:
        """Turn an observation into a belief, with explicit bias provenance."""
        rng = self._rng(
            "interpret",
            self._stable_id(human),
            observation.target_id,
            observation.tick,
            observation.channel.value,
        )
        neuroticism = self._trait(human, "neuroticism")
        agreeableness = self._trait(human, "agreeableness")
        openness = self._trait(human, "openness")
        fear = self._emotion(human, "fear")
        anger = self._emotion(human, "anger")
        sadness = self._emotion(human, "sadness")
        mood = float(human.emotions.get_mood()) if hasattr(human.emotions, "get_mood") else 0.0

        biases: list[str] = []
        alternatives: list[str] = []
        attribution = "ambiguous"
        valence = 0.0
        claim = ""
        confidence = max(0.05, min(0.95, 0.25 + 0.6 * observation.clarity))
        is_misunderstanding = False

        if observation.target_kind == TargetKind.HUMAN:
            target = (truth or {}).get("target")
            name = observation.attributes.get("name")
            activity = observation.attributes.get("activity_observed")
            truth_activity = None
            if target is not None:
                truth_activity = getattr(
                    getattr(target, "physical_state", None), "current_activity", None
                )
                truth_activity = getattr(truth_activity, "value", truth_activity)

            trust = 0.5
            if social_engine is not None and target is not None:
                try:
                    rel = social_engine.get_relationship(human.uid, target.uid)
                    if rel is not None:
                        trust = float(rel.trust)
                except Exception:
                    pass
            try:
                assoc = human.memory.get_human_association(
                    getattr(target, "uid", observation.target_id)
                )
                valence = float(assoc.get("valence", 0.0))
            except Exception:
                valence = 0.0

            if observation.attributes.get("identity_resolved") and name:
                if truth_activity:
                    claim = f"{name} está {_ACTIVITY_LABELS_ES.get(truth_activity, 'aquí')}."
                else:
                    claim = f"Vi a {name} cerca."
                if clarity_high(observation):
                    confidence = max(confidence, 0.70)
            else:
                # An unidentified person: the reading is constructed, not seen.
                seen_before = bool(observation.attributes.get("previously_seen"))
                if seen_before and agreeableness > 0.45:
                    claim = "Volví a ver a la misma persona que antes por aquí."
                    attribution = "external"
                elif neuroticism + fear > 0.95:
                    claim = "Alguien desconocido merodea por aquí; podría estar vigilando las casas."
                    biases.append("negativity_bias")
                    attribution = "internal"
                    valence = min(valence, -0.25)
                    alternatives.append("Quizá solo es un vecino que pasa.")
                elif agreeableness > 0.62:
                    claim = "Hay alguien por aquí, probablemente un vecino o alguien de paso."
                    biases.append("charitable_attribution")
                    attribution = "external"
                else:
                    claim = "Había una persona cerca, no alcancé a ver quién era."
                    attribution = "ambiguous"
                confidence = min(confidence, 0.45)
                alternatives.append("Podría tratarse de otra persona por completo.")

            # Activity inference under low clarity can simply be wrong.
            if truth_activity and observation.clarity < 0.62:
                guess_pool = ["trabajando", "conversando", "descansando", "comprando"]
                if activity and activity in guess_pool:
                    guess_pool.remove(activity)
                guessed = guess_pool[int(rng.integers(0, len(guess_pool)))]
                if not observation.attributes.get("activity_observed"):
                    biases.append("prior_based_inference")
                    if guessed != truth_activity:
                        is_misunderstanding = True
                        alternatives.append(
                            f"Parecía {guessed}, pero pudo haber estado "
                            f"{_ACTIVITY_LABELS_ES.get(truth_activity, truth_activity)}."
                        )
                        claim = (
                            f"{claim} Parecía {guessed}."
                            if claim
                            else f"Alguien parecía {guessed}."
                        )

            if trust < 0.35:
                biases.append("confirmation_bias")
                alternatives.append(f"Con {name or 'esa persona'}, cualquier cosa parece sospechosa.")

        elif observation.target_kind == TargetKind.HAZARD:
            hazard = observation.target_label or "un peligro"
            severity = float((truth or {}).get("severity", 0.5))
            if neuroticism + fear > 0.9:
                claim = f"El {hazard} es grave; hay que avisar a la familia y resguardarse."
                biases.append("threat_amplification")
                confidence = min(0.95, confidence + 0.20)
                valence = -0.7 * severity
            elif agreeableness > 0.6:
                claim = f"Se nota {hazard}; conviene ayudar a los vecinos a prepararse."
                biases.append("communal_framing")
                valence = -0.4 * severity
            else:
                claim = f"Hay {hazard} en la zona."
                valence = -0.3 * severity
            attribution = "external"
            alternatives.append("Puede que la situación no sea tan seria como parece.")

        elif observation.target_kind in (TargetKind.ENVIRONMENT, TargetKind.LOCATION):
            label = observation.target_label or "el lugar"
            if openness > 0.6:
                claim = f"Me fijé en {label}."
                biases.append("novelty_seeking")
            else:
                claim = f"Estaba en {label}."
            if observation.clarity < 0.4:
                alternatives.append("No estoy seguro de haber visto bien el lugar.")

        elif observation.target_kind == TargetKind.EVENT:
            summary = (truth or {}).get("summary") or observation.target_label
            claim = f"Ocurrió algo: {summary}." if summary else "Ocurrió algo cerca."
            if neuroticism > 0.6:
                biases.append("threat_monitoring")
                valence = -0.2
            alternatives.append("Tal vez no era lo que parecía.")
        else:
            claim = f"Percibí {observation.target_label}."

        # Mood colours confidence: a low mood makes people less certain of good news,
        # but more certain of bad news (negativity bias).
        if mood < -0.2 and valence < 0:
            confidence = min(0.95, confidence + 0.06)
            if "mood_congruence" not in biases:
                biases.append("mood_congruence")
        if anger > 0.55:
            if "hostility_bias" not in biases:
                biases.append("hostility_bias")
            attribution = "internal" if observation.target_kind == TargetKind.HUMAN else attribution

        if observation.detected and observation.clarity < 0.35 and not alternatives:
            alternatives.append("Puede que haya entendido mal lo que pasó.")

        emotional_charge: dict[str, float] = {}
        if valence < -0.15:
            emotional_charge["fear"] = round(min(1.0, abs(valence) * (0.4 + neuroticism)), 3)
            emotional_charge["anxiety"] = round(min(1.0, abs(valence) * 0.5), 3)
        elif valence > 0.15:
            emotional_charge["relief"] = round(min(1.0, valence * 0.6), 3)

        return Interpretation(
            observation_id=observation.observation_id,
            perceiver_uid=str(human.uid),
            tick=observation.tick,
            claim=claim,
            confidence=round(confidence, 3),
            valence=round(valence, 3),
            emotional_charge=emotional_charge,
            attribution=attribution,
            biases_applied=biases,
            alternative_readings=alternatives,
            is_misunderstanding=is_misunderstanding,
        )

    # ------------------------------------------------------------------
    # Memory and belief encoding
    # ------------------------------------------------------------------
    def encode(
        self,
        human: Any,
        observation: Observation,
        interpretation: Interpretation,
    ) -> bool:
        """Encode a perceived episode.  Returns True when a memory was stored."""
        importance = observation.salience * (0.6 + 0.4 * abs(interpretation.valence))
        importance = max(0.0, min(1.0, importance))

        # Working memory always receives attended percepts (capacity-limited).
        try:
            human.memory.working.add(
                WorkingMemoryItem(
                    content=f"[{observation.channel.value}] {interpretation.claim}",
                    category="perception",
                    importance=importance,
                    tick_created=observation.tick,
                    metadata={
                        "observation_id": observation.observation_id,
                        "target_kind": observation.target_kind.value,
                        "clarity": round(observation.clarity, 3),
                        "confidence": interpretation.confidence,
                    },
                )
            )
        except Exception:  # pragma: no cover - working memory is best-effort
            pass

        # Long-term encoding requires a minimum salience, exactly as in memory
        # consolidation.  Low-salience percepts are simply not remembered.
        if importance < 0.30:
            return False

        associated: list[Any] = []
        if observation.target_kind == TargetKind.HUMAN:
            associated.append(observation.target_id)
        record = EpisodicRecord(
            summary=interpretation.claim or f"Percibí {observation.target_label}",
            tick=observation.tick,
            importance=round(importance, 3),
            emotional_valence=interpretation.valence,
            associated_humans=associated,
            location_id=observation.location_id,
            accessibility=round(0.35 + 0.65 * observation.clarity, 3),
            emotional_associations=dict(interpretation.emotional_charge),
            context_tags=["perception", observation.channel.value, observation.target_kind.value],
        )
        try:
            human.memory.episodic.store(record)
        except Exception:  # pragma: no cover
            return False

        if interpretation.valence < -0.20 and observation.location_id:
            try:
                human.memory.associate_location(
                    observation.location_id,
                    "fear",
                    intensity=min(1.0, abs(interpretation.valence)),
                    valence=interpretation.valence,
                )
            except Exception:
                pass
        self.stats["memories_encoded"] += 1
        return True

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def perceive(
        self,
        human: Any,
        *,
        tick: int,
        locations: Any = None,
        co_located_humans: Optional[Iterable[Any]] = None,
        environment_state: Any = None,
        hazards: Any = None,
        social_engine: Any = None,
        extra_stimuli: Optional[list[dict[str, Any]]] = None,
        max_others: int = 6,
        hour: Optional[int] = None,
    ) -> PerceptionSnapshot:
        """Run one perception cycle for one individual."""
        snapshot = self.get_snapshot(str(human.uid))
        snapshot.tick = tick
        self.stats["ticks_processed"] += 1

        loc_id = getattr(human.physical_state, "current_location_id", None)
        location = None
        if locations is not None and loc_id:
            location = locations.get_optional(loc_id) if hasattr(locations, "get_optional") else None
        is_outdoor = bool(getattr(location, "is_outdoor", False))
        if hour is None:
            hour = int(getattr(environment_state, "hour_of_day", 12) or 12)
        hour = int(hour) % 24
        rain = float(getattr(environment_state, "rainfall_mm_per_hour", 0.0) or 0.0)
        temperature = float(getattr(environment_state, "temperature_celsius", 27.0) or 27.0)

        acuity = self.acuity_for(human, hour=hour, is_outdoor=is_outdoor, rainfall_mm_per_hour=rain)
        snapshot.acuity = acuity

        stimuli: list[tuple[dict[str, Any], float, bool, Optional[tuple[float, float]], Optional[dict[str, Any]]]] = []

        # 1. Co-located humans (the dominant social stimulus).
        others = list(co_located_humans or [])
        if others and len(others) > max_others:
            rng = self._rng("sample", self._stable_id(human), tick)
            idx = rng.choice(len(others), size=max_others, replace=False)
            others = [others[int(i)] for i in idx]

        for other in others:
            if getattr(other, "uid", None) == getattr(human, "uid", None):
                continue
            distance = self._micro_distance(self._stable_id(human), self._stable_id(other))
            activity = getattr(other.physical_state, "current_activity", None)
            activity_value = getattr(activity, "value", None)
            signal = 0.55
            if activity_value in ("work", "exercise", "play_sport", "travel"):
                signal += 0.12
            if activity_value == "socialize":
                signal += 0.08
            if getattr(other, "active_health_conditions", None):
                signal += 0.05
            familiar = False
            try:
                familiar = float(
                    human.memory.get_human_association(other.uid).get("intensity", 0.0)
                ) > 0.0
            except Exception:
                familiar = False
            if familiar:
                signal += 0.10
            stim = self._stimulus(
                TargetKind.HUMAN, str(other.uid), getattr(other, "name", ""), signal
            )
            stim["familiar"] = familiar
            # Detection randomness keys off the deterministic identity serial so
            # the same seed yields the same perception across process runs.
            stim["detect_key"] = self._stable_id(other)
            stimuli.append((stim, distance, True, None, {"target": other}))

        # 2. Hazards present in the territory.
        if hazards is not None:
            flood = float(getattr(hazards, "flood_risk_level", 0.0) or 0.0)
            landslide = float(getattr(hazards, "landslide_risk_level", 0.0) or 0.0)
            if flood > 0.35:
                stimuli.append(
                    (
                        self._stimulus(TargetKind.HAZARD, "hazard:flood", _HAZARD_LABELS_ES["flood"], 0.55 + 0.4 * flood),
                        self._micro_distance(self._stable_id(human), "flood"),
                        True,
                        None,
                        {"attributes": {"hazard": "flood", "risk": round(flood, 2)}, "severity": flood},
                    )
                )
            if landslide > 0.4:
                stimuli.append(
                    (
                        self._stimulus(TargetKind.HAZARD, "hazard:landslide", _HAZARD_LABELS_ES["landslide"], 0.5 + 0.4 * landslide),
                        self._micro_distance(self._stable_id(human), "landslide"),
                        True,
                        None,
                        {"attributes": {"hazard": "landslide", "risk": round(landslide, 2)}, "severity": landslide},
                    )
                )
            if temperature >= 33.0 and is_outdoor:
                stimuli.append(
                    (
                        self._stimulus(TargetKind.HAZARD, "hazard:heat", _HAZARD_LABELS_ES["heat"], 0.5),
                        self._micro_distance(self._stable_id(human), "heat"),
                        True,
                        None,
                        {"attributes": {"hazard": "heat", "temperature_c": round(temperature, 1)}, "severity": min(1.0, (temperature - 30.0) / 10.0)},
                    )
                )

        # 3. Immediate environment.
        if rain > 1.0:
            stimuli.append(
                (
                    self._stimulus(TargetKind.ENVIRONMENT, "env:rain", _HAZARD_LABELS_ES["rain"], 0.5),
                    0.0,
                    True,
                    None,
                    {"attributes": {"rainfall_mm_per_hour": round(rain, 2)}},
                )
            )
        if loc_id:
            label = getattr(location, "name", loc_id) if location else loc_id
            stimuli.append(
                (
                    self._stimulus(TargetKind.LOCATION, str(loc_id), str(label), 0.30),
                    0.0,
                    True,
                    None,
                    {"attributes": {"location_type": getattr(getattr(location, "location_type", None), "value", None), "is_outdoor": is_outdoor}},
                )
            )

        for stim in extra_stimuli or []:
            stimuli.append(
                (
                    stim,
                    float(stim.get("distance_m", 0.0)),
                    bool(stim.get("same_location", True)),
                    stim.get("coordinates"),
                    {"attributes": stim.get("attributes", {}), "severity": stim.get("severity", 0.5)},
                )
            )

        # 4. Detect, rank and attend.
        candidates: list[tuple[Observation, Optional[dict[str, Any]]]] = []
        for stim, distance, same_location, coords, truth in stimuli:
            self.stats["stimuli_considered"] += 1
            channel = PerceptionChannel.VISUAL
            observation = self.observe_stimulus(
                human,
                stim,
                tick=tick,
                acuity=acuity,
                distance_m=distance,
                same_location=same_location,
                is_outdoor=is_outdoor,
                rain=rain,
                location_id=loc_id,
                coordinates=coords,
                channel=channel,
                ground_truth=truth,
            )
            # If vision failed for a nearby human, hearing may still catch them.
            if (
                not observation.detected
                and stim["target_kind"] == TargetKind.HUMAN
                and same_location
            ):
                observation = self.observe_stimulus(
                    human,
                    stim,
                    tick=tick,
                    acuity=acuity,
                    distance_m=distance,
                    same_location=same_location,
                    is_outdoor=is_outdoor,
                    rain=rain,
                    location_id=loc_id,
                    coordinates=coords,
                    channel=PerceptionChannel.AUDITORY,
                    ground_truth=truth,
                )
                if observation.detected:
                    observation.attributes.setdefault("heard_not_seen", True)

            if observation.detected:
                self.stats["observations_detected"] += 1
                # Re-identification across encounters is memory, not acuity: a
                # stranger can be recognised as "the same person as before"
                # without their name ever becoming known.
                if (
                    observation.target_kind == TargetKind.HUMAN
                    and snapshot.has_perceived(observation.target_id)
                    and not observation.attributes.get("identity_resolved")
                ):
                    observation.attributes["previously_seen"] = True
                candidates.append((observation, truth))
            else:
                self.stats["observations_missed"] += 1

        # Attention: rank by personal relevance, retain detail capacity.
        scored = [
            (self._attention_weight(human, {
                "target_kind": obs.target_kind,
                "familiar": obs.provenance.get("familiar", False),
            }, obs.clarity) * obs.salience, obs, truth)
            for obs, truth in candidates
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        capacity = min(acuity.detail_capacity, self.max_observations_per_tick)
        attended = scored[:capacity]
        self.stats["suppressed_by_attention"] += len(scored) - len(attended)
        self.stats["attended"] += len(attended)

        for _score, observation, truth in attended:
            interpretation = self.interpret(
                human, observation, truth=truth, social_engine=social_engine
            )
            snapshot.record(observation, interpretation)
            snapshot.total_detections += 1
            if interpretation.is_misunderstanding:
                snapshot.total_misunderstandings += 1
                self.stats["misunderstandings"] += 1

            known = snapshot.known_entities.get(observation.target_id, {})
            identity = bool(observation.attributes.get("identity_resolved"))
            snapshot.known_entities[observation.target_id] = {
                "kind": observation.target_kind.value,
                "label": observation.target_label,
                "first_seen_tick": known.get("first_seen_tick", tick),
                "last_seen_tick": tick,
                "times_perceived": int(known.get("times_perceived", 0)) + 1,
                "identity_resolved": bool(known.get("identity_resolved", False) or identity),
                "max_clarity": round(max(float(known.get("max_clarity", 0.0)), observation.clarity), 3),
            }

            self.encode(human, observation, interpretation)

            # Belief registration: perceived facts enter the epistemic store.
            try:
                if interpretation.confidence >= 0.45 and observation.target_kind in (
                    TargetKind.HUMAN,
                    TargetKind.HAZARD,
                ):
                    from saltbor.cognition.epistemic.beliefs import EpistemicBelief
                    human.epistemic.register_belief(
                        EpistemicBelief(
                            belief_id=f"perc_{observation.observation_id[:12]}",
                            subject=observation.target_id,
                            predicate="observed_as",
                            object_val=interpretation.claim,
                            confidence=interpretation.confidence,
                            source_type="direct_observation",
                            provenance=f"perception:{observation.channel.value}",
                            created_tick=tick,
                            context_tags=["perception", observation.target_kind.value],
                        )
                    )
            except Exception:
                pass

        # Trim rolling buffers; long-term memory holds the history.
        if len(snapshot.observations) > 60:
            snapshot.observations = snapshot.observations[-60:]
        if len(snapshot.interpretations) > 60:
            snapshot.interpretations = snapshot.interpretations[-60:]

        return snapshot

    # ------------------------------------------------------------------
    # Event witnessing
    # ------------------------------------------------------------------
    def perceive_event(
        self,
        human: Any,
        event: Any,
        *,
        tick: Optional[int] = None,
        locations: Any = None,
        environment_state: Any = None,
        hour: Optional[int] = None,
    ) -> Optional[tuple[Observation, Interpretation]]:
        """Attempt to witness an event.  Returns ``(observation, interpretation)``."""
        event_location = getattr(event, "location_id", None)
        my_location = getattr(human.physical_state, "current_location_id", None)
        if event_location and my_location and event_location != my_location:
            return None

        snapshot = self.get_snapshot(str(human.uid))
        if hour is None:
            hour = int(getattr(environment_state, "hour_of_day", 12) or 12)
        hour = int(hour) % 24
        rain = float(getattr(environment_state, "rainfall_mm_per_hour", 0.0) or 0.0)
        acuity = snapshot.acuity
        distance = self._micro_distance(
            self._stable_id(human), getattr(event, "event_id", "event")
        )
        stim = self._stimulus(
            TargetKind.EVENT,
            str(getattr(event, "event_id", "event")),
            getattr(getattr(event, "event_type", None), "value", "evento"),
            float(getattr(event, "importance", 0.5) or 0.5),
        )
        truth = {
            "summary": getattr(getattr(event, "event_type", None), "value", "evento"),
            "attributes": {
                "event_type": getattr(getattr(event, "event_type", None), "value", None),
                "participants": [
                    str(p) for p in (
                        getattr(event, "source_human_id", None),
                        getattr(event, "target_human_id", None),
                    ) if p
                ],
            },
        }
        observation = self.observe_stimulus(
            human,
            stim,
            tick=int(tick if tick is not None else getattr(event, "tick", 0)),
            acuity=acuity,
            distance_m=distance,
            same_location=True,
            is_outdoor=bool(getattr(locations.get_optional(my_location), "is_outdoor", False))
            if (locations is not None and my_location) else False,
            rain=rain,
            location_id=my_location,
            ground_truth=truth,
        )
        if not observation.detected:
            self.stats["observations_missed"] += 1
            return None

        interpretation = self.interpret(human, observation, truth=truth)
        snapshot.record(observation, interpretation)
        snapshot.total_detections += 1
        if interpretation.is_misunderstanding:
            snapshot.total_misunderstandings += 1
        self.encode(human, observation, interpretation)
        self.stats["observations_detected"] += 1
        return observation, interpretation

    # ------------------------------------------------------------------
    # Second-hand information
    # ------------------------------------------------------------------
    def receive_report(
        self,
        human: Any,
        *,
        claim: str,
        source_uid: Optional[str],
        credibility: float,
        tick: int,
        subject: str = "report",
        location_id: Optional[str] = None,
        social_engine: Any = None,
    ) -> tuple[Observation, Interpretation]:
        """Ingest testimony, gossip or rumour as a second-hand percept.

        The receiver never gets first-hand clarity.  Trust in the source
        modulates both clarity and confidence, which is how a confident liar
        and a hesitant witness produce different beliefs.
        """
        trust = 0.5
        if social_engine is not None and source_uid:
            try:
                rel = social_engine.get_relationship(human.uid, source_uid)
                if rel is not None:
                    trust = float(rel.trust)
            except Exception:
                trust = 0.5

        effective = max(0.05, min(1.0, credibility * (0.5 + 0.5 * trust)))
        observation = Observation(
            perceiver_uid=str(human.uid),
            tick=tick,
            channel=PerceptionChannel.SOCIAL_REPORT,
            target_kind=TargetKind.EVENT,
            target_id=subject,
            target_label=claim,
            location_id=location_id,
            distance_m=0.0,
            signal_strength=effective,
            detection_probability=effective,
            detected=True,
            clarity=round(0.25 + 0.5 * effective, 3),
            attributes={"reported_claim": claim, "source_uid": source_uid},
            provenance={
                "model": "testimony_v1",
                "source_trust": round(trust, 3),
                "credibility": round(credibility, 3),
            },
        )
        interpretation = Interpretation(
            observation_id=observation.observation_id,
            perceiver_uid=str(human.uid),
            tick=tick,
            claim=f"Me contaron que {claim}",
            confidence=round(0.2 + 0.6 * effective, 3),
            valence=-0.1 if "peligro" in claim.lower() or "robo" in claim.lower() else 0.0,
            attribution="external",
            biases_applied=["testimony_trust"] if trust > 0.6 else ["testimony_skepticism"],
            alternative_readings=["Puede que me lo hayan contado mal."],
            is_misunderstanding=False,
        )
        snapshot = self.get_snapshot(str(human.uid))
        snapshot.record(observation, interpretation)
        snapshot.total_detections += 1
        # The receiver now *knows of* the subject, but only as testimony: the
        # entity is registered with second-hand confidence, never first-hand.
        snapshot.known_entities[subject] = {
            "kind": TargetKind.EVENT.value,
            "label": claim,
            "first_seen_tick": tick,
            "last_seen_tick": tick,
            "confidence": round(0.2 + 0.6 * effective, 3),
            "source": "testimony",
        }
        self.stats["reports_received"] += 1
        self.encode(human, observation, interpretation)
        return observation, interpretation

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "stats": dict(self.stats),
            "snapshots": {uid: snap.to_dict() for uid, snap in self.snapshots.items()},
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.stats.update({str(k): int(v) for k, v in (data.get("stats") or {}).items()})
        self.snapshots = {
            uid: PerceptionSnapshot.from_dict(payload)
            for uid, payload in (data.get("snapshots") or {}).items()
        }


def clarity_high(observation: Observation) -> bool:
    """Helper used by interpretation templates."""
    return observation.clarity >= 0.60
