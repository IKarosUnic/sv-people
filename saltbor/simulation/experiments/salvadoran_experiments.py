"""
Salvadoran Environment and Cultural Context Validation Experiments (Section 19.10).

Covers the 10 mandatory Salvadoran empirical validation experiments:
- EXP_SV_01: Urban and Rural Contextual Differences
- EXP_SV_02: Seasonal Climate and Agricultural Consequences (Canícula, Temporales)
- EXP_SV_03: Local Market, Tienda de Esquina, and 'El Fiado' Informal Commerce
- EXP_SV_04: Intergenerational Cultural and Culinary Transmission (Pupusas, Lore)
- EXP_SV_05: Regional Language Variation (Voseo, Ustedeo, Sociolinguistic Registers)
- EXP_SV_06: Family Remittances and Household Economic Transformation
- EXP_SV_07: Community Celebrations and Local Economic Multipliers (Fiestas Patronales)
- EXP_SV_08: Geographic Accessibility and Rainy Season Transit Degradation
- EXP_SV_09: Community Cooperation during Environmental Shocks (ADESCO Faena Comunal)
- EXP_SV_10: Multi-Agent Adaptation to Distinct Salvadoran Environments
"""

from __future__ import annotations
import time
from typing import Any, Optional

from saltbor.simulation.experiments.base import BaseExperiment, ExperimentConfig, ExperimentResult
from saltbor.simulation.runner import SimulationRunner
from saltbor.world.salvadoran.geography import SalvadoranGeographyEngine
from saltbor.world.salvadoran.climate import (
    SalvadoranClimateEngine,
    SalvadoranWeatherPhenomenon,
    SalvadoranSeason,
)
from saltbor.culture.salvadoran.foodways import SalvadoranFoodwaysEngine
from saltbor.culture.salvadoran.festivities import SalvadoranFestivityEngine
from saltbor.culture.salvadoran.heritage import SalvadoranCulturalEngine
from saltbor.economy.salvadoran.informal_commerce import InformalCommerceEngine
from saltbor.economy.salvadoran.remittances import RemittanceEngine
from saltbor.economy.salvadoran.livelihoods import SalvadoranLivelihoodsEngine
from saltbor.social.language.salvadoran_spanish import SalvadoranSpanishEngine, LinguisticRegister
from saltbor.knowledge.salvadoran.history import SalvadoranHistoricalMemoryEngine
from saltbor.social.salvadoran.community import ADESCOEngine


# ===========================================================================
# EXP_SV_01: Urban vs. Rural Contextual Differences
# ===========================================================================

