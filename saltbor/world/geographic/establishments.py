"""
Real Establishment Directory for Saltbor (Phase 0.8).

Manages verified commercial, public, social, and productive establishments:
- Spatial indexing for sub-millisecond proximity queries
- Categorical and territorial filtering (department, municipality, district)
- Rigorous validation state guarantees (never present unverified as confirmed)
- Operating hours and accessibility evaluation
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from saltbor.datasets.salvadoran.establishments_data import (
    SALVADORAN_ESTABLISHMENTS_P8,
    EstablishmentCategory,
    RealEstablishmentRecord,
    ValidationStatus,
)
from saltbor.world.geographic.models import (
    EstablishmentCategory as ModelCategory,
    GeoPoint,
    RealPlace,
    SpatialQueryResult,
    ValidationState,
)
from saltbor.world.geographic.spatial_index import SpatialGridIndex

logger = logging.getLogger(__name__)


def _record_to_place(r: RealEstablishmentRecord) -> RealPlace:
    return RealPlace(
        place_id=r.establishment_id,
        name=r.name,
        category=ModelCategory(r.category.value),
        sub_category=r.sub_category,
        department_code=r.department_code,
        municipality_id=r.municipality_id,
        district_id=r.district_id,
        point=GeoPoint(r.latitude, r.longitude),
        address=r.address,
        source_name=r.source_name,
        source_id=r.source_id,
        source_publication_date=r.source_publication_date,
        source_update_date=r.source_update_date,
        saltbor_fetch_date=r.saltbor_fetch_date,
        independent_verification_date=r.independent_verification_date,
        confidence_level=r.confidence_level,
        validation_state=ValidationState(r.validation_status.value),
        opening_hours=r.opening_hours,
        accessibility_rating=r.accessibility_rating,
        contact_phone=r.contact_phone,
        capacity=r.estimated_daily_capacity,
        metadata={"notes": r.notes},
    )


class EstablishmentDirectory:
    """Directory of real-world establishments with spatial queries and status filtering."""

    def __init__(self, load_defaults: bool = True) -> None:
        self._places: dict[str, RealPlace] = {}
        self._spatial_index: SpatialGridIndex[RealPlace] = SpatialGridIndex(cell_size_degrees=0.02)

        if load_defaults:
            for rec in SALVADORAN_ESTABLISHMENTS_P8.values():
                self.register_place(_record_to_place(rec))

    def register_place(self, place: RealPlace) -> None:
        """Register or update an establishment."""
        self._places[place.place_id] = place
        self._spatial_index.insert(
            place.place_id,
            place.point.latitude,
            place.point.longitude,
            place,
        )

    def remove_place(self, place_id: str) -> bool:
        """Remove an establishment from the directory and index."""
        if place_id in self._places:
            del self._places[place_id]
            self._spatial_index.remove(place_id)
            return True
        return False

    def get_by_id(self, place_id: str) -> Optional[RealPlace]:
        return self._places.get(place_id)

    def __len__(self) -> int:
        return len(self._places)

    def get_all(self, confirmed_only: bool = True) -> list[RealPlace]:
        if confirmed_only:
            return [p for p in self._places.values() if p.is_confirmed]
        return list(self._places.values())

    def get_by_category(
        self,
        category: ModelCategory | str,
        confirmed_only: bool = True,
    ) -> list[RealPlace]:
        cat_str = category.value if isinstance(category, ModelCategory) else str(category)
        return [
            p for p in self._places.values()
            if p.category.value == cat_str and (not confirmed_only or p.is_confirmed)
        ]

    def get_by_status(self, state: ValidationState | str) -> list[RealPlace]:
        st_val = state.value if isinstance(state, ValidationState) else str(state)
        return [p for p in self._places.values() if p.validation_state.value == st_val]

    def get_by_department(
        self,
        department_code: str,
        confirmed_only: bool = True,
    ) -> list[RealPlace]:
        code = department_code.upper()
        return [
            p for p in self._places.values()
            if p.department_code == code and (not confirmed_only or p.is_confirmed)
        ]

    def get_by_municipality(
        self,
        municipality_id: str,
        confirmed_only: bool = True,
    ) -> list[RealPlace]:
        muni = municipality_id.lower()
        return [
            p for p in self._places.values()
            if p.municipality_id == muni and (not confirmed_only or p.is_confirmed)
        ]

    def get_by_district(
        self,
        district_id: str,
        confirmed_only: bool = True,
    ) -> list[RealPlace]:
        dist = district_id.lower()
        return [
            p for p in self._places.values()
            if p.district_id == dist and (not confirmed_only or p.is_confirmed)
        ]

    def find_places_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        category: Optional[ModelCategory | str] = None,
        sub_category: Optional[str] = None,
        confirmed_only: bool = True,
    ) -> list[SpatialQueryResult]:
        """Sub-millisecond query for places near a coordinate within a radius."""
        cat_str = category.value if isinstance(category, ModelCategory) else (category if category else None)

        def predicate(p: RealPlace) -> bool:
            if confirmed_only and not p.is_confirmed:
                return False
            if cat_str and p.category.value != cat_str:
                return False
            if sub_category and p.sub_category != sub_category:
                return False
            return True

        hits = self._spatial_index.find_within_radius(lat, lon, radius_km, predicate=predicate)

        return [
            SpatialQueryResult(
                entity_id=p.place_id,
                name=p.name,
                entity_type=p.sub_category,
                distance_km=round(dist, 3),
                latitude=p.point.latitude,
                longitude=p.point.longitude,
                validation_state=p.validation_state.value,
                metadata={
                    "category": p.category.value,
                    "address": p.address,
                    "opening_hours": p.opening_hours,
                    "confidence": p.confidence_level,
                },
            )
            for p, dist in hits
        ]

    def find_nearest_place(
        self,
        lat: float,
        lon: float,
        category: Optional[ModelCategory | str] = None,
        sub_category: Optional[str] = None,
        confirmed_only: bool = True,
        max_radius_km: float = 80.0,
    ) -> Optional[SpatialQueryResult]:
        """Find the single closest establishment matching criteria."""
        results = self.find_places_nearby(
            lat=lat,
            lon=lon,
            radius_km=max_radius_km,
            category=category,
            sub_category=sub_category,
            confirmed_only=confirmed_only,
        )
        return results[0] if results else None
