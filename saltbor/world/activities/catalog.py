"""Activity definitions and catalog for the Saltbor simulation.

Defines the requirements, durations, and physical/social/economic effects
of activities humans can engage in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.types import ActivityType, LocationType, SkillCategory, Tick


@dataclass(frozen=True)
class ActivityRequirement:
    """Preconditions required to initiate an activity."""

    min_energy: float = 0.05
    max_hunger: float = 0.95
    min_money: float = 0.0
    allowed_location_types: tuple[LocationType, ...] = ()
    required_location_resources: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivityEffect:
    """Consequences applied upon participating in or completing an activity."""

    energy_delta: float = 0.0
    hunger_delta: float = 0.0  # Positive = increases hunger, negative = reduces hunger
    social_delta: float = 0.0  # Positive = satisfies social need
    money_delta: float = 0.0   # Positive = earns money, negative = costs money
    health_delta: float = 0.0
    skill_category: Optional[SkillCategory] = None
    skill_gain: float = 0.0


@dataclass(frozen=True)
class ActivityDefinition:
    """Specification of an activity available in Saltbor."""

    activity_type: ActivityType
    name: str
    description: str
    default_duration_ticks: int  # 1 tick = 15 simulated minutes
    requirements: ActivityRequirement
    effects_per_tick: ActivityEffect
    is_interruptible: bool = True


class ActivityCatalog:
    """Master catalog of activities executable by synthetic humans."""

    def __init__(self) -> None:
        self._activities: dict[ActivityType, ActivityDefinition] = {}
        self._register_defaults()

    def register(self, definition: ActivityDefinition) -> None:
        self._activities[definition.activity_type] = definition

    def get(self, activity_type: ActivityType) -> ActivityDefinition:
        if activity_type not in self._activities:
            raise KeyError(f"Activity '{activity_type.value}' not found in catalog.")
        return self._activities[activity_type]

    def can_perform(
        self,
        activity_type: ActivityType,
        energy: float,
        hunger: float,
        money: float,
        location_type: LocationType,
    ) -> bool:
        """Check whether a human meets the baseline physical and spatial requirements."""
        defn = self.get(activity_type)
        req = defn.requirements

        if energy < req.min_energy:
            return False
        if hunger > req.max_hunger and activity_type not in (ActivityType.EAT, ActivityType.COOK):
            return False
        if money < req.min_money:
            return False
        if req.allowed_location_types and location_type not in req.allowed_location_types:
            return False

        return True

    def _register_defaults(self) -> None:
        # 1. SLEEP (Home only, restores full energy, 32 ticks = 8 hours)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SLEEP,
                name="Dormir / Descanso profundo",
                description="Restful sleep at home to restore energy and cognitive clarity.",
                default_duration_ticks=32,
                requirements=ActivityRequirement(
                    min_energy=0.0,
                    allowed_location_types=(LocationType.RESIDENTIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.035,   # +1.12 over 32 ticks (caps at 1.0)
                    hunger_delta=+0.005,   # Slightly hungry after waking up
                    social_delta=0.0,
                    money_delta=0.0,
                    health_delta=+0.002,
                ),
                is_interruptible=False,
            )
        )

        # 2. REST (Short nap or quiet break, 2 ticks = 30 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.REST,
                name="Descansar / Reposar",
                description="Brief sit-down or quiet relaxation to catch breath.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.0,
                    allowed_location_types=(
                        LocationType.RESIDENTIAL,
                        LocationType.PUBLIC_SPACE,
                        LocationType.RECREATIONAL,
                    ),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.08,
                    hunger_delta=+0.002,
                    social_delta=0.0,
                    money_delta=0.0,
                ),
            )
        )

        # 3. EAT (Meal at restaurant or home, 2 ticks = 30 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.EAT,
                name="Comer",
                description="Eating a nutritious meal to satisfy hunger and recover physical vitality.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.01,
                    allowed_location_types=(
                        LocationType.RESIDENTIAL,
                        LocationType.COMMERCIAL,
                    ),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.04,
                    hunger_delta=-0.45,    # -0.90 over 2 ticks (satisfies hunger)
                    social_delta=+0.05,
                    money_delta=-1.50,     # Small meal cost if outside
                ),
            )
        )

        # 4. COOK (Prepare food at home, 2 ticks = 30 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COOK,
                name="Cocinar",
                description="Preparing a homemade meal from household ingredients.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=-0.35,
                    social_delta=+0.02,
                    money_delta=0.0,     # Home cooking consumes pantry items; cash is spent on groceries
                    skill_category=SkillCategory.CREATIVE,
                    skill_gain=0.01,
                ),
            )
        )

        # 5. WORK (Job shift, 16 ticks = 4 hours)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.WORK,
                name="Trabajar",
                description="Productive labor at workshop, clinic, farm cooperative, or school.",
                default_duration_ticks=16,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(
                        LocationType.WORKPLACE,
                        LocationType.COMMERCIAL,
                        LocationType.EDUCATIONAL,
                    ),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.025,
                    hunger_delta=+0.012,
                    social_delta=+0.01,
                    money_delta=+0.90,     # Realistic net earnings per tick (~$14.40 per 4h shift)
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.005,
                ),
            )
        )

        # 6. STUDY (Learning, 4 ticks = 1 hour)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.STUDY,
                name="Estudiar / Aprender",
                description="Reading, studying, or attending a workshop at school or community center.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(
                        LocationType.EDUCATIONAL,
                        LocationType.PUBLIC_SPACE,
                        LocationType.RESIDENTIAL,
                    ),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.008,
                    social_delta=+0.02,
                    money_delta=0.0,
                    skill_category=SkillCategory.ACADEMIC,
                    skill_gain=0.02,
                ),
            )
        )

        # 7. SHOP (Groceries or supplies, 2 ticks = 30 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SHOP,
                name="Comprar provisiones",
                description="Visiting the market or store to buy food, tools, or supplies.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    min_money=5.0,
                    allowed_location_types=(LocationType.COMMERCIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.005,
                    social_delta=+0.03,
                    money_delta=-5.0,
                ),
            )
        )

        # 8. SOCIALIZE (Plaza, park, restaurant, 3 ticks = 45 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SOCIALIZE,
                name="Socializar / Platicar",
                description="Engaging in conversations, sharing stories, and connecting with others.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(
                        LocationType.PUBLIC_SPACE,
                        LocationType.RECREATIONAL,
                        LocationType.COMMERCIAL,
                        LocationType.RESIDENTIAL,
                    ),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.006,
                    social_delta=+0.25,    # Strongly satisfies social need
                    money_delta=0.0,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.01,
                ),
            )
        )

        # 9. EXERCISE (Park, outdoors, 3 ticks = 45 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.EXERCISE,
                name="Hacer ejercicio",
                description="Jogging, walking briskly, playing sports in the park or hills.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.30,
                    allowed_location_types=(
                        LocationType.RECREATIONAL,
                        LocationType.NATURAL,
                        LocationType.PUBLIC_SPACE,
                    ),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.05,
                    hunger_delta=+0.02,
                    social_delta=+0.05,
                    money_delta=0.0,
                    health_delta=+0.01,
                    skill_category=SkillCategory.PHYSICAL,
                    skill_gain=0.015,
                ),
            )
        )

        # 10. RELAX (Unwind, read, enjoy nature, 2 ticks = 30 mins)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.RELAX,
                name="Relajarse / Esparcimiento",
                description="Contemplation, quiet walking, sitting in the plaza or park.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.03,
                    hunger_delta=+0.004,
                    social_delta=+0.02,
                    money_delta=0.0,
                ),
            )
        )

        # 11. TRAVEL (Moving between locations, duration set dynamically by router)
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.TRAVEL,
                name="Desplazarse / Caminar",
                description="Walking across Saltbor from one location to another.",
                default_duration_ticks=1,
                requirements=ActivityRequirement(
                    min_energy=0.02,
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.008,
                    social_delta=0.0,
                    money_delta=0.0,
                ),
            )
        )

        # ---------------------------------------------------------------------
        # Phase 1.4 Civilization Integration Activities
        # ---------------------------------------------------------------------
        # 12. COMMUNITY_MEETING
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COMMUNITY_MEETING,
                name="Reunión de ADESCO / Asamblea Comunal",
                description="Participar en la asamblea vecinal, discutir obras comunitarias y votar propuestas.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RESIDENTIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.005,
                    social_delta=+0.20,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.015,
                ),
            )
        )

        # 13. COMMUNITY_PROPOSAL
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COMMUNITY_PROPOSAL,
                name="Proponer Proyecto Comunal / Faena",
                description="Formular una iniciativa comunitaria de mejora vecinal o agua potable.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RESIDENTIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.03,
                    hunger_delta=+0.005,
                    social_delta=+0.15,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.02,
                ),
            )
        )

        # 14. LITIGATE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.LITIGATE,
                name="Demanda / Litigio ante el Tribunal",
                description="Presentar una queja formal o disputa de linderos/deudas ante la autoridad judicial.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.WORKPLACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.04,
                    hunger_delta=+0.01,
                    money_delta=-1.0,
                    social_delta=-0.02,
                ),
            )
        )

        # 15. SEEK_MEDIATION
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_MEDIATION,
                name="Buscar Mediación Comunal de Conflictos",
                description="Acudir a un líder comunal o facilitador judicial para resolver pacíficamente una disputa.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RESIDENTIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.15,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.015,
                ),
            )
        )

        # 16. COMMERCE_SELL
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COMMERCE_SELL,
                name="Venta en Puesto / Tienda de Esquina",
                description="Atender clientes en la tienda o canasto del mercado vendiendo artículos del diario.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.035,
                    hunger_delta=+0.015,
                    money_delta=+3.50,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.02,
                ),
            )
        )

        # 17. COMMERCE_BUY
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COMMERCE_BUY,
                name="Compra del Diario / Abastecimiento",
                description="Comprar víveres básicos y granos en la pulpería o mercado.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=-0.15,
                    money_delta=0.0,  # Transaction managed by commerce engine to prevent double deduction
                    social_delta=+0.05,
                ),
            )
        )

        # 18. BUSINESS_CREATE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.BUSINESS_CREATE,
                name="Fundar Microempresa o Taller",
                description="Invertir capital ahorrado en registrar y abrir un nuevo emprendimiento.",
                default_duration_ticks=6,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    min_money=30.0,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.WORKPLACE, LocationType.RESIDENTIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.05,
                    money_delta=-5.0,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.03,
                ),
            )
        )

        # 19. SEEK_CREDIT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_CREDIT,
                name="Solicitar Crédito o Fiado",
                description="Solicitar un préstamo para insumos de cosecha o registrarse en el cuaderno de fiado.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.05,
                ),
            )
        )

        # 20. REPAY_DEBT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.REPAY_DEBT,
                name="Abonar Deuda o Cuota de Crédito",
                description="Pagar oportunamente el abono de la deuda o cancelar el saldo fiado.",
                default_duration_ticks=1,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    min_money=5.0,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    money_delta=-5.0,
                    social_delta=+0.10,
                ),
            )
        )

        # 21. RECEIVE_REMITTANCE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.RECEIVE_REMITTANCE,
                name="Cobrar Remesa Familiar",
                description="Retirar la transferencia económica enviada por familiares en el exterior.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    money_delta=+35.0,
                    social_delta=+0.10,
                ),
            )
        )

        # 22. TEACH_APPRENTICE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.TEACH_APPRENTICE,
                name="Enseñar a Aprendiz en Taller",
                description="Instruir a un joven en técnicas de carpintería, panadería o tejido artesanal.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.EDUCATIONAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.04,
                    money_delta=+0.75,
                    social_delta=+0.15,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.02,
                ),
            )
        )

        # 23. LEARN_TRADE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.LEARN_TRADE,
                name="Aprender Oficio con Maestro",
                description="Practicar herramientas y procesos bajo la supervisión directa del maestro de oficio.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.EDUCATIONAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.04,
                    money_delta=-0.25,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.035,
                ),
            )
        )

        # 24. CONDUCT_EXPERIMENT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.CONDUCT_EXPERIMENT,
                name="Realizar Ensayo o Experimento Empírico",
                description="Probar empíricamente una hipótesis agrícola o técnica midiendo resultados.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.NATURAL, LocationType.WORKPLACE, LocationType.EDUCATIONAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.05,
                    hunger_delta=+0.015,
                    skill_category=SkillCategory.MENTAL,
                    skill_gain=0.03,
                ),
            )
        )

        # 25. SHARE_DISCOVERY
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SHARE_DISCOVERY,
                name="Compartir Hallazgo o Saberes",
                description="Transmitir un descubrimiento o técnica validada a otros miembros de la comunidad.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.EDUCATIONAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.25,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.015,
                ),
            )
        )

        # 26. ATTEND_CELEBRATION
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.ATTEND_CELEBRATION,
                name="Asistir a Fiesta Patronal o Festival",
                description="Compartir música, gastronomía típica y danza comunitaria en las fiestas del pueblo.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RECREATIONAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.03,
                    hunger_delta=-0.10,
                    social_delta=+0.35,
                    money_delta=-1.50,
                ),
            )
        )

        # 27. ORGANIZE_EVENT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.ORGANIZE_EVENT,
                name="Organizar Celebración o Evento",
                description="Coordinar comisiones de fiesta, tarima, comida comunal y torito pinto.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RESIDENTIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.05,
                    social_delta=+0.20,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.02,
                ),
            )
        )

        # 28. SEEK_EMPLOYMENT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_EMPLOYMENT,
                name="Buscar Empleo o Jornal",
                description="Preguntar por trabajo en talleres, fincas agrícolas o tiendas comerciales.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.WORKPLACE, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.04,
                    hunger_delta=+0.015,
                ),
            )
        )

        # 29. NEGOTIATE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.NEGOTIATE,
                name="Negociar Términos o Precios",
                description="Llegar a un acuerdo sobre precios, cuotas de arriendo o repartición de cosechas.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.05,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.015,
                ),
            )
        )

        # 30. COOPERATE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COOPERATE,
                name="Colaborar en Faena de Ayuda Mutua",
                description="Trabajo conjunto entre vecinos para construir o reparar una vivienda o camino.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RESIDENTIAL, LocationType.NATURAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.06,
                    hunger_delta=+0.02,
                    social_delta=+0.30,
                    skill_category=SkillCategory.PHYSICAL,
                    skill_gain=0.02,
                ),
            )
        )

        # 31. MIGRATE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.MIGRATE,
                name="Migrar a Otra Región o Comunidad",
                description="Trasladarse temporal o permanentemente por razones económicas o familiares.",
                default_duration_ticks=8,
                requirements=ActivityRequirement(
                    min_energy=0.30,
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.10,
                    hunger_delta=+0.04,
                    money_delta=-5.0,
                ),
            )
        )

        # -------------------------------------------------------------------
        # Phase 1.5 Everyday Life, Commercial, Labor, Housing & Leisure Activities
        # -------------------------------------------------------------------

        # 32. WINDOW_SHOPPING
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.WINDOW_SHOPPING,
                name="Ver Vitrinas / Vitrinear",
                description="Mirar productos y exhibiciones comerciales sin intención de comprar ni entrar.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    hunger_delta=+0.005,
                    social_delta=+0.02,
                    money_delta=0.0,
                ),
            )
        )

        # 33. BROWSE_STORE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.BROWSE_STORE,
                name="Curiosear en Tienda / Pulpería",
                description="Entrar a un establecimiento para inspeccionar mercadería y novedades.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.005,
                    social_delta=+0.03,
                    money_delta=0.0,
                ),
            )
        )

        # 34. COMPARE_PRICES
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COMPARE_PRICES,
                name="Comparar Precios entre Puestos",
                description="Revisar precios en diferentes locales para evaluar conveniencia y presupuesto.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.005,
                    money_delta=0.0,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.005,
                ),
            )
        )

        # 35. PURCHASE_GOODS
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.PURCHASE_GOODS,
                name="Comprar Bienes y Provisiones",
                description="Adquirir bienes, ropa o enseres según presupuesto y disponibilidad.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    min_money=0.25,
                    allowed_location_types=(LocationType.COMMERCIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    social_delta=+0.02,
                    money_delta=0.0,  # Explicitly debited in engine transaction
                ),
            )
        )

        # 36. DINE_OUT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.DINE_OUT,
                name="Comer en Comedor o Pupusería",
                description="Disfrutar de comida preparada y socializar en un establecimiento gastronómico.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.COMMERCIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.04,
                    hunger_delta=-0.35,
                    social_delta=+0.10,
                    money_delta=0.0,  # Paid at eatery transaction
                ),
            )
        )

        # 37. SEEK_ENTERTAINMENT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_ENTERTAINMENT,
                name="Entretenimiento y Recreación",
                description="Asistir a espectáculos, billares, juegos o música en la comunidad.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RECREATIONAL, LocationType.PUBLIC_SPACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.01,
                    social_delta=+0.15,
                    money_delta=0.0,
                ),
            )
        )

        # 38. VISIT_PARK
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.VISIT_PARK,
                name="Pasear o Descansar en el Parque",
                description="Caminar bajo los árboles, sentarse en bancas o disfrutar del aire libre.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.RECREATIONAL, LocationType.PUBLIC_SPACE, LocationType.NATURAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.03,
                    hunger_delta=+0.008,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 39. VISIT_FRIEND
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.VISIT_FRIEND,
                name="Visitar Amigo o Vecino",
                description="Ir a la casa de un amigo para platicar, convivir y fortalecer la amistad.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.01,
                    social_delta=+0.20,
                    money_delta=0.0,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.01,
                ),
            )
        )

        # 40. VISIT_RELATIVE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.VISIT_RELATIVE,
                name="Visita Familiar",
                description="Visitar a padres, abuelos o familiares para cuidar y compartir.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.01,
                    social_delta=+0.25,
                    money_delta=0.0,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.01,
                ),
            )
        )

        # 41. ATTEND_EVENT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.ATTEND_EVENT,
                name="Asistir a Evento o Festejo",
                description="Participar en eventos culturales, religiosos o festividades barriales.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RECREATIONAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.025,
                    hunger_delta=+0.015,
                    social_delta=+0.25,
                    money_delta=0.0,
                ),
            )
        )

        # 42. SEARCH_EMPLOYMENT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEARCH_EMPLOYMENT,
                name="Buscar Empleo u Oportunidades",
                description="Consultar vacantes en talleres, comercios y preguntar por trabajo.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.WORKPLACE, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.01,
                    social_delta=+0.05,
                    money_delta=0.0,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.005,
                ),
            )
        )

        # 43. APPLY_FOR_JOB
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.APPLY_FOR_JOB,
                name="Postular a Empleo",
                description="Presentar solicitud o candidatura ante un taller o negocio.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 44. ATTEND_INTERVIEW
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.ATTEND_INTERVIEW,
                name="Entrevista Laboral",
                description="Conversar con el empleador para evaluar idoneidad y condiciones.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.05,
                    money_delta=0.0,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.01,
                ),
            )
        )

        # 45. NEGOTIATE_SALARY
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.NEGOTIATE_SALARY,
                name="Negociar Remuneración y Horario",
                description="Pactar salario diario, destajo y condiciones de contratación.",
                default_duration_ticks=1,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    social_delta=+0.05,
                    money_delta=0.0,
                    skill_category=SkillCategory.SOCIAL,
                    skill_gain=0.01,
                ),
            )
        )

        # 46. ACCEPT_JOB
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.ACCEPT_JOB,
                name="Aceptar Empleo",
                description="Formalizar el acuerdo laboral y comenzar como empleado.",
                default_duration_ticks=1,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    social_delta=+0.10,
                    money_delta=0.0,
                ),
            )
        )

        # 47. REJECT_JOB
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.REJECT_JOB,
                name="Rechazar Oferta Laboral",
                description="Declinar una propuesta por salario insuficiente o condiciones desfavorables.",
                default_duration_ticks=1,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    social_delta=+0.02,
                    money_delta=0.0,
                ),
            )
        )

        # 48. RESIGN
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.RESIGN,
                name="Renunciar al Empleo",
                description="Abandonar el puesto de trabajo por impago, mejor opción o responsabilidades familiares.",
                default_duration_ticks=1,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.WORKPLACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    social_delta=-0.02,
                    money_delta=0.0,
                ),
            )
        )

        # 49. START_BUSINESS
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.START_BUSINESS,
                name="Iniciar Emprendimiento o Taller",
                description="Abrir un negocio propio, puesto de venta o microempresa artesanal.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.25,
                    min_money=20.0,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.WORKPLACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.04,
                    hunger_delta=+0.02,
                    social_delta=+0.10,
                    money_delta=0.0,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.015,
                ),
            )
        )

        # 50. CLOSE_BUSINESS
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.CLOSE_BUSINESS,
                name="Cerrar Negocio Insolvente",
                description="Liquidar un establecimiento que no cubre costos operativos.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.WORKPLACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=-0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 51. SEEK_HOUSING
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_HOUSING,
                name="Buscar Vivienda o Cuarto de Alquiler",
                description="Preguntar por habitaciones disponibles, mesones o casas en alquiler.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    hunger_delta=+0.01,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 52. RENT_HOUSING
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.RENT_HOUSING,
                name="Arrendar Vivienda",
                description="Pactar alquiler con propietario y mudarse a la vivienda.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 53. SEEK_SHELTER
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_SHELTER,
                name="Buscar Albergue o Alojamiento Temporal",
                description="Acudir a albergue comunal o solicitar posada ante precariedad habitacional.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.RESIDENTIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.02,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 54. REQUEST_ASSISTANCE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.REQUEST_ASSISTANCE,
                name="Pedir Ayuda Familiar o Vecinal",
                description="Solicitar apoyo económico o víveres ante crisis, enfermedad o desempleo.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 55. OFFER_ASSISTANCE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.OFFER_ASSISTANCE,
                name="Brindar Ayuda Solidaria",
                description="Compartir alimentos, alojamiento o dinero con alguien en necesidad.",
                default_duration_ticks=2,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.02,
                    social_delta=+0.15,
                    money_delta=0.0,
                ),
            )
        )

        # 56. PARTICIPATE_IN_HOBBY
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.PARTICIPATE_IN_HOBBY,
                name="Practicar Afición / Pasatiempo",
                description="Bordado, jardinería, talla de madera, música o lectura personal.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.RECREATIONAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.008,
                    social_delta=+0.02,
                    money_delta=0.0,
                    skill_category=SkillCategory.CREATIVE,
                    skill_gain=0.01,
                ),
            )
        )

        # 57. PLAY_SPORT
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.PLAY_SPORT,
                name="Jugar Fútbol o Deporte Vecinal",
                description="Participar en partidos de fútbol comunales o juegos deportivos.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.25,
                    allowed_location_types=(LocationType.RECREATIONAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.06,
                    hunger_delta=+0.03,
                    social_delta=+0.20,
                    money_delta=0.0,
                    skill_category=SkillCategory.PHYSICAL,
                    skill_gain=0.02,
                ),
            )
        )

        # 58. EXPLORE_LOCATION
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.EXPLORE_LOCATION,
                name="Explorar Lugares Poco Familiares",
                description="Recorrer nuevos cantones, veredas y rincones por curiosidad personal.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.NATURAL, LocationType.ROAD),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.03,
                    hunger_delta=+0.015,
                    social_delta=+0.02,
                    money_delta=0.0,
                ),
            )
        )

        # 59. SEEK_MEDICAL_CARE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SEEK_MEDICAL_CARE,
                name="Buscar Atención Médica / Clínica",
                description="Acudir a una unidad de salud o clínica para ser atendido por enfermedad o herida.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.05,
                    allowed_location_types=(LocationType.HEALTH_FACILITY, LocationType.PUBLIC_SPACE, LocationType.COMMERCIAL),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.01,
                    hunger_delta=+0.005,
                    social_delta=+0.05,
                    money_delta=0.0,
                ),
            )
        )

        # 60. REST_RECOVER
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.REST_RECOVER,
                name="Reposo por Convalecencia",
                description="Descansar en cama para recuperar salud y aliviar síntomas de enfermedad.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.0,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.05,
                    hunger_delta=+0.008,
                    social_delta=-0.01,
                    money_delta=0.0,
                ),
            )
        )

        # 61. COURTSHIP_DATE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COURTSHIP_DATE,
                name="Cita Romántica / Salida en Pareja",
                description="Compartir una salida romántica en pupusería, parque o plaza para cultivar el vínculo amoroso.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.COMMERCIAL, LocationType.RECREATIONAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.015,
                    hunger_delta=+0.005,
                    social_delta=+0.35,
                    money_delta=-1.50,
                ),
            )
        )

        # 62. SPEND_TIME_WITH_PARTNER
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.SPEND_TIME_WITH_PARTNER,
                name="Convivencia y Tiempo en Pareja",
                description="Conversar, colaborar o descansar en el hogar junto al cónyuge o pareja.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.10,
                    allowed_location_types=(LocationType.RESIDENTIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=+0.01,
                    hunger_delta=+0.005,
                    social_delta=+0.25,
                    money_delta=0.0,
                ),
            )
        )

        # 63. CARE_FOR_CHILD
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.CARE_FOR_CHILD,
                name="Cuidado y Alimentación Infantil",
                description="Atender necesidades biológicas, educativas y afectivas de los hijos menores.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.EDUCATIONAL, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.03,
                    hunger_delta=+0.01,
                    social_delta=+0.20,
                    money_delta=0.0,
                ),
            )
        )

        # 64. CARE_FOR_ELDER
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.CARE_FOR_ELDER,
                name="Asistencia a Familiar Mayor",
                description="Cuidar, alimentar y apoyar a parientes ancianos con movilidad o salud reducida.",
                default_duration_ticks=3,
                requirements=ActivityRequirement(
                    min_energy=0.15,
                    allowed_location_types=(LocationType.RESIDENTIAL,),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.025,
                    hunger_delta=+0.01,
                    social_delta=+0.15,
                    money_delta=0.0,
                ),
            )
        )

        # 65. COMMUNITY_CLEANUP
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.COMMUNITY_CLEANUP,
                name="Limpieza Comunal y Restauración",
                description="Participar en faenas voluntarias de limpieza de quebradas, caminos y fuentes de agua.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(LocationType.PUBLIC_SPACE, LocationType.NATURAL, LocationType.ROAD),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.05,
                    hunger_delta=+0.02,
                    social_delta=+0.15,
                    money_delta=0.0,
                    skill_category=SkillCategory.PHYSICAL,
                    skill_gain=0.01,
                ),
            )
        )

        # 66. REPAIR_DAMAGE
        self.register(
            ActivityDefinition(
                activity_type=ActivityType.REPAIR_DAMAGE,
                name="Reparación de Daños o Vivienda",
                description="Reparar techos, paredes o enseres dañados tras tormentas, accidentes o siniestros.",
                default_duration_ticks=4,
                requirements=ActivityRequirement(
                    min_energy=0.20,
                    allowed_location_types=(LocationType.RESIDENTIAL, LocationType.WORKPLACE, LocationType.PUBLIC_SPACE),
                ),
                effects_per_tick=ActivityEffect(
                    energy_delta=-0.05,
                    hunger_delta=+0.02,
                    social_delta=+0.05,
                    money_delta=-2.0,
                    skill_category=SkillCategory.TECHNICAL,
                    skill_gain=0.02,
                ),
            )
        )
