"""Memory consolidation and selective forgetting engine.

Implements decay, reinforcement through access, emotional protection
against forgetting, and pruning of trivial records below significance threshold.
"""

from __future__ import annotations

import math
from typing import Optional

from saltbor.cognition.memory.episodic import EpisodicMemory, EpisodicRecord
from saltbor.cognition.memory.semantic import SemanticFact, SemanticMemory
from saltbor.core.types import Tick


class MemoryConsolidator:
    """Orchestrates memory decay, consolidation, and forgetting."""

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

    def consolidate(
        self,
        episodic: EpisodicMemory,
        semantic: Optional[SemanticMemory],
        current_tick: Tick,
    ) -> dict[str, int]:
        """Run consolidation cycle over episodic memory:

        1. Re-evaluate importance with decay
        2. Forget memories dropping below threshold
        3. Optionally synthesize repeated patterns into semantic facts
        """
        forgotten_count = 0
        preserved_count = 0

        to_remove = []
        for rec in episodic.get_all():
            new_imp = self.calculate_decayed_importance(rec, current_tick)
            rec.importance = new_imp

            if new_imp < self.forget_threshold:
                to_remove.append(rec.memory_id)
                forgotten_count += 1
            else:
                preserved_count += 1

        for mid in to_remove:
            episodic.remove(mid)

        return {
            "forgotten": forgotten_count,
            "preserved": preserved_count,
            "remaining": episodic.count,
        }
