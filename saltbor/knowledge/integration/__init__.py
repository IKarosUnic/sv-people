"""Integration bridges connecting knowledge with memory and decisions."""

from saltbor.knowledge.integration.memory_bridge import KnowledgeMemoryBridge
from saltbor.knowledge.integration.decision_bridge import (
    KnowledgeDecisionBridge,
    KnowledgeSeekingOption,
)

__all__ = [
    "KnowledgeMemoryBridge",
    "KnowledgeDecisionBridge",
    "KnowledgeSeekingOption",
]
