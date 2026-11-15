"""Unit tests for PublicServiceCapacityEngine (Phase 1.14)."""

import pytest
from saltbor.territory.models import ServiceCapacityStatus, ServiceCategory
from saltbor.territory.public_services import PublicServiceCapacityEngine


def test_public_services_initialization():
    engine = PublicServiceCapacityEngine()
    assert len(engine.facilities) >= 6
    # Ensure unconfigured facility exists and capacity is None
    unconf = engine.get_facility("osm_unverified_school_cabañas")
    assert unconf is not None
    assert unconf.configured_capacity_per_day is None
    assert unconf.status == ServiceCapacityStatus.UNCONFIGURED


def test_service_demand_and_queue_overload():
    engine = PublicServiceCapacityEngine()
    fac = engine.get_facility("salud_chalatenango")
    assert fac is not None
    initial_cap = fac.configured_capacity_per_day

    # Normal demand (within capacity)
    ok, served, unmet = engine.submit_service_demand("salud_chalatenango", 30)
    assert ok is True
    assert served == 30
    assert unmet == 0
    assert fac.status == ServiceCapacityStatus.OPERATIONAL

    # Surge demand exceeding daily throughput
    ok, served2, unmet2 = engine.submit_service_demand("salud_chalatenango", 100)
    assert ok is True
    assert unmet2 > 0
    assert fac.status in (ServiceCapacityStatus.DEGRADED, ServiceCapacityStatus.OVERLOADED)
    assert fac.current_waiting_queue > 0

    # Reset queues
    engine.reset_daily_queues()
    assert fac.current_daily_demand == 0
    assert fac.current_waiting_queue == 0
    assert fac.status == ServiceCapacityStatus.OPERATIONAL


def test_spatial_accessibility_and_gaps():
    engine = PublicServiceCapacityEngine()
    
    # Near San Salvador Centro to Hospital Rosales
    acc_ss = engine.compute_community_accessibility(
        comm_lat=13.6989,
        comm_lon=-89.1914,
        category=ServiceCategory.HEALTHCARE,
    )
    assert acc_ss["has_accessible_facility"] is True
    assert acc_ss["distance_km"] < 3.0
    assert acc_ss["accessibility_index"] > 0.60

    # Remote caserío in Chalatenango
    acc_remote = engine.compute_community_accessibility(
        comm_lat=14.2500,
        comm_lon=-88.8500,
        category=ServiceCategory.HEALTHCARE,
    )
    assert acc_remote["distance_km"] > 15.0
    assert acc_remote["accessibility_index"] < acc_ss["accessibility_index"]

    # Detect infrastructure gaps
    communities = [
        {"community_id": "c1", "name": "Caserío Montaña", "latitude": 14.3000, "longitude": -88.8000, "department_code": "CH"},
        {"community_id": "c2", "name": "Barrio El Centro", "latitude": 13.6989, "longitude": -89.1914, "department_code": "SS"},
    ]
    gaps = engine.detect_infrastructure_gaps(communities, ServiceCategory.HEALTHCARE)
    assert len(gaps) >= 1
    assert gaps[0]["community_id"] == "c1"
