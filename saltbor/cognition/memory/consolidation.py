"""Memory consolidation, compression, and selective forgetting engine.

Implements decay, reinforcement through access, emotional protection
against forgetting, compression of repeated experiences into semantic knowledge,
and selective archiving of trivial records without loss of persistent history.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional

from saltbor.cognition.memory.episodic import EpisodicMemory, EpisodicRecord
from saltbor.cognition.memory.procedural import ProceduralMemory
from saltbor.cognition.memory.semantic import SemanticFact, SemanticMemory
from saltbor.core.types import Tick


class MemoryConsolidator:
    """Orchestrates memory decay, consolidation, compression, and forgetting."""

    def __init__(
        self,
        base_decay_rate: float = 0.05,
        forget_threshold: float = 0.05,
    ) -> None:
        self.base_decay_rate = base_decay_rate
        self.forget_threshold = forget_threshold

    def calculate_decayed_importance(
        self,
        record: EpisodicRecord,
        current_tick: Tick,
    ) -> float:
        """Calculate new importance considering age, emotional charge, and retrieval frequency."""
        ticks_elapsed = max(0, current_tick - record.tick)
        if ticks_elapsed == 0:
            return record.importance

        # Protection 1: High emotional intensity protects against decay
        # |valence| in [0, 1] -> emotional factor in [0.3, 1.0]
        emotional_intensity = abs(record.emotional_valence)
        decay_reduction = 0.3 + 0.7 * (1.0 - emotional_intensity)

        # Protection 2: Frequent recall strengthens memory (spacing effect)
        recall_protection = 1.0 / (1.0 + 0.15 * record.access_count)

        effective_decay = self.base_decay_rate * decay_reduction * recall_protection
        decayed = record.importance * math.exp(-effective_decay * (ticks_elapsed / 96.0))
        return max(0.0, decayed)

    def calculate_accessibility(
        self,
        record: EpisodicRecord,
        current_tick: Tick,
    ) -> float:
        """Calculate active retrieval accessibility. Compressed/routine records lose accessibility faster."""
        ticks_elapsed = max(0, current_tick - record.tick)
        if ticks_elapsed == 0:
            return record.accessibility

        emotional_intensity = abs(record.emotional_valence)
        decay_rate = self.base_decay_rate * (1.5 if record.is_compressed else 1.0)
        decay_reduction = 0.2 + 0.8 * (1.0 - emotional_intensity)
        recall_boost = 1.0 / (1.0 + 0.20 * record.access_count)

        acc_decay = decay_rate * decay_reduction * recall_boost
        decayed_acc = record.accessibility * math.exp(-acc_decay * (ticks_elapsed / 96.0))
        return max(0.0, min(1.0, decayed_acc))

    def compress_repeated_experiences(
        self,
        episodic: EpisodicMemory,
        semantic: Optional[SemanticMemory],
        current_tick: Tick,
    ) -> int:
        """Synthesize recurring episodic routines into generalized semantic knowledge.

        For example, multiple meals at Comedor Doña María become a semantic belief:
        "Regularly eats meals at Comedor Doña María".
        """
        if not semantic:
            return 0

        # Group uncompressed records by location
        location_records: dict[str, list[EpisodicRecord]] = defaultdict(list)
        for rec in episodic.get_all():
            if rec.location_id and not rec.is_compressed:
                location_records[rec.location_id].append(rec)

        compressed_count = 0
        for loc_id, records in location_records.items():
            if len(records) >= 3:
                fact_id = f"habit_location_{loc_id}"
                content = f"Habitual pattern: frequent activity and visits at {loc_id}"
                semantic.update_with_evidence(
                    fact_id=fact_id,
                    is_confirming=True,
                    delta=0.20,
                    new_content=content,
                    current_tick=current_tick,
                )
                for rec in records:
                    rec.is_compressed = True
                compressed_count += len(records)

        return compressed_count

    def consolidate(
        self,
        episodic: EpisodicMemory,
        semantic: Optional[SemanticMemory] = None,
        procedural: Optional[ProceduralMemory] = None,
        current_tick: Tick = 0,
    ) -> dict[str, int]:
        """Run consolidation cycle over memory systems:

        1. Re-evaluate importance & accessibility with decay and emotional protection
        2. Compress repeated experiences into generalized semantic beliefs
        3. Transition trivial records below threshold to persistent historical archive
        4. Apply skill atrophy to prolonged inactive procedural competencies
        """
        # 1. Compress patterns
        compressed_count = self.compress_repeated_experiences(episodic, semantic, current_tick)

        # 2. Re-evaluate and selective forgetting
        forgotten_count = 0
        preserved_count = 0
        to_archive = []

        for rec in episodic.get_all():
            new_imp = self.calculate_decayed_importance(rec, current_tick)
            new_acc = self.calculate_accessibility(rec, current_tick)
            rec.importance = new_imp
            rec.accessibility = new_acc

            if new_imp < self.forget_threshold or new_acc < self.forget_threshold:
                to_archive.append(rec.memory_id)
                forgotten_count += 1
            else:
                preserved_count += 1

        for mid in to_archive:
            episodic.remove(mid)

        # 3. Procedural memory decay
        if procedural:
            procedural.decay_inactive_skills(current_tick)

        return {
            "forgotten": forgotten_count,
            "preserved": preserved_count,
            "remaining": episodic.count,
            "compressed": compressed_count,
        }
