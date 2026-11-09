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
from saltbor.core.types import Tick
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

    def record_event(
        self,
        event: SimulationEvent,
        importance: Optional[float] = None,
        emotional_valence: float = 0.0,
    ) -> None:
        """Register an event in memory.

        Always placed in working memory buffer. If importance exceeds threshold (>=0.15),
        also encoded into long-term episodic memory.
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

        # 2. Selective long-term encoding: only memories with sufficient salience
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
            )
            self.episodic.store(rec)

    def consolidate(self, current_tick: Tick) -> dict[str, int]:
        """Execute memory consolidation, decay, and selective forgetting."""
        return self.consolidator.consolidate(
            episodic=self.episodic,
            semantic=self.semantic,
            current_tick=current_tick,
        )

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
