"""Serialization and deserialization helpers for persisting simulation objects.

Converts rich domain objects to/from flat dictionaries suitable for SQLite
storage.  Nested structures (demographics, personality, emotions, etc.) are
stored as JSON text columns.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from saltbor.core.types import (
    DataSource,
    EmotionType,
    Gender,
    NeedType,
    RelationshipType,
)
from saltbor.events.types import EventType, SimulationEvent

logger = logging.getLogger(__name__)


def _uuid_str(val: Any) -> str | None:
    """Coerce a UUID or string to its string form, or return None."""
    if val is None:
        return None
    return str(val)


def _uuid_or_none(val: Any) -> UUID | None:
    """Coerce a string back to :class:`UUID`, or return ``None``."""
    if val is None or val == "":
        return None
    return UUID(str(val))


class Serializer:
    """Converts domain objects to DB-ready dicts and back.

    All ``serialize_*`` methods return a flat :class:`dict` whose keys match
    the column names of the corresponding table.  Nested sub-objects are
    JSON-encoded into ``*_json`` columns.

    All ``deserialize_*`` methods accept a :class:`sqlite3.Row` (or any
    mapping with string keys) and reconstruct the domain object.
    """

    # ------------------------------------------------------------------
    # SyntheticHuman
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_human(human: Any) -> dict[str, Any]:
        """Serialize a *SyntheticHuman* into a flat dict for the ``humans`` table.

        Parameters:
            human: A SyntheticHuman instance.  Only its public attributes are
                accessed, so duck-typing is sufficient.

        Returns:
            Dict with keys matching ``humans`` table columns.
        """
        identity = human.identity

        # Demographics — convert the dataclass / model to a plain dict.
        demographics_data: dict[str, Any] = {}
        if hasattr(human, "demographics") and human.demographics is not None:
            demo = human.demographics
            demographics_data = {
                "age": getattr(demo, "age", None),
                "gender": getattr(demo, "gender", Gender.MALE).value
                if hasattr(getattr(demo, "gender", None), "value")
                else str(getattr(demo, "gender", "")),
                "occupation": getattr(demo, "occupation", ""),
                "education_level": getattr(demo, "education_level", ""),
                "income_level": getattr(demo, "income_level", ""),
                "native_language": getattr(demo, "native_language", ""),
                "data_source": getattr(demo, "data_source", DataSource.MOCK_GENERATED).value
                if hasattr(getattr(demo, "data_source", None), "value")
                else str(getattr(demo, "data_source", "")),
            }

        # Physical state
        physical_data: dict[str, Any] = {}
        if hasattr(human, "physical_state") and human.physical_state is not None:
            ps = human.physical_state
            physical_data = {
                "energy": getattr(ps, "energy", 1.0),
                "hunger": getattr(ps, "hunger", 0.0),
                "health": getattr(ps, "health", 1.0),
                "current_location_id": getattr(ps, "current_location_id", None),
                "money": getattr(ps, "money", 0.0),
                "home_location_id": getattr(ps, "home_location_id", None),
                "work_location_id": getattr(ps, "work_location_id", None),
            }

        # Personality traits  — dict[str, {base_value, current_value, drift_rate}]
        personality_data: dict[str, Any] = {}
        if hasattr(human, "personality") and human.personality is not None:
            personality_obj = human.personality
            if isinstance(personality_obj, dict):
                personality_data = personality_obj
            elif hasattr(personality_obj, "traits"):
                traits = personality_obj.traits
                if hasattr(traits, "model_dump"):
                    personality_data = traits.model_dump()
                elif hasattr(traits, "dict"):
                    personality_data = traits.dict()
                elif isinstance(traits, dict):
                    personality_data = traits
                else:
                    personality_data = getattr(traits, "__dict__", {})

        # Emotions — dict[EmotionType, {intensity, duration_remaining, decay_rate}]
        emotions_data: dict[str, Any] = {}
        if hasattr(human, "emotions") and human.emotions is not None:
            emotions_obj = human.emotions
            if isinstance(emotions_obj, dict):
                emotions_data = {
                    (k.value if isinstance(k, EmotionType) else str(k)): v
                    for k, v in emotions_obj.items()
                }
            elif hasattr(emotions_obj, "emotions"):
                raw = emotions_obj.emotions
                emotions_data = {
                    (k.value if isinstance(k, EmotionType) else str(k)): v
                    for k, v in raw.items()
                }

        return {
            "uid": str(identity.uid),
            "serial": identity.serial,
            "given_name": identity.given_name,
            "family_name": identity.family_name,
            "nickname": identity.nickname,
            "data_source": identity.data_source.value
            if hasattr(identity.data_source, "value")
            else str(identity.data_source),
            "demographics_json": json.dumps(demographics_data, default=str),
            "physical_state_json": json.dumps(physical_data, default=str),
            "personality_json": json.dumps(personality_data, default=str),
            "emotions_json": json.dumps(emotions_data, default=str),
        }

    @staticmethod
    def deserialize_human_row(row: Any) -> dict[str, Any]:
        """Deserialize a ``humans`` row into a reconstruction dict.

        Because this module must not depend on the full ``SyntheticHuman``
        class (which may import heavy modules), we return a plain dict that
        the caller can pass to the ``SyntheticHuman`` reconstruction factory.

        Keys returned::

            uid, serial, given_name, family_name, nickname, data_source,
            demographics, physical_state, personality, emotions
        """
        return {
            "uid": row["uid"],
            "serial": row["serial"],
            "given_name": row["given_name"],
            "family_name": row["family_name"],
            "nickname": row["nickname"],
            "data_source": row["data_source"],
            "demographics": json.loads(row["demographics_json"]),
            "physical_state": json.loads(row["physical_state_json"]),
            "personality": json.loads(row["personality_json"]),
            "emotions": json.loads(row["emotions_json"]),
        }

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_relationship(rel: Any) -> dict[str, Any]:
        """Serialize a Relationship into a flat dict for the ``relationships`` table."""
        return {
            "relationship_id": _uuid_str(rel.relationship_id),
            "human_a_uid": _uuid_str(rel.human_a_id),
            "human_b_uid": _uuid_str(rel.human_b_id),
            "relationship_type": rel.relationship_type.value
            if isinstance(rel.relationship_type, RelationshipType)
            else str(rel.relationship_type),
            "trust": float(rel.trust),
            "affinity": float(rel.affinity),
            "familiarity": float(rel.familiarity),
            "interaction_count": int(rel.interaction_count),
            "last_interaction_tick": int(rel.last_interaction_tick) if rel.last_interaction_tick is not None else 0,
            "history_json": json.dumps(
                getattr(rel, "history", []), default=str
            ),
        }

    @staticmethod
    def deserialize_relationship(row: Any) -> dict[str, Any]:
        """Deserialize a ``relationships`` row into a reconstruction dict.

        Returns a plain dict with native Python types so the caller can
        reconstruct the domain object.
        """
        return {
            "relationship_id": _uuid_or_none(row["relationship_id"]),
            "human_a_id": _uuid_or_none(row["human_a_uid"]),
            "human_b_id": _uuid_or_none(row["human_b_uid"]),
            "relationship_type": RelationshipType(row["relationship_type"]),
            "trust": float(row["trust"]),
            "affinity": float(row["affinity"]),
            "familiarity": float(row["familiarity"]),
            "interaction_count": int(row["interaction_count"]),
            "last_interaction_tick": int(row["last_interaction_tick"]),
            "history": json.loads(row["history_json"]),
        }

    # ------------------------------------------------------------------
    # SimulationEvent
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_event(event: SimulationEvent) -> dict[str, Any]:
        """Serialize a :class:`SimulationEvent` for the ``events_log`` table."""
        return {
            "event_id": _uuid_str(event.event_id),
            "event_type": event.event_type.value
            if isinstance(event.event_type, EventType)
            else str(event.event_type),
            "tick": int(event.tick),
            "source_human_uid": _uuid_str(event.source_human_id),
            "target_human_uid": _uuid_str(event.target_human_id),
            "location_id": event.location_id,
            "data_json": json.dumps(event.data, default=str),
            "importance": float(event.importance),
        }

    @staticmethod
    def deserialize_event(row: Any) -> SimulationEvent:
        """Reconstruct a :class:`SimulationEvent` from a DB row."""
        return SimulationEvent(
            event_id=UUID(row["event_id"]),
            event_type=EventType(row["event_type"]),
            tick=int(row["tick"]),
            source_human_id=_uuid_or_none(row["source_human_uid"]),
            target_human_id=_uuid_or_none(row["target_human_uid"]),
            location_id=row["location_id"],
            data=json.loads(row["data_json"]),
            importance=float(row["importance"]),
        )

    # ------------------------------------------------------------------
    # EpisodicRecord
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_episodic(record: Any) -> dict[str, Any]:
        """Serialize an episodic memory record."""
        associated = getattr(record, "associated_humans", [])
        return {
            "memory_id": _uuid_str(record.memory_id),
            "summary": str(record.summary),
            "tick": int(record.tick),
            "importance": float(record.importance),
            "emotional_valence": float(record.emotional_valence),
            "associated_humans_json": json.dumps(
                [str(h) for h in associated], default=str
            ),
            "location_id": getattr(record, "location_id", None),
            "access_count": int(getattr(record, "access_count", 0)),
            "last_accessed": int(getattr(record, "last_accessed", 0)),
        }

    @staticmethod
    def deserialize_episodic(row: Any) -> dict[str, Any]:
        """Deserialize an episodic memory row into a reconstruction dict."""
        assoc_raw = json.loads(row["associated_humans_json"])
        return {
            "memory_id": _uuid_or_none(row["memory_id"]),
            "summary": row["summary"],
            "tick": int(row["tick"]),
            "importance": float(row["importance"]),
            "emotional_valence": float(row["emotional_valence"]),
            "associated_humans": [_uuid_or_none(h) for h in assoc_raw],
            "location_id": row["location_id"],
            "access_count": int(row["access_count"]),
            "last_accessed": int(row["last_accessed"]),
        }

    # ------------------------------------------------------------------
    # SemanticFact
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_semantic(fact: Any) -> dict[str, Any]:
        """Serialize a semantic fact."""
        return {
            "fact_id": str(fact.fact_id),
            "category": str(getattr(fact, "category", "")),
            "content": str(fact.content),
            "confidence": float(getattr(fact, "confidence", 1.0)),
            "source": str(getattr(fact, "source", "")),
            "learned_tick": int(getattr(fact, "learned_tick", 0)),
        }

    @staticmethod
    def deserialize_semantic(row: Any) -> dict[str, Any]:
        """Deserialize a semantic fact row."""
        return {
            "fact_id": row["fact_id"],
            "category": row["category"],
            "content": row["content"],
            "confidence": float(row["confidence"]),
            "source": row["source"],
            "learned_tick": int(row["learned_tick"]),
        }

    # ------------------------------------------------------------------
    # Skill (procedural memory)
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_procedural(skill: Any) -> dict[str, Any]:
        """Serialize a skill / procedural memory."""
        return {
            "skill_id": str(skill.skill_id),
            "name": str(getattr(skill, "name", "")),
            "category": str(getattr(skill, "category", "")),
            "level": float(getattr(skill, "level", 0.0)),
            "experience_points": float(getattr(skill, "experience_points", 0.0)),
            "practice_count": int(getattr(skill, "practice_count", 0)),
        }

    @staticmethod
    def deserialize_procedural(row: Any) -> dict[str, Any]:
        """Deserialize a procedural memory row."""
        return {
            "skill_id": row["skill_id"],
            "name": row["name"],
            "category": row["category"],
            "level": float(row["level"]),
            "experience_points": float(row["experience_points"]),
            "practice_count": int(row["practice_count"]),
        }

    # ------------------------------------------------------------------
    # Goal
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_goal(goal: Any) -> dict[str, Any]:
        """Serialize a goal dict or goal object."""
        if isinstance(goal, dict):
            return {
                "goal_id": str(goal.get("goal_id", "")),
                "description": str(goal.get("description", "")),
                "priority": float(goal.get("priority", 0.5)),
                "need_type": goal.get("need_type"),
                "progress": float(goal.get("progress", 0.0)),
                "deadline_tick": goal.get("deadline_tick"),
                "status": str(goal.get("status", "active")),
            }
        return {
            "goal_id": _uuid_str(getattr(goal, "goal_id", "")) or "",
            "description": str(getattr(goal, "description", "")),
            "priority": float(getattr(goal, "priority", 0.5)),
            "need_type": getattr(goal, "need_type", None),
            "progress": float(getattr(goal, "progress", 0.0)),
            "deadline_tick": getattr(goal, "deadline_tick", None),
            "status": str(getattr(goal, "status", "active")),
        }

    @staticmethod
    def deserialize_goal(row: Any) -> dict[str, Any]:
        """Deserialize a goals row."""
        return {
            "goal_id": row["goal_id"],
            "human_uid": row["human_uid"],
            "description": row["description"],
            "priority": float(row["priority"]),
            "need_type": row["need_type"],
            "progress": float(row["progress"]),
            "deadline_tick": row["deadline_tick"],
            "status": row["status"],
        }


# ---------------------------------------------------------------------------
# Avoid circular imports — these are only needed inside serialize_human for
# enum-value extraction.  Import them lazily inside the method bodies above
# (they're used via getattr().value so only need the class at call time).
# ---------------------------------------------------------------------------
from saltbor.core.types import DataSource, Gender  # noqa: E402
