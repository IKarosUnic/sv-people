"""High-performance SQLite persistence for millions of persistent individuals and aggregates.

Features:
- Optimized WAL mode with tuned page cache.
- Multi-column indexes for fast district, coordinate, and LOD queries.
- Chunked bulk transactions (executemany) for massive ingest and checkpointing.
- Compact blob storage for cognitive snapshots.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterator, Optional

from saltbor.persistence.database import DatabaseManager
from saltbor.population.multilevel.models import (
    CommunityAggregate,
    PersistentIndividualRecord,
)

logger = logging.getLogger(__name__)


class MultilevelPersistenceEngine:
    """Manages high-throughput SQLite storage for persistent civilization entities."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create optimized persistent tables and indexes if they do not exist."""
        conn = self.db.get_connection()

        # Tuned SQLite pragmas for extreme throughput
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-64000") # 64 MB memory cache
        conn.execute("PRAGMA temp_store=MEMORY")

        ddl_population = """
        CREATE TABLE IF NOT EXISTS persistent_population (
            uid                 TEXT    PRIMARY KEY,
            serial              INTEGER NOT NULL,
            given_name          TEXT    NOT NULL,
            family_name         TEXT    NOT NULL,
            gender              TEXT    NOT NULL,
            age_years           REAL    NOT NULL,
            occupation          TEXT    NOT NULL,
            current_location_id TEXT    NOT NULL,
            lat                 REAL    NOT NULL,
            lon                 REAL    NOT NULL,
            wealth              REAL    NOT NULL DEFAULT 100.0,
            health              REAL    NOT NULL DEFAULT 0.95,
            energy              REAL    NOT NULL DEFAULT 0.80,
            hunger              REAL    NOT NULL DEFAULT 0.20,
            happiness           REAL    NOT NULL DEFAULT 0.50,
            community_id        TEXT    NOT NULL DEFAULT 'comunidad_centro',
            district_id         TEXT    NOT NULL DEFAULT 'distrito_san_salvador',
            household_id        TEXT    NOT NULL DEFAULT 'hogar_default',
            lod_tier            INTEGER NOT NULL DEFAULT 2,
            is_exceptional      INTEGER NOT NULL DEFAULT 0,
            exception_reason    TEXT    NOT NULL DEFAULT '',
            packed_state        BLOB,
            updated_tick        INTEGER NOT NULL DEFAULT 0
        );
        """

        ddl_communities = """
        CREATE TABLE IF NOT EXISTS community_aggregates (
            community_id        TEXT    PRIMARY KEY,
            district_id         TEXT    NOT NULL,
            name                TEXT    NOT NULL,
            center_lat          REAL    NOT NULL,
            center_lon          REAL    NOT NULL,
            total_population    INTEGER NOT NULL,
            age_cohorts_json    TEXT    NOT NULL,
            occupations_json    TEXT    NOT NULL,
            total_wealth        REAL    NOT NULL,
            mean_wealth         REAL    NOT NULL,
            gini_coefficient    REAL    NOT NULL,
            food_reserves_kg    REAL    NOT NULL,
            water_reserves_liters REAL  NOT NULL,
            daily_production    REAL    NOT NULL,
            updated_tick        INTEGER NOT NULL DEFAULT 0
        );
        """

        conn.execute(ddl_population)
        conn.execute(ddl_communities)

        # High-selectivity indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pop_district ON persistent_population (district_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pop_community ON persistent_population (community_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pop_lod ON persistent_population (lod_tier);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pop_exceptional ON persistent_population (is_exceptional);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pop_coords ON persistent_population (lat, lon);")
        conn.commit()

    def save_batch(self, records: list[PersistentIndividualRecord], chunk_size: int = 5000) -> None:
        """Persist a large batch of records using chunked executemany transactions."""
        conn = self.db.get_connection()
        sql = """
        INSERT OR REPLACE INTO persistent_population (
            uid, serial, given_name, family_name, gender, age_years, occupation,
            current_location_id, lat, lon, wealth, health, energy, hunger, happiness,
            community_id, district_id, household_id, lod_tier, is_exceptional,
            exception_reason, packed_state, updated_tick
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        total = len(records)
        for i in range(0, total, chunk_size):
            chunk = records[i : i + chunk_size]
            param_tuples = [
                (
                    r.uid,
                    r.serial,
                    r.given_name,
                    r.family_name,
                    r.gender,
                    r.age_years,
                    r.occupation,
                    r.current_location_id,
                    r.lat,
                    r.lon,
                    r.wealth,
                    r.health,
                    r.energy,
                    r.hunger,
                    r.happiness,
                    r.community_id,
                    r.district_id,
                    r.household_id,
                    r.lod_tier,
                    1 if r.is_exceptional else 0,
                    r.exception_reason,
                    r.packed_cognitive_state,
                    r.last_update_tick,
                )
                for r in chunk
            ]
            conn.executemany(sql, param_tuples)
            conn.commit()

    def load_record(self, uid: str) -> Optional[PersistentIndividualRecord]:
        """Fetch a single individual record by UID."""
        conn = self.db.get_connection()
        cur = conn.execute("SELECT * FROM persistent_population WHERE uid = ?", (uid,))
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def load_by_district(self, district_id: str, limit: int = 10000) -> list[PersistentIndividualRecord]:
        """Fetch records by administrative district."""
        conn = self.db.get_connection()
        cur = conn.execute("SELECT * FROM persistent_population WHERE district_id = ? LIMIT ?", (district_id, limit))
        return [self._row_to_record(r) for r in cur.fetchall()]

    def count_total(self) -> int:
        """Return total row count of persistent population."""
        conn = self.db.get_connection()
        cur = conn.execute("SELECT COUNT(*) FROM persistent_population")
        return cur.fetchone()[0]

    def _row_to_record(self, row: sqlite3.Row) -> PersistentIndividualRecord:
        return PersistentIndividualRecord(
            uid=row["uid"],
            serial=row["serial"],
            given_name=row["given_name"],
            family_name=row["family_name"],
            gender=row["gender"],
            age_years=row["age_years"],
            occupation=row["occupation"],
            current_location_id=row["current_location_id"],
            lat=row["lat"],
            lon=row["lon"],
            wealth=row["wealth"],
            health=row["health"],
            energy=row["energy"],
            hunger=row["hunger"],
            happiness=row["happiness"],
            community_id=row["community_id"],
            district_id=row["district_id"],
            household_id=row["household_id"],
            lod_tier=row["lod_tier"],
            is_exceptional=bool(row["is_exceptional"]),
            exception_reason=row["exception_reason"],
            packed_cognitive_state=row["packed_state"],
            last_update_tick=row["updated_tick"],
        )
