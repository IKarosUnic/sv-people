"""Semantic memory system for synthetic humans.

Stores generalized factual knowledge, beliefs, world facts, and social knowledge
decoupled from specific temporal episodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import Tick


@dataclass
class SemanticFact:
    """A single factual knowledge item or belief held by a human."""

    fact_id: str
    category: str        # e.g., 'world', 'social', 'location', 'self', 'work', 'habit'
    content: str
    confidence: float = 1.0   # 0.0 to 1.0 (certainty of belief)
    source: str = ""          # origin (e.g. 'direct_experience', 'hearsay', 'innate', 'compression')
    learned_tick: Tick = 0
    verification_count: int = 1
    contradiction_count: int = 0
    last_updated_tick: Tick = 0


class SemanticMemory:
    """Repository of facts, beliefs, and learned world associations."""

    def __init__(self) -> None:
        self._facts: dict[str, SemanticFact] = {}

    def store(self, fact: SemanticFact) -> None:
        """Store or update a semantic fact."""
        self._facts[fact.fact_id] = fact

    def get(self, fact_id: str) -> Optional[SemanticFact]:
        return self._facts.get(fact_id)

    def get_all(self) -> list[SemanticFact]:
        return list(self._facts.values())

    def update_confidence(self, fact_id: str, delta: float) -> None:
        """Adjust confidence level in an existing belief, bounded to [0.0, 1.0]."""
        if fact_id in self._facts:
            f = self._facts[fact_id]
            f.confidence = max(0.0, min(1.0, f.confidence + delta))

    def update_with_evidence(
        self,
        fact_id: str,
        is_confirming: bool,
        delta: float = 0.15,
        new_content: Optional[str] = None,
        current_tick: Tick = 0,
    ) -> None:
        """Update a belief following new evidence.

        If contradictory evidence reduces confidence below 0.20 and *new_content* is provided,
        the belief is updated/revised.
        """
        fact = self._facts.get(fact_id)
        if not fact:
            if new_content:
                self.store(
                    SemanticFact(
                        fact_id=fact_id,
                        category="experience",
                        content=new_content,
                        confidence=0.6,
                        source="new_evidence",
                        learned_tick=current_tick,
                    )
                )
            return

        if is_confirming:
            fact.confidence = min(1.0, fact.confidence + delta)
            fact.verification_count += 1
        else:
            fact.confidence = max(0.0, fact.confidence - delta)
            fact.contradiction_count += 1
            if fact.confidence <= 0.20 and new_content:
                fact.content = new_content
                fact.confidence = 0.65
                fact.source = "revised_evidence"

        fact.last_updated_tick = current_tick

    def revise_belief(self, fact_id: str, new_content: str, confidence: float = 0.8, tick: Tick = 0) -> None:
        """Explicitly revise an existing belief after decisive evidence."""
        if fact_id in self._facts:
            f = self._facts[fact_id]
            f.content = new_content
            f.confidence = confidence
            f.source = "revised_after_insight"
            f.last_updated_tick = tick

    def query(
        self,
        category: Optional[str] = None,
        keywords: Optional[list[str]] = None,
    ) -> list[SemanticFact]:
        """Search facts by category and/or keyword matching."""
        results = list(self._facts.values())
        if category:
            results = [f for f in results if f.category == category]
        if keywords:
            kw_set = {k.lower() for k in keywords}
            results = [
                f for f in results
                if any(kw in f.content.lower() for kw in kw_set)
            ]
        return results

    @property
    def count(self) -> int:
        return len(self._facts)
