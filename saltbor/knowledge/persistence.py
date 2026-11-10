"""SQLite Persistence Adapter for Saltbor Knowledge Graph Architecture.

Handles serialization, saving, and loading of canonical nodes, relationships,
individual epistemic overlays, collective repositories, and hypotheses.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph, CollectiveKnowledgeItem
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.hypothesis_graph import Hypothesis, HypothesisDiscoveryGraph
from saltbor.knowledge.layers.individual_graph import EpistemicClaim, IndividualKnowledgeGraph
from saltbor.persistence.database import DatabaseManager

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    """DAO for Knowledge Graph entities and individual overlays in SQLite."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.create_tables()

    def create_tables(self) -> None:
        """Create knowledge tables if they do not exist."""
        conn = self.db.get_connection()
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                node_id             TEXT    PRIMARY KEY,
                node_type           TEXT    NOT NULL,
                label               TEXT    NOT NULL,
                description         TEXT    NOT NULL DEFAULT '',
                properties_json     TEXT    NOT NULL DEFAULT '{}',
                created_tick        INTEGER NOT NULL DEFAULT 0,
                origin_type         TEXT    NOT NULL DEFAULT 'world_genesis',
                origin_id           TEXT,
                validation_status   TEXT    NOT NULL DEFAULT 'canonical',
                version             INTEGER NOT NULL DEFAULT 1,
                external_ref        TEXT
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                rel_id              TEXT    PRIMARY KEY,
                source_id           TEXT    NOT NULL,
                target_id           TEXT    NOT NULL,
                rel_type            TEXT    NOT NULL,
                weight              REAL    NOT NULL DEFAULT 1.0,
                confidence          REAL    NOT NULL DEFAULT 1.0,
                provenance_source   TEXT    NOT NULL DEFAULT 'canonical',
                created_tick        INTEGER NOT NULL DEFAULT 0,
                metadata_json       TEXT    NOT NULL DEFAULT '{}'
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS individual_knowledge (
                human_uid           TEXT    NOT NULL,
                target_id           TEXT    NOT NULL,
                is_relationship     INTEGER NOT NULL DEFAULT 0,
                confidence          REAL    NOT NULL DEFAULT 0.5,
                source_pathway      TEXT    NOT NULL DEFAULT 'observation',
                source_agent_id     TEXT,
                acquired_tick       INTEGER NOT NULL DEFAULT 0,
                last_verified_tick  INTEGER NOT NULL DEFAULT 0,
                verification_count  INTEGER NOT NULL DEFAULT 1,
                contradiction_count INTEGER NOT NULL DEFAULT 0,
                is_misconception    INTEGER NOT NULL DEFAULT 0,
                is_forgotten        INTEGER NOT NULL DEFAULT 0,
                personal_notes_json TEXT    NOT NULL DEFAULT '{}',
                PRIMARY KEY (human_uid, target_id)
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS collective_knowledge (
                group_id            TEXT    NOT NULL,
                item_id             TEXT    NOT NULL,
                is_relationship     INTEGER NOT NULL DEFAULT 0,
                group_type          TEXT    NOT NULL DEFAULT 'community',
                consensus_level     REAL    NOT NULL DEFAULT 0.8,
                documentation_type  TEXT    NOT NULL DEFAULT 'oral_tradition',
                custodian_uids_json TEXT    NOT NULL DEFAULT '[]',
                recorded_tick       INTEGER NOT NULL DEFAULT 0,
                is_endangered       INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (group_id, item_id)
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS hypotheses_records (
                hypothesis_id       TEXT    PRIMARY KEY,
                creator_uid         TEXT    NOT NULL,
                title               TEXT    NOT NULL,
                target_phenomenon   TEXT    NOT NULL DEFAULT '',
                statement           TEXT    NOT NULL DEFAULT '',
                assumptions_json    TEXT    NOT NULL DEFAULT '[]',
                status              TEXT    NOT NULL DEFAULT 'proposed',
                prior_confidence    REAL    NOT NULL DEFAULT 0.5,
                posterior_confidence REAL   NOT NULL DEFAULT 0.5,
                created_tick        INTEGER NOT NULL DEFAULT 0,
                updated_tick        INTEGER NOT NULL DEFAULT 0,
                replications_count  INTEGER NOT NULL DEFAULT 0
            )
            """)

            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knodes_type ON knowledge_nodes(node_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_krels_source ON knowledge_relationships(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_krels_target ON knowledge_relationships(target_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_indiv_human ON individual_knowledge(human_uid)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collec_group ON collective_knowledge(group_id)")

    # -------------------------------------------------------------------------
    # Node & Relationship Persistence
    # -------------------------------------------------------------------------

    def save_node(self, node: KnowledgeNode) -> None:
        conn = self.db.get_connection()
        t_val = str(node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type)
        v_val = str(node.validation_status.value if isinstance(node.validation_status, ValidationStatus) else node.validation_status)
        with conn:
            conn.execute("""
            INSERT OR REPLACE INTO knowledge_nodes (
                node_id, node_type, label, description, properties_json,
                created_tick, origin_type, origin_id, validation_status, version, external_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node.node_id,
                t_val,
                node.label,
                node.description,
                json.dumps(node.properties),
                node.created_tick,
                node.origin_type,
                node.origin_id,
                v_val,
                node.version,
                node.external_ref,
            ))

    def load_node(self, node_id: str) -> Optional[KnowledgeNode]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM knowledge_nodes WHERE node_id = ?", (node_id,))
        row = cur.fetchone()
        if not row:
            return None
        return KnowledgeNode(
            node_id=row["node_id"],
            node_type=row["node_type"],
            label=row["label"],
            description=row["description"],
            properties=json.loads(row["properties_json"]),
            created_tick=row["created_tick"],
            origin_type=row["origin_type"],
            origin_id=row["origin_id"],
            validation_status=row["validation_status"],
            version=row["version"],
            external_ref=row["external_ref"],
        )

    def save_relationship(self, rel: KnowledgeRelationship) -> None:
        conn = self.db.get_connection()
        r_val = str(rel.rel_type.value if isinstance(rel.rel_type, RelationshipType) else rel.rel_type)
        with conn:
            conn.execute("""
            INSERT OR REPLACE INTO knowledge_relationships (
                rel_id, source_id, target_id, rel_type, weight, confidence,
                provenance_source, created_tick, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rel.rel_id,
                rel.source_id,
                rel.target_id,
                r_val,
                rel.weight,
                rel.confidence,
                rel.provenance_source,
                rel.created_tick,
                json.dumps(rel.metadata),
            ))

    def load_relationship(self, rel_id: str) -> Optional[KnowledgeRelationship]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM knowledge_relationships WHERE rel_id = ?", (rel_id,))
        row = cur.fetchone()
        if not row:
            return None
        return KnowledgeRelationship(
            rel_id=row["rel_id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            rel_type=row["rel_type"],
            weight=row["weight"],
            confidence=row["confidence"],
            provenance_source=row["provenance_source"],
            created_tick=row["created_tick"],
            metadata=json.loads(row["metadata_json"]),
        )

    # -------------------------------------------------------------------------
    # Individual Knowledge Persistence
    # -------------------------------------------------------------------------

    def save_individual_knowledge(self, graph: IndividualKnowledgeGraph) -> None:
        conn = self.db.get_connection()
        with conn:
            for node_id, claim in graph._node_claims.items():
                conn.execute("""
                INSERT OR REPLACE INTO individual_knowledge (
                    human_uid, target_id, is_relationship, confidence, source_pathway,
                    source_agent_id, acquired_tick, last_verified_tick, verification_count,
                    contradiction_count, is_misconception, is_forgotten, personal_notes_json
                ) VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    graph.human_uid,
                    node_id,
                    claim.confidence,
                    claim.source_pathway,
                    claim.source_agent_id,
                    claim.acquired_tick,
                    claim.last_verified_tick,
                    claim.verification_count,
                    claim.contradiction_count,
                    1 if claim.is_misconception else 0,
                    1 if claim.is_forgotten else 0,
                    json.dumps(claim.personal_notes),
                ))

            for rel_id, claim in graph._rel_claims.items():
                conn.execute("""
                INSERT OR REPLACE INTO individual_knowledge (
                    human_uid, target_id, is_relationship, confidence, source_pathway,
                    source_agent_id, acquired_tick, last_verified_tick, verification_count,
                    contradiction_count, is_misconception, is_forgotten, personal_notes_json
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    graph.human_uid,
                    rel_id,
                    claim.confidence,
                    claim.source_pathway,
                    claim.source_agent_id,
                    claim.acquired_tick,
                    claim.last_verified_tick,
                    claim.verification_count,
                    claim.contradiction_count,
                    1 if claim.is_misconception else 0,
                    1 if claim.is_forgotten else 0,
                    json.dumps(claim.personal_notes),
                ))

    def load_individual_knowledge(
        self,
        human_uid: str,
        global_graph: Optional[GlobalKnowledgeGraph] = None,
    ) -> IndividualKnowledgeGraph:
        graph = IndividualKnowledgeGraph(human_uid=human_uid, global_graph=global_graph)
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM individual_knowledge WHERE human_uid = ?", (human_uid,))
        rows = cur.fetchall()

        for row in rows:
            claim = EpistemicClaim(
                target_id=row["target_id"],
                is_relationship=bool(row["is_relationship"]),
                confidence=row["confidence"],
                source_pathway=row["source_pathway"],
                source_agent_id=row["source_agent_id"],
                acquired_tick=row["acquired_tick"],
                last_verified_tick=row["last_verified_tick"],
                verification_count=row["verification_count"],
                contradiction_count=row["contradiction_count"],
                is_misconception=bool(row["is_misconception"]),
                is_forgotten=bool(row["is_forgotten"]),
                personal_notes=json.loads(row["personal_notes_json"]),
            )
            if claim.is_relationship:
                graph._rel_claims[claim.target_id] = claim
            else:
                graph._node_claims[claim.target_id] = claim

        return graph

    # -------------------------------------------------------------------------
    # Hypothesis Persistence
    # -------------------------------------------------------------------------

    def save_hypothesis(self, hyp: Hypothesis) -> None:
        conn = self.db.get_connection()
        s_val = str(hyp.status.value if isinstance(hyp.status, ValidationStatus) else hyp.status)
        with conn:
            conn.execute("""
            INSERT OR REPLACE INTO hypotheses_records (
                hypothesis_id, creator_uid, title, target_phenomenon, statement,
                assumptions_json, status, prior_confidence, posterior_confidence,
                created_tick, updated_tick, replications_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hyp.hypothesis_id,
                hyp.creator_uid,
                hyp.title,
                hyp.target_phenomenon,
                hyp.statement,
                json.dumps(hyp.assumptions),
                s_val,
                hyp.prior_confidence,
                hyp.posterior_confidence,
                hyp.created_tick,
                hyp.updated_tick,
                hyp.replications_count,
            ))

    def load_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM hypotheses_records WHERE hypothesis_id = ?", (hypothesis_id,))
        row = cur.fetchone()
        if not row:
            return None
        return Hypothesis(
            hypothesis_id=row["hypothesis_id"],
            creator_uid=row["creator_uid"],
            title=row["title"],
            target_phenomenon=row["target_phenomenon"],
            statement=row["statement"],
            assumptions=json.loads(row["assumptions_json"]),
            status=row["status"],
            prior_confidence=row["prior_confidence"],
            posterior_confidence=row["posterior_confidence"],
            created_tick=row["created_tick"],
            updated_tick=row["updated_tick"],
            replications_count=row["replications_count"],
        )
