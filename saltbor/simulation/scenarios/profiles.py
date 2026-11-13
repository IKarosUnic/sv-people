"""Configurable Civilization Scenario Profiles for SALTBOR Phase 1.4.

Defines 6 scalable community profiles rooted in authentic Salvadoran geography and demographics:
1. MICRO_COMMUNITY: 20 individuals, 1 neighborhood hamlet (Barrio San Esteban / Centro Histórico).
2. SMALL_COMMUNITY: 100 individuals, rural cantón / agricultural village.
3. URBAN_NEIGHBORHOOD: 300 individuals, historic commercial barrio (El Calvario / La Vega).
4. URBAN_DISTRICT: 1,000 individuals, AMSS municipality district (D.L. 762).
5. CITY_SCALE: 10,000 individuals, Metropolitan San Salvador (AMSS).
6. REGIONAL_SCALE: 100,000 individuals, national territory macro-scale.

Each profile defines:
- Population numbers (persistent and active budget)
- Geographic boundary and area
- Household structure and distribution
- Occupation distribution
- Economic cash baselines and informal business setup
- Community structures (ADESCOs, cooperatives, tienditas, workshops)
- Multi-tier LOD distribution
- Simulation scheduler profile (frequency and tick budgets)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ScenarioProfileType(str, Enum):
    MICRO_COMMUNITY = "micro_community"
    SMALL_COMMUNITY = "small_community"
    URBAN_NEIGHBORHOOD = "urban_neighborhood"
    URBAN_DISTRICT = "urban_district"
    CITY_SCALE = "city_scale"
    REGIONAL_SCALE = "regional_scale"


@dataclass(frozen=True)
class HouseholdConfig:
    count: int
    avg_size: float
    dwelling_types: tuple[str, ...] = ("adobe_y_teja", "bloque_y_lamina", "mixto_concreto")


@dataclass(frozen=True)
class OccupationDistribution:
    weights: dict[str, float]


@dataclass(frozen=True)
class EconomicProfile:
    baseline_cash_mean: float
    baseline_cash_std: float
    corner_stores_count: int
    market_stalls_count: int
    remittance_recipient_pct: float
    monthly_remittance_avg_usd: float
    cooperative_credit_active: bool = True


@dataclass(frozen=True)
class LODBudget:
    lod0_full_cognition: int       # Full individual deliberative architecture
    lod1_heuristic_routine: int    # Rule-based routine behaviors
    lod2_cohort_aggregate: int     # Statistical cohort agents
    lod3_community_aggregate: int  # Meso-level community density
    lod4_macro_regional: int       # Regional demographic pools


@dataclass(frozen=True)
class ScenarioProfile:
    profile_type: ScenarioProfileType
    name: str
    description: str
    initial_population: int
    active_population_budget: int
    geographic_area_m2: float
    center_coordinates: tuple[float, float] # (lat, lon) or local (x, y)
    households: HouseholdConfig
    occupations: OccupationDistribution
    economics: EconomicProfile
    lod_distribution: LODBudget
    scheduler_profile: dict[str, Any]

    @property
    def total_population(self) -> int:
        return self.initial_population


# -----------------------------------------------------------------------------
# 1. MICRO_COMMUNITY (Default 20 Individuals)
# -----------------------------------------------------------------------------
MICRO_COMMUNITY = ScenarioProfile(
    profile_type=ScenarioProfileType.MICRO_COMMUNITY,
    name="Micro-Comunidad Barrio San Esteban",
    description="Núcleo vecinal fundacional de 20 habitantes en el Centro Histórico de San Salvador. Cohesión alta, conocimiento mutuo total.",
    initial_population=20,
    active_population_budget=20,
    geographic_area_m2=250_000.0, # 500m x 500m
    center_coordinates=(13.6978, -89.1915),
    households=HouseholdConfig(
        count=6,
        avg_size=3.33,
        dwelling_types=("adobe_y_teja", "bloque_y_lamina"),
    ),
    occupations=OccupationDistribution(
        weights={
            "Carpintero Maestro": 0.05,
            "Cocinera y Dueña de Comedor": 0.05,
            "Joven Aprendiz de Carpintería": 0.05,
            "Profesora de Escuela": 0.05,
            "Enfermero Comunitario": 0.05,
            "Comerciante de Granos Básicos": 0.05,
            "Agricultor y Cooperativista": 0.10,
            "Estudiante Secundaria": 0.10,
            "Mecánico Soldador": 0.05,
            "Vendedora de Frutas y Verduras": 0.05,
            "Albañil Maestro de Obra": 0.05,
            "Costurera y Sastra Artesanal": 0.05,
            "Joven Bachiller y Emprendedor": 0.05,
            "Curandera y Partera Tradicional": 0.05,
            "Apicultor y Productor de Miel": 0.05,
            "Músico y Promotora Cultural": 0.05,
            "Panadero Comunal": 0.05,
            "Conductor de Microbús / Transporte": 0.05,
            "Policía Comunitario": 0.05,
            "Líder Comunal ADESCO": 0.05,
        }
    ),
    economics=EconomicProfile(
        baseline_cash_mean=110.0,
        baseline_cash_std=45.0,
        corner_stores_count=2,
        market_stalls_count=4,
        remittance_recipient_pct=0.35,
        monthly_remittance_avg_usd=250.0,
    ),
    lod_distribution=LODBudget(
        lod0_full_cognition=20,
        lod1_heuristic_routine=0,
        lod2_cohort_aggregate=0,
        lod3_community_aggregate=0,
        lod4_macro_regional=0,
    ),
    scheduler_profile={
        "ticks_per_second_target": 10,
        "perception_radius_m": 50.0,
        "deliberation_frequency": "per_tick",
    },
)

# -----------------------------------------------------------------------------
# 2. SMALL_COMMUNITY (100 Individuals)
# -----------------------------------------------------------------------------
SMALL_COMMUNITY = ScenarioProfile(
    profile_type=ScenarioProfileType.SMALL_COMMUNITY,
    name="Comunidad Rural / Cantón Las Flores",
    description="Población rural articulada de 100 habitantes con fuerte vocación agroecológica, ADESCO activa y círculos de cuchubales.",
    initial_population=100,
    active_population_budget=60,
    geographic_area_m2=1_000_000.0, # 1km x 1km
    center_coordinates=(13.6820, -89.2100),
    households=HouseholdConfig(
        count=26,
        avg_size=3.85,
        dwelling_types=("adobe_y_teja", "bloque_y_lamina", "bahareque"),
    ),
    occupations=OccupationDistribution(
        weights={
            "Agricultor y Cooperativista": 0.30,
            "Vendedora de Frutas y Verduras": 0.12,
            "Albañil Maestro de Obra": 0.08,
            "Cocinera y Dueña de Comedor": 0.06,
            "Estudiante Secundaria": 0.14,
            "Costurera y Sastra Artesanal": 0.06,
            "Apicultor y Productor de Miel": 0.06,
            "Profesora de Escuela": 0.04,
            "Enfermero Comunitario": 0.04,
            "Comerciante de Granos Básicos": 0.05,
            "Líder Comunal ADESCO": 0.05,
        }
    ),
    economics=EconomicProfile(
        baseline_cash_mean=85.0,
        baseline_cash_std=35.0,
        corner_stores_count=4,
        market_stalls_count=8,
        remittance_recipient_pct=0.45,
        monthly_remittance_avg_usd=220.0,
    ),
    lod_distribution=LODBudget(
        lod0_full_cognition=40,
        lod1_heuristic_routine=60,
        lod2_cohort_aggregate=0,
        lod3_community_aggregate=0,
        lod4_macro_regional=0,
    ),
    scheduler_profile={
        "ticks_per_second_target": 25,
        "perception_radius_m": 75.0,
        "deliberation_frequency": "staggered",
    },
)

# -----------------------------------------------------------------------------
# 3. URBAN_NEIGHBORHOOD (300 Individuals)
# -----------------------------------------------------------------------------
URBAN_NEIGHBORHOOD = ScenarioProfile(
    profile_type=ScenarioProfileType.URBAN_NEIGHBORHOOD,
    name="Barrio Urbano El Calvario y La Vega",
    description="Barrio urbano tradicional de 300 habitantes con intensa actividad mercantil, talleres de oficio y dinámicas de vecindad densa.",
    initial_population=300,
    active_population_budget=100,
    geographic_area_m2=2_250_000.0, # 1.5km x 1.5km
    center_coordinates=(13.6950, -89.1920),
    households=HouseholdConfig(
        count=82,
        avg_size=3.65,
        dwelling_types=("bloque_y_lamina", "mixto_concreto", "adobe_y_teja"),
    ),
    occupations=OccupationDistribution(
        weights={
            "Vendedora de Frutas y Verduras": 0.20,
            "Comerciante de Granos Básicos": 0.12,
            "Albañil Maestro de Obra": 0.10,
            "Carpintero Maestro": 0.08,
            "Mecánico Soldador": 0.08,
            "Cocinera y Dueña de Comedor": 0.08,
            "Conductor de Microbús / Transporte": 0.08,
            "Costurera y Sastra Artesanal": 0.06,
            "Estudiante Secundaria": 0.10,
            "Profesora de Escuela": 0.04,
            "Policía Comunitario": 0.03,
            "Líder Comunal ADESCO": 0.03,
        }
    ),
    economics=EconomicProfile(
        baseline_cash_mean=125.0,
        baseline_cash_std=55.0,
        corner_stores_count=8,
        market_stalls_count=24,
        remittance_recipient_pct=0.40,
        monthly_remittance_avg_usd=280.0,
    ),
    lod_distribution=LODBudget(
        lod0_full_cognition=50,
        lod1_heuristic_routine=150,
        lod2_cohort_aggregate=100,
        lod3_community_aggregate=0,
        lod4_macro_regional=0,
    ),
    scheduler_profile={
        "ticks_per_second_target": 40,
        "perception_radius_m": 40.0,
        "deliberation_frequency": "hierarchical",
    },
)

# -----------------------------------------------------------------------------
# 4. URBAN_DISTRICT (1,000 Individuals)
# -----------------------------------------------------------------------------
URBAN_DISTRICT = ScenarioProfile(
    profile_type=ScenarioProfileType.URBAN_DISTRICT,
    name="Distrito Urbano San Salvador Centro",
    description="Distrito administrativo completo con 1,000 habitantes. Múltiples barrios, mercado central, tribunal y juzgados de paz.",
    initial_population=1_000,
    active_population_budget=150,
    geographic_area_m2=6_250_000.0, # 2.5km x 2.5km
    center_coordinates=(13.6980, -89.1900),
    households=HouseholdConfig(
        count=270,
        avg_size=3.70,
        dwelling_types=("mixto_concreto", "bloque_y_lamina"),
    ),
    occupations=OccupationDistribution(
        weights={
            "Vendedora de Frutas y Verduras": 0.18,
            "Comerciante de Granos Básicos": 0.14,
            "Conductor de Microbús / Transporte": 0.10,
            "Albañil Maestro de Obra": 0.10,
            "Mecánico Soldador": 0.08,
            "Cocinera y Dueña de Comedor": 0.08,
            "Estudiante Secundaria": 0.12,
            "Profesora de Escuela": 0.05,
            "Enfermero Comunitario": 0.05,
            "Policía Comunitario": 0.04,
            "Líder Comunal ADESCO": 0.03,
            "Curandera y Partera Tradicional": 0.03,
        }
    ),
    economics=EconomicProfile(
        baseline_cash_mean=140.0,
        baseline_cash_std=65.0,
        corner_stores_count=20,
        market_stalls_count=80,
        remittance_recipient_pct=0.38,
        monthly_remittance_avg_usd=300.0,
    ),
    lod_distribution=LODBudget(
        lod0_full_cognition=60,
        lod1_heuristic_routine=240,
        lod2_cohort_aggregate=700,
        lod3_community_aggregate=0,
        lod4_macro_regional=0,
    ),
    scheduler_profile={
        "ticks_per_second_target": 60,
        "perception_radius_m": 35.0,
        "deliberation_frequency": "selective_salience",
    },
)

# -----------------------------------------------------------------------------
# 5. CITY_SCALE (10,000 Individuals)
# -----------------------------------------------------------------------------
CITY_SCALE = ScenarioProfile(
    profile_type=ScenarioProfileType.CITY_SCALE,
    name="Escala Ciudad — AMSS Metropolitano",
    description="Simulación a escala urbana de 10,000 individuos con gestión de cohortes agregadas y micro-núcleos focales interactivos.",
    initial_population=10_000,
    active_population_budget=200,
    geographic_area_m2=25_000_000.0, # 5km x 5km
    center_coordinates=(13.7000, -89.2000),
    households=HouseholdConfig(
        count=2_600,
        avg_size=3.85,
    ),
    occupations=OccupationDistribution(
        weights={
            "Vendedora de Frutas y Verduras": 0.16,
            "Comerciante de Granos Básicos": 0.14,
            "Conductor de Microbús / Transporte": 0.12,
            "Albañil Maestro de Obra": 0.10,
            "Mecánico Soldador": 0.08,
            "Cocinera y Dueña de Comedor": 0.08,
            "Estudiante Secundaria": 0.14,
            "Profesora de Escuela": 0.06,
            "Enfermero Comunitario": 0.05,
            "Policía Comunitario": 0.04,
            "Otros Oficios Urbanos": 0.03,
        }
    ),
    economics=EconomicProfile(
        baseline_cash_mean=160.0,
        baseline_cash_std=80.0,
        corner_stores_count=120,
        market_stalls_count=450,
        remittance_recipient_pct=0.35,
        monthly_remittance_avg_usd=320.0,
    ),
    lod_distribution=LODBudget(
        lod0_full_cognition=50,
        lod1_heuristic_routine=250,
        lod2_cohort_aggregate=3_700,
        lod3_community_aggregate=6_000,
        lod4_macro_regional=0,
    ),
    scheduler_profile={
        "ticks_per_second_target": 100,
        "perception_radius_m": 30.0,
        "deliberation_frequency": "gpu_frustum_culling",
    },
)

# -----------------------------------------------------------------------------
# 6. REGIONAL_SCALE (100,000 Individuals)
# -----------------------------------------------------------------------------
REGIONAL_SCALE = ScenarioProfile(
    profile_type=ScenarioProfileType.REGIONAL_SCALE,
    name="Escala Regional Nacional — El Salvador",
    description="Macro-escala nacional con 100,000 agentes modelando flujos de remesas, migración interdepartamental y corredores comerciales.",
    initial_population=100_000,
    active_population_budget=300,
    geographic_area_m2=21_000_000_000.0, # 21,041 km2
    center_coordinates=(13.7942, -88.8965),
    households=HouseholdConfig(
        count=25_000,
        avg_size=4.00,
    ),
    occupations=OccupationDistribution(
        weights={
            "Agricultura y Agroindustria": 0.28,
            "Comercio Informal y Formal": 0.24,
            "Servicios y Transporte": 0.16,
            "Construcción y Oficios": 0.12,
            "Estudiantes y Jóvenes": 0.12,
            "Sector Público y Comunitario": 0.08,
        }
    ),
    economics=EconomicProfile(
        baseline_cash_mean=135.0,
        baseline_cash_std=75.0,
        corner_stores_count=1_200,
        market_stalls_count=4_500,
        remittance_recipient_pct=0.42,
        monthly_remittance_avg_usd=310.0,
    ),
    lod_distribution=LODBudget(
        lod0_full_cognition=100,
        lod1_heuristic_routine=400,
        lod2_cohort_aggregate=15_000,
        lod3_community_aggregate=35_000,
        lod4_macro_regional=49_500,
    ),
    scheduler_profile={
        "ticks_per_second_target": 150,
        "perception_radius_m": 25.0,
        "deliberation_frequency": "regional_partition_stream",
    },
)

SCENARIO_PROFILES: dict[ScenarioProfileType, ScenarioProfile] = {
    ScenarioProfileType.MICRO_COMMUNITY: MICRO_COMMUNITY,
    ScenarioProfileType.SMALL_COMMUNITY: SMALL_COMMUNITY,
    ScenarioProfileType.URBAN_NEIGHBORHOOD: URBAN_NEIGHBORHOOD,
    ScenarioProfileType.URBAN_DISTRICT: URBAN_DISTRICT,
    ScenarioProfileType.CITY_SCALE: CITY_SCALE,
    ScenarioProfileType.REGIONAL_SCALE: REGIONAL_SCALE,
}


def get_profile(profile_type: str | ScenarioProfileType) -> ScenarioProfile:
    """Retrieve scenario profile by key or enum."""
    if isinstance(profile_type, str):
        try:
            pt = ScenarioProfileType(profile_type.lower())
        except ValueError:
            pt = ScenarioProfileType.MICRO_COMMUNITY
    else:
        pt = profile_type
    return SCENARIO_PROFILES.get(pt, MICRO_COMMUNITY)


def list_profiles_summary() -> list[dict[str, Any]]:
    """Return JSON-serializable list of all scenario profiles."""
    return [
        {
            "id": p.profile_type.value,
            "name": p.name,
            "description": p.description,
            "initial_population": p.initial_population,
            "active_budget": p.active_population_budget,
            "area_m2": p.geographic_area_m2,
            "households_count": p.households.count,
            "corner_stores_count": p.economics.corner_stores_count,
            "remittance_pct": p.economics.remittance_recipient_pct,
            "lod_breakdown": {
                "lod0": p.lod_distribution.lod0_full_cognition,
                "lod1": p.lod_distribution.lod1_heuristic_routine,
                "lod2": p.lod_distribution.lod2_cohort_aggregate,
                "lod3": p.lod_distribution.lod3_community_aggregate,
                "lod4": p.lod_distribution.lod4_macro_regional,
            },
        }
        for p in SCENARIO_PROFILES.values()
    ]
