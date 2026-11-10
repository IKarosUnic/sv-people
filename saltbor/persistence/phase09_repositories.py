"""Repositories for Phase 0.9 Social Networks, Communities, and Collective Systems."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from saltbor.persistence.database import DatabaseManager
from saltbor.social.network.graph_engine import SocialEdge, SocialRelationType, BondState
from saltbor.social.community.engine import Community, CommunityType, CommunityStatus, CommunityMembership, MembershipRole
from saltbor.social.economy.collective_economy import CollectiveEnterprise, CollectiveOrgType, EconomicMemberShare
from saltbor.social.reputation.reputation_system import ContextualReputationRecord, ReputationDomain

logger = logging.getLogger(__name__)


class SocialEdgeRepository:
    """Persistence operations for SocialEdge dynamic graph ties."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, edge: SocialEdge) -> None:
        sql = """
        INSERT OR REPLACE INTO social_edges (
            edge_id, source_uid, target_uid, relation_types_json,
            intensity, trust, affinity, reciprocity, interaction_frequency,
            conflict_level, status, created_tick, last_interaction_tick, history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        types_json = json.dumps([r.value for r in edge.relation_types])
        hist_json = json.dumps(edge.history[-50:])
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    edge.edge_id,
                    edge.source_id,
                    edge.target_id,
                    types_json,
                    edge.intensity,
                    edge.trust,
                    edge.affinity,
                    edge.reciprocity,
                    edge.interaction_frequency,
                    edge.conflict_level,
                    edge.status.value,
                    edge.created_tick,
                    edge.last_interaction_tick,
                    hist_json,
                ),
            )

    def save_all(self, edges: list[SocialEdge]) -> None:
        with self.db.transaction():
            for e in edges:
                self.save(e)

    def load_all(self) -> list[SocialEdge]:
        rows = self.db.execute("SELECT * FROM social_edges").fetchall()
        edges: list[SocialEdge] = []
        for r in rows:
            types = {SocialRelationType(v) for v in json.loads(r["relation_types_json"])}
            status = BondState(r["status"])
            history = json.loads(r["history_json"])
            edge = SocialEdge(
                edge_id=r["edge_id"],
                source_id=r["source_uid"],
                target_id=r["target_uid"],
                relation_types=types,
                intensity=r["intensity"],
                trust=r["trust"],
                affinity=r["affinity"],
                reciprocity=r["reciprocity"],
                interaction_frequency=r["interaction_frequency"],
                conflict_level=r["conflict_level"],
                status=status,
                created_tick=r["created_tick"],
                last_interaction_tick=r["last_interaction_tick"],
                history=history,
            )
            edges.append(edge)
        return edges

    def count(self) -> int:
        row = self.db.execute("SELECT COUNT(*) as c FROM social_edges").fetchone()
        return row["c"] if row else 0


class CommunityRepository:
    """Persistence operations for Emergent Community instances."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, community: Community) -> None:
        sql = """
        INSERT OR REPLACE INTO emergent_communities (
            community_id, name, community_type, collective_identity,
            headquarters_location_id, resources_json, reputation,
            internal_conflict_level, status, created_tick, members_json, history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        members_data = {
            uid: {
                "role": m.role.value,
                "joined_tick": m.joined_tick,
                "commitment": m.commitment,
                "status": m.status,
                "satisfaction": m.satisfaction,
            }
            for uid, m in community.members.items()
        }
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    community.community_id,
                    community.name,
                    community.community_type.value,
                    community.collective_identity,
                    community.headquarters_location_id,
                    json.dumps(community.resources),
                    community.reputation,
                    community.internal_conflict_level,
                    community.status.value,
                    community.created_tick,
                    json.dumps(members_data),
                    json.dumps(community.history[-50:]),
                ),
            )

    def load_all(self) -> list[Community]:
        rows = self.db.execute("SELECT * FROM emergent_communities").fetchall()
        communities: list[Community] = []
        for r in rows:
            comm = Community(
                community_id=r["community_id"],
                name=r["name"],
                community_type=CommunityType(r["community_type"]),
                collective_identity=r["collective_identity"],
                headquarters_location_id=r["headquarters_location_id"],
                resources=json.loads(r["resources_json"]),
                reputation=r["reputation"],
                internal_conflict_level=r["internal_conflict_level"],
                status=CommunityStatus(r["status"]),
                created_tick=r["created_tick"],
                history=json.loads(r["history_json"]),
            )
            members_raw = json.loads(r["members_json"])
            for uid, mdata in members_raw.items():
                comm.members[uid] = CommunityMembership(
                    human_uid=uid,
                    role=MembershipRole(mdata["role"]),
                    joined_tick=mdata["joined_tick"],
                    commitment=mdata["commitment"],
                    status=mdata["status"],
                    satisfaction=mdata["satisfaction"],
                )
            communities.append(comm)
        return communities


class CollectiveEnterpriseRepository:
    """Persistence operations for Collective Enterprise records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, enterprise: CollectiveEnterprise) -> None:
        sql = """
        INSERT OR REPLACE INTO collective_enterprises (
            org_id, name, org_type, location_id, treasury_usd,
            shared_inventory_json, members_json, is_active, created_tick
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        members_data = {
            uid: {
                "role": m.role,
                "equity_ratio": m.equity_ratio,
                "invested_capital": m.invested_capital,
                "accumulated_dividends": m.accumulated_dividends,
            }
            for uid, m in enterprise.members.items()
        }
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    enterprise.org_id,
                    enterprise.name,
                    enterprise.org_type.value,
                    enterprise.location_id,
                    enterprise.treasury_usd,
                    json.dumps(enterprise.shared_inventory),
                    json.dumps(members_data),
                    1 if enterprise.is_active else 0,
                    enterprise.created_tick,
                ),
            )

    def load_all(self) -> list[CollectiveEnterprise]:
        rows = self.db.execute("SELECT * FROM collective_enterprises").fetchall()
        enterprises: list[CollectiveEnterprise] = []
        for r in rows:
            ent = CollectiveEnterprise(
                org_id=r["org_id"],
                name=r["name"],
                org_type=CollectiveOrgType(r["org_type"]),
                location_id=r["location_id"],
                treasury_usd=r["treasury_usd"],
                shared_inventory=json.loads(r["shared_inventory_json"]),
                is_active=bool(r["is_active"]),
                created_tick=r["created_tick"],
            )
            members_raw = json.loads(r["members_json"])
            for uid, mdata in members_raw.items():
                ent.members[uid] = EconomicMemberShare(
                    human_uid=uid,
                    role=mdata["role"],
                    equity_ratio=mdata["equity_ratio"],
                    invested_capital=mdata["invested_capital"],
                    accumulated_dividends=mdata["accumulated_dividends"],
                )
            enterprises.append(ent)
        return enterprises


class ReputationRepository:
    """Persistence operations for Contextual Reputation records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, record: ContextualReputationRecord) -> None:
        sql = """
        INSERT OR REPLACE INTO reputation_profiles (
            profile_key, subject_uid, observer_uid, domain, community_id,
            score, confidence, fulfilled_agreements, violated_agreements,
            cooperation_count, conflict_count, last_updated_tick
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        key = f"{record.subject_uid}_{record.observer_uid or 'global'}_{record.domain.value}_{record.community_id or 'none'}"
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    key,
                    record.subject_uid,
                    record.observer_uid,
                    record.domain.value,
                    record.community_id,
                    record.score,
                    record.confidence,
                    record.fulfilled_agreements,
                    record.violated_agreements,
                    record.cooperation_count,
                    record.conflict_count,
                    record.last_updated_tick,
                ),
            )

    def load_all(self) -> list[ContextualReputationRecord]:
        rows = self.db.execute("SELECT * FROM reputation_profiles").fetchall()
        records: list[ContextualReputationRecord] = []
        for r in rows:
            rec = ContextualReputationRecord(
                subject_uid=r["subject_uid"],
                observer_uid=r["observer_uid"],
                domain=ReputationDomain(r["domain"]),
                community_id=r["community_id"],
                score=r["score"],
                confidence=r["confidence"],
                fulfilled_agreements=r["fulfilled_agreements"],
                violated_agreements=r["violated_agreements"],
                cooperation_count=r["cooperation_count"],
                conflict_count=r["conflict_count"],
                last_updated_tick=r["last_updated_tick"],
            )
            records.append(rec)
        return records
