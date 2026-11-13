"""Perception models for SALTBOR (Phase 1.6 §5).

The simulation must never give an individual omniscient knowledge.  These
models make the epistemic boundary explicit:

* ``Observation`` records what a *specific channel* of a *specific person*
  managed to detect, how clearly, and at what distance.
* ``Interpretation`` records what that person concluded from the observation,
  including the biases that shaped the conclusion and the alternative readings
  another person could reasonably have reached.
* ``PerceptionSnapshot`` is the rolling, per-individual perceptual state that
  the API, the UI and the experiments read.

The separation of "objective signal" from "detected signal" from "believed
claim" is deliberate and is what allows two individuals standing in the same
place to leave with different memories of the same event.
"""

from __future__ import annotations

import dataclasses
import enum
import uuid
from typing import Any, Optional


class PerceptionChannel(str, enum.Enum):
    """The sensory or informational channel an observation arrived through."""

    VISUAL = "visual"
    AUDITORY = "auditory"
    OLFACTORY = "olfactory"
    TACTILE = "tactile"
    SOCIAL_REPORT = "social_report"   # testimony, gossip, rumour
    MEMORY_RECALL = "memory_recall"   # reconstructed from prior experience


class TargetKind(str, enum.Enum):
    """What kind of thing was perceived."""

    HUMAN = "human"
    LOCATION = "location"
    ACTIVITY = "activity"
    HAZARD = "hazard"
    ENVIRONMENT = "environment"
    OBJECT = "object"
    EVENT = "event"
    INSTITUTION = "institution"


@dataclasses.dataclass
class AcuityProfile:
    """A person's effective perceptual capacity at one moment.

    Every value is in ``[0, 1]``.  ``attention`` is the share of the perceptual
    field actually processed; the rest is never encoded at all.
    """

    visual: float = 1.0
    auditory: float = 1.0
    olfactory: float = 1.0
    attention: float = 1.0
    fatigue_factor: float = 1.0
    age_factor: float = 1.0
    health_factor: float = 1.0
    environmental_factor: float = 1.0
    detail_capacity: int = 7
    provenance: dict[str, Any] = dataclasses.field(default_factory=dict)

    def channel(self, channel: PerceptionChannel) -> float:
        base = {
            PerceptionChannel.VISUAL: self.visual,
            PerceptionChannel.AUDITORY: self.auditory,
            PerceptionChannel.OLFACTORY: self.olfactory,
            PerceptionChannel.TACTILE: 1.0,
            PerceptionChannel.SOCIAL_REPORT: 1.0,
            PerceptionChannel.MEMORY_RECALL: 0.8,
        }.get(channel, 1.0)
        return max(0.0, min(1.0, base))

    def to_dict(self) -> dict[str, Any]:
        return {
            "visual": round(self.visual, 3),
            "auditory": round(self.auditory, 3),
            "olfactory": round(self.olfactory, 3),
            "attention": round(self.attention, 3),
            "fatigue_factor": round(self.fatigue_factor, 3),
            "age_factor": round(self.age_factor, 3),
            "health_factor": round(self.health_factor, 3),
            "environmental_factor": round(self.environmental_factor, 3),
            "detail_capacity": self.detail_capacity,
            "provenance": dict(self.provenance),
        }


