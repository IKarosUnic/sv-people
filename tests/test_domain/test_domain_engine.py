"""Unit tests for UniversalDomainEngine and HumanActivityCatalog."""

import pytest
from saltbor.domain.catalog import HumanActivityCatalog
from saltbor.domain.engine import UniversalDomainEngine
from saltbor.domain.models import ActivityCategory, DomainCategory, DomainDefinition, DomainStatus


def test_domain_engine_initialization():
    ude = UniversalDomainEngine(experiment_db_path=":memory:")
    domains = ude.list_domains()
    assert len(domains) >= 6
    active_ids = ude.active_domain_ids
    assert "food_gastronomy" in active_ids
    assert "commerce_retail" in active_ids
    assert "education" in active_ids
    assert "healthcare" in active_ids
    assert "transportation" in active_ids
    assert "agriculture" in active_ids


def test_custom_domain_registration_and_activation():
    ude = UniversalDomainEngine(experiment_db_path=":memory:")
    custom = DomainDefinition(
        domain_id="housing_urban",
        name="Housing and Urban Development",
        category=DomainCategory.HOUSING,
        purpose="Simulate tenancy, rent affordability, and informal settlements.",
        geographic_scope="San Salvador Metropolitan Area (AMSS)",
        resources=["housing_units", "tenancy_contracts", "construction_materials"],
        activities=["housing.rent_unit", "housing.build_dwelling"],
    )
    assert ude.register_domain(custom) is True
    assert ude.activate_domain("housing_urban") is True
    assert "housing_urban" in ude.active_domain_ids

    # Deactivation
    assert ude.deactivate_domain("housing_urban") is True
    assert "housing_urban" not in ude.active_domain_ids


def test_domain_validation_rejects_invalid_schemas():
    ude = UniversalDomainEngine(experiment_db_path=":memory:")
    invalid = DomainDefinition(domain_id="", name="", category=DomainCategory.CUSTOM, purpose="")
    errors = ude.validate_domain_configuration(invalid)
    assert len(errors) >= 3
    assert ude.register_domain(invalid) is False


def test_human_activity_catalog_retrieval_and_filtering():
    catalog = HumanActivityCatalog()
    all_acts = catalog.list_all()
    assert len(all_acts) >= 30

    food_acts = catalog.get_by_category(ActivityCategory.FOOD)
    assert len(food_acts) >= 6
    act_ids = [a.activity_id for a in food_acts]
    assert "food.buy_food" in act_ids
    assert "food.visit_restaurant" in act_ids
    assert "food.compare_prices" in act_ids

    # Check eligibility rules
    assert catalog.can_perform("food.buy_food", energy=0.5, hunger=0.5, money=10.0) is True
    assert catalog.can_perform("food.buy_food", energy=0.01, hunger=0.5, money=10.0) is False  # Too tired
    assert catalog.can_perform("food.buy_food", energy=0.5, hunger=0.5, money=0.50) is False  # Cannot afford min_money=2.0
