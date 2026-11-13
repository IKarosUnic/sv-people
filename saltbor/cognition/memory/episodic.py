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
    accessibility: float = 1.0       # 0.0 (dormant/forgotten) to 1.0 (readily accessible)
    is_compressed: bool = False      # Abstracted into generalized semantic knowledge
    is_dormant: bool = False         # Below active retrieval threshold (preserved in history)
    emotional_associations: dict[str, float] = field(default_factory=dict)
    context_tags: list[str] = field(default_factory=list)
    # Provenance: the event this record was encoded from, kept separate from
    # the record's own (reconstructible) content.  Optional for backward
    # compatibility with databases written before Phase 1.7.
    source_event_id: Optional[str] = None

    def touch(self, current_tick: Tick, reinforcement: float = 0.2) -> None:
        """Mark memory as recalled, increasing access frequency and freshness."""
        self.access_count += 1
        self.last_accessed = current_tick
        self.accessibility = min(1.0, self.accessibility + reinforcement)
        if self.accessibility >= 0.10:
            self.is_dormant = False


class EpisodicMemory:
    """Autobiographical episodic memory bank.

    Maintains active working-episodic representations for fast cognitive recall,
    while guaranteeing persistent historical archival without indiscriminate data loss.
    """

    def __init__(self, max_records: int = 500) -> None:
        self.max_records = max_records
        self._records: dict[MemoryID, EpisodicRecord] = {}
        self._history_archive: dict[MemoryID, EpisodicRecord] = {}

    def store(self, record: EpisodicRecord) -> None:
        """Add an episodic record to active memory and historical archive."""
        self._records[record.memory_id] = record
        self._history_archive[record.memory_id] = record

    def get(self, memory_id: MemoryID, include_archive: bool = True) -> Optional[EpisodicRecord]:
        rec = self._records.get(memory_id)
        if rec is None and include_archive:
            rec = self._history_archive.get(memory_id)
        return rec

    def get_all(self, include_dormant: bool = False) -> list[EpisodicRecord]:
        """Return all memories in active recall.

        If *include_dormant* is True, returns all historical memories.
        """
        if include_dormant:
            return list(self._history_archive.values())
        return list(self._records.values())

    def get_stored_history(self) -> list[EpisodicRecord]:
        """Return the complete persistent history of all lived events."""
        return list(self._history_archive.values())

    def remove(self, memory_id: MemoryID) -> None:
        """Move memory from active recall into dormant archive.

        Data remains stored in the individual's persistent history, but
        loses daily cognitive accessibility.
        """
        rec = self._records.pop(memory_id, None)
        if rec:
            rec.is_dormant = True
            rec.accessibility = 0.0
            self._history_archive[memory_id] = rec

    def retrieve(
        self,
        current_tick: Tick,
        associated_human: Optional[HumanID] = None,
        location_id: Optional[LocationID] = None,
        keywords: Optional[list[str]] = None,
        limit: int = 5,
        min_accessibility: float = 0.05,
    ) -> list[EpisodicRecord]:
        """Recall relevant episodic memories scored by recency, importance, relevance, and accessibility.

        Score = (importance * 0.35) + (recency * 0.25) + (relevance * 0.25) + (accessibility * 0.15)
        """
        if not self._records:
            return []

        scored: list[tuple[float, EpisodicRecord]] = []
        kw_set = {k.lower() for k in keywords} if keywords else set()

        for rec in self._records.values():
            if rec.accessibility < min_accessibility:
                continue

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
                summary_words = set(rec.summary.lower().split()) | {t.lower() for t in rec.context_tags}
                overlap = len(kw_set & summary_words)
                relevance += min(0.4, overlap * 0.1)

            total_score = (
                (rec.importance * 0.35)
                + (recency * 0.25)
                + (relevance * 0.25)
                + (rec.accessibility * 0.15)
            )
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
        """Count of active accessible episodic memories."""
        return len(self._records)

    @property
    def total_stored_count(self) -> int:
        """Count of all stored episodic memories (active + dormant)."""
        return len(self._history_archive)
