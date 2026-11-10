"""
Unit Tests for Salvadoran Environmental, Geographic, Cultural, and Socio-Economic Engine (Section 19).

Covers:
- Salvadoran Geographic & Territorial Organization (14 departments, settlements, transit routing)
- Salvadoran Climate Engine (verano, invierno, canícula, crop impact)
- Foodways & Pupusería Microenterprise Operations
- Festivities & Patron Saint Celebrations
- Cultural Heritage, Traditional Crafts, and Non-Homogeneous Stance
- Informal Commerce, Purchases 'del Diario', and 'El Fiado' Ledger
- Family Remittances, Allocation Shares, and Housing Quality
- Rural Livelihoods: Milpas, Coffee Harvest, and Fishing Trips
- Salvadoran Spanish Pragmatics: Voseo, Ustedeo, and Registers
- Historical Memory & Bounded Cohort Awareness
- Community Dynamics: ADESCO Faenas and Cuchubales
"""

import pytest
from saltbor.datasets.salvadoran import (
    SALVADORAN_DEPARTMENTS,
    SALVADORAN_SETTLEMENTS,
    SALVADORAN_GEOGRAPHIC_FEATURES,
    SALVADORAN_FOOD_CATALOG,
    SALVADORAN_FESTIVITIES,
    SALVADORAN_LEXICON,
    SalvadoranZone,
    LinguisticRegister,
)
from saltbor.world.salvadoran.geography import SalvadoranGeographyEngine
from saltbor.world.salvadoran.climate import (
    SalvadoranClimateEngine,
    SalvadoranSeason,
    SalvadoranWeatherPhenomenon,
)
from saltbor.culture.salvadoran.foodways import SalvadoranFoodwaysEngine
from saltbor.culture.salvadoran.festivities import SalvadoranFestivityEngine
from saltbor.culture.salvadoran.heritage import SalvadoranCulturalEngine
from saltbor.economy.salvadoran.informal_commerce import InformalCommerceEngine
from saltbor.economy.salvadoran.remittances import RemittanceEngine
from saltbor.economy.salvadoran.livelihoods import SalvadoranLivelihoodsEngine
from saltbor.social.language.salvadoran_spanish import SalvadoranSpanishEngine
from saltbor.knowledge.salvadoran.history import SalvadoranHistoricalMemoryEngine
from saltbor.social.salvadoran.community import ADESCOEngine


def test_salvadoran_geography_departments_and_routing():
    """Verify 14 departments, zones, features, and road friction."""
    geo = SalvadoranGeographyEngine()

    # All 14 departments present
    depts = geo.get_all_departments()
    assert len(depts) == 14
    codes = {d.code for d in depts}
    assert {"AH", "SA", "SO", "CH", "LL", "SS", "CU", "LP", "CA", "SV", "US", "SM", "MO", "LU"} == codes

    # Departments by zone
    occidental = geo.get_departments_by_zone(SalvadoranZone.OCCIDENTAL)
    assert len(occidental) == 3

    # Settlement lookups
    ss = geo.get_settlement("ss_san_salvador")
    assert ss is not None
    assert ss.is_rural is False

    taj = geo.get_settlement("so_tajcuicuitlapan")
    assert taj is not None
    assert taj.is_rural is True

    # Transit calculation
    transit = geo.calculate_transit_profile("ss_san_salvador", "so_tajcuicuitlapan", is_rainy_season=False)
    assert transit["is_accessible"] is True
    assert transit["distance_km"] > 0.0

    # Physical features
    volcanoes = geo.get_volcanoes()
    assert len(volcanoes) >= 5
    assert any("Ilamatepec" in v.name for v in volcanoes)

    # Separation of experimental nodes
    assert geo.is_real_world_settlement("ss_san_salvador") is True
    assert geo.is_real_world_settlement("saltbor_fictional_testbed") is False
    geo.register_experimental_settlement("exp_01", "Saltbor Valley", "SS")
    assert geo.is_real_world_settlement("exp_01") is False


