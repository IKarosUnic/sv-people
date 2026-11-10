"""Salvadoran dataset package initialization."""

from saltbor.datasets.salvadoran.departments import (
    SALVADORAN_DEPARTMENTS,
    DepartmentData,
    SalvadoranZone,
)
from saltbor.datasets.salvadoran.municipalities import (
    SALVADORAN_SETTLEMENTS,
    SalvadoranSettlementNode,
    SettlementClassification,
)
from saltbor.datasets.salvadoran.physical_geography import (
    SALVADORAN_GEOGRAPHIC_FEATURES,
    GeographicFeatureType,
    SalvadoranGeographicFeature,
)
from saltbor.datasets.salvadoran.culture_data import (
    SALVADORAN_FOOD_CATALOG,
    SALVADORAN_FESTIVITIES,
    SalvadoranFoodItem,
    SalvadoranFestivity,
)
from saltbor.datasets.salvadoran.lexicon_data import (
    SALVADORAN_LEXICON,
    LinguisticRegister,
    SalvadoranLexicalEntry,
)
from saltbor.datasets.salvadoran.territory_data import (
    AdministrativeLevel,
    SalvadoranDepartmentProfile,
    SalvadoranMunicipalityData,
    SalvadoranDistrictData,
    PhysicalFeatureData,
    RoadSegmentData,
    SALVADORAN_DEPARTMENTS_P8,
    SALVADORAN_MUNICIPALITIES_P8,
    SALVADORAN_DISTRICTS_P8,
    SALVADORAN_PHYSICAL_FEATURES_P8,
    SALVADORAN_ROAD_NETWORK_P8,
)
from saltbor.datasets.salvadoran.establishments_data import (
    ValidationStatus,
    EstablishmentCategory,
    RealEstablishmentRecord,
    SALVADORAN_ESTABLISHMENTS_P8,
)

__all__ = [
    "SALVADORAN_DEPARTMENTS",
    "DepartmentData",
    "SalvadoranZone",
    "SALVADORAN_SETTLEMENTS",
    "SalvadoranSettlementNode",
    "SettlementClassification",
    "SALVADORAN_GEOGRAPHIC_FEATURES",
    "GeographicFeatureType",
    "SalvadoranGeographicFeature",
    "SALVADORAN_FOOD_CATALOG",
    "SALVADORAN_FESTIVITIES",
    "SalvadoranFoodItem",
    "SalvadoranFestivity",
    "SALVADORAN_LEXICON",
    "LinguisticRegister",
    "SalvadoranLexicalEntry",
    # Phase 0.8 Territorial Additions
    "AdministrativeLevel",
    "SalvadoranDepartmentProfile",
    "SalvadoranMunicipalityData",
    "SalvadoranDistrictData",
    "PhysicalFeatureData",
    "RoadSegmentData",
    "SALVADORAN_DEPARTMENTS_P8",
    "SALVADORAN_MUNICIPALITIES_P8",
    "SALVADORAN_DISTRICTS_P8",
    "SALVADORAN_PHYSICAL_FEATURES_P8",
    "SALVADORAN_ROAD_NETWORK_P8",
    "ValidationStatus",
    "EstablishmentCategory",
    "RealEstablishmentRecord",
    "SALVADORAN_ESTABLISHMENTS_P8",
]
