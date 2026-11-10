"""Compositional Reasoning Engine for Saltbor Phase 0.6.

Combines known concepts, materials, tools, and techniques to synthesize
novel workflows and practical procedures, validating domain feasibility.
"""

from __future__ import annotations

import dataclasses
from typing import Optional
from uuid import uuid4

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProcedureDefinition, ProcedureStep


@dataclasses.dataclass
class CompositionProposal:
    """A synthesized capability or procedure resulting from combining known components."""

    proposal_id: str
    name: str
    description: str
    contributing_concept_ids: list[str]
    synthesized_procedure: ProcedureDefinition
    feasibility_score: float            # [0.0, 1.0]
    is_physically_feasible: bool
    feasibility_notes: str


class CompositionalReasoningEngine:
    """Combines existing capabilities into new procedures."""

    def compose_procedure(
        self,
        graph: IndividualKnowledgeGraph,
        primary_skill_id: str,
        secondary_skill_id: str,
        material_concept_id: str,
        tool_concept_id: str,
        novel_product_name: str,
        agent_skills: dict[str, float],
        agent_inventory: dict[str, float],
        tick: int = 0,
    ) -> Optional[CompositionProposal]:
        """Synthesize a new production or crafting procedure by composing capabilities."""
        # 1. Prerequisite verification: Agent must know all components
        required_elements = [material_concept_id, tool_concept_id]
        for elem in required_elements:
            if not graph.knows_concept(elem, min_confidence=0.3):
                return None

        # Check skills
        p_lvl = agent_skills.get(primary_skill_id, 0.0)
        s_lvl = agent_skills.get(secondary_skill_id, 0.0)
        if p_lvl < 0.25 or s_lvl < 0.20:
            return None

        # 2. Feasibility evaluation
        # Feasibility increases with skill proficiency and tool availability
        tool_available = agent_inventory.get(tool_concept_id, 0.0) >= 1.0
        mat_available = agent_inventory.get(material_concept_id, 0.0) >= 2.0

        feasibility = (p_lvl * 0.4 + s_lvl * 0.3 + (0.3 if tool_available else 0.1))
        is_feasible = feasibility >= 0.40 and (p_lvl >= 0.3 or s_lvl >= 0.3)

        notes = "Physically and technically feasible" if is_feasible else "Inadequate skill or tools"

        proc_id = f"proc_comp_{uuid4().hex[:8]}"
        steps = [
            ProcedureStep(
                step_index=1,
                name=f"Prepare {material_concept_id}",
                description=f"Inspect and dress {material_concept_id} using {tool_concept_id}",
                required_skill_id=primary_skill_id,
                min_skill_level=0.3,
                duration_ticks=2,
                consumed_materials={material_concept_id: 1.0},
                required_tools=[tool_concept_id],
            ),
            ProcedureStep(
                step_index=2,
                name=f"Execute {novel_product_name} assembly",
                description=f"Apply {secondary_skill_id} principles to craft final article",
                required_skill_id=secondary_skill_id,
                min_skill_level=0.25,
                duration_ticks=3,
                consumed_materials={material_concept_id: 1.0},
                required_tools=[tool_concept_id],
            ),
        ]

        synthesized_proc = ProcedureDefinition(
            procedure_id=proc_id,
            name=f"Synthesized: {novel_product_name}",
            domain="crafting",
            description=f"Composition of {primary_skill_id} and {secondary_skill_id} with {material_concept_id}",
            prerequisite_concepts=[material_concept_id, tool_concept_id],
            required_skills={primary_skill_id: 0.35, secondary_skill_id: 0.30},
            required_tools=[tool_concept_id],
            input_materials={material_concept_id: 2.0},
            output_products={novel_product_name: 1.0},
            execution_steps=steps,
            base_duration_ticks=5,
            difficulty=0.45,
            failure_risk=max(0.05, 0.35 - feasibility * 0.3),
        )

        proposal = CompositionProposal(
            proposal_id=f"comp_{uuid4().hex[:8]}",
            name=f"Composition of {novel_product_name}",
            description=synthesized_proc.description,
            contributing_concept_ids=[primary_skill_id, secondary_skill_id, material_concept_id, tool_concept_id],
            synthesized_procedure=synthesized_proc,
            feasibility_score=feasibility,
            is_physically_feasible=is_feasible,
            feasibility_notes=notes,
        )

        # Register novel concept in agent's individual knowledge graph
        concept_node = KnowledgeNode(
            node_id=f"concept_{novel_product_name.lower().replace(' ', '_')}",
            node_type=NodeType.PROCEDURE,
            label=f"Procedure: {novel_product_name}",
            description=synthesized_proc.description,
            properties={"procedure_id": proc_id, "feasibility": feasibility},
            created_tick=tick,
            origin_type="compositional_reasoning",
            origin_id=graph.human_uid,
            validation_status=ValidationStatus.PROPOSED,
        )
        graph.register_local_node(concept_node, confidence=feasibility, tick=tick)

        return proposal
