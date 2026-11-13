"""Tests for the Phase 1.6 perception engine.

These tests assert the *epistemic boundary*: an individual may only know what
they perceived, with the clarity their own acuity allowed, and interpretations
must diverge between people facing the same stimulus.
"""

from __future__ import annotations

import pytest

from saltbor.cognition.perception.engine import PerceptionEngine
from saltbor.cognition.perception.models import (
    Observation,
    PerceptionChannel,
    PerceptionSnapshot,
    TargetKind,
)
from saltbor.population.human import SyntheticHuman


def _human(
    age: float = 30,
    energy: float = 1.0,
    seed: int = 1,
    name: str = "Persona",
    serial: int = 1,
) -> SyntheticHuman:
    # Identity serials are assigned deterministically by the population manager
    # in a real run; perception derives its randomness from them so the same
    # seed reproduces across process runs.
    human = SyntheticHuman.create(name=name, age=age, seed=seed, serial=serial)
    human.physical_state.current_location_id = "plaza_central"
    human.physical_state.home_location_id = "casa_norte_1"
    human.physical_state.energy = energy
    return human


def _observation(clarity: float, target=None, **kwargs) -> Observation:
    return Observation(
        perceiver_uid="observer",
        tick=1,
        channel=kwargs.pop("channel", PerceptionChannel.VISUAL),
        target_kind=kwargs.pop("target_kind", TargetKind.HUMAN),
        target_id=kwargs.pop("target_id", "target-1"),
        target_label=kwargs.pop("target_label", "una persona"),
        location_id="plaza_central",
        distance_m=kwargs.pop("distance_m", 30.0),
        signal_strength=kwargs.pop("signal_strength", 0.6),
        detection_probability=kwargs.pop("detection_probability", 0.6),
        detected=True,
        clarity=clarity,
        attributes=kwargs.pop("attributes", {}),
    )


def test_perception_is_partial_and_not_omniscient():
    """An observer does not detect every stimulus, and knows fewer entities than exist."""
    engine = PerceptionEngine(seed=5)
    observer = _human(age=74, energy=0.2, serial=1)
    targets = [
        _human(age=25, seed=100 + i, name=f"Objetivo {i}", serial=10 + i) for i in range(6)
    ]

    snapshot = engine.perceive(observer, tick=1, co_located_humans=targets, hour=22)

    assert engine.stats.get("stimuli_considered", 0) >= 1
    assert snapshot.total_observations > 0
    assert len(snapshot.known_entities) <= len(targets) + 1
    # A tired elderly observer at night perceives worse than a rested adult at
    # midday; the boundary is relative, because acuity is a product of factors.
    rested_noon = engine.acuity_for(_human(age=25, energy=1.0, serial=99), hour=12, is_outdoor=True)
    assert snapshot.acuity.visual < rested_noon.visual
    assert snapshot.acuity.fatigue_factor < rested_noon.fatigue_factor
    assert engine.stats["observations_missed"] > 0 or len(snapshot.known_entities) < 6


def test_acuity_depends_on_age_fatigue_and_time_of_day():
    engine = PerceptionEngine(seed=1)
    adult = _human(age=30, energy=1.0)
    elder = _human(age=85, energy=1.0, seed=2)
    tired = _human(age=30, energy=0.05, seed=3)

    day = engine.acuity_for(adult, hour=12, is_outdoor=True)
    night = engine.acuity_for(adult, hour=23, is_outdoor=True)
    elder_day = engine.acuity_for(elder, hour=12, is_outdoor=True)
    tired_day = engine.acuity_for(tired, hour=12, is_outdoor=True)

    assert day.visual > night.visual
    assert day.visual > elder_day.visual
    assert tired_day.fatigue_factor < day.fatigue_factor
    assert elder_day.detail_capacity <= day.detail_capacity


def test_clarity_gates_identity_and_detail():
    """A stranger is never identity-resolved, and low clarity hides activity."""
    engine = PerceptionEngine(seed=2)
    observer = _human(age=30)
    observer.physical_state.current_activity = None
    target = _human(age=32, seed=9, name="Desconocido")

    low = engine.observe_stimulus(
        observer,
        {
            "target_kind": TargetKind.HUMAN,
            "target_id": str(target.uid),
            "target_label": target.name,
            "signal": 0.6,
            "detect_key": engine._stable_id(target),
        },
        tick=1,
        acuity=engine.acuity_for(observer, hour=23, is_outdoor=True, rainfall_mm_per_hour=20.0),
        distance_m=25.0,
        same_location=True,
        is_outdoor=True,
        rain=20.0,
        location_id="plaza_central",
        ground_truth={"target": target},
    )
    # Whatever the detection draw, low clarity never yields a name: that is the
    # epistemic contract, not a particular random outcome.
    assert low.attributes.get("identity_resolved") is not True
    assert "name" not in low.attributes
    if low.detected:
        assert low.clarity < 0.55


