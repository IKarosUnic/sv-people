"""Tests for world geography, locations, routing, and activities."""

from saltbor.core.types import ActivityType, LocationType
from saltbor.world.activities.catalog import ActivityCatalog
from saltbor.world.geography.grid import Position, distance
from saltbor.world.locations.registry import LocationRegistry
from saltbor.world.navigation.pathfinding import NavigationGraph


def test_locations_registry(locations: LocationRegistry):
    assert len(locations.get_all()) == 16
    plaza = locations.get("plaza_central")
    assert plaza.location_type == LocationType.PUBLIC_SPACE
    assert plaza.is_open(12) is True

    market = locations.get("mercado_central")
    assert market.is_open(12) is True
    assert market.is_open(2) is False  # Closed at 2 AM


def test_navigation_routing(locations: LocationRegistry, nav_graph: NavigationGraph):
    plaza = locations.get("plaza_central")
    market = locations.get("mercado_central")

    route = nav_graph.find_route(plaza.position, market.position)
    assert len(route) >= 2
    travel_dist = nav_graph.travel_distance(plaza.position, market.position)
    assert travel_dist > 10.0

    ticks = nav_graph.travel_time_ticks(plaza.position, market.position)
    assert ticks >= 1


def test_activity_preconditions(activity_catalog: ActivityCatalog):
    # Cannot work when exhausted
    can_work = activity_catalog.can_perform(
        activity_type=ActivityType.WORK,
        energy=0.05,
        hunger=0.2,
        money=50.0,
        location_type=LocationType.WORKPLACE,
    )
    assert can_work is False

    # Can sleep at home even when tired
    can_sleep = activity_catalog.can_perform(
        activity_type=ActivityType.SLEEP,
        energy=0.05,
        hunger=0.2,
        money=0.0,
        location_type=LocationType.RESIDENTIAL,
    )
    assert can_sleep is True
