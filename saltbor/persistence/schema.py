"""Database schema creation and version management for Saltbor persistence."""

from __future__ import annotations

import logging

from saltbor.persistence.database import DatabaseManager

logger = logging.getLogger(__name__)

# Current schema version — bump when making breaking changes.
_SCHEMA_VERSION: int = 3


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

    _TABLE_CULTURAL_ELEMENTS = """
    CREATE TABLE IF NOT EXISTS cultural_elements (
        element_id          TEXT    PRIMARY KEY,
        name                TEXT    NOT NULL,
        element_type        TEXT    NOT NULL,
        description         TEXT    NOT NULL DEFAULT '',
        origin_human_uid    TEXT,
        created_tick        INTEGER NOT NULL DEFAULT 0,
        practitioners_json  TEXT    NOT NULL DEFAULT '[]',
        geographic_json     TEXT    NOT NULL DEFAULT '{}',
        metadata_json       TEXT    NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_LOANS = """
    CREATE TABLE IF NOT EXISTS credit_loans (
        loan_id             TEXT    PRIMARY KEY,
        borrower_uid        TEXT    NOT NULL,
        lender_uid          TEXT,
        lender_institution_id TEXT,
        loan_type           TEXT    NOT NULL DEFAULT 'informal_personal',
        principal           REAL    NOT NULL,
        interest_rate       REAL    NOT NULL DEFAULT 0.05,
        balance_remaining   REAL    NOT NULL,
        status              TEXT    NOT NULL DEFAULT 'active',
        issued_tick         INTEGER NOT NULL DEFAULT 0,
        due_tick            INTEGER NOT NULL DEFAULT 0,
        history_json        TEXT    NOT NULL DEFAULT '[]'
    )
    """

    _TABLE_BUSINESSES = """
    CREATE TABLE IF NOT EXISTS businesses (
        business_id         TEXT    PRIMARY KEY,
        name                TEXT    NOT NULL,
        business_type       TEXT    NOT NULL,
        owner_uid           TEXT    NOT NULL,
        location_id         TEXT    NOT NULL,
        cash_reserve        REAL    NOT NULL DEFAULT 0.0,
        accumulated_debt    REAL    NOT NULL DEFAULT 0.0,
        employees_json      TEXT    NOT NULL DEFAULT '{}',
        status              TEXT    NOT NULL DEFAULT 'active',
        metadata_json       TEXT    NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_INSTITUTIONS = """
    CREATE TABLE IF NOT EXISTS institutions (
        institution_id      TEXT    PRIMARY KEY,
        name                TEXT    NOT NULL,
        institution_type    TEXT    NOT NULL,
        headquarters_location_id TEXT NOT NULL,
        members_json        TEXT    NOT NULL DEFAULT '{}',
        treasury_money      REAL    NOT NULL DEFAULT 0.0,
        reputation          REAL    NOT NULL DEFAULT 0.5,
        legitimacy          REAL    NOT NULL DEFAULT 0.8,
        metadata_json       TEXT    NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_MULTI_RELATIONSHIPS = """
    CREATE TABLE IF NOT EXISTS relationships_multidimensional (
        rel_id              TEXT    PRIMARY KEY,
        human_a_uid         TEXT    NOT NULL,
        human_b_uid         TEXT    NOT NULL,
        rel_type            TEXT    NOT NULL DEFAULT 'acquaintance',
        affection           REAL    NOT NULL DEFAULT 0.0,
        trust               REAL    NOT NULL DEFAULT 0.5,
        respect             REAL    NOT NULL DEFAULT 0.5,
        familiarity         REAL    NOT NULL DEFAULT 0.0,
        cooperation         REAL    NOT NULL DEFAULT 0.5,
        dependence          REAL    NOT NULL DEFAULT 0.0,
        conflict            REAL    NOT NULL DEFAULT 0.0,
        resentment          REAL    NOT NULL DEFAULT 0.0,
        reciprocity         REAL    NOT NULL DEFAULT 0.0,
        obligation          REAL    NOT NULL DEFAULT 0.0,
        history_json        TEXT    NOT NULL DEFAULT '[]'
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

    _TABLE_GEO_ENTITIES = """
    CREATE TABLE IF NOT EXISTS geo_entities (
        entity_id       TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        level           TEXT NOT NULL,
        parent_id       TEXT,
        department_code TEXT NOT NULL,
        municipality_id TEXT,
        district_id     TEXT,
        latitude        REAL NOT NULL,
        longitude       REAL NOT NULL,
        elevation_m     REAL NOT NULL DEFAULT 0.0,
        population      INTEGER NOT NULL DEFAULT 0,
        metadata_json   TEXT NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_GEO_ESTABLISHMENTS = """
    CREATE TABLE IF NOT EXISTS geo_establishments (
        establishment_id    TEXT PRIMARY KEY,
        name                TEXT NOT NULL,
        category            TEXT NOT NULL,
        sub_category        TEXT NOT NULL,
        department_code     TEXT NOT NULL,
        municipality_id     TEXT NOT NULL,
        district_id         TEXT NOT NULL,
        latitude            REAL NOT NULL,
        longitude           REAL NOT NULL,
        address             TEXT NOT NULL DEFAULT '',
        source_name         TEXT NOT NULL DEFAULT '',
        validation_state    TEXT NOT NULL DEFAULT 'CONFIRMADO',
        confidence_level    REAL NOT NULL DEFAULT 1.0,
        opening_hours       TEXT NOT NULL DEFAULT '',
        accessibility_rating REAL NOT NULL DEFAULT 0.5,
        metadata_json       TEXT NOT NULL DEFAULT '{}'
    )
    """

    _TABLE_GEO_DATASET_VERSIONS = """
    CREATE TABLE IF NOT EXISTS geo_dataset_versions (
        version_id          TEXT PRIMARY KEY,
        parent_version_id   TEXT,
        created_at_iso      TEXT NOT NULL,
        description         TEXT NOT NULL DEFAULT '',
        checksum            TEXT NOT NULL,
        record_count        INTEGER NOT NULL DEFAULT 0,
        diff_json           TEXT NOT NULL DEFAULT '{}'
    )
    """

    # Phase 0.9 Social Networks, Communities, and Collective Systems
    _TABLE_SOCIAL_EDGES = """
    CREATE TABLE IF NOT EXISTS social_edges (
        edge_id             TEXT PRIMARY KEY,
        source_uid          TEXT NOT NULL,
        target_uid          TEXT NOT NULL,
        relation_types_json TEXT NOT NULL DEFAULT '[]',
        intensity           REAL NOT NULL DEFAULT 0.5,
        trust               REAL NOT NULL DEFAULT 0.5,
        affinity            REAL NOT NULL DEFAULT 0.5,
        reciprocity         REAL NOT NULL DEFAULT 0.0,
        interaction_frequency REAL NOT NULL DEFAULT 0.1,
        conflict_level      REAL NOT NULL DEFAULT 0.0,
        status              TEXT NOT NULL DEFAULT 'active',
        created_tick        INTEGER NOT NULL DEFAULT 0,
        last_interaction_tick INTEGER NOT NULL DEFAULT 0,
        history_json        TEXT NOT NULL DEFAULT '[]'
    )
    """

    _TABLE_COMMUNITIES = """
    CREATE TABLE IF NOT EXISTS emergent_communities (
        community_id        TEXT PRIMARY KEY,
        name                TEXT NOT NULL,
        community_type      TEXT NOT NULL,
        collective_identity TEXT NOT NULL DEFAULT '',
        headquarters_location_id TEXT,
        resources_json      TEXT NOT NULL DEFAULT '{}',
        reputation          REAL NOT NULL DEFAULT 0.6,
        internal_conflict_level REAL NOT NULL DEFAULT 0.0,
        status              TEXT NOT NULL DEFAULT 'stable',
        created_tick        INTEGER NOT NULL DEFAULT 0,
        members_json        TEXT NOT NULL DEFAULT '{}',
        history_json        TEXT NOT NULL DEFAULT '[]'
    )
    """

    _TABLE_COLLECTIVE_ENTERPRISES = """
    CREATE TABLE IF NOT EXISTS collective_enterprises (
        org_id              TEXT PRIMARY KEY,
        name                TEXT NOT NULL,
        org_type            TEXT NOT NULL,
        location_id         TEXT,
        treasury_usd        REAL NOT NULL DEFAULT 0.0,
        shared_inventory_json TEXT NOT NULL DEFAULT '{}',
        members_json        TEXT NOT NULL DEFAULT '{}',
        is_active           INTEGER NOT NULL DEFAULT 1,
        created_tick        INTEGER NOT NULL DEFAULT 0
    )
    """

    _TABLE_REPUTATION_PROFILES = """
    CREATE TABLE IF NOT EXISTS reputation_profiles (
        profile_key         TEXT PRIMARY KEY,
        subject_uid         TEXT NOT NULL,
        observer_uid        TEXT,
        domain              TEXT NOT NULL,
        community_id        TEXT,
        score               REAL NOT NULL DEFAULT 0.5,
        confidence          REAL NOT NULL DEFAULT 0.5,
        fulfilled_agreements INTEGER NOT NULL DEFAULT 0,
        violated_agreements INTEGER NOT NULL DEFAULT 0,
        cooperation_count   INTEGER NOT NULL DEFAULT 0,
        conflict_count      INTEGER NOT NULL DEFAULT 0,
        last_updated_tick   INTEGER NOT NULL DEFAULT 0
    )
    """

    # --- Phase 1.5 Tables ---
    _TABLE_LABOR_VACANCIES = """
    CREATE TABLE IF NOT EXISTS labor_vacancies (
        vacancy_id          TEXT PRIMARY KEY,
        business_id         TEXT NOT NULL,
        employer_uid        TEXT NOT NULL,
        title               TEXT NOT NULL,
        required_skill      TEXT NOT NULL,
        min_skill_level     REAL NOT NULL DEFAULT 0.0,
        offered_daily_wage  REAL NOT NULL DEFAULT 10.0,
        contract_type       TEXT NOT NULL DEFAULT 'informal_wage',
        location_id         TEXT NOT NULL,
        is_filled           INTEGER NOT NULL DEFAULT 0,
        is_cancelled        INTEGER NOT NULL DEFAULT 0,
        created_tick        INTEGER NOT NULL DEFAULT 0
    )
    """

    _TABLE_LABOR_CONTRACTS = """
    CREATE TABLE IF NOT EXISTS labor_contracts (
        contract_id         TEXT PRIMARY KEY,
        employee_uid        TEXT NOT NULL,
        employer_uid        TEXT NOT NULL,
        business_id         TEXT NOT NULL,
        title               TEXT NOT NULL,
        daily_wage          REAL NOT NULL DEFAULT 10.0,
        contract_type       TEXT NOT NULL DEFAULT 'informal_wage',
        location_id         TEXT NOT NULL,
        start_tick          INTEGER NOT NULL DEFAULT 0,
        end_tick            INTEGER,
        is_active           INTEGER NOT NULL DEFAULT 1,
        total_wages_paid    REAL NOT NULL DEFAULT 0.0,
        missed_paydays      INTEGER NOT NULL DEFAULT 0
    )
    """

    _TABLE_HOUSING_UNITS = """
    CREATE TABLE IF NOT EXISTS housing_units (
        unit_id             TEXT PRIMARY KEY,
        name                TEXT NOT NULL,
        location_id         TEXT NOT NULL,
        tenure_type         TEXT NOT NULL DEFAULT 'rental',
        capacity            INTEGER NOT NULL DEFAULT 4,
        rent_per_day        REAL NOT NULL DEFAULT 0.0,
        owner_uid           TEXT,
        quality_score       REAL NOT NULL DEFAULT 0.70
    )
    """

    _TABLE_HOUSING_LEASES = """
    CREATE TABLE IF NOT EXISTS housing_leases (
        lease_id            TEXT PRIMARY KEY,
        unit_id             TEXT NOT NULL,
        tenant_uid          TEXT NOT NULL,
        landlord_uid        TEXT,
        rent_per_day        REAL NOT NULL DEFAULT 0.0,
        start_tick          INTEGER NOT NULL DEFAULT 0,
        end_tick            INTEGER,
        is_active           INTEGER NOT NULL DEFAULT 1,
        total_rent_paid     REAL NOT NULL DEFAULT 0.0,
        accumulated_arrears REAL NOT NULL DEFAULT 0.0
    )
    """

    _TABLE_COMMERCIAL_ESTABLISHMENTS = """
    CREATE TABLE IF NOT EXISTS commercial_establishments (
        establishment_id    TEXT PRIMARY KEY,
        name                TEXT NOT NULL,
        establishment_type  TEXT NOT NULL,
        location_id         TEXT NOT NULL,
        is_verified_real    INTEGER NOT NULL DEFAULT 0,
        cash_box_usd        REAL NOT NULL DEFAULT 50.0,
        operating_cost_per_day REAL NOT NULL DEFAULT 4.0,
        reputation          REAL NOT NULL DEFAULT 0.75
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
        # Geographic lookups
        "CREATE INDEX IF NOT EXISTS idx_geo_establishments_dept ON geo_establishments(department_code)",
        "CREATE INDEX IF NOT EXISTS idx_geo_establishments_muni ON geo_establishments(municipality_id)",
        "CREATE INDEX IF NOT EXISTS idx_geo_establishments_dist ON geo_establishments(district_id)",
        "CREATE INDEX IF NOT EXISTS idx_geo_establishments_cat ON geo_establishments(category)",
        "CREATE INDEX IF NOT EXISTS idx_geo_entities_dept ON geo_entities(department_code)",
        "CREATE INDEX IF NOT EXISTS idx_geo_entities_level ON geo_entities(level)",
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
            cls._TABLE_CULTURAL_ELEMENTS,
            cls._TABLE_LOANS,
            cls._TABLE_BUSINESSES,
            cls._TABLE_INSTITUTIONS,
            cls._TABLE_MULTI_RELATIONSHIPS,
            cls._TABLE_GEO_ENTITIES,
            cls._TABLE_GEO_ESTABLISHMENTS,
            cls._TABLE_GEO_DATASET_VERSIONS,
            cls._TABLE_SOCIAL_EDGES,
            cls._TABLE_COMMUNITIES,
            cls._TABLE_COLLECTIVE_ENTERPRISES,
            cls._TABLE_REPUTATION_PROFILES,
            cls._TABLE_LABOR_VACANCIES,
            cls._TABLE_LABOR_CONTRACTS,
            cls._TABLE_HOUSING_UNITS,
            cls._TABLE_HOUSING_LEASES,
            cls._TABLE_COMMERCIAL_ESTABLISHMENTS,
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
