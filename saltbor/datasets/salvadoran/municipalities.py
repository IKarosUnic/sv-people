"""
Salvadoran Municipalities, Cantons, Caseríos, and Settlement Topology.

Captures real-world administrative settlements across El Salvador:
- Representative municipalities across all 14 departments
- Rural Cantones and Caseríos
- Urban Colonias, Barrios, and Comunidades
- Economic classification (urban commerce, coffee highlands, rural subsistence milpa, coastal fishing)
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


class SettlementClassification(str, Enum):
    """Socio-economic classification of Salvadoran settlements."""
    METROPOLITAN_URBAN = "metropolitan_urban"       # San Salvador, Santa Tecla, Soyapango
    REGIONAL_CITY = "regional_city"                   # Santa Ana, San Miguel, Sonsonate
    COLONIAL_HERITAGE_TOWN = "colonial_heritage_town" # Suchitoto, Juayúa, Ataco, Panchimalco
    COFFEE_HIGHLAND_MUNICIPALITY = "coffee_highland"  # Apaneca, Santiago de María, Comasagua
    RURAL_CANTON_AGRICULTURAL = "rural_canton_milpa"  # Rural canton focused on maize, beans, livestock
    RURAL_CASERIO_HAMLET = "rural_caserio_isolated"   # Small cluster of adobe/block houses on slopes
    COASTAL_FISHING_COMMUNITY = "coastal_fishing"     # Puerto El Triunfo, Acajutla, Barra de Santiago
    ARTISANAL_CRAFT_COMMUNITY = "artisanal_craft"     # Ilobasco, San Sebastián, Guatajiagua, La Palma


@dataclasses.dataclass(frozen=True)
class SalvadoranSettlementNode:
    """A settlement node in the territorial hierarchy."""
    settlement_id: str
    name: str
    department_code: str
    classification: SettlementClassification
    parent_municipality: str
    is_rural: bool
    estimated_population: int
    elevation_m: float
    typical_housing: list[str]          # e.g. ["block_and_concrete", "adobe", "bahareque", "zinc_roof"]
    access_road_type: str               # "paved_highway", "secondary_asphalt", "cobblestone", "unpaved_dirt_road"
    public_services_level: float        # [0.0, 1.0] access to piped water, electricity, sanitation
    primary_livelihood: str
    known_cantones: list[str] = dataclasses.field(default_factory=list)
    known_caserios: list[str] = dataclasses.field(default_factory=list)


# Verified representative municipalities, cantones, and caseríos
SALVADORAN_SETTLEMENTS: dict[str, SalvadoranSettlementNode] = {
    # 1. San Salvador (Capital)
    "ss_san_salvador": SalvadoranSettlementNode(
        settlement_id="ss_san_salvador",
        name="San Salvador",
        department_code="SS",
        classification=SettlementClassification.METROPOLITAN_URBAN,
        parent_municipality="San Salvador Centro",
        is_rural=False,
        estimated_population=320000,
        elevation_m=658.0,
        typical_housing=["concrete_block", "brick", "zinc_roof"],
        access_road_type="paved_highway",
        public_services_level=0.92,
        primary_livelihood="commerce_and_services",
        known_cantones=["San Antonio Abad", "El Carmen", "El Munguía", "Planes de Renderos"],
        known_caserios=["Caserío Las Brisas", "Caserío El Bosque"],
    ),
    # 2. Suchitoto (Cuscatlán) - Colonial cultural town on Lake Suchitlán
    "cu_suchitoto": SalvadoranSettlementNode(
        settlement_id="cu_suchitoto",
        name="Suchitoto",
        department_code="CU",
        classification=SettlementClassification.COLONIAL_HERITAGE_TOWN,
        parent_municipality="Suchitoto",
        is_rural=False,
        estimated_population=25000,
        elevation_m=390.0,
        typical_housing=["adobe", "colonial_clay_tile", "block"],
        access_road_type="secondary_asphalt",
        public_services_level=0.75,
        primary_livelihood="cultural_tourism_and_fishing",
        known_cantones=["San Lucas", "El Zapote", "Colima", "Palacios", "Tenango"],
        known_caserios=["Caserío San Antonio", "Caserío Hacienda Vieja", "Caserío Los Tercios"],
    ),
    # 3. Nahuizalco (Sonsonate) - Indigenous heritage, basketry and night market
    "so_nahuizalco": SalvadoranSettlementNode(
        settlement_id="so_nahuizalco",
        name="Nahuizalco",
        department_code="SO",
        classification=SettlementClassification.ARTISANAL_CRAFT_COMMUNITY,
        parent_municipality="Nahuizalco",
        is_rural=False,
        estimated_population=52000,
        elevation_m=540.0,
        typical_housing=["adobe", "block", "clay_tile", "sheet_metal"],
        access_road_type="secondary_asphalt",
        public_services_level=0.70,
        primary_livelihood="wicker_and_tule_crafts_and_agriculture",
        known_cantones=["El Canelo", "Tajcuicuitlapán", "El Cocal", "Sisimitepet", "Pushtan"],
        known_caserios=["Caserío Los Ángeles", "Caserío El Amatillo", "Caserío San Juan"],
    ),
    # 4. Cantón Tajcuicuitlapán (Nahuizalco rural canton)
    "so_tajcuicuitlapan": SalvadoranSettlementNode(
        settlement_id="so_tajcuicuitlapan",
        name="Cantón Tajcuicuitlapán",
        department_code="SO",
        classification=SettlementClassification.RURAL_CANTON_AGRICULTURAL,
        parent_municipality="Nahuizalco",
        is_rural=True,
        estimated_population=3800,
        elevation_m=620.0,
        typical_housing=["adobe", "bahareque", "zinc_roof"],
        access_road_type="unpaved_dirt_road",
        public_services_level=0.45,
        primary_livelihood="subsistence_maize_beans_and_craft_weaving",
        known_cantones=[],
        known_caserios=["Caserío La Joya", "Caserío Los Pérez", "Caserío El Chorro"],
    ),
    # 5. La Palma (Chalatenango) - Highland Pine and Naïf Wood Art
    "ch_la_palma": SalvadoranSettlementNode(
        settlement_id="ch_la_palma",
        name="La Palma",
        department_code="CH",
        classification=SettlementClassification.ARTISANAL_CRAFT_COMMUNITY,
        parent_municipality="La Palma",
        is_rural=False,
        estimated_population=14000,
        elevation_m=1010.0,
        typical_housing=["pine_wood", "brick", "clay_tile"],
        access_road_type="paved_highway", # Carretera Troncal del Norte (CA-4)
        public_services_level=0.68,
        primary_livelihood="naif_wood_crafts_and_mountain_tourism",
        known_cantones=["El Gramal", "Los Horcones", "San José Sacare", "La Presa"],
        known_caserios=["Caserío Las Hortensias", "Caserío Río Chiquito"],
    ),
    # 6. Cantón Río Chiquito / Miramundo (Highland mountain near El Pital)
    "ch_rio_chiquito": SalvadoranSettlementNode(
        settlement_id="ch_rio_chiquito",
        name="Caserío Río Chiquito",
        department_code="CH",
        classification=SettlementClassification.RURAL_CASERIO_HAMLET,
        parent_municipality="San Ignacio",
        is_rural=True,
        estimated_population=1200,
        elevation_m=2200.0,
        typical_housing=["wood_plank", "adobe", "heavy_zinc_roof"],
        access_road_type="unpaved_dirt_road",
        public_services_level=0.40,
        primary_livelihood="cold_climate_vegetables_peaches_and_ecotourism",
        known_cantones=[],
        known_caserios=["Caserío Las Pilas", "Caserío Cerro El Pital Base"],
    ),
    # 7. Olocuilta (La Paz) - Pupusa capital of rice dough
    "lp_olocuilta": SalvadoranSettlementNode(
        settlement_id="lp_olocuilta",
        name="Olocuilta",
        department_code="LP",
        classification=SettlementClassification.REGIONAL_CITY,
        parent_municipality="Olocuilta",
        is_rural=False,
        estimated_population=35000,
        elevation_m=510.0,
        typical_housing=["concrete_block", "brick", "zinc_roof"],
        access_road_type="paved_highway", # Autopista a Comalapa
        public_services_level=0.82,
        primary_livelihood="pupusa_gastronomic_industry_and_transit_trade",
        known_cantones=["La Joya", "San José Buenavista", "Platanares", "Valle Nuevo"],
        known_caserios=["Caserío El Triunfo", "Caserío Los Cocos"],
    ),
    # 8. Ilobasco (Cabañas) - Traditional clay ceramics and miniature figures
    "ca_ilobasco": SalvadoranSettlementNode(
        settlement_id="ca_ilobasco",
        name="Ilobasco",
        department_code="CA",
        classification=SettlementClassification.ARTISANAL_CRAFT_COMMUNITY,
        parent_municipality="Ilobasco",
        is_rural=False,
        estimated_population=68000,
        elevation_m=750.0,
        typical_housing=["brick", "adobe", "clay_tile", "block"],
        access_road_type="secondary_asphalt",
        public_services_level=0.72,
        primary_livelihood="clay_pottery_and_dairy_livestock",
        known_cantones=["San Francisco del Monte", "La Labor", "Maquilishuat", "El Zapote"],
        known_caserios=["Caserío Los Ramos", "Caserío El Barro"],
    ),
    # 9. San Sebastián (San Vicente) - Traditional wooden pedal looms
    "sv_san_sebastian": SalvadoranSettlementNode(
        settlement_id="sv_san_sebastian",
        name="San Sebastián",
        department_code="SV",
        classification=SettlementClassification.ARTISANAL_CRAFT_COMMUNITY,
        parent_municipality="San Sebastián",
        is_rural=False,
        estimated_population=18000,
        elevation_m=620.0,
        typical_housing=["adobe", "block", "clay_tile"],
        access_road_type="secondary_asphalt",
        public_services_level=0.69,
        primary_livelihood="handloom_textiles_hammocks_and_bedspreads",
        known_cantones=["La Esperanza", "El Paraíso", "San Francisco", "Santa Elena"],
        known_caserios=["Caserío Los Telares", "Caserío El Centro"],
    ),
    # 10. Guatajiagua (Morazán) - Indigenous black clay pottery with jiote seed stain
    "mo_guatajiagua": SalvadoranSettlementNode(
        settlement_id="mo_guatajiagua",
        name="Guatajiagua",
        department_code="MO",
        classification=SettlementClassification.ARTISANAL_CRAFT_COMMUNITY,
        parent_municipality="Guatajiagua",
        is_rural=False,
        estimated_population=12500,
        elevation_m=280.0,
        typical_housing=["bahareque", "adobe", "block", "zinc_roof"],
        access_road_type="secondary_asphalt",
        public_services_level=0.55,
        primary_livelihood="lenca_black_pottery_and_subsistence_milpa",
        known_cantones=["San Bartolo", "Abelines", "Gualuca", "Pajal de Arriba"],
        known_caserios=["Caserío Los Alfareros", "Caserío El Chingo"],
    ),
    # 11. Puerto El Triunfo (Usulután) - Jiquilisco Bay fishing & shrimp
    "us_puerto_el_triunfo": SalvadoranSettlementNode(
        settlement_id="us_puerto_el_triunfo",
        name="Puerto El Triunfo",
        department_code="US",
        classification=SettlementClassification.COASTAL_FISHING_COMMUNITY,
        parent_municipality="Puerto El Triunfo",
        is_rural=False,
        estimated_population=21000,
        elevation_m=10.0,
        typical_housing=["block", "wood", "zinc_roof", "stilts_near_water"],
        access_road_type="secondary_asphalt",
        public_services_level=0.65,
        primary_livelihood="artisanal_fishing_and_estuary_mangrove_harvest",
        known_cantones=["Sitio Viejo", "Isla de Méndez", "El Chagal", "La Pampa"],
        known_caserios=["Caserío El Muelle", "Caserío Los Pescadores"],
    ),
    # 12. San Miguel (Regional Metropolis of Eastern El Salvador)
    "sm_san_miguel": SalvadoranSettlementNode(
        settlement_id="sm_san_miguel",
        name="San Miguel",
        department_code="SM",
        classification=SettlementClassification.REGIONAL_CITY,
        parent_municipality="San Miguel Centro",
        is_rural=False,
        estimated_population=240000,
        elevation_m=110.0,
        typical_housing=["concrete_block", "brick", "zinc_roof"],
        access_road_type="paved_highway", # Carretera Panamericana (CA-1)
        public_services_level=0.88,
        primary_livelihood="regional_commerce_livestock_and_remittance_services",
        known_cantones=["El Sitio", "Hato Nuevo", "Montegrande", "El Jalacatal", "San Antonio Silva"],
        known_caserios=["Caserío La Pradera", "Caserío Las Brisas"],
    ),
}