def test_known_person_resolves_earlier_than_stranger():
    engine = PerceptionEngine(seed=3)
    observer = _human(age=30, serial=1)
    target = _human(age=30, seed=11, name="Vecina Conocida", serial=2)
    observer.memory.associate_human(target.uid, "familiarity", 0.9, valence=0.4)

    known = engine._resolve_human_attributes(observer, target, clarity=0.45, distances_known=True)
    stranger_target = _human(age=30, seed=12, name="Extraño", serial=3)
    stranger = engine._resolve_human_attributes(observer, stranger_target, clarity=0.45, distances_known=True)

    assert known["identity_resolved"] is True
    assert known["name"] == "Vecina Conocida"
    assert stranger["identity_resolved"] is False


def test_same_stimulus_yields_different_interpretations():
    engine = PerceptionEngine(seed=4)
    anxious = _human(age=35)
    trusting = _human(age=35, seed=2)
    anxious.personality.traits.neuroticism.base_value = 0.98
    anxious.personality.traits.neuroticism.current_value = 0.98
    trusting.personality.traits.agreeableness.base_value = 0.9
    trusting.personality.traits.agreeableness.current_value = 0.9

    observation = _observation(0.33, attributes={"identity_resolved": False})

    a = engine.interpret(anxious, observation)
    b = engine.interpret(trusting, observation)

    assert a.claim != b.claim
    assert a.biases_applied != b.biases_applied
    assert a.alternative_readings and b.alternative_readings


def test_low_clarity_invents_activity_and_can_misunderstand():
    engine = PerceptionEngine(seed=6)
    observer = _human(age=30)
    target = _human(age=31, seed=8)
    from saltbor.core.types import ActivityType

    target.physical_state.current_activity = ActivityType.WORK
    observer.memory.associate_human(target.uid, "familiarity", 0.9, valence=0.3)

    observation = _observation(
        0.28,
        target=target,
        attributes={"identity_resolved": True, "name": target.name},
    )
    interpretation = engine.interpret(observer, observation, truth={"target": target})

    assert "prior_based_inference" in interpretation.biases_applied
    assert interpretation.alternative_readings


def test_memory_encoding_requires_salience():
    engine = PerceptionEngine(seed=7)
    observer = _human(age=30)
    before = observer.memory.episodic.total_stored_count

    trivial = _observation(0.1, target_kind=TargetKind.LOCATION, signal_strength=0.05)
    trivial_interp = engine.interpret(observer, trivial)
    assert engine.encode(observer, trivial, trivial_interp) is False
    assert observer.memory.episodic.total_stored_count == before

    salient = _observation(0.85, target_kind=TargetKind.HAZARD, signal_strength=0.9)
    salient_interp = engine.interpret(observer, salient, truth={"severity": 0.9})
    assert engine.encode(observer, salient, salient_interp) is True
    assert observer.memory.episodic.total_stored_count > before


def test_second_hand_report_is_marked_as_testimony():
    engine = PerceptionEngine(seed=8)
    observer = _human(age=30)

    observation, interpretation = engine.receive_report(
        observer,
        claim="robaron en el mercado",
        source_uid="source-1",
        credibility=0.8,
        tick=12,
        subject="theft_at_market",
    )

    assert observation.channel is PerceptionChannel.SOCIAL_REPORT
    assert interpretation.confidence < 1.0
    assert "Me contaron" in interpretation.claim
    assert engine.has_perceived(str(observer.uid), "theft_at_market")


def test_perception_is_deterministic_for_same_seed_uid_and_tick():
    def run_once() -> tuple[int, float]:
        engine = PerceptionEngine(seed=99)
        observer = _human(age=28, seed=4, serial=1)
        targets = [_human(age=30, seed=50 + i, serial=20 + i) for i in range(4)]
        snapshot = engine.perceive(observer, tick=7, co_located_humans=targets, hour=14)
        clarity_sum = round(sum(o.clarity for o in snapshot.observations), 6)
        return snapshot.total_observations, clarity_sum

    assert run_once() == run_once()


def test_snapshot_roundtrip_preserves_known_entities():
    engine = PerceptionEngine(seed=10)
    observer = _human(age=30)
    engine.perceive(observer, tick=3, co_located_humans=[_human(age=31, seed=21, serial=5)], hour=12)

    snapshot = engine.get_snapshot(str(observer.uid))
    restored = PerceptionSnapshot.from_dict(snapshot.to_dict())

    assert restored.human_uid == snapshot.human_uid
    assert restored.total_observations == snapshot.total_observations
    assert restored.known_entities.keys() == snapshot.known_entities.keys()
    assert restored.acuity.to_dict() == snapshot.acuity.to_dict()


def test_engine_state_roundtrip():
    engine = PerceptionEngine(seed=11)
    observer = _human(age=30)
    engine.perceive(observer, tick=2, co_located_humans=[_human(age=33, seed=31, serial=6)], hour=9)

    payload = engine.to_dict()
    other = PerceptionEngine(seed=11)
    other.load_dict(payload)

    assert set(other.snapshots) == set(engine.snapshots)
    assert other.stats["observations_detected"] == engine.stats["observations_detected"]
