"""Unit and integration tests for the Cultural Evolution Engine."""

import pytest
import numpy as np
from saltbor.culture.element import CulturalElement, CulturalElementType
from saltbor.culture.transmission import CulturalTransmissionEngine
from saltbor.culture.festival import Festival, FestivalManager, FestivalStatus
from saltbor.population.human import SyntheticHuman


def test_cultural_element_lifecycle_and_mutation():
    elem = CulturalElement(
        element_id="elem_weaving_1",
        name="Traditional Weaving",
        element_type=CulturalElementType.SKILL_CRAFT,
        description="Traditional loom weaving method",
        created_tick=100,
    )
    assert elem.adoption_count == 0
    assert elem.authenticity == 1.0

    # Register adoption
    parent = SyntheticHuman.create(name="Maria Ramos", serial=1, age=35.0, seed=10)
    elem.register_adoption(parent.uid, "taller_artesanal", tick=120)
    assert elem.adoption_count == 1
    assert parent.uid in elem.practitioners

    # Mutate / Reinterpret
    innovator = SyntheticHuman.create(name="Mateo Ramos", serial=2, age=20.0, seed=11)
    mutated = elem.create_mutation(innovator.uid, "Fine Loom Weaving", "Tighter weave technique", current_tick=150)
    assert mutated.variant_of_id == elem.element_id
    assert elem.mutations_count == 1
    assert mutated.authenticity < 1.0


def test_cultural_transmission_multi_channel():
    parent = SyntheticHuman.create(name="Maria Ramos", serial=1, age=35.0, seed=10)
    child = SyntheticHuman.create(name="Lucia Ramos", serial=2, age=8.0, seed=11)

    engine = CulturalTransmissionEngine(rng=np.random.default_rng(42))

    tradition = CulturalElement(
        element_id="trad_solstice",
        name="Winter Solstice Gathering",
        element_type=CulturalElementType.TRADITION,
        description="Annual gathering at the town square",
        created_tick=10,
    )
    engine.register_element(tradition)
    engine.grant_element_directly(parent.uid, tradition.element_id, "plaza_central", tick=10)

    # Transmission via family channel
    success = False
    for tick in range(20, 25):
        ok, msg, res = engine.attempt_transmission(
            element_id=tradition.element_id,
            source_human=parent,
            learner=child,
            channel="family",
            current_tick=tick,
            trust_in_source=0.9,
        )
        if ok:
            success = True
            break

    assert success is True
    assert tradition.adoption_count >= 2
    assert child.uid in tradition.practitioners


def test_festival_lifecycle_and_tradition_formation():
    manager = FestivalManager()
    organizer = SyntheticHuman.create(name="Elena Ortiz", serial=3, age=40.0, seed=12)

    fest = manager.propose_festival(
        festival_id="fest_harvest",
        name="Harvest Jubilee",
        description="Celebration of the summer maize harvest",
        host_location_id="plaza_central",
        scheduled_tick=200,
        required_food=20.0,
        required_wood=8.0,
        required_labor=4,
        proposer_uid=organizer.uid,
    )
    assert fest.status == FestivalStatus.PROPOSED

    # Contribute partial resources & labor
    res = manager.prepare_step(fest.festival_id, organizer, food_donation=10.0, wood_donation=4.0, labor_ticks=2)
    assert res is True
    assert fest.is_materially_ready() is False

    # Complete required resources
    manager.prepare_step(fest.festival_id, organizer, food_donation=10.0, wood_donation=4.0, labor_ticks=2)
    assert fest.is_materially_ready() is True

    # Assemble attendees
    attendees = [
        organizer,
        SyntheticHuman.create(name="Person A", serial=4, age=25.0, seed=13),
        SyntheticHuman.create(name="Person B", serial=5, age=26.0, seed=14),
        SyntheticHuman.create(name="Person C", serial=6, age=27.0, seed=15),
    ]

    # Hold festival celebration
    held, summary, tradition = manager.execute_celebration(fest.festival_id, current_tick=200, attendees=attendees)
    assert held is True
    assert fest.status == FestivalStatus.COMPLETED
    assert len(fest.attendee_uids) == 4
    assert tradition is not None