class ExperimentSV_01_UrbanRuralDifferences(BaseExperiment):
    """Validate structural differences between urban and rural Salvadoran settlements."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_01",
            name="Urban vs. Rural Contextual Differences",
            description="Compares service levels, infrastructure, livelihoods, and market dependency between San Salvador and rural cantons.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        geo = SalvadoranGeographyEngine()

        urban = geo.get_settlement("ss_san_salvador")
        rural = geo.get_settlement("so_tajcuicuitlapan")

        assert urban is not None and rural is not None

        # Compare service levels and infrastructure
        urban_services = urban.public_services_level
        rural_services = rural.public_services_level
        assert urban_services > rural_services
        assert urban.access_road_type == "paved_highway"
        assert rural.access_road_type == "unpaved_dirt_road"

        # Compare primary livelihoods
        assert "commerce" in urban.primary_livelihood
        assert "maize" in rural.primary_livelihood or "subsistence" in rural.primary_livelihood

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_01",
            name="Urban vs. Rural Contextual Differences",
            success=True,
            summary="Demonstrated authentic territorial differentiation between metropolitan urban centers and agricultural cantons.",
            hypotheses=[
                {"hypothesis": "Urban settlements exhibit higher service access and commercial dependency", "confirmed": True},
                {"hypothesis": "Rural cantons rely on unpaved dirt roads and subsistence farming", "confirmed": True},
            ],
            metrics={
                "urban_services_level": urban_services,
                "rural_services_level": rural_services,
                "urban_road": urban.access_road_type,
                "rural_road": rural.access_road_type,
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_02: Seasonal Climate & Agricultural Consequences
# ===========================================================================

class ExperimentSV_02_SeasonalClimateAgriculture(BaseExperiment):
    """Validate causal consequences of canícula and temporales on crops."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_02",
            name="Seasonal Climate & Agricultural Consequences",
            description="Evaluates causal damage of canícula intraestival on maize and tropical temporales on beans.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        climate = SalvadoranClimateEngine(seed=42)

        # 1. Normal rainy season snapshot in June (Siembra de Primera)
        env_june = climate.evaluate_environment(month=6, day_of_month=15)
        impact_maiz_normal = climate.calculate_crop_impact(env_june, "maiz")
        assert impact_maiz_normal["yield_multiplier"] >= 1.0

        # 2. Canícula dry spell in late July
        env_canicula = climate.evaluate_environment(
            month=7, day_of_month=25, forced_phenomenon=SalvadoranWeatherPhenomenon.CANICULA_SECA
        )
        impact_maiz_canicula = climate.calculate_crop_impact(env_canicula, "maiz")
        assert impact_maiz_canicula["yield_multiplier"] < 0.70
        assert "Estrés hídrico" in impact_maiz_canicula["status_description"]

        # 3. Continuous temporal tropical (4 days of continuous rain) on beans
        env_temporal = climate.evaluate_environment(
            month=9, day_of_month=20, consecutive_rainy_days=4, forced_phenomenon=SalvadoranWeatherPhenomenon.TEMPORAL_TROPICAL
        )
        impact_frijol_temporal = climate.calculate_crop_impact(env_temporal, "frijol")
        assert impact_frijol_temporal["yield_multiplier"] <= 0.50
        assert "pudrición" in impact_frijol_temporal["status_description"] or "antracnosis" in impact_frijol_temporal["status_description"]

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_02",
            name="Seasonal Climate & Agricultural Consequences",
            success=True,
            summary="Causal agricultural consequences of Salvadoran canícula and temporales successfully validated.",
            hypotheses=[
                {"hypothesis": "Canícula intraestival causes severe moisture deficit in flowering maize", "confirmed": True},
                {"hypothesis": "Prolonged temporales induce fungal rot in bean crops", "confirmed": True},
            ],
            metrics={
                "maize_yield_normal": impact_maiz_normal["yield_multiplier"],
                "maize_yield_canicula": impact_maiz_canicula["yield_multiplier"],
                "bean_yield_temporal": impact_frijol_temporal["yield_multiplier"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_03: Local Market & 'El Fiado' Informal Commerce
# ===========================================================================

class ExperimentSV_03_LocalMarketInformalCommerce(BaseExperiment):
    """Validate informal grocery operations, purchases 'del diario', and 'el fiado' ledger."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_03",
            name="Local Market & Informal Commerce Dynamics",
            description="Validates daily subsistence cash purchases and neighborhood store informal credit (fiado).",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        commerce = InformalCommerceEngine()

        store = commerce.register_corner_store(
            store_id="tienda_la_esperanza",
            name="Tienda La Esperanza",
            owner_uid="dona_teresa",
            location_id="barrio_el_calvario",
            starting_cash=45.0,
        )

        # 1. Household with small cash conducts purchase 'del diario'
        daily_pur = commerce.purchase_del_diario(
            store_id="tienda_la_esperanza",
            customer_uid="vecina_marta",
            customer_cash=3.00,
            needed_items=["frijol_rojo_lb", "arroz_lb", "huevos_unidad", "pan_frances"],
        )
        assert daily_pur["success"] is True
        assert daily_pur["total_spent_usd"] <= 3.00
        assert "pan_frances" in daily_pur["purchased_items"]

        # 2. Emergency purchase on credit ('el fiado')
        credit_req = commerce.request_fiado_credit(
            store_id="tienda_la_esperanza",
            customer_uid="vecina_marta",
            item_amount_usd=8.50,
            customer_reputation=0.80,
        )
        assert credit_req["approved"] is True
        assert credit_req["new_balance_usd"] == 8.50

        # 3. Excessive credit request rejected
        excessive_req = commerce.request_fiado_credit(
            store_id="tienda_la_esperanza",
            customer_uid="vecina_marta",
            item_amount_usd=50.00,
            customer_reputation=0.80,
        )
        assert excessive_req["approved"] is False

        # 4. Debt settlement increases trust and credit limit
        settle = commerce.settle_fiado_balance(
            store_id="tienda_la_esperanza",
            customer_uid="vecina_marta",
            payment_amount_usd=8.50,
        )
        assert settle["success"] is True
        assert settle["remaining_debt_usd"] == 0.0
        assert settle["updated_trust_score"] > 0.80

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_03",
            name="Local Market & Informal Commerce Dynamics",
            success=True,
            summary="Validated realistic cash flow constraints and community-based informal credit accounting.",
            hypotheses=[
                {"hypothesis": "Households buy fractionally based on daily pocket money", "confirmed": True},
                {"hypothesis": "Reputation governs approval, limit, and settlement of informal debt", "confirmed": True},
            ],
            metrics={
                "daily_purchase_spent_usd": daily_pur["total_spent_usd"],
                "credit_approved_usd": credit_req["charged_usd"],
                "final_trust_score": settle["updated_trust_score"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_04: Cultural Transmission Between Generations
# ===========================================================================

class ExperimentSV_04_CulturalTransmissionGenerations(BaseExperiment):
    """Validate transmission of traditional culinary and folklore heritage across generations."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_04",
            name="Intergenerational Cultural Transmission",
            description="Transmits traditional pupusa making and oral folklore from grandmother to granddaughter.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        foodways = SalvadoranFoodwaysEngine()
        culture = SalvadoranCulturalEngine()

        # Transmission from grandmother (expert) to granddaughter (novice)
        res_pupusa = foodways.transmit_recipe_knowledge(
            teacher_uid="abuela_rosa",
            learner_uid="nieta_sofia",
            food_item_id="pupusa_revuelta",
            teacher_proficiency=0.92,
            relationship_closeness=0.90,
        )
        assert res_pupusa["success"] is True
        assert res_pupusa["acquired_proficiency"] > 0.60
        assert res_pupusa["cultural_affinity_boost"] > 0.10

        # Stance evaluation shows non-homogeneity: elder holds deep folklore memory, youth has higher openness
        stance_elder = culture.evaluate_individual_cultural_stance(age=68, is_rural=True, openness=0.4)
        stance_youth = culture.evaluate_individual_cultural_stance(age=17, is_rural=True, openness=0.8)

        assert stance_elder["folklore_familiarity"] > stance_youth["folklore_familiarity"]
        assert stance_youth["openness_to_cultural_innovation"] > stance_elder["openness_to_cultural_innovation"]
        # Both retain high culinary attachment (pupusas)
        assert stance_elder["gastronomic_attachment"] == stance_youth["gastronomic_attachment"]

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_04",
            name="Intergenerational Cultural Transmission",
            success=True,
            summary="Demonstrated authentic non-homogenized transmission of traditional skills and values.",
            hypotheses=[
                {"hypothesis": "Close familial bonds enable rapid mastery of traditional recipes", "confirmed": True},
                {"hypothesis": "Generational cohorts exhibit divergent folklore familiarity while sharing gastronomic identity", "confirmed": True},
            ],
            metrics={
                "acquired_proficiency": res_pupusa["acquired_proficiency"],
                "elder_folklore_score": stance_elder["folklore_familiarity"],
                "youth_folklore_score": stance_youth["folklore_familiarity"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_05: Regional Language Variation
# ===========================================================================

class ExperimentSV_05_RegionalLanguageVariation(BaseExperiment):
    """Validate voseo, ustedeo, and sociolinguistic register differentiation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_05",
            name="Regional Language Variation & Register Differentiation",
            description="Evaluates selection of authentic voseo, ustedeo, and rural campesino discourse.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        lang = SalvadoranSpanishEngine()

        # 1. Friends communicating in casual context -> Collegiate informal (voseo)
        reg_friends = lang.determine_appropriate_register(speaker_age=25, recipient_age=26, relationship_trust=0.7)
        utt_friends = lang.render_greeting("carlos", "roberto", reg_friends)
        assert reg_friends == LinguisticRegister.COLLEGIATE_INFORMAL
        assert utt_friends.uses_voseo is True
        assert "chero" in utt_friends.text or "estás" in utt_friends.text

        # 2. Young person speaking to elderly neighbor -> Respectful elder (strict ustedeo)
        reg_elder = lang.determine_appropriate_register(speaker_age=22, recipient_age=65, is_family=False)
        utt_elder = lang.render_greeting("sofia", "don_manuel", reg_elder)
        assert reg_elder == LinguisticRegister.RESPECTFUL_ELDER
        assert utt_elder.uses_voseo is False
        assert "usted" in utt_elder.text or "Dios" in utt_elder.text

        # 3. Community organizer calling for communal work -> Faena comunal
        utt_faena = lang.render_community_cooperation_call("lider_adesco", "vecino_juan", register=LinguisticRegister.RURAL_CAMPESINO)
        assert "faena comunal" in utt_faena.text
        assert "ADESCO" in utt_faena.text

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_05",
            name="Regional Language Variation & Register Differentiation",
            success=True,
            summary="Demonstrated natural, non-stereotypical Salvadoran communication matching contextual pragmatics.",
            hypotheses=[
                {"hypothesis": "Peer conversations adopt natural voseo and colloquial caliche", "confirmed": True},
                {"hypothesis": "Interactions with venerable elders mandate reverential ustedeo", "confirmed": True},
            ],
            metrics={
                "peer_register": reg_friends.value,
                "peer_uses_voseo": utt_friends.uses_voseo,
                "elder_register": reg_elder.value,
                "elder_uses_voseo": utt_elder.uses_voseo,
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_06: Migration & Family Remittances
# ===========================================================================

class ExperimentSV_06_MigrationRemittances(BaseExperiment):
    """Validate household economic resilience and budget transformation through remittances."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_06",
            name="Migration & Household Remittance Dynamics",
            description="Evaluates budget allocation and shock resilience for households receiving international remittances.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        remit = RemittanceEngine()

        profile = remit.register_household_remittance(
            household_id="hogar_perez",
            monthly_amount_usd=250.0,
            sender_relation="hijo_en_los_angeles",
            reliability=0.95,
        )

        initial_cash = 20.0
        # Normal monthly remittance arrival
        res_normal = remit.process_monthly_remittance("hogar_perez", current_household_cash=initial_cash)
        assert res_normal["received"] is True
        assert res_normal["remittance_amount_usd"] == 250.0
        # Verified allocation shares
        budget = res_normal["allocated_budget"]
        assert budget["food_and_subsistence"] == 112.50 # 45%
        assert budget["housing_construction"] == 62.50   # 25%
        assert res_normal["new_housing_quality"] > 0.40

        # Emergency shock remittance (crisis sends 35% extra relief)
        res_crisis = remit.process_monthly_remittance("hogar_perez", current_household_cash=res_normal["final_cash_usd"], is_emergency_crisis=True)
        assert res_crisis["remittance_amount_usd"] > 250.0

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_06",
            name="Migration & Household Remittance Dynamics",
            success=True,
            summary="Demonstrated that remittances act as essential social security, driving housing improvement and shock buffer.",
            hypotheses=[
                {"hypothesis": "Remittances fund subsistence needs while steadily improving housing quality", "confirmed": True},
                {"hypothesis": "Transnational relatives expand transfers during acute family emergencies", "confirmed": True},
            ],
            metrics={
                "monthly_transfer_usd": res_normal["remittance_amount_usd"],
                "food_allocation_usd": budget["food_and_subsistence"],
                "housing_allocation_usd": budget["housing_construction"],
                "emergency_transfer_usd": res_crisis["remittance_amount_usd"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_07: Community Celebrations & Local Economic Multipliers
# ===========================================================================

class ExperimentSV_07_PatronSaintFestivalEconomics(BaseExperiment):
    """Validate economic stimulus and social cohesion generated by patron saint celebrations."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_07",
            name="Community Celebrations & Economic Multipliers",
            description="Evaluates microenterprise revenue surges during patron saint festivities.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        fest = SalvadoranFestivityEngine()

        event = fest.organize_festivity(
            event_id="fiestas_agostinas_2026",
            festivity_type_id="fiestas_agostinas",
            location_id="san_salvador_centro",
            organizing_households=["hogar_01", "hogar_02", "hogar_03", "hogar_04"],
            community_fund_contribution=200.0,
        )

        # Community fundraising
        fest.contribute_to_festivity("fiestas_agostinas_2026", "hogar_05", 100.0)
        fest.contribute_to_festivity("fiestas_agostinas_2026", "hogar_06", 150.0)
        fest.contribute_to_festivity("fiestas_agostinas_2026", "hogar_07", 100.0)

        assert event.is_fully_funded is True

        # Execution of festivities with pupuserías and artisan stands
        outcome = fest.execute_celebration(
            event_id="fiestas_agostinas_2026",
            local_pupuserias_count=5,
            artisan_vendors_count=10,
        )

        assert outcome["total_economic_turnover_usd"] > 1500.0
        assert outcome["social_cohesion_index"] > 0.50

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_07",
            name="Community Celebrations & Economic Multipliers",
            success=True,
            summary="Celebrations stimulate local informal commerce and foster collective identity.",
            hypotheses=[
                {"hypothesis": "Festivities inject significant liquidity into micro-merchants and pupuserías", "confirmed": True},
                {"hypothesis": "Cooperative fundraising builds measurable community social cohesion", "confirmed": True},
            ],
            metrics={
                "total_turnover_usd": outcome["total_economic_turnover_usd"],
                "vendors_benefited": outcome["vendors_benefited"],
                "social_cohesion_index": outcome["social_cohesion_index"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_08: Geographic Accessibility & Road Degradation
# ===========================================================================

class ExperimentSV_08_TransportAccessibility(BaseExperiment):
    """Validate transit speed degradation on rural dirt roads during the rainy season."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_08",
            name="Geographic Accessibility & Seasonal Road Degradation",
            description="Compares travel times between paved highways and rural dirt roads during dry vs. rainy seasons.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        geo = SalvadoranGeographyEngine()

        # Route 1: Paved Highway (San Salvador to Olocuilta)
        route_paved_dry = geo.calculate_transit_profile("ss_san_salvador", "lp_olocuilta", is_rainy_season=False)
        route_paved_rain = geo.calculate_transit_profile("ss_san_salvador", "lp_olocuilta", is_rainy_season=True)
        assert route_paved_dry["is_accessible"] is True
        assert route_paved_rain["is_accessible"] is True
        # Paved highway remains fast even in rain
        assert route_paved_rain["effective_speed_kmh"] >= 40.0

        # Route 2: Steep rural dirt road (Nahuizalco to Cantón Tajcuicuitlapán)
        route_dirt_dry = geo.calculate_transit_profile("so_nahuizalco", "so_tajcuicuitlapan", is_rainy_season=False)
        route_dirt_rain = geo.calculate_transit_profile("so_nahuizalco", "so_tajcuicuitlapan", is_rainy_season=True)
        assert route_dirt_dry["is_accessible"] is True
        # Speed drops drastically due to mud
        assert route_dirt_rain["effective_speed_kmh"] < route_dirt_dry["effective_speed_kmh"]
        assert route_dirt_rain["transit_hours"] > route_dirt_dry["transit_hours"]

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_08",
            name="Geographic Accessibility & Seasonal Road Degradation",
            success=True,
            summary="Demonstrated severe seasonal friction on unpaved rural roads compared to paved highways.",
            hypotheses=[
                {"hypothesis": "Paved national highways sustain high passability in all weather", "confirmed": True},
                {"hypothesis": "Unpaved rural cantonal roads suffer steep speed penalties during rainy season", "confirmed": True},
            ],
            metrics={
                "paved_dry_hours": route_paved_dry["transit_hours"],
                "paved_rain_hours": route_paved_rain["transit_hours"],
                "dirt_dry_hours": route_dirt_dry["transit_hours"],
                "dirt_rain_hours": route_dirt_rain["transit_hours"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_09: Community Cooperation during Environmental Disruption
# ===========================================================================

class ExperimentSV_09_CommunityCooperationDisruption(BaseExperiment):
    """Validate ADESCO mobilization and collective faena to repair road damage after a storm."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_09",
            name="Community Cooperation during Environmental Disruption",
            description="Evaluates ADESCO collective faena to clear a landslide and reopen cantonal access.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        adesco = ADESCOEngine()

        # Create communal repair project
        faena = adesco.create_faena_project(
            project_id="faena_cuesta_tajcuicuitlapan",
            name="Despeje de Derrumbe en Cuesta del Cantón",
            community_id="canton_tajcuicuitlapan",
            target_problem="derrumbe_de_tierra_tras_temporal",
            required_hours=24.0, # 6 neighbors x 4 hours
        )
        assert faena.is_completed is False

        # Volunteers assemble with shovels and picks
        volunteers = ["don_manuel", "juan_perez", "carlos_bicho", "tomas_vecino", "antonio_milpero", "roberto_chero"]
        for vol in volunteers:
            adesco.contribute_labor_to_faena("faena_cuesta_tajcuicuitlapan", vol, hours_contributed=4.0)

        assert faena.is_completed is True
        assert faena.cohesion_boost > 0.50

        # Cuchubal savings circle operates alongside
        cuchubal = adesco.create_cuchubal(
            circle_id="tanda_vecinas_centro",
            name="Cuchubal Solidario de Vecinas",
            organizer_uid="dona_maria",
            member_uids=["dona_maria", "marta_pupusera", "teresa_tienda", "elena_costurera"],
            contribution_usd=10.0,
        )
        turn1 = adesco.execute_cuchubal_turn("tanda_vecinas_centro")
        assert turn1["success"] is True
        assert turn1["pot_received_usd"] == 40.0 # 4 members x $10

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_09",
            name="Community Cooperation during Environmental Disruption",
            success=True,
            summary="Demonstrated effective grassroots mobilization through ADESCO faenas and mutual aid cuchubales.",
            hypotheses=[
                {"hypothesis": "Neighbors organize collective labor to restore essential infrastructure", "confirmed": True},
                {"hypothesis": "Informal rotating credit circles provide liquidity to community households", "confirmed": True},
            ],
            metrics={
                "faena_hours_accumulated": faena.accumulated_labor_hours,
                "volunteers_count": len(faena.volunteers_registered),
                "cohesion_generated": faena.cohesion_boost,
                "cuchubal_pot_awarded_usd": turn1["pot_received_usd"],
            },
            duration_seconds=round(t_elapsed, 4),
        )


# ===========================================================================
# EXP_SV_10: Multi-Agent Adaptation to Distinct Salvadoran Environments
# ===========================================================================

class ExperimentSV_10_IndividualAdaptationEnvironments(BaseExperiment):
    """Validate divergent adaptation across highland, coastal, and urban Salvadoran environments."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_SV_10",
            name="Individual Adaptation across Salvadoran Environments",
            description="Evaluates economic resilience and coping mechanisms of a campesino, a fisherman, and an urban vendor.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        livelihoods = SalvadoranLivelihoodsEngine()
        foodways = SalvadoranFoodwaysEngine()

        # 1. Highland Campesino (Chalatenango): Milpa harvest
        milpa = livelihoods.register_milpa(
            plot_id="milpa_chalate_01",
            cultivator_uid="campesino_mardoqueo",
            location_id="canton_el_gramal",
            area_manzanas=1.0,
            is_rented=True,
        )
        # Normal harvest
        res_milpa_normal = livelihoods.harvest_milpa("milpa_chalate_01", weather_yield_multiplier=1.0)
        assert res_milpa_normal["family_food_secure"] is True
        # Drought shock harvest (canícula)
        res_milpa_drought = livelihoods.harvest_milpa("milpa_chalate_01", weather_yield_multiplier=0.45)
        # Surplus drops, domestic reserve protected first
        assert res_milpa_drought["commercial_surplus_sold_quintales"] < res_milpa_normal["commercial_surplus_sold_quintales"]

        # 2. Coastal Fisherman (Puerto El Triunfo, Usulután)
        # Safe sea day
        fish_safe = livelihoods.simulate_artisanal_fishing_trip("pescador_chemita", is_safe_sea=True)
        assert fish_safe["success"] is True
        assert fish_safe["net_profit_usd"] > 20.0
        # Storm day (vientos de norte o temporal)
        fish_storm = livelihoods.simulate_artisanal_fishing_trip("pescador_chemita", is_safe_sea=False)
        assert fish_storm["success"] is False

        # 3. Urban Pupusera (San Salvador)
        pupuseria = foodways.open_pupuseria(
            business_id="pupuseria_la_bendicion",
            owner_uid="dona_gloria",
            name="Pupusería La Bendición",
            location_id="barrio_san_jacinto",
        )
        day_sales = foodways.simulate_day_trading("pupuseria_la_bendicion", demand_multiplier=1.1)
        assert day_sales["net_profit_usd"] > 50.0

        t_elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id="EXP_SV_10",
            name="Individual Adaptation across Salvadoran Environments",
            success=True,
            summary="Demonstrated authentic environmental grounding: livelihoods respond to distinct ecological opportunities and risks.",
            hypotheses=[
                {"hypothesis": "Campesino livelihood absorbs drought through subsistence reservation", "confirmed": True},
                {"hypothesis": "Fisherman livelihood is governed by maritime weather safety", "confirmed": True},
                {"hypothesis": "Urban pupusera thrives on cash velocity and localized foot traffic", "confirmed": True},
            ],
            metrics={
                "milpa_normal_surplus": res_milpa_normal["commercial_surplus_sold_quintales"],
                "milpa_drought_surplus": res_milpa_drought["commercial_surplus_sold_quintales"],
                "fishing_safe_profit_usd": fish_safe["net_profit_usd"],
                "pupuseria_daily_profit_usd": day_sales["net_profit_usd"],
            },
            duration_seconds=round(t_elapsed, 4),
        )
