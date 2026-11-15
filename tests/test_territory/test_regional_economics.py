"""Unit tests for RegionalEconomicNetworkEngine (Phase 1.14)."""

import pytest
from saltbor.territory.models import SupplyChainRole
from saltbor.territory.regional_economics import RegionalEconomicNetworkEngine


def test_regional_economics_initialization():
    engine = RegionalEconomicNetworkEngine(random_seed=42)
    assert len(engine.nodes) >= 4
    assert len(engine.links) >= 2
    assert engine.total_currency_in_circulation_usd > 0


def test_conserved_supply_chain_trade():
    engine = RegionalEconomicNetworkEngine(random_seed=42)
    initial_cash = sum(n.cash_balance_usd for n in engine.nodes.values())

    ok, msg, tx = engine.execute_supply_chain_trade(
        buyer_id="wholesaler_tiendona_ss",
        seller_id="farm_usulutan_1",
        commodity="maiz_quintal",
        quantity_units=5,
        link_id="link_usulutan_tiendona",
        tick=10,
    )
    assert ok is True
    assert tx is not None
    assert tx.total_paid_usd > 0
    assert tx.commodity == "maiz_quintal"

    # Conserved check: total network currency remains unchanged!
    final_cash = sum(n.cash_balance_usd for n in engine.nodes.values())
    assert abs(final_cash - initial_cash) < 1e-4

    # Seller inventory decreased, buyer inventory increased
    seller = engine.get_node("farm_usulutan_1")
    buyer = engine.get_node("wholesaler_tiendona_ss")
    assert buyer.inventory_units["maiz_quintal"] >= 45


def test_echelon_price_transmission():
    engine = RegionalEconomicNetworkEngine(random_seed=42)
    
    transmission = engine.compute_echelon_price_transmission(
        farmgate_cost_usd=18.0,
        producer_id="farm_usulutan_1",
        wholesaler_id="wholesaler_tiendona_ss",
        retailer_id="tiendita_soyapango",
        commodity="maiz_quintal",
        farm_to_wholesale_link_id="link_usulutan_tiendona",
        wholesale_to_retail_link_id="link_tiendona_soyapango",
    )
    assert transmission["farmgate_cost_usd"] == 18.0
    assert transmission["wholesale_selling_price_usd"] > transmission["farmgate_cost_usd"]
    assert transmission["final_consumer_retail_price_usd"] > transmission["wholesale_selling_price_usd"]
    assert transmission["cumulative_transport_share_pct"] > 0.0


def test_daily_economic_cycle_and_solvency():
    engine = RegionalEconomicNetworkEngine(random_seed=42)
    
    # Run daily cycle
    cycle_res = engine.execute_daily_economic_cycle(tick=96)
    assert cycle_res["solvent_nodes_count"] >= 3
    assert cycle_res["total_wages_paid_usd"] > 0

    # Test bankruptcy mechanics: drain a node's cash
    tiendita = engine.get_node("tiendita_soyapango")
    tiendita.cash_balance_usd = 0.0
    tiendita.consecutive_loss_days = 2
    
    cycle_res2 = engine.execute_daily_economic_cycle(tick=192)
    assert tiendita.is_solvent is False
    assert cycle_res2["bankrupt_nodes_count"] >= 1
