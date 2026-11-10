"""
Salvadoran Geographic, Cultural, and Socio-Economic Datasets.

Provides structured, verified, versioned, and locally cached reference data for:
- 14 Departments across 4 Zones (Occidental, Central, Paracentral, Oriental)
- Municipalities, Cantons, and Caseríos
- Major Physical Geography (Volcanoes, Rivers, Lakes, Mountain Ranges)
- National Road and Transit Infrastructure
- Cultural Foodways, Festivities, and Traditional Crafts
- Authentic Salvadoran Spanish Lexicon and Pragmatics
- Historical Milestones and Social Processes

Strictly separates verified real-world territorial data from fictional simulation testbeds.
All data is 100% offline and pure Python.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


class SalvadoranZone(str, Enum):
    """The four historical geographic zones of El Salvador."""
    OCCIDENTAL = "occidental"       # Ahuachapán, Santa Ana, Sonsonate
    CENTRAL = "central"             # La Libertad, Chalatenango, Cuscatlán, San Salvador
    PARACENTRAL = "paracentral"     # La Paz, Cabañas, San Vicente
    ORIENTAL = "oriental"           # Usulután, San Miguel, Morazán, La Unión


@dataclasses.dataclass(frozen=True)
class DepartmentData:
    """Territorial and geographic profile of a Salvadoran department."""
    code: str
    name: str
    zone: SalvadoranZone
    cabecera: str
    area_km2: float
    population_approx: int
    primary_economic_activities: list[str]
    typical_elevation_m: float
    climate_zone: str
    notable_geographic_features: list[str]


# The 14 official departments of the Republic of El Salvador
SALVADORAN_DEPARTMENTS: dict[str, DepartmentData] = {
    "AH": DepartmentData(
        code="AH",
        name="Ahuachapán",
        zone=SalvadoranZone.OCCIDENTAL,
        cabecera="Ahuachapán",
        area_km2=1239.6,
        population_approx=370000,
        primary_economic_activities=["coffee_cultivation", "geothermal_energy", "subsistence_agriculture", "artisan_crafts"],
        typical_elevation_m=780.0,
        climate_zone="tropical_savanna_highland",
        notable_geographic_features=["Los Ausoles", "Río Paz", "Parque Nacional El Imposible", "Laguna El Espino"],
    ),
    "SA": DepartmentData(
        code="SA",
        name="Santa Ana",
        zone=SalvadoranZone.OCCIDENTAL,
        cabecera="Santa Ana",
        area_km2=2023.2,
        population_approx=590000,
        primary_economic_activities=["coffee_processing", "commerce", "sugar_cane", "livestock", "light_manufacturing"],
        typical_elevation_m=665.0,
        climate_zone="tropical_savanna_temperate",
        notable_geographic_features=["Volcán de Santa Ana (Ilamatepec)", "Lago de Coatepeque", "Lago de Güija", "Cerro Verde"],
    ),
    "SO": DepartmentData(
        code="SO",
        name="Sonsonate",
        zone=SalvadoranZone.OCCIDENTAL,
        cabecera="Sonsonate",
        area_km2=1225.2,
        population_approx=510000,
        primary_economic_activities=["port_logistics", "sugar_refining", "coffee", "indigenous_crafts", "coastal_fishing"],
        typical_elevation_m=225.0,
        climate_zone="tropical_warm_coastal",
        notable_geographic_features=["Volcán de Izalco", "Puerto de Acajutla", "Río Sensunapán", "Ruta de Las Flores"],
    ),
    "CH": DepartmentData(
        code="CH",
        name="Chalatenango",
        zone=SalvadoranZone.CENTRAL,
        cabecera="Chalatenango",
        area_km2=2016.6,
        population_approx=205000,
        primary_economic_activities=["highland_vegetables", "dairy_cattle", "handicrafts", "remittances", "ecotourism"],
        typical_elevation_m=450.0,
        climate_zone="temperate_highland_mountain",
        notable_geographic_features=["Cerro El Pital (2730m)", "Río Lempa", "Embalse Cerrón Grande", "La Palma", "Río Sumpul"],
    ),
    "LL": DepartmentData(
        code="LL",
        name="La Libertad",
        zone=SalvadoranZone.CENTRAL,
        cabecera="Santa Tecla",
        area_km2=1652.9,
        population_approx=840000,
        primary_economic_activities=["commerce", "coastal_tourism", "surf_industry", "coffee", "services", "suburban_residential"],
        typical_elevation_m=920.0,
        climate_zone="tropical_subtropical_coastal",
        notable_geographic_features=["Cordillera del Bálsamo", "Puerto de La Libertad", "Playas El Tunco/El Zonte", "Río Lempa norte"],
    ),
    "SS": DepartmentData(
        code="SS",
        name="San Salvador",
        zone=SalvadoranZone.CENTRAL,
        cabecera="San Salvador",
        area_km2=886.2,
        population_approx=1800000,
        primary_economic_activities=["formal_commerce", "informal_markets", "financial_services", "manufacturing", "government", "telecommunications"],
        typical_elevation_m=658.0,
        climate_zone="tropical_savanna_urban",
        notable_geographic_features=["Volcán de San Salvador (Quezaltepec)", "Lago de Ilopango", "Río Acelhuate", "Cerro San Jacinto"],
    ),
    "CU": DepartmentData(
        code="CU",
        name="Cuscatlán",
        zone=SalvadoranZone.CENTRAL,
        cabecera="Cojutepeque",
        area_km2=756.2,
        population_approx=270000,
        primary_economic_activities=["traditional_cured_meats", "sugar_cane", "ceramics", "textiles", "maize_beans"],
        typical_elevation_m=850.0,
        climate_zone="tropical_savanna",
        notable_geographic_features=["Cerro de las Pavas", "Lago de Ilopango norte", "Suchitoto", "Río Lempa"],
    ),
    "LP": DepartmentData(
        code="LP",
        name="La Paz",
        zone=SalvadoranZone.PARACENTRAL,
        cabecera="Zacatecoluca",
        area_km2=1223.6,
        population_approx=375000,
        primary_economic_activities=["international_airport_hub", "pupusa_industry", "sugar_cane", "coastal_tourism", "shrimp_farming"],
        typical_elevation_m=210.0,
        climate_zone="tropical_warm_alluvial",
        notable_geographic_features=["Olocuilta", "Costa del Sol", "Estero de Jaltepeque", "Río Jiboa", "Volcán Chinchontepec falda sur"],
    ),
    "CA": DepartmentData(
        code="CA",
        name="Cabañas",
        zone=SalvadoranZone.PARACENTRAL,
        cabecera="Sensuntepeque",
        area_km2=1103.5,
        population_approx=170000,
        primary_economic_activities=["clay_pottery", "dairy_farming", "grain_subsistence", "remittances"],
        typical_elevation_m=820.0,
        climate_zone="tropical_dry_plateau",
        notable_geographic_features=["Ilobasco (cerámica tradicional)", "Embalse Cerrón Grande", "Presa 5 de Noviembre", "Río Titihuapa"],
    ),
    "SV": DepartmentData(
        code="SV",
        name="San Vicente",
        zone=SalvadoranZone.PARACENTRAL,
        cabecera="San Vicente",
        area_km2=1184.0,
        population_approx=190000,
        primary_economic_activities=["sugar_mills", "textile_weaving", "sweets_camotes", "maize_sorghum", "cattle"],
        typical_elevation_m=390.0,
        climate_zone="tropical_savanna_warm",
        notable_geographic_features=["Volcán de San Vicente (Chinchontepec)", "San Sebastián (telares de pedal)", "Río Lempa", "Río Acahuapa"],
    ),
    "US": DepartmentData(
        code="US",
        name="Usulután",
        zone=SalvadoranZone.ORIENTAL,
        cabecera="Usulután",
        area_km2=2130.4,
        population_approx=385000,
        primary_economic_activities=["coffee_highland", "basic_grains", "salt_extraction", "artisanal_fishing", "shrimp_estuary"],
        typical_elevation_m=90.0,
        climate_zone="tropical_warm_alluvial",
        notable_geographic_features=["Bahía de Jiquilisco", "Sierra Tecapa-Chinameca", "Laguna de Alegría", "Río Lempa desembocadura", "Puerto El Triunfo"],
    ),
    "SM": DepartmentData(
        code="SM",
        name="San Miguel",
        zone=SalvadoranZone.ORIENTAL,
        cabecera="San Miguel",
        area_km2=2077.1,
        population_approx=520000,
        primary_economic_activities=["regional_wholesale_commerce", "livestock", "services", "remittances", "coffee", "dairy"],
        typical_elevation_m=110.0,
        climate_zone="tropical_hot_savanna",
        notable_geographic_features=["Volcán Chaparrastique", "Río Grande de San Miguel", "Laguna de Olomega", "Moncagua"],
    ),
    "MO": DepartmentData(
        code="MO",
        name="Morazán",
        zone=SalvadoranZone.ORIENTAL,
        cabecera="San Francisco Gotera",
        area_km2=1447.4,
        population_approx=210000,
        primary_economic_activities=["black_pottery", "henequen_fiber", "subsistence_grains", "pine_forestry", "historical_ecotourism", "remittances"],
        typical_elevation_m=650.0,
        climate_zone="tropical_mountain_subtropical",
        notable_geographic_features=["Río Torola", "Guatajiagua (cerámica negra)", "Perquín", "Cerro Gigante", "Comunidades repobladas"],
    ),
    "LU": DepartmentData(
        code="LU",
        name="La Unión",
        zone=SalvadoranZone.ORIENTAL,
        cabecera="La Unión",
        area_km2=2074.3,
        population_approx=275000,
        primary_economic_activities=["maritime_port", "island_fisheries", "customs_transit", "cattle", "remittances", "coastal_trade"],
        typical_elevation_m=5.0,
        climate_zone="tropical_hot_coastal",
        notable_geographic_features=["Golfo de Fonseca", "Volcán de Conchagua", "Puerto de La Unión", "Islas Meanguera y Conchagüita", "Río Goascorán"],
    ),
}