def test_salvadoran_climate_seasons_and_crop_impact():
    """Verify dry/rainy seasonality, canícula, and causal crop impacts."""
    climate = SalvadoranClimateEngine(seed=123)

    # Dry season (Verano: January)
    snap_jan = climate.evaluate_environment(month=1, day_of_month=15)
    assert snap_jan.season == SalvadoranSeason.EPOCA_SECA_VERANO
    assert snap_jan.daily_rainfall_mm == 0.0

    # Rainy season (Invierno: June)
    snap_jun = climate.evaluate_environment(month=6, day_of_month=15)
    assert snap_jun.season == SalvadoranSeason.EPOCA_LLUVIOSA_INVIERNO
    assert snap_jun.daily_rainfall_mm > 0.0

    # Canícula intraestival (Late July)
    snap_canicula = climate.evaluate_environment(month=7, day_of_month=25)
    assert snap_canicula.is_canicular_active is True

    # Causal crop impact
    impact_maiz = climate.calculate_crop_impact(snap_canicula, "maiz")
    assert impact_maiz["yield_multiplier"] < 0.70

    # Temporal impacts
    snap_temporal = climate.evaluate_environment(
        month=10, consecutive_rainy_days=4, forced_phenomenon=SalvadoranWeatherPhenomenon.TEMPORAL_TROPICAL
    )
    assert snap_temporal.river_flooding_risk > 0.50
    assert snap_temporal.artisan_fishing_safe is False


def test_foodways_and_pupuseria_operations():
    """Verify pupusería economics, ingredient margins, and recipe transmission."""
    foodways = SalvadoranFoodwaysEngine()

    pupuseria = foodways.open_pupuseria(
        business_id="pupuseria_olocuilta",
        owner_uid="dona_adela",
        name="Pupusería El Triunfo",
        location_id="lp_olocuilta",
        dough_specialty="masa_de_arroz",
    )

    day = foodways.simulate_day_trading("pupuseria_olocuilta", demand_multiplier=1.2)
    assert day["pupusas_sold"] == 180
    assert day["net_profit_usd"] > 0.0
    assert day["owner_take_home_usd"] > day["family_helpers_share_usd"]

    # Recipe transmission
    trans = foodways.transmit_recipe_knowledge("dona_adela", "hija_karen", "pupusa_queso_loroco")
    assert trans["success"] is True
    assert trans["acquired_proficiency"] > 0.50


def test_festivities_patron_saint_and_multipliers():
    """Verify patron saint festivity organization and economic stimulation."""
    fest = SalvadoranFestivityEngine()

    event = fest.organize_festivity(
        event_id="carnaval_sm_2026",
        festivity_type_id="carnaval_san_miguel",
        location_id="sm_san_miguel",
        organizing_households=["h1", "h2", "h3"],
        community_fund_contribution=400.0,
    )
    fest.contribute_to_festivity("carnaval_sm_2026", "h4", 150.0)
    assert event.is_fully_funded is True

    summary = fest.execute_celebration("carnaval_sm_2026", local_pupuserias_count=8, artisan_vendors_count=15)
    assert summary["total_economic_turnover_usd"] > 2000.0
    assert summary["social_cohesion_index"] > 0.50


def test_cultural_crafts_and_heterogeneous_stance():
    """Verify traditional craft production and individual cultural differentiation."""
    culture = SalvadoranCulturalEngine()

    # Guatajiagua black pottery
    craft = culture.produce_craft_item("artisan_lenca", "barro_negro_guatajiagua", skill_level=0.85)
    assert craft["success"] is True
    assert craft["quality_rating"] >= 0.85
    assert craft["estimated_market_value_usd"] > 8.0

    # Non-homogeneous cultural stance
    rural_elder = culture.evaluate_individual_cultural_stance(age=72, is_rural=True, openness=0.35)
    urban_youth = culture.evaluate_individual_cultural_stance(age=19, is_rural=False, openness=0.85)

    assert rural_elder["folklore_familiarity"] > urban_youth["folklore_familiarity"]
    assert urban_youth["openness_to_cultural_innovation"] > rural_elder["openness_to_cultural_innovation"]


def test_informal_commerce_and_fiado_credit():
    """Verify daily subsistence purchasing and neighborhood store fiado ledger."""
    commerce = InformalCommerceEngine()
    store = commerce.register_corner_store("tienda_san_pedro", "Tienda San Pedro", "don_pedro", "barrio_centro")

    # Purchase del diario
    daily = commerce.purchase_del_diario("tienda_san_pedro", "cliente_jose", 2.50, ["arroz_lb", "frijol_rojo_lb"])
    assert daily["success"] is True
    assert daily["total_spent_usd"] <= 2.50

    # Request fiado
    credit = commerce.request_fiado_credit("tienda_san_pedro", "cliente_jose", 6.00, customer_reputation=0.75)
    assert credit["approved"] is True
    assert credit["new_balance_usd"] == 6.00

    # Settle debt
    settle = commerce.settle_fiado_balance("tienda_san_pedro", "cliente_jose", 6.00)
    assert settle["success"] is True
    assert settle["remaining_debt_usd"] == 0.0


