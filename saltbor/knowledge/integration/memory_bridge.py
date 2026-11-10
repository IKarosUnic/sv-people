"""Memory Engine Bridge for Saltbor Phase 0.6.

Bridges the Knowledge Graph with the existing MemoryEngine (episodic,
semantic, procedural, working memory, and consolidation).
"""

from __future__ import annotations

import logging
from typing import Optional

from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.cognition.memory.procedural import Skill
from saltbor.cognition.memory.semantic import SemanticFact
from saltbor.core.types import SkillCategory, Tick
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProcedureDefinition

logger = logging.getLogger(__name__)


class KnowledgeMemoryBridge:
    """Synchronizes knowledge claims with agent's unified MemoryEngine."""

    @staticmethod
    def sync_concept_to_semantic_memory(
        concept_id: str,
        concept_label: str,
        confidence: float,
        source: str,
        memory: MemoryEngine,
        tick: Tick = 0,
    ) -> None:
        """Store or update concept belief in semantic memory."""
        fact = SemanticFact(
            fact_id=f"fact_{concept_id}",
            category="knowledge_concept",
            content=f"Understands concept '{concept_label}'",
            confidence=confidence,
            source=source,
            learned_tick=tick,
            last_updated_tick=tick,
        )
        memory.semantic.store(fact)

    @staticmethod
    def record_learning_episode(
        memory: MemoryEngine,
        summary: str,
        importance: float,
        valence: float = 0.2,
        associated_peers: Optional[list[str]] = None,
        tick: Tick = 0,
    ) -> None:
        """Record an episodic memory trace of learning or discovery."""
        rec = EpisodicRecord(
            memory_id=f"ep_learn_{tick}_{len(memory.episodic._history_archive)}",
            summary=summary,
            tick=tick,
            importance=importance,
            emotional_valence=valence,
            associated_humans=associated_peers or [],
        )
        memory.episodic.store(rec)

    @staticmethod
    def sync_procedure_to_procedural_memory(
        procedure: ProcedureDefinition,
        practical_level: float,
        memory: MemoryEngine,
        tick: Tick = 0,
    ) -> None:
        """Register practical procedure execution capacity in procedural memory."""
        skill = Skill(
            skill_id=f"proc_{procedure.procedure_id}",
            name=procedure.name,
            category=SkillCategory.TECHNICAL,
            level=practical_level,
            experience_points=practical_level * 50.0,
            practice_count=1,
            last_practiced_tick=tick,
        )
        memory.procedural.register_skill(skill)

    @staticmethod
    def consolidate_knowledge_and_memory(
        graph: IndividualKnowledgeGraph,
        memory: MemoryEngine,
        elapsed_ticks: int,
        retention_rate: float = 0.95,
    ) -> int:
        """Consolidate memories and apply decay across both knowledge graph and memory engine."""
        # Consolidate standard memory engine
        memory.consolidate(current_tick=elapsed_ticks)
        # Apply knowledge graph forgetting
        forgotten_count = graph.apply_decay(elapsed_ticks=elapsed_ticks, retention_rate=retention_rate)
        return forgotten_count
