"""Database schema creation and version management for Saltbor persistence."""

from __future__ import annotations

import logging

from saltbor.persistence.database import DatabaseManager

logger = logging.getLogger(__name__)

# Current schema version — bump when making breaking changes.
_SCHEMA_VERSION: int = 1


class SchemaManager:
    """Creates and migrates the SQLite schema used by Saltbor.

    All methods are class-level so callers do not need to instantiate.
    """

    # ------------------------------------------------------------------
    # Table DDL
    # ------------------------------------------------------------------

    _TABLE_HUMANS = """
    CREATE TABLE IF NOT EXISTS humans (
        uid             TEXT    PRIMARY KEY,
        serial          INTEGER NOT NULL,
        given_name      TEXT    NOT NULL DEFAULT '',
        family_name     TEXT    NOT NULL DEFAULT '',
        nickname        TEXT,
        data_source     TEXT    NOT NULL DEFAULT 'mock_generated',
        demographics_json   TEXT NOT NULL DEFAULT '{}',
        physical_state_json TEXT NOT NULL DEFAULT '{}',
        personality_json    TEXT NOT NULL DEFAULT '{}',
        emotions_json       TEXT NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_MEMORIES_EPISODIC = """
    CREATE TABLE IF NOT EXISTS memories_episodic (
        memory_id           TEXT    PRIMARY KEY,
        human_uid           TEXT    NOT NULL,
        summary             TEXT    NOT NULL DEFAULT '',
        tick                INTEGER NOT NULL DEFAULT 0,
        importance          REAL    NOT NULL DEFAULT 0.5,
        emotional_valence   REAL    NOT NULL DEFAULT 0.0,
        associated_humans_json TEXT NOT NULL DEFAULT '[]',
        location_id         TEXT,
        access_count        INTEGER NOT NULL DEFAULT 0,
        last_accessed       INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (human_uid) REFERENCES humans(uid) ON DELETE CASCADE
    )
    """

    _TABLE_MEMORIES_SEMANTIC = """
    CREATE TABLE IF NOT EXISTS memories_semantic (
        fact_id         TEXT    NOT NULL,
        human_uid       TEXT    NOT NULL,
        category        TEXT    NOT NULL DEFAULT '',
        content         TEXT    NOT NULL DEFAULT '',
        confidence      REAL    NOT NULL DEFAULT 1.0,
        source          TEXT    NOT NULL DEFAULT '',
        learned_tick    INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (human_uid, fact_id),
        FOREIGN KEY (human_uid) REFERENCES humans(uid) ON DELETE CASCADE
    )
    """

    _TABLE_MEMORIES_PROCEDURAL = """
    CREATE TABLE IF NOT EXISTS memories_procedural (
        skill_id            TEXT    NOT NULL,
        human_uid           TEXT    NOT NULL,
        name                TEXT    NOT NULL DEFAULT '',
        category            TEXT    NOT NULL DEFAULT '',
        level               REAL    NOT NULL DEFAULT 0.0,
        experience_points   REAL    NOT NULL DEFAULT 0.0,
        practice_count      INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (human_uid, skill_id),
        FOREIGN KEY (human_uid) REFERENCES humans(uid) ON DELETE CASCADE
    )
    """

    _TABLE_RELATIONSHIPS = """
    CREATE TABLE IF NOT EXISTS relationships (
        relationship_id     TEXT    PRIMARY KEY,
        human_a_uid         TEXT    NOT NULL,
        human_b_uid         TEXT    NOT NULL,
        relationship_type   TEXT    NOT NULL DEFAULT 'stranger',
        trust               REAL    NOT NULL DEFAULT 0.5,
        affinity            REAL    NOT NULL DEFAULT 0.5,
        familiarity         REAL    NOT NULL DEFAULT 0.0,
        interaction_count   INTEGER NOT NULL DEFAULT 0,
        last_interaction_tick INTEGER NOT NULL DEFAULT 0,
        history_json        TEXT    NOT NULL DEFAULT '[]',
        FOREIGN KEY (human_a_uid) REFERENCES humans(uid) ON DELETE CASCADE,
        FOREIGN KEY (human_b_uid) REFERENCES humans(uid) ON DELETE CASCADE
    )
    """

    _TABLE_EVENTS_LOG = """
    CREATE TABLE IF NOT EXISTS events_log (
        event_id            TEXT    PRIMARY KEY,
        event_type          TEXT    NOT NULL,
        tick                INTEGER NOT NULL DEFAULT 0,
        source_human_uid    TEXT,
        target_human_uid    TEXT,
        location_id         TEXT,
        data_json           TEXT    NOT NULL DEFAULT '{}',
        importance          REAL    NOT NULL DEFAULT 0.5
    )
    """

    _TABLE_SIMULATION_STATE = """
    CREATE TABLE IF NOT EXISTS simulation_state (
        key         TEXT PRIMARY KEY,
        value_json  TEXT NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_GOALS = """
    CREATE TABLE IF NOT EXISTS goals (
        goal_id         TEXT    PRIMARY KEY,
        human_uid       TEXT    NOT NULL,
        description     TEXT    NOT NULL DEFAULT '',
        priority        REAL    NOT NULL DEFAULT 0.5,
        need_type       TEXT,
        progress        REAL    NOT NULL DEFAULT 0.0,
        deadline_tick   INTEGER,
        status          TEXT    NOT NULL DEFAULT 'active',
        FOREIGN KEY (human_uid) REFERENCES humans(uid) ON DELETE CASCADE
    )
    """

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------

    _INDEXES: list[str] = [
        # Per-human lookups
        "CREATE INDEX IF NOT EXISTS idx_episodic_human ON memories_episodic(human_uid)",
        "CREATE INDEX IF NOT EXISTS idx_semantic_human ON memories_semantic(human_uid)",
        "CREATE INDEX IF NOT EXISTS idx_procedural_human ON memories_procedural(human_uid)",
        "CREATE INDEX IF NOT EXISTS idx_relationships_a ON relationships(human_a_uid)",
        "CREATE INDEX IF NOT EXISTS idx_relationships_b ON relationships(human_b_uid)",
        "CREATE INDEX IF NOT EXISTS idx_goals_human ON goals(human_uid)",
        # Tick-based lookups
        "CREATE INDEX IF NOT EXISTS idx_episodic_tick ON memories_episodic(tick)",
        "CREATE INDEX IF NOT EXISTS idx_events_tick ON events_log(tick)",
        # Event-type lookups
        "CREATE INDEX IF NOT EXISTS idx_events_type ON events_log(event_type)",
        # Events by human
        "CREATE INDEX IF NOT EXISTS idx_events_source ON events_log(source_human_uid)",
        "CREATE INDEX IF NOT EXISTS idx_events_target ON events_log(target_human_uid)",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def create_tables(cls, db: DatabaseManager) -> None:
        """Create all tables and indexes if they don't already exist.

        Parameters:
            db: An *open* :class:`DatabaseManager`.
        """
        conn = db.get_connection()
        for ddl in (
            cls._TABLE_HUMANS,
            cls._TABLE_MEMORIES_EPISODIC,
            cls._TABLE_MEMORIES_SEMANTIC,
            cls._TABLE_MEMORIES_PROCEDURAL,
            cls._TABLE_RELATIONSHIPS,
            cls._TABLE_EVENTS_LOG,
            cls._TABLE_SIMULATION_STATE,
            cls._TABLE_GOALS,
        ):
            conn.execute(ddl)

        for idx in cls._INDEXES:
            conn.execute(idx)

        conn.commit()

        # Store schema version if not already present.
        current = cls.get_schema_version(db)
        if current is None:
            cls.set_schema_version(db, _SCHEMA_VERSION)

        logger.info("Schema ready (version %s).", cls.get_schema_version(db))

    @classmethod
    def get_schema_version(cls, db: DatabaseManager) -> int | None:
        """Return the current schema version, or ``None`` if unset."""
        try:
            row = db.execute(
                "SELECT value_json FROM simulation_state WHERE key = 'schema_version'"
            ).fetchone()
        except Exception:
            return None
        if row is None:
            return None
        import json

        return int(json.loads(row["value_json"]))

    @classmethod
    def set_schema_version(cls, db: DatabaseManager, version: int) -> None:
        """Persist the schema version number."""
        import json

        db.execute(
            "INSERT OR REPLACE INTO simulation_state (key, value_json) VALUES (?, ?)",
            ("schema_version", json.dumps(version)),
        )
        db.get_connection().commit()
