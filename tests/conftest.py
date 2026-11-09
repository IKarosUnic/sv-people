"""Shared pytest fixtures for the Saltbor simulation test suite."""

import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

from saltbor.core.clock import SimulationClock
from saltbor.core.config import SimulationConfig
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.schema import SchemaManager
from saltbor.population.factory import PopulationFactory
from saltbor.population.human import SyntheticHuman
from saltbor.social.engine import SocialEngine
from saltbor.world.activities.catalog import ActivityCatalog
from saltbor.world.locations.registry import LocationRegistry
from saltbor.world.navigation.pathfinding import NavigationGraph


@pytest.fixture
def config() -> SimulationConfig:
    return SimulationConfig(
        random_seed=42,
        initial_population_size=20,
        checkpoint_interval_ticks=96,
    )


@pytest.fixture
def clock(config: SimulationConfig) -> SimulationClock:
    return SimulationClock(config=config)


@pytest.fixture
def temp_db() -> Generator[DatabaseManager, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    db = DatabaseManager(db_path)
    db.connect()
    SchemaManager.create_tables(db)
    try:
        yield db
    finally:
        db.close()
        try:
            db_path.unlink()
        except OSError:
            pass


@pytest.fixture
def locations() -> LocationRegistry:
    return LocationRegistry.create_saltbor_map()


@pytest.fixture
def nav_graph(locations: LocationRegistry) -> NavigationGraph:
    return NavigationGraph.build_saltbor_graph(locations)


@pytest.fixture
def activity_catalog() -> ActivityCatalog:
    return ActivityCatalog()


@pytest.fixture
def social_engine() -> SocialEngine:
    return SocialEngine()


@pytest.fixture
def population_20(config: SimulationConfig) -> list[SyntheticHuman]:
    return PopulationFactory.create_population(config=config, try_nemotron=False)
