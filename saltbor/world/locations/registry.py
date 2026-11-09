"""Location registry and the initial Saltbor settlement map.

Defines the spatial layout and functional properties of all initial locations
in the settlement of Saltbor.
"""

from __future__ import annotations

import math
from typing import Optional

from saltbor.core.types import ActivityType, Coordinate, LocationID, LocationType
from saltbor.world.geography.grid import BoundingBox, Position, distance
from saltbor.world.locations.models import Location, LocationSchedule


class LocationRegistry:
    """In-memory registry of all locations in the simulation world."""

    def __init__(self) -> None:
        self._locations: dict[LocationID, Location] = {}

    def register(self, location: Location) -> None:
        """Register a location. Raises ValueError if location_id already exists."""
        if location.location_id in self._locations:
            raise ValueError(f"Location '{location.location_id}' is already registered.")
        self._locations[location.location_id] = location

    def get(self, location_id: LocationID) -> Location:
        """Retrieve a location by ID. Raises KeyError if not found."""
        if location_id not in self._locations:
            raise KeyError(f"Location '{location_id}' not found.")
        return self._locations[location_id]

    def get_optional(self, location_id: LocationID) -> Optional[Location]:
        """Retrieve a location by ID, or None if not found."""
        return self._locations.get(location_id)

    def get_by_type(self, location_type: LocationType) -> list[Location]:
        """Return all locations matching the given type."""
        return [loc for loc in self._locations.values() if loc.location_type == location_type]

    def get_all(self) -> list[Location]:
        """Return all registered locations."""
        return list(self._locations.values())

    def find_nearest(
        self,
        pos: Coordinate | Position,
        location_type: Optional[LocationType] = None,
        only_open_at: Optional[int] = None,
    ) -> Optional[Location]:
        """Find the closest location to `pos`, optionally filtered by type and schedule."""
        p = Position(pos[0], pos[1]) if isinstance(pos, tuple) else pos
        candidates = self.get_by_type(location_type) if location_type else self.get_all()

        if only_open_at is not None:
            candidates = [loc for loc in candidates if loc.is_open(only_open_at)]

        if not candidates:
            return None

        return min(candidates, key=lambda loc: distance(p, Position(*loc.position)))

    @classmethod
    def create_saltbor_map(cls) -> LocationRegistry:
        """Build and populate the initial Saltbor settlement map (~500m x 500m)."""
        registry = cls()

        # -------------------------------------------------------------------
        # 1. Central Plaza (Town Heart)
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="plaza_central",
                name="Plaza Mayor de Saltbor",
                location_type=LocationType.PUBLIC_SPACE,
                position=(250.0, 250.0),
                bounding_box=BoundingBox(min_x=230.0, min_y=230.0, max_x=270.0, max_y=270.0),
                schedule=LocationSchedule(always_open=True),
                available_activities=[ActivityType.SOCIALIZE, ActivityType.RELAX, ActivityType.TRAVEL],
                capacity=60,
                description="The lively central square of Saltbor with a fountain, benches, and shade trees.",
                is_outdoor=True,
            )
        )

        # -------------------------------------------------------------------
        # 2. Commercial / Market
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="mercado_central",
                name="Mercado Municipal de Saltbor",
                location_type=LocationType.COMMERCIAL,
                position=(220.0, 280.0),
                bounding_box=BoundingBox(min_x=205.0, min_y=265.0, max_x=235.0, max_y=295.0),
                schedule=LocationSchedule(default_hours=(6, 19)),
                available_activities=[ActivityType.SHOP, ActivityType.SOCIALIZE, ActivityType.WORK],
                capacity=25,
                resources={"food_stock": 250, "goods_stock": 150},
                description="Vibrant municipal market offering fresh produce, pantry goods, and local crafts.",
                is_outdoor=False,
            )
        )

        # -------------------------------------------------------------------
        # 3. Restaurant / Dining
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="comedor_dona_maria",
                name="Comedor y Pupusería Doña María",
                location_type=LocationType.COMMERCIAL,
                position=(280.0, 260.0),
                bounding_box=BoundingBox(min_x=270.0, min_y=250.0, max_x=290.0, max_y=270.0),
                schedule=LocationSchedule(default_hours=(6, 21)),
                available_activities=[ActivityType.EAT, ActivityType.SOCIALIZE, ActivityType.WORK],
                capacity=20,
                resources={"meals_available": 100},
                description="Beloved local eatery known for hot pupusas, daily specials, and neighborly chatter.",
                is_outdoor=False,
            )
        )

        # -------------------------------------------------------------------
        # 4. Educational / School
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="escuela_comunal",
                name="Escuela Comunal de Saltbor",
                location_type=LocationType.EDUCATIONAL,
                position=(180.0, 200.0),
                bounding_box=BoundingBox(min_x=160.0, min_y=180.0, max_x=200.0, max_y=220.0),
                schedule=LocationSchedule(default_hours=(7, 16)),
                available_activities=[ActivityType.STUDY, ActivityType.SOCIALIZE, ActivityType.WORK],
                capacity=35,
                resources={"books": 80, "supplies": 50},
                description="Primary and community school with classrooms, a small library, and a courtyard.",
                is_outdoor=False,
            )
        )

        # -------------------------------------------------------------------
        # 5. Workplaces
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="taller_artesanal",
                name="Taller y Herrería El Roble",
                location_type=LocationType.WORKPLACE,
                position=(150.0, 310.0),
                bounding_box=BoundingBox(min_x=135.0, min_y=295.0, max_x=165.0, max_y=325.0),
                schedule=LocationSchedule(default_hours=(7, 17)),
                available_activities=[ActivityType.WORK, ActivityType.SOCIALIZE],
                capacity=12,
                resources={"tools": 40, "materials": 100},
                description="Carpentry, metalwork, and repair workshop serving the entire valley.",
                is_outdoor=False,
            )
        )

        registry.register(
            Location(
                location_id="cooperativa_agricola",
                name="Cooperativa Agrícola Saltbor",
                location_type=LocationType.WORKPLACE,
                position=(360.0, 320.0),
                bounding_box=BoundingBox(min_x=340.0, min_y=300.0, max_x=380.0, max_y=340.0),
                schedule=LocationSchedule(default_hours=(6, 17)),
                available_activities=[ActivityType.WORK, ActivityType.SHOP, ActivityType.SOCIALIZE],
                capacity=18,
                resources={"grain": 200, "fertilizer": 60},
                description="Agricultural hub managing farming supplies, crop storage, and field dispatch.",
                is_outdoor=False,
            )
        )

        registry.register(
            Location(
                location_id="clinica_salud",
                name="Clínica y Puesto de Salud",
                location_type=LocationType.WORKPLACE,
                position=(310.0, 190.0),
                bounding_box=BoundingBox(min_x=295.0, min_y=175.0, max_x=325.0, max_y=205.0),
                schedule=LocationSchedule(default_hours=(7, 19)),
                available_activities=[ActivityType.WORK, ActivityType.RELAX, ActivityType.REST],
                capacity=15,
                resources={"medical_supplies": 80},
                description="Community health post providing outpatient care, basic first aid, and wellness checks.",
                is_outdoor=False,
            )
        )

        # -------------------------------------------------------------------
        # 6. Recreational / Park & Community
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="parque_la_ceiba",
                name="Parque Ecológico La Ceiba",
                location_type=LocationType.RECREATIONAL,
                position=(240.0, 150.0),
                bounding_box=BoundingBox(min_x=210.0, min_y=120.0, max_x=270.0, max_y=180.0),
                schedule=LocationSchedule(default_hours=(5, 22)),
                available_activities=[ActivityType.EXERCISE, ActivityType.RELAX, ActivityType.SOCIALIZE],
                capacity=50,
                description="Shaded community park with walking trails, a century-old ceiba tree, and a soccer field.",
                is_outdoor=True,
            )
        )

        registry.register(
            Location(
                location_id="casa_comunal",
                name="Casa Comunal y Centro Social",
                location_type=LocationType.PUBLIC_SPACE,
                position=(210.0, 210.0),
                bounding_box=BoundingBox(min_x=195.0, min_y=195.0, max_x=225.0, max_y=225.0),
                schedule=LocationSchedule(default_hours=(8, 22)),
                available_activities=[ActivityType.SOCIALIZE, ActivityType.RELAX, ActivityType.STUDY],
                capacity=40,
                description="Community center for meetings, cultural workshops, and celebrations.",
                is_outdoor=False,
            )
        )

        # -------------------------------------------------------------------
        # 7. Residential Houses (Housing the 20 individuals)
        # -------------------------------------------------------------------
        houses_data = [
            ("casa_norte_1", "Casa Barrio El Calvario 1", (230.0, 390.0), 5),
            ("casa_norte_2", "Casa Barrio El Calvario 2", (270.0, 400.0), 5),
            ("casa_sur_1", "Casa Barrio La Esperanza 1", (160.0, 110.0), 5),
            ("casa_sur_2", "Casa Barrio La Esperanza 2", (290.0, 100.0), 5),
            ("casa_este_1", "Casa Colonia Los Almendros 1", (410.0, 240.0), 5),
            ("casa_oeste_1", "Casa Colonia San José 1", (90.0, 260.0), 5),
        ]

        for hid, hname, hpos, hcap in houses_data:
            registry.register(
                Location(
                    location_id=hid,
                    name=hname,
                    location_type=LocationType.RESIDENTIAL,
                    position=hpos,
                    bounding_box=BoundingBox(
                        min_x=hpos[0] - 12.0, min_y=hpos[1] - 12.0,
                        max_x=hpos[0] + 12.0, max_y=hpos[1] + 12.0
                    ),
                    schedule=LocationSchedule(always_open=True),
                    available_activities=[
                        ActivityType.SLEEP, ActivityType.REST,
                        ActivityType.EAT, ActivityType.COOK,
                        ActivityType.RELAX, ActivityType.SOCIALIZE,
                    ],
                    capacity=hcap,
                    resources={"food_pantry": 30},
                    description=f"Family residential house in Saltbor ({hname}).",
                    is_outdoor=False,
                )
            )

        # -------------------------------------------------------------------
        # 8. Natural Surroundings
        # -------------------------------------------------------------------
        registry.register(
            Location(
                location_id="bosque_colinas",
                name="Colinas y Sendero del Río",
                location_type=LocationType.NATURAL,
                position=(440.0, 420.0),
                bounding_box=BoundingBox(min_x=390.0, min_y=370.0, max_x=490.0, max_y=470.0),
                schedule=LocationSchedule(default_hours=(5, 18)),
                available_activities=[ActivityType.EXERCISE, ActivityType.RELAX],
                capacity=100,
                description="Scenic forested hills along the river with birdwatching and natural paths.",
                is_outdoor=True,
            )
        )

        return registry
