"""Human Activity Catalog for SALTBOR Universal Domain Simulation.

Defines the comprehensive multi-domain activity repertoire for synthetic humans:
- Food & Gastronomy
- Commerce & Retail
- Education & Learning
- Healthcare & Prevention
- Transportation & Mobility
- Agriculture & Livelihood

Activities are affected by individual characteristics, needs, knowledge,
preferences, resources, relationships, geography, and environmental conditions.
No deterministic scripts: agents can refuse, postpone, browse without buying,
or choose alternative options.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from saltbor.core.types import ActivityType
from saltbor.domain.models import (
    ActivityCategory,
    ActivityEffectSpec,
    ActivityRequirementSpec,
    DomainActivity,
)
from saltbor.world.activities.catalog import ActivityCatalog

logger = logging.getLogger(__name__)


class HumanActivityCatalog:
    """Master catalog describing multi-domain activities synthetic humans can perform."""

    def __init__(self, core_catalog: Optional[ActivityCatalog] = None) -> None:
        self.core_catalog = core_catalog or ActivityCatalog()
        self._activities: Dict[str, DomainActivity] = {}
        self._activities_by_domain: Dict[str, List[str]] = {}
        self._activities_by_category: Dict[ActivityCategory, List[str]] = {cat: [] for cat in ActivityCategory}
        self._register_default_domain_activities()

    def register(self, activity: DomainActivity) -> None:
        """Register a domain-specific activity."""
        self._activities[activity.activity_id] = activity
        self._activities_by_domain.setdefault(activity.domain_id, []).append(activity.activity_id)
        self._activities_by_category.setdefault(activity.category, []).append(activity.activity_id)

    def get(self, activity_id: str) -> Optional[DomainActivity]:
        """Retrieve a domain activity definition by ID."""
        return self._activities.get(activity_id)

    def get_by_domain(self, domain_id: str) -> List[DomainActivity]:
        """Retrieve all activities associated with a domain."""
        act_ids = self._activities_by_domain.get(domain_id, [])
        return [self._activities[aid] for aid in act_ids if aid in self._activities]

    def get_by_category(self, category: ActivityCategory) -> List[DomainActivity]:
        """Retrieve all activities under a given high-level category."""
        act_ids = self._activities_by_category.get(category, [])
        return [self._activities[aid] for aid in act_ids if aid in self._activities]

    def list_all(self) -> List[DomainActivity]:
        """Return all registered activities."""
        return list(self._activities.values())

    def can_perform(
        self,
        activity_id: str,
        energy: float,
        hunger: float,
        money: float,
        facility_type: Optional[str] = None,
        skills: Optional[Dict[str, float]] = None,
    ) -> bool:
        """Check whether an individual satisfies baseline requirements for an activity."""
        activity = self.get(activity_id)
        if not activity:
            return False

        req = activity.requirements
        if energy < req.min_energy:
            return False
        if hunger > req.max_hunger and activity.category != ActivityCategory.FOOD:
            return False
        if money < req.min_money:
            return False
        if req.required_facility_type and facility_type != req.required_facility_type:
            return False
        if req.required_skills and skills:
            for s_name, s_min in req.required_skills.items():
                if skills.get(s_name, 0.0) < s_min:
                    return False

        return True

    def _register_default_domain_activities(self) -> None:
        """Register the comprehensive set of required multi-domain human activities."""

        # ---------------------------------------------------------------------
        # 1. FOOD & GASTRONOMY ACTIVITIES
        # ---------------------------------------------------------------------
        self.register(
            DomainActivity(
                activity_id="food.buy_food",
                name="Comprar Alimentos / Mercadería",
                category=ActivityCategory.FOOD,
                domain_id="food_gastronomy",
                description="Visits a market, grocery store, or vendor to purchase raw food supplies.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.10, min_money=2.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, hunger_delta=0.01, money_delta=-2.50),
                context_tags=["groceries", "market", "nutrition"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="food.prepare_meals",
                name="Preparar Comida en el Hogar",
                category=ActivityCategory.FOOD,
                domain_id="food_gastronomy",
                description="Prepares home-cooked meals using available pantry inventory.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.15, max_hunger=0.90),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.04, hunger_delta=-0.25, money_delta=0.0),
                context_tags=["home", "cooking", "family"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="food.eat_outside",
                name="Comer en la Calle / Puesto Callejero",
                category=ActivityCategory.FOOD,
                domain_id="food_gastronomy",
                description="Purchases and consumes ready-to-eat street food quickly.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.05, min_money=1.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=0.05, hunger_delta=-0.35, money_delta=-1.50),
                context_tags=["street_food", "quick_eat"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="food.visit_restaurant",
                name="Visitar Pupusería o Restaurante",
                category=ActivityCategory.FOOD,
                domain_id="food_gastronomy",
                description="Dines at a sit-down establishment, pupusería, or eatery for leisure and meal.",
                default_duration_ticks=3,
                requirements=ActivityRequirementSpec(min_energy=0.10, min_money=3.50),
                effects_per_tick=ActivityEffectSpec(energy_delta=0.08, hunger_delta=-0.30, social_delta=0.15, money_delta=-2.00),
                context_tags=["pupuseria", "restaurant", "dining", "social"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="food.compare_prices",
                name="Cotizar Precios de Comida",
                category=ActivityCategory.FOOD,
                domain_id="food_gastronomy",
                description="Checks multiple stalls or menus before deciding whether or where to buy.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.10),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.01, hunger_delta=0.01),
                context_tags=["price_comparison", "consumer_search"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="food.recommend_establishment",
                name="Recomendar Establecimiento Culinario",
                category=ActivityCategory.FOOD,
                domain_id="food_gastronomy",
                description="Shares word-of-mouth dining recommendations with friends and neighbors.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.10),
                effects_per_tick=ActivityEffectSpec(social_delta=0.10),
                context_tags=["social_proof", "reputation", "word_of_mouth"],
            )
        )

        # ---------------------------------------------------------------------
        # 2. COMMERCE & RETAIL ACTIVITIES
        # ---------------------------------------------------------------------
        self.register(
            DomainActivity(
                activity_id="commerce.open_business",
                name="Abrir / Operar Negocio Propio",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Opens a commercial store or service facility to attend customers.",
                default_duration_ticks=8,
                requirements=ActivityRequirementSpec(min_energy=0.20, min_money=10.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.03, money_delta=4.00, skill_gains={"commerce": 0.05}),
                context_tags=["entrepreneurship", "retail", "working"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.look_for_products",
                name="Buscar Productos en el Mercado",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Searches for specific goods across commercial districts.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.10),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02),
                context_tags=["search", "shopping"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.browse_without_buying",
                name="Mirar Vitrinas / Consultar sin Comprar",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Enters a commercial establishment, browses merchandise, and departs without buying.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.05),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.01),
                context_tags=["browsing", "window_shopping", "non_purchase"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.purchasing",
                name="Realizar Compra Comercial",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Completes a cash or credit purchase for goods or domestic supplies.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.05, min_money=5.0),
                effects_per_tick=ActivityEffectSpec(money_delta=-10.00, social_delta=0.02),
                context_tags=["transaction", "retail_buying"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.negotiating",
                name="Regatear / Negociar Condiciones",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Engages in price negotiation or credit terms (*fiado*) with a merchant.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.10),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, social_delta=0.05),
                context_tags=["bargaining", "fiado", "informal_credit"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.seek_employment",
                name="Buscar Trabajo / Ofrecer Servicios",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Applies for job vacancies or seeks day-labor opportunities in commercial hubs.",
                default_duration_ticks=4,
                requirements=ActivityRequirementSpec(min_energy=0.20),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.04),
                context_tags=["labor", "job_search", "livelihood"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.work",
                name="Jornada Laboral / Trabajo",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Performs contracted or informal labor shifts in exchange for wages.",
                default_duration_ticks=8,
                requirements=ActivityRequirementSpec(min_energy=0.25),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.05, hunger_delta=0.03, money_delta=2.50),
                context_tags=["employment", "wage_labor"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="commerce.change_suppliers",
                name="Cambiar de Proveedor Comercial",
                category=ActivityCategory.COMMERCE,
                domain_id="commerce_retail",
                description="Evaluates wholesale suppliers and establishes new commercial terms.",
                default_duration_ticks=3,
                requirements=ActivityRequirementSpec(min_energy=0.15, min_money=20.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.03),
                context_tags=["supply_chain", "business_operations"],
            )
        )

        # ---------------------------------------------------------------------
        # 3. EDUCATION ACTIVITIES
        # ---------------------------------------------------------------------
        self.register(
            DomainActivity(
                activity_id="education.attend_school",
                name="Asistir a Clases / Escuela",
                category=ActivityCategory.EDUCATION,
                domain_id="education",
                description="Attends structured schooling sessions at elementary, secondary, or university facilities.",
                default_duration_ticks=6,
                requirements=ActivityRequirementSpec(min_energy=0.15, max_hunger=0.85),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.03, social_delta=0.08, skill_gains={"academic": 0.08}),
                context_tags=["school", "classes", "youth", "attendance"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="education.studying",
                name="Estudiar / Realizar Tareas",
                category=ActivityCategory.EDUCATION,
                domain_id="education",
                description="Engages in self-directed study, homework, or research.",
                default_duration_ticks=4,
                requirements=ActivityRequirementSpec(min_energy=0.15),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, skill_gains={"academic": 0.05}),
                context_tags=["homework", "study", "intellectual"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="education.abandon_studies",
                name="Deserción Escolar / Abandonar Estudios",
                category=ActivityCategory.EDUCATION,
                domain_id="education",
                description="Discontinues formal educational enrollment due to economic, distance, or family pressure.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.05),
                effects_per_tick=ActivityEffectSpec(social_delta=-0.10),
                context_tags=["dropout", "economic_stress", "vulnerability"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="education.return_to_education",
                name="Reincorporarse a la Educación",
                category=ActivityCategory.EDUCATION,
                domain_id="education",
                description="Re-enrolls in formal schooling, adult literacy, or evening degree programs.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.20, min_money=5.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, social_delta=0.15),
                context_tags=["re-enrollment", "lifelong_learning"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="education.seek_training",
                name="Buscar Capacitación Técnica",
                category=ActivityCategory.EDUCATION,
                domain_id="education",
                description="Participates in vocational training (ITCA, INSAFORP) to acquire practical trade skills.",
                default_duration_ticks=4,
                requirements=ActivityRequirementSpec(min_energy=0.20, min_money=3.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.04, skill_gains={"vocational": 0.12}),
                context_tags=["technical_training", "insaforp", "vocational"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="education.teaching",
                name="Impartir Clases / Docencia",
                category=ActivityCategory.EDUCATION,
                domain_id="education",
                description="Teaches students in formal schools or community tutoring sessions.",
                default_duration_ticks=6,
                requirements=ActivityRequirementSpec(min_energy=0.25),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.04, money_delta=2.80, social_delta=0.10),
                context_tags=["teaching", "pedagogy", "employment"],
            )
        )

        # ---------------------------------------------------------------------
        # 4. HEALTHCARE & SOCIAL SERVICES ACTIVITIES
        # ---------------------------------------------------------------------
        self.register(
            DomainActivity(
                activity_id="health.seek_medical_attention",
                name="Buscar Atención Médica / Consulta",
                category=ActivityCategory.HEALTH,
                domain_id="healthcare",
                description="Visits a clinic, health unit (Unidad de Salud), or hospital for acute symptoms.",
                default_duration_ticks=4,
                requirements=ActivityRequirementSpec(min_energy=0.05, min_money=0.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, health_delta=0.08, money_delta=-1.0),
                context_tags=["clinical_consultation", "unidad_de_salud", "treatment"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="health.delay_treatment",
                name="Postergar Tratamiento por Recursos o Distancia",
                category=ActivityCategory.HEALTH,
                domain_id="healthcare",
                description="Decides to endure illness and defer clinical care due to transport cost, waiting time, or lack of funds.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.0),
                effects_per_tick=ActivityEffectSpec(health_delta=-0.02),
                context_tags=["treatment_delay", "health_barrier", "economic_rationing"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="health.attend_preventive",
                name="Asistir a Control Preventivo / Vacunación",
                category=ActivityCategory.HEALTH,
                domain_id="healthcare",
                description="Attends preventive checkups, prenatal care, or immunization campaigns.",
                default_duration_ticks=3,
                requirements=ActivityRequirementSpec(min_energy=0.10),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.01, health_delta=0.05),
                context_tags=["prevention", "vaccination", "checkup"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="health.provide_care",
                name="Brindar Cuidados a Familiar Enfermo",
                category=ActivityCategory.HEALTH,
                domain_id="healthcare",
                description="Provides domestic caregiving and nursing to sick or elderly family members.",
                default_duration_ticks=6,
                requirements=ActivityRequirementSpec(min_energy=0.15),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.04, social_delta=0.15),
                context_tags=["caregiving", "family_care", "domestic_support"],
            )
        )

        # ---------------------------------------------------------------------
        # 5. TRANSPORTATION & MOBILITY ACTIVITIES
        # ---------------------------------------------------------------------
        self.register(
            DomainActivity(
                activity_id="transport.commuting",
                name="Desplazarse en Transporte Público / Colectivo",
                category=ActivityCategory.TRANSPORTATION,
                domain_id="transportation",
                description="Commutes along urban or rural bus routes (*bus/microbús*).",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.05, min_money=0.25),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, money_delta=-0.15),
                context_tags=["bus", "commute", "transit"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="transport.route_choice",
                name="Elegir Ruta o Modalidad de Viaje",
                category=ActivityCategory.TRANSPORTATION,
                domain_id="transportation",
                description="Assesses travel time, congestion, and safety to choose a transit path.",
                default_duration_ticks=1,
                requirements=ActivityRequirementSpec(min_energy=0.05),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.01),
                context_tags=["navigation", "modal_split"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="transport.waiting_transit",
                name="Esperar Transporte en Parada",
                category=ActivityCategory.TRANSPORTATION,
                domain_id="transportation",
                description="Waits at bus stop for delayed transit lines or overcrowded units.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.05),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02),
                context_tags=["waiting_time", "transit_delay"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="transport.respond_service_interruption",
                name="Reaccionar a Bloqueo de Carretera / Interrupción",
                category=ActivityCategory.TRANSPORTATION,
                domain_id="transportation",
                description="Adapts travel itinerary due to road obstruction, landslide, or service suspension.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.05),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.03),
                context_tags=["disruption", "detour", "resilience"],
            )
        )

        # ---------------------------------------------------------------------
        # 6. AGRICULTURE & LIVELIHOOD ACTIVITIES
        # ---------------------------------------------------------------------
        self.register(
            DomainActivity(
                activity_id="agriculture.planting",
                name="Siembra de Granos Básicos (Maíz / Frijol)",
                category=ActivityCategory.AGRICULTURE,
                domain_id="agriculture",
                description="Prepares soil and plants basic grain crops aligned with seasonal rainfall.",
                default_duration_ticks=8,
                requirements=ActivityRequirementSpec(min_energy=0.30, min_money=10.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.06, hunger_delta=0.04, money_delta=-1.50, skill_gains={"farming": 0.08}),
                context_tags=["planting", "milpa", "maize", "beans"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="agriculture.harvesting",
                name="Cosecha y Recolección Agrícola",
                category=ActivityCategory.AGRICULTURE,
                domain_id="agriculture",
                description="Harvests ripe agricultural crops and sorts grain for storage or market.",
                default_duration_ticks=8,
                requirements=ActivityRequirementSpec(min_energy=0.25),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.06, hunger_delta=0.03, skill_gains={"farming": 0.06}),
                context_tags=["harvest", "crops", "food_production"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="agriculture.selling_production",
                name="Vender Cosecha en Mercado Local",
                category=ActivityCategory.AGRICULTURE,
                domain_id="agriculture",
                description="Transports agricultural yield to municipal wholesale or retail markets to sell.",
                default_duration_ticks=4,
                requirements=ActivityRequirementSpec(min_energy=0.15),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.03, money_delta=5.00),
                context_tags=["crop_sales", "agricultural_commerce"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="agriculture.buying_inputs",
                name="Comprar Insumos y Fertilizantes",
                category=ActivityCategory.AGRICULTURE,
                domain_id="agriculture",
                description="Purchases seeds, fertilizer, and agricultural supplies from agroservices.",
                default_duration_ticks=2,
                requirements=ActivityRequirementSpec(min_energy=0.10, min_money=15.0),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.02, money_delta=-8.00),
                context_tags=["agroservices", "fertilizer", "seeds"],
            )
        )
        self.register(
            DomainActivity(
                activity_id="agriculture.environmental_adaptation",
                name="Adaptar Riego / Manejo por Sequía (Canícula)",
                category=ActivityCategory.AGRICULTURE,
                domain_id="agriculture",
                description="Implements soil moisture conservation and supplemental irrigation during drought.",
                default_duration_ticks=4,
                requirements=ActivityRequirementSpec(min_energy=0.20),
                effects_per_tick=ActivityEffectSpec(energy_delta=-0.04),
                context_tags=["irrigation", "canicula", "drought_resilience"],
            )
        )
