"""Unified memory engine facade for synthetic humans.

Combines working, episodic, semantic, and procedural memory systems with
autonomous consolidation and selective forgetting.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

from saltbor.cognition.memory.consolidation import MemoryConsolidator
from saltbor.cognition.memory.episodic import EpisodicMemory, EpisodicRecord
from saltbor.cognition.memory.procedural import ProceduralMemory, Skill
from saltbor.cognition.memory.semantic import SemanticFact, SemanticMemory
from saltbor.cognition.memory.working import WorkingMemory, WorkingMemoryItem
from saltbor.core.config import SimulationConfig
from saltbor.core.types import EmotionType, HumanID, LocationID, Tick
from saltbor.events.types import SimulationEvent


class MemoryEngine:
    """Integrated cognitive memory architecture for an individual."""

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        cfg = config or SimulationConfig()
        self.working = WorkingMemory(capacity=cfg.max_working_memory_items)
        self.episodic = EpisodicMemory(max_records=500)
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.consolidator = MemoryConsolidator(base_decay_rate=cfg.memory_decay_rate)
        self.max_memory_bytes = cfg.max_memory_bytes_per_human

        # Emotional Associations (people and places)
        self.location_associations: dict[LocationID, dict[str, float]] = {}
        self.human_associations: dict[HumanID, dict[str, float]] = {}

    def associate_location(
        self,
        location_id: LocationID,
        emotion_name: str,
        intensity: float,
        valence: float = 0.0,
    ) -> None:
        """Register or reinforce an emotional association with a location."""
        if location_id not in self.location_associations:
            self.location_associations[location_id] = {
                "valence": valence,
                "intensity": intensity,
                emotion_name: intensity,
            }
        else:
            assoc = self.location_associations[location_id]
            assoc[emotion_name] = max(assoc.get(emotion_name, 0.0), intensity)
            assoc["valence"] = max(-1.0, min(1.0, assoc["valence"] * 0.6 + valence * 0.4))
            assoc["intensity"] = max(assoc["intensity"], intensity)

    def associate_human(
        self,
        human_id: HumanID,
        emotion_name: str,
        intensity: float,
        valence: float = 0.0,
    ) -> None:
        """Register or reinforce an emotional association with an individual."""
        if human_id not in self.human_associations:
            self.human_associations[human_id] = {
                "valence": valence,
                "intensity": intensity,
                emotion_name: intensity,
            }
        else:
            assoc = self.human_associations[human_id]
            assoc[emotion_name] = max(assoc.get(emotion_name, 0.0), intensity)
            assoc["valence"] = max(-1.0, min(1.0, assoc["valence"] * 0.6 + valence * 0.4))
            assoc["intensity"] = max(assoc["intensity"], intensity)

    def get_location_association(self, location_id: LocationID) -> dict[str, float]:
        """Return emotional association for a given location, or neutral default."""
        return self.location_associations.get(location_id, {"valence": 0.0, "intensity": 0.0})

    def get_human_association(self, human_id: HumanID) -> dict[str, float]:
        """Return emotional association for a given human, or neutral default."""
        return self.human_associations.get(human_id, {"valence": 0.0, "intensity": 0.0})

    def record_event(
        self,
        event: SimulationEvent,
        importance: Optional[float] = None,
        emotional_valence: float = 0.0,
        emotional_charges: Optional[dict[str, float]] = None,
    ) -> None:
        """Register an event in memory.

        Always placed in working memory buffer. If importance exceeds threshold (>=0.15),
        also encoded into long-term episodic memory and associative stores.
        """
        imp = importance if importance is not None else event.importance
        summary_text = f"{event.event_type.value}: {event.data}" if event.data else event.event_type.value

        # 1. Immediate working memory
        self.working.add(
            WorkingMemoryItem(
                content=summary_text,
                category="event",
                importance=imp,
                tick_created=event.tick,
                metadata={"event_type": event.event_type.value},
            )
        )

        # 2. Emotional associations with location & persons
        charges = emotional_charges or {}
        if event.location_id and (abs(emotional_valence) > 0.1 or charges):
            dom_emotion = max(charges, key=charges.get) if charges else ("joy" if emotional_valence > 0 else "distress")
            dom_intensity = charges.get(dom_emotion, abs(emotional_valence))
            self.associate_location(event.location_id, dom_emotion, dom_intensity, emotional_valence)

        for person_id in [event.source_human_id, event.target_human_id]:
            if person_id and (abs(emotional_valence) > 0.1 or charges):
                dom_emotion = max(charges, key=charges.get) if charges else ("joy" if emotional_valence > 0 else "distress")
                dom_intensity = charges.get(dom_emotion, abs(emotional_valence))
                self.associate_human(person_id, dom_emotion, dom_intensity, emotional_valence)

        # 3. Selective long-term encoding: only memories with sufficient salience
        if imp >= 0.15:
            assoc = []
            if event.source_human_id:
                assoc.append(event.source_human_id)
            if event.target_human_id:
                assoc.append(event.target_human_id)

            rec = EpisodicRecord(
                summary=summary_text,
                tick=event.tick,
                importance=imp,
                emotional_valence=emotional_valence,
                associated_humans=assoc,
                location_id=event.location_id,
                emotional_associations=charges,
            )
            self.episodic.store(rec)

    def consolidate(self, current_tick: Tick) -> dict[str, int]:
        """Execute memory consolidation, compression, decay, and selective archiving."""
        return self.consolidator.consolidate(
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
            current_tick=current_tick,
        )

    def query_by_association(self, location_id: Optional[LocationID] = None, human_id: Optional[HumanID] = None) -> list[EpisodicRecord]:
        """Query episodic memories associated with a location or human."""
        results: list[EpisodicRecord] = []
        for rec in self.episodic.get_all(include_dormant=False):
            if location_id and rec.location_id == location_id:
                results.append(rec)
            elif human_id and human_id in rec.associated_humans:
                results.append(rec)
        return results

    def get_memory_stats(self) -> dict[str, Any]:
        """Measure item counts and approximate logical memory footprint."""
        working_count = self.working.count
        episodic_count = self.episodic.count
        semantic_count = self.semantic.count
        procedural_count = self.procedural.count

        # Approximate logical memory size: serialize records to estimate byte footprint
        approx_bytes = (
            working_count * 200
            + episodic_count * 350
            + semantic_count * 250
            + procedural_count * 150
        )

        return {
            "working_items": working_count,
            "episodic_records": episodic_count,
            "semantic_facts": semantic_count,
            "skills": procedural_count,
            "approx_bytes": approx_bytes,
            "quota_bytes": self.max_memory_bytes,
            "usage_pct": round((approx_bytes / self.max_memory_bytes) * 100, 3),
        }
