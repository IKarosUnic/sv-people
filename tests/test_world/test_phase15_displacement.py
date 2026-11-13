"""Regression test: severe disasters must displace zone residents, not only lease holders."""

import types

from saltbor.accidents.models import DisasterEvent
from saltbor.core.config import SimulationConfig
from saltbor.core.types import DisasterType
from saltbor.population.human import SyntheticHuman
from saltbor.simulation.extension_runtime import ExtensionRuntime


class _Population:
    def __init__(self, humans):
        self._humans = humans

    def get_all(self):
        return self._humans


def _runtime_with(humans) -> ExtensionRuntime:
    stub_runner = types.SimpleNamespace(
        config=SimulationConfig(random_seed=42),
        population=_Population(humans),
    )
    return ExtensionRuntime(stub_runner)


def _resident(name, serial, home):
    human = SyntheticHuman.create(name=name, serial=serial, age=30.0, money=20.0, seed=serial)
    human.physical_state.home_location_id = home
    return human


def test_severe_disaster_displaces_zone_residents_without_lease():
    in_zone = _resident("Residente Zona", 1, "casa_norte_1")
    outside = _resident("Residente Fuera", 2, "casa_este_1")
    runtime = _runtime_with([in_zone, outside])

    disaster = DisasterEvent(
        disaster_id="dis_test",
        disaster_type=DisasterType.FLOODING,
        affected_location_ids=["casa_norte_1"],
        severity=0.85,
    )

    runtime._include_zone_residents(disaster)

    assert str(in_zone.uid) in disaster.displaced_human_ids
    assert str(outside.uid) not in disaster.displaced_human_ids


def test_minor_disaster_does_not_displace_anyone():
    in_zone = _resident("Residente Zona", 3, "casa_norte_1")
    runtime = _runtime_with([in_zone])

    disaster = DisasterEvent(
        disaster_id="dis_minor",
        disaster_type=DisasterType.FLOODING,
        affected_location_ids=["casa_norte_1"],
        severity=0.40,
    )

    runtime._include_zone_residents(disaster)

    assert disaster.displaced_human_ids == []
