"""Unit and integration tests for Phase 0.5 Geography, Terrain & Environment."""

import pytest
from saltbor.world.geography.terrain import TerrainGrid, TerrainSurfaceType
from saltbor.world.environment.weather import EnvironmentEngine, WeatherCondition, Season


def test_terrain_grid_and_slope_penalties():
    grid = TerrainGrid(width_meters=100.0, height_meters=100.0, cell_size_meters=10.0)

    # Set cell (0, 0) as plains and cell (0, 1) with steep elevation
    grid.set_cell(0, 0, elevation=10.0, surface=TerrainSurfaceType.SOIL)
    grid.set_cell(0, 1, elevation=45.0, surface=TerrainSurfaceType.ROCK)

    prop_flat = grid.get_cell_properties(0.0, 0.0)
    assert prop_flat.surface_type == TerrainSurfaceType.SOIL

    # Speed multiplier between (0,0) and (0,10)
    speed_mult = grid.calculate_speed_multiplier(from_pos=(5.0, 5.0), to_pos=(5.0, 15.0))
    assert speed_mult < 0.7  # Steep uphill penalty


def test_river_barrier_and_crossing():
    grid = TerrainGrid(width_meters=100.0, height_meters=100.0, cell_size_meters=10.0)

    # Place river at y=50m
    for x in range(10):
        grid.set_cell(x, 5, elevation=5.0, surface=TerrainSurfaceType.RIVER, is_walkable=False)

    # Place bridge at x=5, y=5
    grid.set_cell(5, 5, elevation=6.0, surface=TerrainSurfaceType.BRIDGE, is_walkable=True)

    # Impassable river cell
    assert grid.is_traversable(15.0, 55.0) is False

    # Traversable bridge cell
    assert grid.is_traversable(55.0, 55.0) is True


def test_environment_engine_seasons_and_crop_impact():
    env = EnvironmentEngine(ticks_per_year=96, seed=42)

    # Tick 10: Summer
    state_summer = env.step(current_tick=10)
    assert state_summer.season in (Season.VERANO, Season.INVIERNO)

    # Force a drought condition
    env.force_weather_condition(WeatherCondition.DROUGHT, duration_ticks=10)
    assert env.state.weather_condition == WeatherCondition.DROUGHT
    assert env.get_crop_yield_multiplier() < 0.7
