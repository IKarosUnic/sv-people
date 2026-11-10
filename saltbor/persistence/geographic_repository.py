"""
Geographic and Establishment Persistence Repository (Phase 0.8).

Provides Data Access Object (DAO) methods for persisting and querying:
- Geographic territorial entities (departments, municipalities, districts)
- Real establishments with validation states
- Dataset version snapshots, diffs, and audit logs
- Safe transactional loading by department or municipality.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Optional

from saltbor.persistence.database import DatabaseManager
from saltbor.world.geographic.models import (
    EstablishmentCategory,
    GeoBoundingBox,
    GeographicEntity,
    GeoPoint,
    RealPlace,
    TerritorialLevel,
    ValidationState,
)
from saltbor.world.geographic.updater import DatasetDiff, DatasetVersionSnapshot

logger = logging.getLogger(__name__)


class GeographicRepository:
    """SQLite DAO for Salvadoran territorial data and establishments."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # Establishments
    # -------------------------------------------------------------------------

    def save_place(self, place: RealPlace) -> None:
        """Insert or replace an establishment."""
        sql = """
        INSERT OR REPLACE INTO geo_establishments (
            establishment_id, name, category, sub_category, department_code,
            municipality_id, district_id, latitude, longitude, address,
            source_name, validation_state, confidence_level, opening_hours,
            accessibility_rating, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        meta = {
            "source_id": place.source_id,
            "source_pub": place.source_publication_date,
            "source_update": place.source_update_date,
            "saltbor_fetch": place.saltbor_fetch_date,
            "independent_verification": place.independent_verification_date,
            "contact_phone": place.contact_phone,
            "capacity": place.capacity,
            "extra": place.metadata,
        }
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    place.place_id,
                    place.name,
                    place.category.value,
                    place.sub_category,
                    place.department_code,
                    place.municipality_id,
                    place.district_id,
                    place.point.latitude,
                    place.point.longitude,
                    place.address,
                    place.source_name,
                    place.validation_state.value,
                    place.confidence_level,
                    place.opening_hours,
                    place.accessibility_rating,
                    json.dumps(meta),
                ),
            )

    def save_places_batch(self, places: list[RealPlace]) -> None:
        """Batch save establishments inside a single transaction."""
        sql = """
        INSERT OR REPLACE INTO geo_establishments (
            establishment_id, name, category, sub_category, department_code,
            municipality_id, district_id, latitude, longitude, address,
            source_name, validation_state, confidence_level, opening_hours,
            accessibility_rating, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = []
        for p in places:
            meta = {
                "source_id": p.source_id,
                "source_pub": p.source_publication_date,
                "source_update": p.source_update_date,
                "saltbor_fetch": p.saltbor_fetch_date,
                "independent_verification": p.independent_verification_date,
                "contact_phone": p.contact_phone,
                "capacity": p.capacity,
                "extra": p.metadata,
            }
            params.append((
                p.place_id,
                p.name,
                p.category.value,
                p.sub_category,
                p.department_code,
                p.municipality_id,
                p.district_id,
                p.point.latitude,
                p.point.longitude,
                p.address,
                p.source_name,
                p.validation_state.value,
                p.confidence_level,
                p.opening_hours,
                p.accessibility_rating,
                json.dumps(meta),
            ))
        with self.db.transaction():
            self.db.executemany(sql, params)

    def get_place(self, place_id: str) -> Optional[RealPlace]:
        """Fetch establishment by id."""
        sql = "SELECT * FROM geo_establishments WHERE establishment_id = ?"
        row = self.db.execute(sql, (place_id,)).fetchone()
        if not row:
            return None
        return self._row_to_place(row)

    def get_all_places(self, confirmed_only: bool = True) -> list[RealPlace]:
        """Fetch all establishments."""
        if confirmed_only:
            sql = "SELECT * FROM geo_establishments WHERE validation_state = 'CONFIRMADO'"
        else:
            sql = "SELECT * FROM geo_establishments"
        rows = self.db.execute(sql).fetchall()
        return [self._row_to_place(r) for r in rows]

    def get_places_by_department(self, dept_code: str, confirmed_only: bool = True) -> list[RealPlace]:
        """Fetch establishments in a department."""
        if confirmed_only:
            sql = "SELECT * FROM geo_establishments WHERE department_code = ? AND validation_state = 'CONFIRMADO'"
        else:
            sql = "SELECT * FROM geo_establishments WHERE department_code = ?"
        rows = self.db.execute(sql, (dept_code.upper(),)).fetchall()
        return [self._row_to_place(r) for r in rows]

    def get_places_by_municipality(self, muni_id: str, confirmed_only: bool = True) -> list[RealPlace]:
        """Fetch establishments in a municipality."""
        if confirmed_only:
            sql = "SELECT * FROM geo_establishments WHERE municipality_id = ? AND validation_state = 'CONFIRMADO'"
        else:
            sql = "SELECT * FROM geo_establishments WHERE municipality_id = ?"
        rows = self.db.execute(sql, (muni_id.lower(),)).fetchall()
        return [self._row_to_place(r) for r in rows]

    def _row_to_place(self, row: Any) -> RealPlace:
        meta = json.loads(row["metadata_json"] or "{}")
        return RealPlace(
            place_id=row["establishment_id"],
            name=row["name"],
            category=EstablishmentCategory(row["category"]),
            sub_category=row["sub_category"],
            department_code=row["department_code"],
            municipality_id=row["municipality_id"],
            district_id=row["district_id"],
            point=GeoPoint(row["latitude"], row["longitude"]),
            address=row["address"],
            source_name=row["source_name"],
            source_id=meta.get("source_id", ""),
            source_publication_date=meta.get("source_pub", "2024-01-01"),
            source_update_date=meta.get("source_update", "2024-01-01"),
            saltbor_fetch_date=meta.get("saltbor_fetch", "2026-11-10"),
            independent_verification_date=meta.get("independent_verification"),
            confidence_level=row["confidence_level"],
            validation_state=ValidationState(row["validation_state"]),
            opening_hours=row["opening_hours"],
            accessibility_rating=row["accessibility_rating"],
            contact_phone=meta.get("contact_phone"),
            capacity=meta.get("capacity", 50),
            metadata=meta.get("extra", {}),
        )

    # -------------------------------------------------------------------------
    # Territorial Entities
    # -------------------------------------------------------------------------

    def save_entity(self, entity: GeographicEntity) -> None:
        sql = """
        INSERT OR REPLACE INTO geo_entities (
            entity_id, name, level, parent_id, department_code, municipality_id,
            district_id, latitude, longitude, elevation_m, population, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        meta = {
            "alt_names": list(entity.alternate_names),
            "source_name": entity.source_name,
            "source_ref": entity.source_reference,
            "ref_date": entity.reference_date,
            "confidence": entity.confidence_level,
            "validation": entity.validation_state.value,
            "is_rural": entity.is_rural,
            "extra": entity.metadata,
        }
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    entity.entity_id,
                    entity.name,
                    entity.level.value,
                    entity.parent_id,
                    entity.department_code,
                    entity.municipality_id,
                    entity.district_id,
                    entity.center_point.latitude,
                    entity.center_point.longitude,
                    entity.elevation_m,
                    entity.approx_population,
                    json.dumps(meta),
                ),
            )

    def get_entity(self, entity_id: str) -> Optional[GeographicEntity]:
        sql = "SELECT * FROM geo_entities WHERE entity_id = ?"
        row = self.db.execute(sql, (entity_id,)).fetchone()
        if not row:
            return None
        meta = json.loads(row["metadata_json"] or "{}")
        return GeographicEntity(
            entity_id=row["entity_id"],
            name=row["name"],
            alternate_names=tuple(meta.get("alt_names", [])),
            level=TerritorialLevel(row["level"]),
            parent_id=row["parent_id"],
            department_code=row["department_code"],
            municipality_id=row["municipality_id"],
            district_id=row["district_id"],
            center_point=GeoPoint(row["latitude"], row["longitude"]),
            bounding_box=None,
            elevation_m=row["elevation_m"],
            approx_population=row["population"],
            source_name=meta.get("source_name", "CNR"),
            source_reference=meta.get("source_ref", ""),
            reference_date=meta.get("ref_date", "2024-05-01"),
            confidence_level=meta.get("confidence", 1.0),
            validation_state=ValidationState(meta.get("validation", "CONFIRMADO")),
            is_rural=meta.get("is_rural", False),
            metadata=meta.get("extra", {}),
        )

    # -------------------------------------------------------------------------
    # Dataset Versions
    # -------------------------------------------------------------------------

    def save_version(self, version: DatasetVersionSnapshot) -> None:
        sql = """
        INSERT OR REPLACE INTO geo_dataset_versions (
            version_id, parent_version_id, created_at_iso, description,
            checksum, record_count, diff_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        diff_dict = {}
        if version.diff_from_parent:
            diff_dict = {
                "added": version.diff_from_parent.added_ids,
                "modified": version.diff_from_parent.modified_ids,
                "removed": version.diff_from_parent.removed_ids,
                "relocated": version.diff_from_parent.relocated_ids,
                "duplicates": version.diff_from_parent.duplicates_found,
                "summary": version.diff_from_parent.summary,
            }
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    version.version_id,
                    version.parent_version_id,
                    version.created_at_iso,
                    version.description,
                    version.checksum,
                    len(version.records),
                    json.dumps(diff_dict),
                ),
            )

    def get_version(self, version_id: str) -> Optional[dict[str, Any]]:
        sql = "SELECT * FROM geo_dataset_versions WHERE version_id = ?"
        row = self.db.execute(sql, (version_id,)).fetchone()
        if not row:
            return None
        return {
            "version_id": row["version_id"],
            "parent_version_id": row["parent_version_id"],
            "created_at_iso": row["created_at_iso"],
            "description": row["description"],
            "checksum": row["checksum"],
            "record_count": row["record_count"],
            "diff": json.loads(row["diff_json"] or "{}"),
        }
