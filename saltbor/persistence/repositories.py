"""Repository classes for SQLite-backed persistence in Saltbor.

Provides clean Data Access Objects (DAOs) for humans, relationships,
memories, events, and simulation state checkpoints.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
import uuid
from uuid import UUID

from saltbor.cognition.autonomy.engine import AutonomyEngine, Goal
from saltbor.cognition.cognitive.engine import CognitiveEngine
from saltbor.cognition.decision.engine import DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.learning.engine import LearningEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.cognition.memory.procedural import Skill
from saltbor.cognition.memory.semantic import SemanticFact
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import DataSource, Gender, HumanID, SkillCategory, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.phase09_repositories import (
    CollectiveEnterpriseRepository,
    CommunityRepository,
    ReputationRepository,
    SocialEdgeRepository,
)
from saltbor.persistence.serialization import Serializer
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.social.relationship import Relationship

logger = logging.getLogger(__name__)


class HumanRepository:
    """Persistence operations for SyntheticHuman records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, human: SyntheticHuman) -> None:
        """Insert or replace a synthetic human."""
        data = Serializer.serialize_human(human)
        sql = """
        INSERT OR REPLACE INTO humans (
            uid, serial, given_name, family_name, nickname, data_source,
            demographics_json, physical_state_json, personality_json, emotions_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    data["uid"],
                    data["serial"],
                    data["given_name"],
                    data["family_name"],
                    data["nickname"],
                    data["data_source"],
                    data["demographics_json"],
                    data["physical_state_json"],
                    data["personality_json"],
                    data["emotions_json"],
                ),
            )

    def save_all(self, humans: list[SyntheticHuman]) -> None:
        """Bulk save a list of humans in a single transaction."""
        with self.db.transaction():
            for h in humans:
                self.save(h)

    def load_row(self, uid: HumanID | str) -> Optional[dict[str, Any]]:
        """Fetch raw DB dict for human."""
        sql = "SELECT * FROM humans WHERE uid = ?"
        cur = self.db.execute(sql, (str(uid),))
        row = cur.fetchone()
        return dict(row) if row else None

    def reconstruct_human(self, row_dict: dict[str, Any]) -> SyntheticHuman:
        """Reconstruct a live SyntheticHuman from DB row data."""
        deser = Serializer.deserialize_human_row(row_dict)

        # 1. Identity
        ident = HumanIdentity(
            uid=UUID(deser["uid"]),
            serial=deser["serial"],
            given_name=deser["given_name"],
            family_name=deser["family_name"],
            nickname=deser["nickname"],
            data_source=DataSource(deser["data_source"]),
        )

        # 2. Demographics
        demo_d = deser["demographics"]
        from saltbor.lifecycle.demographics.stages import DevelopmentalStage
        stage_str = demo_d.get("stage", "adulthood")
        try:
            stage_enum = DevelopmentalStage(stage_str)
        except (ValueError, TypeError):
            stage_enum = DevelopmentalStage.ADULTHOOD

        demo = Demographics(
            age=demo_d["age"],
            gender=Gender(demo_d["gender"]),
            occupation=demo_d["occupation"],
            education_level=demo_d["education_level"],
            income_level=demo_d["income_level"],
            native_language=demo_d.get("native_language", "Spanish"),
            data_source=DataSource(demo_d.get("data_source", DataSource.MOCK_GENERATED.value)),
            birth_tick=demo_d.get("birth_tick", 0),
            stage=stage_enum,
        )

        # 3. Physical State
        phys_d = deser["physical_state"]
        phys = PhysicalState(
            energy=phys_d.get("energy", 1.0),
            hunger=phys_d.get("hunger", 0.0),
            health=phys_d.get("health", 1.0),
            current_location_id=phys_d.get("current_location_id"),
            money=phys_d.get("money", 100.0),
            home_location_id=phys_d.get("home_location_id"),
            work_location_id=phys_d.get("work_location_id"),
        )

        # 4. Personality
        pers_d = deser["personality"]
        trait_kwargs = {}
        for t_name in [
            "openness", "conscientiousness", "extraversion", "agreeableness",
            "neuroticism", "risk_tolerance", "patience", "persistence"
        ]:
            if t_name in pers_d:
                t_val = pers_d[t_name]
                trait_kwargs[t_name] = TraitValue(
                    base_value=t_val.get("base_value", 0.5),
                    current_value=t_val.get("current_value", 0.5),
                    temperament_value=t_val.get("temperament_value", t_val.get("base_value", 0.5)),
                    drift_rate=t_val.get("drift_rate", 0.005),
                )
            else:
                trait_kwargs[t_name] = TraitValue(base_value=0.5, current_value=0.5)

        if "temperament_name" in pers_d:
            trait_kwargs["temperament_name"] = pers_d["temperament_name"]
        if "personal_values" in pers_d:
            trait_kwargs["personal_values"] = pers_d["personal_values"]
        if "behavioral_patterns" in pers_d:
            trait_kwargs["behavioral_patterns"] = pers_d["behavioral_patterns"]

        traits = PersonalityTraits(**trait_kwargs)
        personality_eng = PersonalityEngine(traits)

        # 5. Emotions
        emot_d = deser.get("emotions", {})
        if isinstance(emot_d, dict) and "active" in emot_d:
            profile = EmotionalProfile(
                emotional_reactivity=emot_d.get("reactivity", 0.5),
                regulation_capacity=emot_d.get("regulation", 0.5),
                expressiveness=emot_d.get("expressiveness", 0.5),
            )
            from saltbor.cognition.emotions.models import EmotionState
            from saltbor.core.types import EmotionType
            for etype_str, estate_data in emot_d.get("active", {}).items():
                try:
                    etype = EmotionType(etype_str)
                    profile.active_emotions[etype] = EmotionState(
                        emotion_type=etype,
                        intensity=estate_data.get("intensity", 0.5),
                        duration_remaining=estate_data.get("duration_remaining", 10),
                        decay_rate=estate_data.get("decay_rate", 0.02),
                    )
                except ValueError:
                    pass
        else:
            profile = EmotionalProfile()
        emotional_eng = EmotionalEngine(profile=profile)

        # 6. Memory & Autonomy
        mem_eng = MemoryEngine()
        autonomy_eng = AutonomyEngine()
        for g_dict in phys_d.get("goals", []):
            raw_gid = g_dict.get("goal_id", "")
            try:
                gid = UUID(raw_gid)
            except (ValueError, TypeError):
                gid = raw_gid if raw_gid else str(uuid.uuid4())
            g = Goal(
                goal_id=gid,
                description=g_dict.get("description", ""),
                priority=g_dict.get("priority", 0.5),
                category=g_dict.get("category", "general"),
                progress=g_dict.get("progress", 0.0),
                status=g_dict.get("status", "active"),
                plan_steps=g_dict.get("plan_steps", []),
                current_step_index=g_dict.get("current_step_index", 0),
                consecutive_failures=g_dict.get("consecutive_failures", 0),
                procrastination_count=g_dict.get("procrastination_count", 0),
                reasoning=g_dict.get("reasoning", ""),
            )
            autonomy_eng.add_goal(g)

        return SyntheticHuman(
            identity=ident,
            demographics=demo,
            physical_state=phys,
            personality=personality_eng,
            emotions=emotional_eng,
            memory=mem_eng,
            cognition=CognitiveEngine(),
            learning=LearningEngine(),
            autonomy=autonomy_eng,
            decision=DecisionEngine(),
        )

    def load(self, uid: HumanID | str) -> Optional[SyntheticHuman]:
        """Load and reconstruct human by UID."""
        row = self.load_row(uid)
        return self.reconstruct_human(row) if row else None

    def load_all(self) -> list[SyntheticHuman]:
        """Load and reconstruct all humans in the database."""
        cur = self.db.execute("SELECT * FROM humans ORDER BY serial ASC")
        rows = cur.fetchall()
        return [self.reconstruct_human(dict(r)) for r in rows]

    def count(self) -> int:
        cur = self.db.execute("SELECT COUNT(*) FROM humans")
        return int(cur.fetchone()[0])


class RelationshipRepository:
    """Persistence operations for social relationships."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, rel: Relationship) -> None:
        data = Serializer.serialize_relationship(rel)
        sql = """
        INSERT OR REPLACE INTO relationships (
            relationship_id, human_a_uid, human_b_uid, relationship_type,
            trust, affinity, familiarity, interaction_count,
            last_interaction_tick, history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    data["relationship_id"],
                    data["human_a_uid"],
                    data["human_b_uid"],
                    data["relationship_type"],
                    data["trust"],
                    data["affinity"],
                    data["familiarity"],
                    data["interaction_count"],
                    data["last_interaction_tick"],
                    data["history_json"],
                ),
            )

    def save_all(self, relationships: list[Relationship]) -> None:
        with self.db.transaction():
            for rel in relationships:
                self.save(rel)

    def load_all(self) -> list[Relationship]:
        cur = self.db.execute("SELECT * FROM relationships")
        rows = cur.fetchall()
        results: list[Relationship] = []
        for r in rows:
            deser = Serializer.deserialize_relationship(dict(r))
            rel = Relationship(
                relationship_id=deser["relationship_id"],
                human_a_id=deser["human_a_id"],
                human_b_id=deser["human_b_id"],
                relationship_type=deser["relationship_type"],
                trust=deser["trust"],
                affinity=deser["affinity"],
                familiarity=deser["familiarity"],
                interaction_count=deser["interaction_count"],
                last_interaction_tick=deser["last_interaction_tick"],
                history=deser["history"],
            )
            results.append(rel)
        return results


class EventLogRepository:
    """Append and query simulation events."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, event: SimulationEvent) -> None:
        data = Serializer.serialize_event(event)
        sql = """
        INSERT OR REPLACE INTO events_log (
            event_id, event_type, tick, source_human_uid,
            target_human_uid, location_id, data_json, importance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            sql,
            (
                data["event_id"],
                data["event_type"],
                data["tick"],
                data["source_human_uid"],
                data["target_human_uid"],
                data["location_id"],
                data["data_json"],
                data["importance"],
            ),
        )

    def save_all(self, events: list[SimulationEvent]) -> None:
        with self.db.transaction():
            for evt in events:
                self.save(evt)

    def load_recent(self, n: int = 50) -> list[SimulationEvent]:
        cur = self.db.execute(
            "SELECT * FROM events_log ORDER BY tick DESC, rowid DESC LIMIT ?",
            (n,),
        )
        return [Serializer.deserialize_event(dict(r)) for r in cur.fetchall()]

    def count(self) -> int:
        cur = self.db.execute("SELECT COUNT(*) FROM events_log")
        return int(cur.fetchone()[0])


class MemoryRepository:
    """Stores episodic, semantic, procedural memories, and goals."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save_episodic_record(self, human_uid: HumanID, record: EpisodicRecord) -> None:
        data = Serializer.serialize_episodic(record)
        sql = """
        INSERT OR REPLACE INTO memories_episodic (
            memory_id, human_uid, summary, tick, importance,
            emotional_valence, associated_humans_json, location_id,
            access_count, last_accessed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            sql,
            (
                data["memory_id"],
                str(human_uid),
                data["summary"],
                data["tick"],
                data["importance"],
                data["emotional_valence"],
                data["associated_humans_json"],
                data["location_id"],
                data["access_count"],
                data["last_accessed"],
            ),
        )

    def load_episodic_for_human(self, human_uid: HumanID) -> list[EpisodicRecord]:
        cur = self.db.execute(
            "SELECT * FROM memories_episodic WHERE human_uid = ?",
            (str(human_uid),),
        )
        records: list[EpisodicRecord] = []
        for r in cur.fetchall():
            d = Serializer.deserialize_episodic(dict(r))
            records.append(
                EpisodicRecord(
                    memory_id=d["memory_id"],
                    summary=d["summary"],
                    tick=d["tick"],
                    importance=d["importance"],
                    emotional_valence=d["emotional_valence"],
                    associated_humans=d["associated_humans"],
                    location_id=d["location_id"],
                    access_count=d["access_count"],
                    last_accessed=d["last_accessed"],
                )
            )
        return records

    def save_procedural_skill(self, human_uid: HumanID, skill: Skill) -> None:
        data = Serializer.serialize_procedural(skill)
        sql = """
        INSERT OR REPLACE INTO memories_procedural (
            skill_id, human_uid, name, category, level,
            experience_points, practice_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            sql,
            (
                data["skill_id"],
                str(human_uid),
                data["name"],
                data["category"],
                data["level"],
                data["experience_points"],
                data["practice_count"],
            ),
        )

    def load_procedural_for_human(self, human_uid: HumanID) -> list[Skill]:
        cur = self.db.execute(
            "SELECT * FROM memories_procedural WHERE human_uid = ?",
            (str(human_uid),),
        )
        skills: list[Skill] = []
        for r in cur.fetchall():
            d = Serializer.deserialize_procedural(dict(r))
            cat = SkillCategory.TECHNICAL
            try:
                cat = SkillCategory(d["category"])
            except ValueError:
                pass
            skills.append(
                Skill(
                    skill_id=d["skill_id"],
                    name=d["name"],
                    category=cat,
                    level=d["level"],
                    experience_points=d["experience_points"],
                    practice_count=d["practice_count"],
                )
            )
        return skills


