"""Working memory system for synthetic humans.

Implements a short-term, low-capacity buffer (Miller's 7 ± 2 items)
holding immediate perceptions, active thoughts, and transient context.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.types import MemoryID, Tick


@dataclass
class WorkingMemoryItem:
    """A single transient item currently held in attention/working memory."""

    item_id: MemoryID = field(default_factory=uuid.uuid4)
    content: str = ""
    category: str = "perception"  # perception, thought, context, speech
    importance: float = 0.5       # 0.0 to 1.0
    tick_created: Tick = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkingMemory:
    """Fixed-capacity working memory buffer.

    When new items arrive exceeding capacity, the item with the lowest
    importance (or oldest if equal) is evicted.
    """

    def __init__(self, capacity: int = 7) -> None:
        self.capacity = max(1, capacity)
        self._items: list[WorkingMemoryItem] = []

    def add(self, item: WorkingMemoryItem) -> Optional[WorkingMemoryItem]:
        """Add an item to working memory.

        If capacity is reached, evicts and returns the least important item.
        Returns None if no eviction occurred.
        """
        evicted: Optional[WorkingMemoryItem] = None
        if len(self._items) >= self.capacity:
            # Find candidate to evict: lowest importance, oldest tick
            eviction_idx = 0
            min_score = (self._items[0].importance, -self._items[0].tick_created)
            for i, it in enumerate(self._items):
                score = (it.importance, -it.tick_created)
                if score < min_score:
                    min_score = score
                    eviction_idx = i

            evicted = self._items.pop(eviction_idx)

        self._items.append(item)
        return evicted

    def get_all(self) -> list[WorkingMemoryItem]:
        """Return all items currently in working memory."""
        return list(self._items)

    def contains(self, item_id: MemoryID) -> bool:
        """Check if an item is present."""
        return any(it.item_id == item_id for it in self._items)

    def clear(self) -> None:
        """Clear the working memory."""
        self._items.clear()

    @property
    def count(self) -> int:
        return len(self._items)

    def get_summary(self) -> str:
        """Compact text representation of working memory contents."""
        if not self._items:
            return "Working memory empty"
        return "; ".join(f"[{it.category}] {it.content}" for it in self._items)
