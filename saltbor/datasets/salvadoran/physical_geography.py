"""
Salvadoran Physical Geography: Volcanoes, Mountains, Rivers, Lakes, and Coastlines.

Captures verified physical features of the Salvadoran landscape:
- Major stratovolcanoes and volcanic calderas
- Hydrographic network (Río Lempa, tributaries, coastal rivers)
- Lakes and reservoirs (Coatepeque, Ilopango, Cerrón Grande)
- National highway network (CA-1 Panamericana, CA-2 Litoral, CA-4 Troncal del Norte)
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


class GeographicFeatureType(str, Enum):
    """Categorization of physical landscape features."""
    VOLCANO = "volcano"
    MOUNTAIN_RANGE = "mountain_range"
    RIVER = "river"
    LAKE_OR_RESERVOIR = "lake_or_reservoir"
    COASTAL_BAY_OR_ESTUARY = "coastal_bay_or_estuary"


@dataclasses.dataclass(frozen=True)
class SalvadoranGeographicFeature:
    """A natural physical feature in the Salvadoran territory."""
    feature_id: str
    name: str
    feature_type: GeographicFeatureType
    department_codes: list[str]
    elevation_or_length_km: float      # Elevation in meters for mountains/volcanoes, or length in km for rivers
    ecological_role: str
    associated_risks: list[str]        # e.g., ["landslides", "flash_floods", "pyroclastic_hazard", "lahars"]
    economic_significance: str


SALVADORAN_GEOGRAPHIC_FEATURES: dict[str, SalvadoranGeographicFeature] = {
    # Volcanoes
    "volcan_ilamatepec": SalvadoranGeographicFeature(
        feature_id="volcan_ilamatepec",
        name="Volcán de Santa Ana (Ilamatepec)",
        feature_type=GeographicFeatureType.VOLCANO,
        department_codes=["SA", "SO"],
        elevation_or_length_km=2381.0, # Highest volcano in El Salvador
        ecological_role="High-altitude cloud forest, aquifer recharge for Coatepeque basin, volcanic soils for premium shade coffee",
        associated_risks=["ash_fall", "lahars", "sulfur_fumes", "landslides_on_steep_slopes"],
        economic_significance="World-class coffee estates, ecotourism trekking, microclimates for cool-weather crops",
    ),
    "volcan_izalco": SalvadoranGeographicFeature(
        feature_id="volcan_izalco",
        name="Volcán de Izalco (El Faro del Pacífico)",
        feature_type=GeographicFeatureType.VOLCANO,
        department_codes=["SO"],
        elevation_or_length_km=1950.0,
        ecological_role="Young volcanic cone with sparse pioneer vegetation and rugged basalt scree slopes",
        associated_risks=["rockfalls", "lahars", "seismic_tremors"],
        economic_significance="Historical national symbol, major national park tourism attraction",
    ),
    "volcan_quezaltepec": SalvadoranGeographicFeature(
        feature_id="volcan_quezaltepec",
        name="Volcán de San Salvador (Quezaltepec)",
        feature_type=GeographicFeatureType.VOLCANO,
        department_codes=["SS", "LL"],
        elevation_or_length_km=1893.0,
        ecological_role="El Boquerón crater, primary biological reserve and freshwater recharge zone for San Salvador metropolitan area",
        associated_risks=["landslides_during_heavy_temporal", "lahars_towards_quebradas", "seismic_faults"],
        economic_significance="Highland restaurants, flower nurseries, coffee fincas, scenic viewpoints",
    ),
    "volcan_chinchontepec": SalvadoranGeographicFeature(
        feature_id="volcan_chinchontepec",
        name="Volcán de San Vicente (Chinchontepec)",
        feature_type=GeographicFeatureType.VOLCANO,
        department_codes=["SV", "LP"],
        elevation_or_length_km=2182.0,
        ecological_role="Twin-peaked stratovolcano with thermal springs (los infiernillos) and deep ravines",
        associated_risks=["severe_debris_flows_and_lahars_during_hurricanes", "flash_floods_downstream"],
        economic_significance="Sugar cane and maize cultivation on fertile lower skirts, geothermal potential",
    ),
    "volcan_chaparrastique": SalvadoranGeographicFeature(
        feature_id="volcan_chaparrastique",
        name="Volcán de San Miguel (Chaparrastique)",
        feature_type=GeographicFeatureType.VOLCANO,
        department_codes=["SM"],
        elevation_or_length_km=2130.0,
        ecological_role="Active volcanic cone with frequent gas emissions, dominating the central eastern plains",
        associated_risks=["frequent_ash_eruptions", "gas_plumes_damaging_coffee", "lahars_towards_cantones"],
        economic_significance="Extensive coffee fincas on upper flanks, cattle pastures on lower aprons",
    ),
    "volcan_conchagua": SalvadoranGeographicFeature(
        feature_id="volcan_conchagua",
        name="Volcán de Conchagua",
        feature_type=GeographicFeatureType.VOLCANO,
        department_codes=["LU"],
        elevation_or_length_km=1225.0,
        ecological_role="Maritime volcanic massif overlooking the Gulf of Fonseca with endemic flora",
        associated_risks=["brush_fires_in_dry_season", "slope_erosion"],
        economic_significance="Spectacular gulf panoramic tourism, camping, artisanal fishing communities at base",
    ),
    # Mountains
    "cerro_el_pital": SalvadoranGeographicFeature(
        feature_id="cerro_el_pital",
        name="Cerro El Pital",
        feature_type=GeographicFeatureType.MOUNTAIN_RANGE,
        department_codes=["CH"],
        elevation_or_length_km=2730.0, # Highest elevation in El Salvador
        ecological_role="Alpine cloud forest, pine-oak woodlands, lowest recorded temperatures in the country (freezing frosts)",
        associated_risks=["severe_frost_destroying_crops", "heavy_fog_reducing_visibility", "isolated_mudslides"],
        economic_significance="Cold-climate high-value horticulture (cabbage, carrots, peaches, flowers), mountain eco-lodges",
    ),
    "cordillera_del_balsamo": SalvadoranGeographicFeature(
        feature_id="cordillera_del_balsamo",
        name="Cordillera del Bálsamo",
        feature_type=GeographicFeatureType.MOUNTAIN_RANGE,
        department_codes=["LL", "SO"],
        elevation_or_length_km=1100.0,
        ecological_role="Coastal mountain range containing the unique native habitat of the Balsam of Peru (Myroxylon balsamum)",
        associated_risks=["highway_derrumbe_at_los_chorros", "erosion_from_real_estate_expansion"],
        economic_significance="Artisanal extraction of aromatic balsam resin, shade coffee, residential expansion",
    ),
    # Rivers
    "rio_lempa": SalvadoranGeographicFeature(
        feature_id="rio_lempa",
        name="Río Lempa",
        feature_type=GeographicFeatureType.RIVER,
        department_codes=["CH", "CU", "CA", "SV", "US", "SM"],
        elevation_or_length_km=422.0, # Primary fluvial spine
        ecological_role="Main drainage basin of El Salvador (over 50% of national territory), vital freshwater and aquatic biodiversity",
        associated_risks=["catastrophic_flooding_of_bajo_lempa_during_temporales", "dam_spillway_discharges"],
        economic_significance="Hydroelectric energy (Cerrón Grande, 5 de Noviembre, 15 de Septiembre, Chaparral), irrigation, artisanal fishing",
    ),
    "rio_grande_san_miguel": SalvadoranGeographicFeature(
        feature_id="rio_grande_san_miguel",
        name="Río Grande de San Miguel",
        feature_type=GeographicFeatureType.RIVER,
        department_codes=["SM", "US"],
        elevation_or_length_km=145.0,
        ecological_role="Drains the eastern plains and slopes of Chaparrastique, feeding the Laguna de Olomega",
        associated_risks=["severe_flooding_of_agricultural_plains_and_panamerican_highway", "sedimentation"],
        economic_significance="Agricultural irrigation for maize, sugar cane, livestock watering, freshwater fisheries",
    ),
    # Lakes
    "lago_coatepeque": SalvadoranGeographicFeature(
        feature_id="lago_coatepeque",
        name="Lago de Coatepeque",
        feature_type=GeographicFeatureType.LAKE_OR_RESERVOIR,
        department_codes=["SA"],
        elevation_or_length_km=745.0, # Elevation of caldera lake
        ecological_role="Large volcanic collapse caldera with thermal springs and periodic turquoise algal blooms",
        associated_risks=["localized_seiche_waves", "cyanobacteria_blooms_affecting_water_quality"],
        economic_significance="Water sports, high-end tourism, local artisanal fishing (guapote, tilapia)",
    ),
    "lago_ilopango": SalvadoranGeographicFeature(
        feature_id="lago_ilopango",
        name="Lago de Ilopango",
        feature_type=GeographicFeatureType.LAKE_OR_RESERVOIR,
        department_codes=["SS", "CU", "LP"],
        elevation_or_length_km=440.0,
        ecological_role="Cataclysmic volcanic caldera (famous Tierra Blanca Joven eruption ~535 AD), central water body",
        associated_risks=["sublacustrine_volcanic_domes", "steep_caldera_rim_landslides"],
        economic_significance="Urban tourism (Apulo), commercial tilapia cage aquaculture, local municipal water supplies",
    ),
    "bahia_jiquilisco": SalvadoranGeographicFeature(
        feature_id="bahia_jiquilisco",
        name="Bahía de Jiquilisco",
        feature_type=GeographicFeatureType.COASTAL_BAY_OR_ESTUARY,
        department_codes=["US"],
        elevation_or_length_km=55.0, # Length of estuarine lagoon
        ecological_role="Ramsar wetland of international importance, largest mangrove ecosystem in El Salvador, sea turtle nesting (hawksbill)",
        associated_risks=["storm_surges", "mangrove_salinization", "estuary_siltation"],
        economic_significance="Artisanal and industrial shrimp farming, sea salt production, snapper and snook fishing, ecotourism",
    ),
}
