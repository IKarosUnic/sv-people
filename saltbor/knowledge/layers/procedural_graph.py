"""Procedural Knowledge Graph (Layer 4).

Represents practical techniques, procedures, and executable workflows.
Strictly enforces the four-way epistemic distinction:
1. Knowing that something exists (Concept acquaintance)
2. Knowing how something works (Mechanistic/causal understanding)
3. Knowing how to perform it (Recipe/procedural knowledge)
4. Having the practical competency to execute it successfully (Skill mastery & resources)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType


@dataclasses.dataclass
class ProcedureStep:
    """An individual execution step in a procedure."""

    step_index: int
    name: str
    description: str
    required_skill_id: Optional[str] = None
    min_skill_level: float = 0.0
    duration_ticks: int = 1
    consumed_materials: dict[str, float] = dataclasses.field(default_factory=dict)
    required_tools: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ProcedureDefinition:
    """The formal, executable specification of a practical procedure."""

    procedure_id: str
    name: str
    domain: str                         # e.g., 'agriculture', 'carpentry', 'commerce', 'metallurgy'
    description: str
    prerequisite_concepts: list[str]    # Concepts that must be known
    required_skills: dict[str, float]   # skill_id -> min_proficiency required
    required_tools: list[str]
    input_materials: dict[str, float]   # item_type -> quantity
    output_products: dict[str, float]   # item_type -> quantity
    execution_steps: list[ProcedureStep]
    base_duration_ticks: int = 10
    difficulty: float = 0.5             # [0.0, 1.0]
    failure_risk: float = 0.1           # baseline probability of failure


@dataclasses.dataclass
class AgentProceduralCompetency:
    """An agent's specific four-stage competency regarding a procedure."""

    procedure_id: str
    knows_existence: bool = False       # Knows that the procedure exists
    knows_mechanism: bool = False       # Understands why/how it works causally
    knows_procedure: bool = False       # Possesses the full recipe/step sequence
    practical_proficiency: float = 0.0  # [0.0, 1.0] practical execution skill
    successful_executions: int = 0
    failed_executions: int = 0

    @property
    def can_perform(self) -> bool:
        """Can initiate the procedure (must know the procedure steps)."""
        return self.knows_procedure

    def evaluate_execution_feasibility(
        self,
        agent_skills: dict[str, float],
        agent_inventory_items: dict[str, float],
        procedure: ProcedureDefinition,
    ) -> tuple[bool, str]:
        """Check if agent can actually execute the procedure successfully right now."""
        if not self.knows_procedure:
            return False, "Agent does not know the procedure steps"

        # Check skills
        for skill_id, min_lvl in procedure.required_skills.items():
            current_lvl = agent_skills.get(skill_id, 0.0)
            if current_lvl < min_lvl:
                return False, f"Insufficient skill proficiency in {skill_id} ({current_lvl:.2f} < {min_lvl:.2f})"

        # Check tools
        for tool in procedure.required_tools:
            if agent_inventory_items.get(tool, 0.0) < 1.0:
                return False, f"Missing required tool: {tool}"

        # Check materials
        for mat, qty in procedure.input_materials.items():
            if agent_inventory_items.get(mat, 0.0) < qty:
                return False, f"Insufficient material: {mat} (needs {qty}, has {agent_inventory_items.get(mat, 0.0)})"

        return True, "Execution preconditions satisfied"


class ProceduralKnowledgeGraph:
    """Registry of known procedures and agents' procedural competencies."""

    def __init__(self) -> None:
        self._procedures: dict[str, ProcedureDefinition] = {}

    def register_procedure(self, proc: ProcedureDefinition) -> None:
        self._procedures[proc.procedure_id] = proc

    def get_procedure(self, procedure_id: str) -> Optional[ProcedureDefinition]:
        return self._procedures.get(procedure_id)

    def all_procedures(self) -> list[ProcedureDefinition]:
        return list(self._procedures.values())
