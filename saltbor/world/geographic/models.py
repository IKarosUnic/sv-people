"""
Geographic Data Models for Saltbor (Phase 0.8).

Defines core primitives, entity types, validation states, and query structures
for real-world territorial simulation in El Salvador.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional


class TerritorialLevel(str, Enum):
    """Hierarchical administrative levels."""
    COUNTRY = "country"
    DEPARTMENT = "department"
    MUNICIPALITY = "municipality"
    DISTRICT = "district"
    CANTON = "canton"
    CASERIO = "caserio"
    BARRIO = "barrio"
    COLONIA = "colonia"
    SETTLEMENT = "settlement"


class ValidationState(str, Enum):
    """Validation states for geographic records and establishments."""
    CONFIRMADO = "CONFIRMADO"
    PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"
    DESACTUALIZADO = "DESACTUALIZADO"
    CERRADO = "CERRADO"
    TRASLADADO = "TRASLADADO"
    DUPLICADO = "DUPLICADO"
    INFORMACION_INSUFICIENTE = "INFORMACION_INSUFICIENTE"


class EstablishmentCategory(str, Enum):
    COMMERCE = "commerce"
    PUBLIC_SERVICE = "public_service"
    SOCIAL_CULTURAL = "social_cultural"
    PRODUCTIVE = "productive"


@dataclasses.dataclass(frozen=True)
class GeoPoint:
    """WGS84 Coordinate point (latitude, longitude) with optional elevation."""
    latitude: float
    longitude: float
    elevation_m: float = 0.0

    def as_tuple(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)

    def __iter__(self):
        yield self.latitude
        yield self.longitude


@dataclasses.dataclass(frozen=True)
class GeoBoundingBox:
    """Axis-aligned geographic bounding box in decimal degrees."""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon

    @property
    def center(self) -> GeoPoint:
        return GeoPoint(
            latitude=(self.min_lat + self.max_lat) / 2.0,
            longitude=(self.min_lon + self.max_lon) / 2.0,
        )


@dataclasses.dataclass(frozen=True)
class GeographicEntity:
    """A territorial entity (department, municipality, district, canton, caserio)."""
    entity_id: str
    name: str
    alternate_names: tuple[str, ...]
    level: TerritorialLevel
    parent_id: Optional[str]
    department_code: str
    municipality_id: Optional[str]
    district_id: Optional[str]
    center_point: GeoPoint
    bounding_box: Optional[GeoBoundingBox]
    elevation_m: float
    approx_population: int
    source_name: str
    source_reference: str
    reference_date: str
    confidence_level: float
    validation_state: ValidationState
    is_rural: bool = False
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class RealPlace:
    """A verified real establishment or point of interest."""
    place_id: str
    name: str
    category: EstablishmentCategory
    sub_category: str
    department_code: str
    municipality_id: str
    district_id: str
    point: GeoPoint
    address: str
    source_name: str
    source_id: str
    source_publication_date: str
    source_update_date: str
    saltbor_fetch_date: str
    independent_verification_date: Optional[str]
    confidence_level: float
    validation_state: ValidationState
    opening_hours: str
    accessibility_rating: float
    contact_phone: Optional[str] = None
    capacity: int = 50
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def is_confirmed(self) -> bool:
        return self.validation_state == ValidationState.CONFIRMADO


@dataclasses.dataclass
class SpatialQueryResult:
    """Result of a spatial proximity query."""
    entity_id: str
    name: str
    entity_type: str
    distance_km: float
    latitude: float
    longitude: float
    validation_state: str
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
