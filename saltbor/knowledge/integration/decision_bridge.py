"""Decision and Planning Bridge for Saltbor Phase 0.6.

Integrates Knowledge Graphs with Multi-Attribute Utility Theory (MAUT) and
hierarchical planning (GOAP and HTN). Ensures agents only select plans within
their known capabilities or autonomously spawn epistemic learning goals.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Optional

from saltbor.cognition.planning.goap import ActionDefinition, WorldState
from saltbor.cognition.planning.htn import HTNTask
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class KnowledgeSeekingOption:
    """An alternative epistemic plan when a high-utility action is blocked by missing knowledge."""

    target_action_id: str
    missing_knowledge_id: str
    suggested_strategy: str             # 'seek_mentor', 'observe_expert', 'experiment', 'consult_records'
    estimated_effort_ticks: int
    target_expert_uid: Optional[str] = None


class KnowledgeDecisionBridge:
    """Filters candidate plans and spawns knowledge-seeking behaviors."""

    @staticmethod
    def filter_executable_actions(
        actions: list[ActionDefinition],
        graph: IndividualKnowledgeGraph,
    ) -> tuple[list[ActionDefinition], list[tuple[ActionDefinition, str]]]:
        """Filter action list: only actions whose required capabilities/concepts are known survive.

        Returns (executable_actions, blocked_actions_with_reasons).
        """
        executable: list[ActionDefinition] = []
        blocked: list[tuple[ActionDefinition, str]] = []

        for act in actions:
            # Check required capabilities in action
            missing: list[str] = []
            for cap in act.required_capabilities:
                if not graph.knows_concept(cap, min_confidence=0.3):
                    missing.append(cap)

            if missing:
                blocked.append((act, f"Missing required knowledge/skill: {', '.join(missing)}"))
            else:
                executable.append(act)

        return executable, blocked

    @staticmethod
    def formulate_epistemic_inquiry_goals(
        blocked_actions: list[tuple[ActionDefinition, str]],
        graph: IndividualKnowledgeGraph,
        known_experts: Optional[dict[str, str]] = None, # concept_id -> expert_uid
    ) -> list[KnowledgeSeekingOption]:
        """Formulate epistemic goals to acquire missing capabilities."""
        options: list[KnowledgeSeekingOption] = []
        known_experts = known_experts or {}

        for act, _ in blocked_actions:
            for cap in act.required_capabilities:
                if not graph.knows_concept(cap, min_confidence=0.3):
                    expert = known_experts.get(cap)
                    strat = "seek_mentor" if expert else "experiment"
                    options.append(
                        KnowledgeSeekingOption(
                            target_action_id=act.action_id,
                            missing_knowledge_id=cap,
                            suggested_strategy=strat,
                            estimated_effort_ticks=10,
                            target_expert_uid=expert,
                        )
                    )

        return options
