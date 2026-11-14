"""Unit tests for ContextualBehaviorEngine."""

import numpy as np
import pytest
from saltbor.domain.behavior import ContextualBehaviorEngine
from saltbor.domain.models import ContextualDecisionOption


def test_contextual_behavior_liquidity_elasticity():
    behavior = ContextualBehaviorEngine()
    opt_expensive = ContextualDecisionOption(
        option_id="restaurant_meal",
        activity_id="food.visit_restaurant",
        perceived_cost=6.0,
        perceived_benefit=4.0,
        distance_meters=100.0,
    )
    opt_cheap = ContextualDecisionOption(
        option_id="street_stall",
        activity_id="food.eat_outside",
        perceived_cost=1.5,
        perceived_benefit=2.5,
        distance_meters=100.0,
    )

    rng = np.random.default_rng(42)
    # Solvent consumer chooses higher quality meal
    choice_rich = behavior.choose_best_option([opt_expensive, opt_cheap], agent_money=50.0, agent_hunger=0.7, agent_energy=0.8, rng=rng)
    assert choice_rich.option_id == "restaurant_meal"

    # Liquidity-stressed consumer chooses cheaper meal
    choice_poor = behavior.choose_best_option([opt_expensive, opt_cheap], agent_money=4.0, agent_hunger=0.7, agent_energy=0.8, rng=rng)
    assert choice_poor.option_id == "street_stall"


def test_non_purchase_rationality():
    behavior = ContextualBehaviorEngine()
    vendors = [
        {"vendor_id": "v1", "name": "Fancy Cafe", "average_price": 8.0, "quality_score": 0.8, "distance_meters": 50.0},
    ]

    # Consumer with $2.00 facing $8.00 vendor decides NOT to buy
    choice = behavior.evaluate_food_vendor_choice(
        vendors=vendors,
        agent_money=2.0,
        agent_hunger=0.4,
        rng=np.random.default_rng(42),
    )
    assert choice.is_non_purchase is True
    assert choice.option_id == "walk_away_no_purchase"


def test_distance_decay_friction():
    behavior = ContextualBehaviorEngine(distance_decay_beta=0.003)
    opt_near = ContextualDecisionOption(
        option_id="near_clinic",
        activity_id="health.seek_medical_attention",
        perceived_cost=0.0,
        perceived_benefit=3.0,
        distance_meters=200.0,
    )
    opt_far = ContextualDecisionOption(
        option_id="far_clinic",
        activity_id="health.seek_medical_attention",
        perceived_cost=0.0,
        perceived_benefit=3.0,
        distance_meters=3500.0,
    )

    score_near = behavior.score_option(opt_near, agent_money=20.0, agent_hunger=0.2, agent_energy=0.7)
    score_far = behavior.score_option(opt_far, agent_money=20.0, agent_hunger=0.2, agent_energy=0.7)
    assert score_near > score_far