def test_family_remittances_and_housing_improvement():
    """Verify monthly remittance inflows, allocation ratios, and housing quality upgrades."""
    remit = RemittanceEngine()
    remit.register_household_remittance("hogar_hernandez", monthly_amount_usd=300.0)

    res = remit.process_monthly_remittance("hogar_hernandez", current_household_cash=50.0)
    assert res["received"] is True
    assert res["remittance_amount_usd"] == 300.0
    budget = res["allocated_budget"]
    assert budget["food_and_subsistence"] == 135.0 # 45%
    assert budget["housing_construction"] == 75.0   # 25%
    assert res["new_housing_quality"] > 0.40


def test_rural_livelihoods_milpa_coffee_fishing():
    """Verify smallholder milpas, coffee picking, and artisanal fishing."""
    liv = SalvadoranLivelihoodsEngine()

    # Milpa
    liv.register_milpa("plot_01", "campesino_don_chepe", "canton_san_lucas", area_manzanas=1.0)
    harvest = liv.harvest_milpa("plot_01", weather_yield_multiplier=1.1)
    assert harvest["family_food_secure"] is True
    assert harvest["commercial_surplus_sold_quintales"] > 15.0

    # Coffee picking
    corta = liv.simulate_coffee_picking_day("cortador_juan", canastos_picked=5, pay_per_canasto_usd=2.50)
    assert corta["daily_wage_earned_usd"] == 12.50

    # Artisanal fishing
    trip = liv.simulate_artisanal_fishing_trip("pescador_tono", is_safe_sea=True)
    assert trip["success"] is True
    assert trip["net_profit_usd"] > 15.0


def test_salvadoran_spanish_pragmatics_and_voseo():
    """Verify authentic voseo, ustedeo, and sociolinguistic register selection."""
    lang = SalvadoranSpanishEngine()

    # Peer collegiate
    reg_peer = lang.determine_appropriate_register(speaker_age=28, recipient_age=29, relationship_trust=0.6)
    assert reg_peer == LinguisticRegister.COLLEGIATE_INFORMAL
    utt_peer = lang.render_greeting("paco", "luis", reg_peer)
    assert utt_peer.uses_voseo is True

    # Elder respect
    reg_elder = lang.determine_appropriate_register(speaker_age=20, recipient_age=68)
    assert reg_elder == LinguisticRegister.RESPECTFUL_ELDER
    utt_elder = lang.render_greeting("paco", "don_lucas", reg_elder)
    assert utt_elder.uses_voseo is False
    assert "usted" in utt_elder.text or "Dios" in utt_elder.text

    # Market inquiry
    inq = lang.render_market_inquiry("paco", "marchanta_rosa", item_name="quesillo")
    assert "quesillo" in inq.text


def test_historical_memory_and_cohort_bounds():
    """Verify historical memory awareness bounded by age and cohort."""
    hist = SalvadoranHistoricalMemoryEngine()

    mem_elder = hist.evaluate_historical_knowledge(age=70, is_rural=True)
    mem_youth = hist.evaluate_historical_knowledge(age=18, is_rural=False)

    m1932_elder = next(m for m in mem_elder if m["milestone_id"] == "levantamiento_1932")
    m1932_youth = next(m for m in mem_youth if m["milestone_id"] == "levantamiento_1932")
    assert m1932_elder["awareness_level"] > m1932_youth["awareness_level"]

    dolar_youth = next(m for m in mem_youth if m["milestone_id"] == "dolarizacion_2001")
    assert dolar_youth["awareness_level"] >= 0.90


def test_adesco_community_organization_and_cuchubal():
    """Verify ADESCO collective faenas and cuchubal rotating credit."""
    adesco = ADESCOEngine()

    # Faena project
    faena = adesco.create_faena_project("f_01", "Arreglo de Puente de Hamaca", "canton_rio", "reparar_puente", required_hours=12.0)
    for v in ["vol_1", "vol_2", "vol_3"]:
        adesco.contribute_labor_to_faena("f_01", v, hours_contributed=4.0)
    assert faena.is_completed is True

    # Cuchubal
    cuchubal = adesco.create_cuchubal("c_01", "Cuchubal de Amigas", "ana", ["ana", "beatriz", "clara"], contribution_usd=15.0)
    turn = adesco.execute_cuchubal_turn("c_01")
    assert turn["success"] is True
    assert turn["pot_received_usd"] == 45.0
