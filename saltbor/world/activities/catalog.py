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
                    money_delta=0.0,
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
                    money_delta=+1.75,     # Earns wage per tick (~$28 per 4h shift)
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