@dataclasses.dataclass
class Observation:
    """What one person actually detected, through one channel.

    ``signal_strength`` is the objective salience of the stimulus before any
    observer effects.  ``detection_probability`` and ``detected`` describe
    whether this observer caught it.  ``clarity`` describes how much detail
    resolved, and ``attributes`` contains only the attributes that clarity
    actually allowed — never the full ground truth.
    """

    observation_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    perceiver_uid: str = ""
    tick: int = 0

    channel: PerceptionChannel = PerceptionChannel.VISUAL
    target_kind: TargetKind = TargetKind.LOCATION
    target_id: str = ""
    target_label: str = ""

    location_id: Optional[str] = None
    coordinates: Optional[tuple[float, float]] = None
    distance_m: float = 0.0

    signal_strength: float = 0.5
    detection_probability: float = 1.0
    detected: bool = True
    clarity: float = 0.5

    attributes: dict[str, Any] = dataclasses.field(default_factory=dict)
    obscured_by: list[str] = dataclasses.field(default_factory=list)
    provenance: dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def salience(self) -> float:
        """Observer-relative importance, used for attention ranking."""
        return max(0.0, min(1.0, self.signal_strength * (0.35 + 0.65 * self.clarity)))

    def identity_resolved(self) -> bool:
        return bool(self.attributes.get("identity_resolved"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "perceiver_uid": self.perceiver_uid,
            "tick": self.tick,
            "channel": self.channel.value,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "target_label": self.target_label,
            "location_id": self.location_id,
            "coordinates": list(self.coordinates) if self.coordinates else None,
            "distance_m": round(self.distance_m, 1),
            "signal_strength": round(self.signal_strength, 3),
            "detection_probability": round(self.detection_probability, 3),
            "detected": self.detected,
            "clarity": round(self.clarity, 3),
            "attributes": dict(self.attributes),
            "obscured_by": list(self.obscured_by),
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Observation":
        return cls(
            observation_id=data.get("observation_id", str(uuid.uuid4())),
            perceiver_uid=data.get("perceiver_uid", ""),
            tick=int(data.get("tick", 0)),
            channel=PerceptionChannel(data.get("channel", "visual")),
            target_kind=TargetKind(data.get("target_kind", "location")),
            target_id=data.get("target_id", ""),
            target_label=data.get("target_label", ""),
            location_id=data.get("location_id"),
            coordinates=tuple(data["coordinates"]) if data.get("coordinates") else None,
            distance_m=float(data.get("distance_m", 0.0)),
            signal_strength=float(data.get("signal_strength", 0.5)),
            detection_probability=float(data.get("detection_probability", 1.0)),
            detected=bool(data.get("detected", True)),
            clarity=float(data.get("clarity", 0.5)),
            attributes=dict(data.get("attributes", {})),
            obscured_by=list(data.get("obscured_by", [])),
            provenance=dict(data.get("provenance", {})),
        )


@dataclasses.dataclass
class Interpretation:
    """What a person understood, believed and felt about an observation."""

    interpretation_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    observation_id: str = ""
    perceiver_uid: str = ""
    tick: int = 0

    claim: str = ""
    confidence: float = 0.5
    valence: float = 0.0
    emotional_charge: dict[str, float] = dataclasses.field(default_factory=dict)
    attribution: str = "ambiguous"       # internal | external | ambiguous
    biases_applied: list[str] = dataclasses.field(default_factory=list)
    alternative_readings: list[str] = dataclasses.field(default_factory=list)
    is_misunderstanding: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "interpretation_id": self.interpretation_id,
            "observation_id": self.observation_id,
            "claim": self.claim,
            "confidence": round(self.confidence, 3),
            "valence": round(self.valence, 3),
            "emotional_charge": {k: round(v, 3) for k, v in self.emotional_charge.items()},
            "attribution": self.attribution,
            "biases_applied": list(self.biases_applied),
            "alternative_readings": list(self.alternative_readings),
            "is_misunderstanding": self.is_misunderstanding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Interpretation":
        return cls(
            interpretation_id=data.get("interpretation_id", str(uuid.uuid4())),
            observation_id=data.get("observation_id", ""),
            perceiver_uid=data.get("perceiver_uid", ""),
            tick=int(data.get("tick", 0)),
            claim=data.get("claim", ""),
            confidence=float(data.get("confidence", 0.5)),
            valence=float(data.get("valence", 0.0)),
            emotional_charge=dict(data.get("emotional_charge", {})),
            attribution=data.get("attribution", "ambiguous"),
            biases_applied=list(data.get("biases_applied", [])),
            alternative_readings=list(data.get("alternative_readings", [])),
            is_misunderstanding=bool(data.get("is_misunderstanding", False)),
        )


@dataclasses.dataclass
class PerceptionSnapshot:
    """Rolling perceptual state for one individual.

    ``known_entities`` is the authoritative record of what this person has
    actually encountered; it is what the rest of the simulation must consult
    instead of assuming knowledge of the world.
    """

    human_uid: str
    tick: int = 0
    acuity: AcuityProfile = dataclasses.field(default_factory=AcuityProfile)
    observations: list[Observation] = dataclasses.field(default_factory=list)
    interpretations: list[Interpretation] = dataclasses.field(default_factory=list)
    known_entities: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    total_observations: int = 0
    total_detections: int = 0
    total_misunderstandings: int = 0

    # The rolling perceptual window is bounded: total counters keep the full
    # history, while the retained detail stays small enough that a checkpoint of
    # a 400-person population does not serialize hundreds of thousands of
    # observations.  What must persist durably is memory, not the raw buffer.
    MAX_RETAINED_OBSERVATIONS: int = 40
    MAX_RETAINED_INTERPRETATIONS: int = 40

    def record(self, observation: Observation, interpretation: Interpretation) -> None:
        """Append one percept, trimming the rolling window."""
        self.observations.append(observation)
        self.interpretations.append(interpretation)
        self.total_observations += 1
        if len(self.observations) > self.MAX_RETAINED_OBSERVATIONS:
            del self.observations[: len(self.observations) - self.MAX_RETAINED_OBSERVATIONS]
        if len(self.interpretations) > self.MAX_RETAINED_INTERPRETATIONS:
            del self.interpretations[: len(self.interpretations) - self.MAX_RETAINED_INTERPRETATIONS]

    def recent(self, n: int = 8) -> list[Observation]:
        return self.observations[-n:]

    def has_perceived(self, entity_id: str) -> bool:
        return entity_id in self.known_entities

    def summary(self) -> dict[str, Any]:
        return {
            "human_uid": self.human_uid,
            "tick": self.tick,
            "acuity": self.acuity.to_dict(),
            "total_observations": self.total_observations,
            "total_detections": self.total_detections,
            "total_misunderstandings": self.total_misunderstandings,
            "known_entities": len(self.known_entities),
            "recent_observations": [o.to_dict() for o in self.recent(8)],
            "recent_interpretations": [
                i.to_dict() for i in self.interpretations[-8:]
            ],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "human_uid": self.human_uid,
            "tick": self.tick,
            "acuity": self.acuity.to_dict(),
            "observations": [o.to_dict() for o in self.observations],
            "interpretations": [i.to_dict() for i in self.interpretations],
            "known_entities": dict(self.known_entities),
            "total_observations": self.total_observations,
            "total_detections": self.total_detections,
            "total_misunderstandings": self.total_misunderstandings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerceptionSnapshot":
        acuity = data.get("acuity") or {}
        return cls(
            human_uid=data.get("human_uid", ""),
            tick=int(data.get("tick", 0)),
            acuity=AcuityProfile(
                visual=float(acuity.get("visual", 1.0)),
                auditory=float(acuity.get("auditory", 1.0)),
                olfactory=float(acuity.get("olfactory", 1.0)),
                attention=float(acuity.get("attention", 1.0)),
                fatigue_factor=float(acuity.get("fatigue_factor", 1.0)),
                age_factor=float(acuity.get("age_factor", 1.0)),
                health_factor=float(acuity.get("health_factor", 1.0)),
                environmental_factor=float(acuity.get("environmental_factor", 1.0)),
                detail_capacity=int(acuity.get("detail_capacity", 7)),
                provenance=dict(acuity.get("provenance", {})),
            ),
            observations=[Observation.from_dict(o) for o in data.get("observations", [])],
            interpretations=[
                Interpretation.from_dict(i) for i in data.get("interpretations", [])
            ],
            known_entities=dict(data.get("known_entities", {})),
            total_observations=int(data.get("total_observations", 0)),
            total_detections=int(data.get("total_detections", 0)),
            total_misunderstandings=int(data.get("total_misunderstandings", 0)),
        )
