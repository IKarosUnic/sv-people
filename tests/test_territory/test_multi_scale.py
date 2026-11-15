"""Unit tests for MultiScaleTerritorialSimulationEngine (Phase 1.14)."""

import pytest
from saltbor.territory.models import TerritorialScale
from saltbor.territory.multi_scale import MultiScaleTerritorialSimulationEngine


def test_multi_scale_initialization():
    engine = MultiScaleTerritorialSimulationEngine()
    assert len(engine.departments) == 14
    assert len(engine.municipalities) == 44
    assert len(engine.communities) >= 262
    assert len(engine.households) >= 30
    assert len(engine.individuals) >= 90


def test_individual_hierarchy_tracing():
    engine = MultiScaleTerritorialSimulationEngine()
    sample_uid = list(engine.individuals.keys())[0]
    
    hierarchy = engine.get_individual_hierarchy(sample_uid)
    assert hierarchy is not None
    assert "level_1_individual" in hierarchy
    assert "level_2_household" in hierarchy
    assert "level_3_workplace" in hierarchy
    assert "level_4_community" in hierarchy
    assert "level_5_municipality" in hierarchy
    assert "level_6_department_national" in hierarchy
    assert hierarchy["level_6_department_national"]["country"] == "El Salvador"


def test_scale_aggregations():
    engine = MultiScaleTerritorialSimulationEngine()
    
    # Department aggregation
    dept_agg = engine.aggregate_population_by_scale(TerritorialScale.LEVEL_6_DEPARTMENT_NATIONAL)
    assert dept_agg["total_population"] == len(engine.individuals)
    assert len(dept_agg["counts_by_department"]) > 0

    # Municipality aggregation
    muni_agg = engine.aggregate_population_by_scale(TerritorialScale.LEVEL_5_MUNICIPALITY)
    assert muni_agg["total_population"] == len(engine.individuals)

    # Community aggregation
    comm_agg = engine.aggregate_population_by_scale(TerritorialScale.LEVEL_4_COMMUNITY)
    assert comm_agg["total_population"] == len(engine.individuals)

    # Household aggregation
    hh_agg = engine.aggregate_population_by_scale(TerritorialScale.LEVEL_2_HOUSEHOLD)
    assert hh_agg["total_population_in_households"] == len(engine.individuals)


def test_population_conservation_zero_duplicates():
    engine = MultiScaleTerritorialSimulationEngine()
    conserved, msg = engine.verify_population_conservation()
    assert conserved is True
    assert "strictly conserved" in msg
    assert "0 duplicates" in msg
