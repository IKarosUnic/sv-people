"""Episodic memory system for synthetic humans.

Stores autobiographical events and experiences with temporal context,
emotional valence, and associative links to people and places.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID, LocationID, MemoryID, Tick


@dataclass
class EpisodicRecord:
    """A record of a single past experience."""

    memory_id: MemoryID = field(default_factory=uuid.uuid4)
    summary: str = ""
    tick: Tick = 0
    importance: float = 0.5          # 0.0 to 1.0 (subjective significance)
    emotional_valence: float = 0.0   # -1.0 (extremely negative) to +1.0 (extremely positive)
    associated_humans: list[HumanID] = field(default_factory=list)
    location_id: Optional[LocationID] = None
    access_count: int = 0
    last_accessed: Tick = 0

    def touch(self, current_tick: Tick) -> None:
        """Mark memory as recalled, increasing access frequency and freshness."""
        self.access_count += 1
        self.last_accessed = current_tick


class EpisodicMemory:
    """Autobiographical episodic memory bank."""

    def __init__(self, max_records: int = 500) -> None:
        self.max_records = max_records
        self._records: dict[MemoryID, EpisodicRecord] = {}

    def store(self, record: EpisodicRecord) -> None:
        """Add an episodic record."""
        self._records[record.memory_id] = record

    def get(self, memory_id: MemoryID) -> Optional[EpisodicRecord]:
        return self._records.get(memory_id)

    def get_all(self) -> list[EpisodicRecord]:
        return list(self._records.values())

    def remove(self, memory_id: MemoryID) -> None:
        self._records.pop(memory_id, None)

    def retrieve(
        self,
        current_tick: Tick,
        associated_human: Optional[HumanID] = None,
        location_id: Optional[LocationID] = None,
        keywords: Optional[list[str]] = None,
        limit: int = 5,
    ) -> list[EpisodicRecord]:
        """Recall relevant episodic memories scored by recency, importance, and relevance.

        Score = importance * 0.4 + recency * 0.3 + relevance * 0.3
        """
        if not self._records:
            return []

        scored: list[tuple[float, EpisodicRecord]] = []
        kw_set = {k.lower() for k in keywords} if keywords else set()

        for rec in self._records.values():
            # Recency factor: exponential decay over simulated days (96 ticks/day)
            age_ticks = max(0, current_tick - rec.tick)
            recency = math.exp(-age_ticks / (96.0 * 7.0))  # Half-life ~ 5 days

            # Relevance factor
            relevance = 0.0
            if associated_human and associated_human in rec.associated_humans:
                relevance += 0.5
            if location_id and location_id == rec.location_id:
                relevance += 0.3
            if kw_set:
                summary_words = set(rec.summary.lower().split())
                overlap = len(kw_set & summary_words)
                relevance += min(0.4, overlap * 0.1)

            total_score = (rec.importance * 0.4) + (recency * 0.3) + (relevance * 0.3)
            scored.append((total_score, rec))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = [pair[1] for pair in scored[:limit]]

        # Update access stats on retrieved memories
        for rec in top:
            rec.touch(current_tick)

        return top

    def get_recent(self, n: int = 5) -> list[EpisodicRecord]:
        """Return the n most chronologically recent episodic memories."""
        return sorted(self._records.values(), key=lambda r: r.tick, reverse=True)[:n]

    @property
    def count(self) -> int:
        return len(self._records)