class SimulationStateRepository:
    """Key-value persistence for global simulation state checkpoints."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save_state(self, key: str, value: Any) -> None:
        val_json = json.dumps(value, default=str)
        self.db.execute(
            "INSERT OR REPLACE INTO simulation_state (key, value_json) VALUES (?, ?)",
            (key, val_json),
        )

    def load_state(self, key: str) -> Optional[Any]:
        cur = self.db.execute(
            "SELECT value_json FROM simulation_state WHERE key = ?",
            (key,),
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def save_tick(self, tick: Tick) -> None:
        self.save_state("current_tick", tick)

    def load_tick(self) -> Optional[Tick]:
        val = self.load_state("current_tick")
        return int(val) if val is not None else None


class CulturalRepository:
    """Persistence operations for CulturalElement records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, elem: Any) -> None:
        sql = """
        INSERT OR REPLACE INTO cultural_elements (
            element_id, name, element_type, description, origin_human_uid,
            created_tick, practitioners_json, geographic_json, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        pract_json = json.dumps([str(u) for u in elem.practitioners])
        geo_json = json.dumps({str(k): v for k, v in elem.geographic_distribution.items()})
        meta_json = json.dumps({
            "authenticity": elem.authenticity,
            "confidence": elem.confidence,
            "is_abandoned": elem.is_abandoned,
            "last_practiced_tick": elem.last_practiced_tick,
            "mutations_count": elem.mutations_count,
            "required_materials": elem.required_materials,
        })
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    elem.element_id,
                    elem.name,
                    elem.element_type.value if hasattr(elem.element_type, "value") else str(elem.element_type),
                    elem.description,
                    str(elem.origin_human_id) if elem.origin_human_id else None,
                    elem.created_tick,
                    pract_json,
                    geo_json,
                    meta_json,
                ),
            )

    def load_all_dicts(self) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT * FROM cultural_elements")
        rows = cur.fetchall()
        return [dict(r) for r in rows]


class LoanRepository:
    """Persistence operations for LoanContract records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, loan: Any) -> None:
        sql = """
        INSERT OR REPLACE INTO credit_loans (
            loan_id, borrower_uid, lender_uid, lender_institution_id,
            loan_type, principal, interest_rate, balance_remaining,
            status, issued_tick, due_tick, history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        hist_json = json.dumps([
            {
                "tick": p.tick,
                "amount": p.amount,
                "principal": p.principal_portion,
                "interest": p.interest_portion,
                "remaining": p.remaining_balance,
            }
            for p in loan.payments
        ])
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    loan.loan_id,
                    str(loan.borrower_uid),
                    str(loan.lender_uid) if loan.lender_uid else None,
                    loan.lender_institution_id,
                    loan.loan_type.value if hasattr(loan.loan_type, "value") else str(loan.loan_type),
                    loan.principal,
                    loan.interest_rate,
                    loan.balance_remaining,
                    loan.status.value if hasattr(loan.status, "value") else str(loan.status),
                    loan.issued_tick,
                    loan.due_tick,
                    hist_json,
                ),
            )

    def load_all_dicts(self) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT * FROM credit_loans")
        return [dict(r) for r in cur.fetchall()]


class BusinessRepository:
    """Persistence operations for BusinessEnterprise records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, biz: Any) -> None:
        sql = """
        INSERT OR REPLACE INTO businesses (
            business_id, name, business_type, owner_uid, location_id,
            cash_reserve, accumulated_debt, employees_json, status, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        emp_json = json.dumps({str(k): v for k, v in biz.employees.items()})
        meta_json = json.dumps({
            "operating_cost_per_day": biz.operating_cost_per_day,
            "reputation": biz.reputation,
            "max_employees": biz.max_employees,
            "retail_prices": {k.value if hasattr(k, "value") else str(k): v for k, v in biz.retail_prices.items()},
        })
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    biz.business_id,
                    biz.name,
                    biz.business_type.value if hasattr(biz.business_type, "value") else str(biz.business_type),
                    str(biz.owner_uid),
                    biz.location_id,
                    biz.cash_reserve,
                    biz.accumulated_debt,
                    emp_json,
                    biz.status.value if hasattr(biz.status, "value") else str(biz.status),
                    meta_json,
                ),
            )

    def load_all_dicts(self) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT * FROM businesses")
        return [dict(r) for r in cur.fetchall()]


class InstitutionRepository:
    """Persistence operations for SocialInstitution records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, inst: Any) -> None:
        sql = """
        INSERT OR REPLACE INTO institutions (
            institution_id, name, institution_type, headquarters_location_id,
            members_json, treasury_money, reputation, legitimacy, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        members_json = json.dumps({str(k): (v.value if hasattr(v, "value") else str(v)) for k, v in inst.members.items()})
        meta_json = json.dumps({
            "charter_description": inst.charter_description,
            "periodic_dues": inst.periodic_dues,
            "bylaws": inst.bylaws,
            "history_log": inst.history_log[-20:],
        })
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    inst.institution_id,
                    inst.name,
                    inst.institution_type.value if hasattr(inst.institution_type, "value") else str(inst.institution_type),
                    inst.headquarters_location_id,
                    members_json,
                    inst.treasury_money,
                    inst.reputation,
                    inst.legitimacy,
                    meta_json,
                ),
            )

    def load_all_dicts(self) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT * FROM institutions")
        return [dict(r) for r in cur.fetchall()]


class MultiRelationshipRepository:
    """Persistence operations for MultiDimensionalRelationship records."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, rel: Any) -> None:
        sql = """
        INSERT OR REPLACE INTO relationships_multidimensional (
            rel_id, human_a_uid, human_b_uid, rel_type, affection,
            trust, respect, familiarity, cooperation, dependence,
            conflict, resentment, reciprocity, obligation, history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        hist_json = json.dumps([
            {
                "tick": h.tick,
                "type": h.interaction_type,
                "desc": h.description,
                "aff": h.impact_affection,
                "trust": h.impact_trust,
                "respect": h.impact_respect,
                "resent": h.impact_resentment,
            }
            for h in rel.history[-15:]
        ])
        with self.db.transaction():
            self.db.execute(
                sql,
                (
                    rel.relationship_id,
                    str(rel.human_a_id),
                    str(rel.human_b_id),
                    rel.relationship_type.value if hasattr(rel.relationship_type, "value") else str(rel.relationship_type),
                    rel.affection,
                    rel.trust,
                    rel.respect,
                    rel.familiarity,
                    rel.cooperation,
                    rel.dependence,
                    rel.conflict,
                    rel.resentment,
                    rel.reciprocity_balance,
                    rel.social_obligation,
                    hist_json,
                ),
            )

    def load_all_dicts(self) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT * FROM relationships_multidimensional")
        return [dict(r) for r in cur.fetchall()]

