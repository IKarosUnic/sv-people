"""Tests for core types, clock, and identity continuity."""

from uuid import UUID

from saltbor.core.clock import SimulationClock
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import HumanIdentity, IdentityFactory
from saltbor.core.types import DataSource


def test_clock_progression(config: SimulationConfig):
    clock = SimulationClock(config=config)
    assert clock.current_tick == 0
    assert clock.current_day == 0
    assert clock.current_hour_int == config.start_hour

    # Advance 4 ticks (1 hour)
    for _ in range(4):
        clock.tick()

    assert clock.current_tick == 4
    assert clock.current_hour_int == config.start_hour + 1


def test_identity_immutability():
    factory = IdentityFactory(start_serial=1)
    ident1 = factory.create(given_name="Carlos", family_name="Rivera")
    assert ident1.serial == 1
    assert ident1.full_name == "Carlos Rivera"
    assert isinstance(ident1.uid, UUID)
    assert ident1.data_source == DataSource.MOCK_GENERATED

    ident2 = factory.create(given_name="Sofia", family_name="Hernandez")
    assert ident2.serial == 2
    assert ident2.uid != ident1.uid
