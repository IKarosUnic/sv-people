"""Capability and Skill Composition System for Saltbor Phase 0.6.

Synthesizes new capabilities, practical procedures, physical objects,
and emerging occupational specializations subject to strict physical and
economic feasibility.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProcedureDefinition, ProcedureStep


@dataclasses.dataclass
class EmergentProfession:
    """An occupational specialization emerging from combined skills and economic demand."""

    profession_id: str
    title: str
    description: str
    constituent_skills: dict[str, float]  # skill_id -> min proficiency
    associated_procedures: list[str]      # procedure_ids
    primary_economic_domain: str
    pioneer_uid: str
    practitioners: list[str] = dataclasses.field(default_factory=list)
    created_tick: int = 0


@dataclasses.dataclass
class FeasibleObjectCreation:
    """A proposed physical artifact that has undergone construction validation."""

    creation_id: str
    name: str
    category: str                         # e.g., 'tool', 'furniture', 'apparatus', 'structural'
    creator_uid: str
    recipe_procedure: ProcedureDefinition
    required_materials: dict[str, float]
    required_tools: list[str]
    is_constructed: bool = False
    physical_durability: float = 1.0
    quality_score: float = 0.5
    created_tick: int = 0


class CapabilityCompositionSystem:
    """Manages creation and validation of new capabilities, objects, and professions."""

    def __init__(self) -> None:
        self.emergent_professions: dict[str, EmergentProfession] = {}
        self.created_objects: dict[str, FeasibleObjectCreation] = {}

    def propose_new_object(
        self,
        name: str,
        category: str,
        creator_uid: str,
        input_materials: dict[str, float],
        required_tools: list[str],
        required_skills: dict[str, float],
        duration_ticks: int = 4,
        tick: int = 0,
    ) -> FeasibleObjectCreation:
        """Formalize a proposed invention as a design/procedure specification."""
        proc_id = f"proc_create_{uuid4().hex[:8]}"
        steps = [
            ProcedureStep(
                step_index=1,
                name=f"Prepare components for {name}",
                description="Process raw input materials",
                duration_ticks=duration_ticks // 2,
                consumed_materials=input_materials,
                required_tools=required_tools,
            ),
            ProcedureStep(
                step_index=2,
                name=f"Assemble {name}",
                description="Join and finish components",
                duration_ticks=duration_ticks - (duration_ticks // 2),
                required_tools=required_tools,
            ),
        ]

        recipe = ProcedureDefinition(
            procedure_id=proc_id,
            name=f"Manufacture {name}",
            domain="crafting",
            description=f"Standard construction recipe for {name}",
            prerequisite_concepts=list(input_materials.keys()) + required_tools,
            required_skills=required_skills,
            required_tools=required_tools,
            input_materials=input_materials,
            output_products={name: 1.0},
            execution_steps=steps,
            base_duration_ticks=duration_ticks,
        )

        obj = FeasibleObjectCreation(
            creation_id=f"obj_prop_{uuid4().hex[:8]}",
            name=name,
            category=category,
            creator_uid=str(creator_uid),
            recipe_procedure=recipe,
            required_materials=input_materials,
            required_tools=required_tools,
            is_constructed=False,
            created_tick=tick,
        )
        self.created_objects[obj.creation_id] = obj
        return obj

    def construct_object(
        self,
        proposed_object: FeasibleObjectCreation,
        builder_inventory: dict[str, float],
        builder_skills: dict[str, float],
        tick: int = 0,
    ) -> tuple[bool, str]:
        """Physically construct the proposed object, verifying materials, tools, and labor."""
        # 1. Check tools
        for tool in proposed_object.required_tools:
            if builder_inventory.get(tool, 0.0) < 1.0:
                return False, f"Construction impossible: missing required tool '{tool}'"

        # 2. Check materials
        for mat, qty in proposed_object.required_materials.items():
            if builder_inventory.get(mat, 0.0) < qty:
                return False, f"Construction impossible: insufficient '{mat}' (needs {qty}, has {builder_inventory.get(mat, 0.0)})"

        # 3. Check skills
        for skill_id, min_lvl in proposed_object.recipe_procedure.required_skills.items():
            lvl = builder_skills.get(skill_id, 0.0)
            if lvl < min_lvl:
                return False, f"Construction failed: builder lacks requisite skill in '{skill_id}' ({lvl:.2f} < {min_lvl:.2f})"

        # 4. Consume materials
        for mat, qty in proposed_object.required_materials.items():
            builder_inventory[mat] -= qty

        # 5. Add finished product to inventory
        builder_inventory[proposed_object.name] = builder_inventory.get(proposed_object.name, 0.0) + 1.0
        proposed_object.is_constructed = True

        # Calculate quality based on skill margin
        avg_skill = sum(builder_skills.get(s, 0.0) for s in proposed_object.recipe_procedure.required_skills) / max(1, len(proposed_object.recipe_procedure.required_skills))
        proposed_object.quality_score = max(0.2, min(1.0, avg_skill * 1.2))

        return True, f"Successfully constructed '{proposed_object.name}' (Quality: {proposed_object.quality_score:.2f})"

    def form_emergent_profession(
        self,
        title: str,
        description: str,
        constituent_skills: dict[str, float],
        associated_procedures: list[str],
        primary_economic_domain: str,
        pioneer_uid: str,
        tick: int = 0,
    ) -> EmergentProfession:
        """Formalize a new occupational specialization."""
        prof_id = f"prof_{uuid4().hex[:8]}"
        prof = EmergentProfession(
            profession_id=prof_id,
            title=title,
            description=description,
            constituent_skills=constituent_skills,
            associated_procedures=associated_procedures,
            primary_economic_domain=primary_economic_domain,
            pioneer_uid=str(pioneer_uid),
            practitioners=[str(pioneer_uid)],
            created_tick=tick,
        )
        self.emergent_professions[prof_id] = prof
        return prof
