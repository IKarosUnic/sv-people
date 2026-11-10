"""Creative Combination and Innovation Engine for Saltbor Phase 0.7 (Section 6).

Implements rigorous combinatorial synthesis across disparate knowledge domains,
tool adaptation, procedural modification, and resource repurposing while
strictly enforcing physical, technical, and resource feasibility constraints.

Governs the 7-stage innovation lifecycle:
IDEA -> HYPOTHESIS -> DESIGN -> PROTOTYPE -> EXPERIMENTATION -> FUNCTIONAL_SOLUTION -> VALIDATED_INNOVATION.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


class InnovationStage(str, Enum):
    """The 7 formal stages of technological and procedural discovery."""

    IDEA = "idea"
    HYPOTHESIS = "hypothesis"
    DESIGN = "design"
    PROTOTYPE = "prototype"
    EXPERIMENTATION = "experimentation"
    FUNCTIONAL_SOLUTION = "functional_solution"
    VALIDATED_INNOVATION = "validated_innovation"


@dataclasses.dataclass
class CreativeInnovation:
    """A synthesized creative breakthrough moving through the innovation lifecycle."""

    innovation_id: str
    name: str
    description: str
    stage: InnovationStage
    creator_uid: str
    domains_combined: list[str]
    contributing_concepts: list[str]
    required_skills: dict[str, float]
    required_materials: dict[str, float]
    required_tools: list[str]
    labor_ticks_required: int
    physical_feasibility: float         # [0.0, 1.0] Must adhere to thermodynamics and mechanics
    economic_viability: float           # [0.0, 1.0] Cost-benefit utility
    tool_adaptation_note: Optional[str] = None
    procedure_modification_note: Optional[str] = None
    alternative_resource_usage_note: Optional[str] = None
    labor_ticks_invested: int = 0
    trial_count: int = 0
    is_physically_sound: bool = True
    created_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "innovation_id": self.innovation_id,
            "name": self.name,
            "stage": self.stage.value,
            "domains": self.domains_combined,
            "concepts": self.contributing_concepts,
            "physical_feasibility": round(self.physical_feasibility, 3),
            "economic_viability": round(self.economic_viability, 3),
            "labor_invested": self.labor_ticks_invested,
            "is_physically_sound": self.is_physically_sound,
        }


class CreativeCombinationEngine:
    """Synthesizes cross-domain capabilities into physically feasible innovations."""

    def synthesize_cross_domain_innovation(
        self,
        creator_uid: str,
        name: str,
        description: str,
        domains: list[str],
        concepts: list[str],
        required_skills: dict[str, float],
        required_materials: dict[str, float],
        required_tools: list[str],
        labor_ticks: int = 12,
        graph: Optional[IndividualKnowledgeGraph] = None,
        agent_skills: Optional[dict[str, float]] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Optional[CreativeInnovation]:
        """Synthesize a new cross-domain idea into a formal innovation proposal.

        Validates that agent actually knows contributing concepts and has minimum skill proficiencies.
        """
        agent_skills = agent_skills or {}

        # 1. Epistemic acquaintance check: agent cannot combine what they do not know
        if graph:
            for c in concepts:
                if not graph.knows_concept(c, min_confidence=0.25):
                    logger.debug("Cannot synthesize innovation: concept '%s' unknown", c)
                    return None

        # 2. Skill check: must have non-zero skill in contributing domains
        skill_sum = sum(agent_skills.get(s, 0.0) for s in required_skills.keys())
        avg_skill = skill_sum / max(1, len(required_skills)) if required_skills else 0.35
        if avg_skill < 0.20:
            logger.debug("Cannot synthesize innovation: average skill proficiency too low (%f)", avg_skill)
            return None

        # 3. Feasibility check: reject arbitrary physical impossibilities
        # Checks for contradictory physical properties
        is_physically_sound = True
        desc_lower = (name + " " + description).lower()
        if "perpetual" in desc_lower or "zero_fuel_engine" in desc_lower:
            is_physically_sound = False

        feasibility = min(0.95, 0.35 + (avg_skill * 0.40) + (0.20 if is_physically_sound else -0.80))
        viability = min(0.90, 0.40 + (len(domains) * 0.15))

        innovation = CreativeInnovation(
            innovation_id=f"innov_{uuid4().hex[:8]}",
            name=name,
            description=description,
            stage=InnovationStage.IDEA,
            creator_uid=str(creator_uid),
            domains_combined=list(domains),
            contributing_concepts=list(concepts),
            required_skills=dict(required_skills),
            required_materials=dict(required_materials),
            required_tools=list(required_tools),
            labor_ticks_required=labor_ticks,
            physical_feasibility=feasibility,
            economic_viability=viability,
            is_physically_sound=is_physically_sound,
            created_tick=tick,
        )

        if epistemic:
            epistemic.register_belief(
                EpistemicBelief(
                    belief_id=innovation.innovation_id,
                    subject=name,
                    predicate="creative_innovation_proposal",
                    object_val=InnovationStage.IDEA.value,
                    belief_type=BeliefType.HYPOTHESIS,
                    confidence=feasibility,
                    source_type="creative_combination",
                    created_tick=tick,
                    updated_tick=tick,
                    evidence_items=[f"Combined domains: {', '.join(domains)}"],
                )
            )

        return innovation

    def advance_stage(
        self,
        innovation: CreativeInnovation,
        agent_skills: dict[str, float],
        agent_inventory: dict[str, float],
        labor_ticks_spent: int = 1,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> tuple[bool, InnovationStage, str]:
        """Progress an innovation along the 7-stage lifecycle.

        Requires requisite skills, tools, materials, and physical feasibility.
        """
        if not innovation.is_physically_sound:
            return False, innovation.stage, "Advancement halted: Physical laws violated"

        innovation.labor_ticks_invested += labor_ticks_spent

        # Lifecycle transition rules
        current = innovation.stage

        if current == InnovationStage.IDEA:
            # Advance to HYPOTHESIS: requires clear rationale
            innovation.stage = InnovationStage.HYPOTHESIS
            return True, innovation.stage, "Formulated into testable structural hypothesis"

        elif current == InnovationStage.HYPOTHESIS:
            # Advance to DESIGN: requires technical drafting
            innovation.stage = InnovationStage.DESIGN
            return True, innovation.stage, "Developed detailed technical schematic and material specification"

        elif current == InnovationStage.DESIGN:
            # Advance to PROTOTYPE: requires assembly of materials and tools
            for tool in innovation.required_tools:
                if agent_inventory.get(tool, 0.0) < 1.0:
                    return False, current, f"Cannot construct prototype: Missing tool '{tool}'"

            for mat, req_qty in innovation.required_materials.items():
                if agent_inventory.get(mat, 0.0) < req_qty:
                    return False, current, f"Cannot construct prototype: Insufficient '{mat}' ({agent_inventory.get(mat, 0.0)} < {req_qty})"

            # Consume prototype materials
            for mat, req_qty in innovation.required_materials.items():
                agent_inventory[mat] = max(0.0, agent_inventory.get(mat, 0.0) - req_qty)

            innovation.stage = InnovationStage.PROTOTYPE
            return True, innovation.stage, "Physical prototype assembled using real inventory resources"

        elif current == InnovationStage.PROTOTYPE:
            # Advance to EXPERIMENTATION: conduct active functional trials
            innovation.stage = InnovationStage.EXPERIMENTATION
            innovation.trial_count += 1
            return True, innovation.stage, "Prototype subjected to operational stress testing"

        elif current == InnovationStage.EXPERIMENTATION:
            # Check skill competency for functional success
            competent = all(
                agent_skills.get(s, 0.0) >= min_l * 0.8
                for s, min_l in innovation.required_skills.items()
            )
            if competent and innovation.labor_ticks_invested >= innovation.labor_ticks_required:
                innovation.stage = InnovationStage.FUNCTIONAL_SOLUTION
                return True, innovation.stage, "Experimental trials passed; functional working solution demonstrated"
            else:
                return False, current, "Trials in progress: more labor or practice required"

        elif current == InnovationStage.FUNCTIONAL_SOLUTION:
            # Advance to VALIDATED_INNOVATION: peer replication or repeated reliability
            innovation.stage = InnovationStage.VALIDATED_INNOVATION
            if epistemic:
                epistemic.register_belief(
                    EpistemicBelief(
                        belief_id=f"val_{innovation.innovation_id}",
                        subject=innovation.name,
                        predicate="validated_innovation",
                        object_val="operational_standard",
                        belief_type=BeliefType.VALIDATED_KNOWLEDGE,
                        confidence=0.95,
                        source_type="empirical_validation",
                        created_tick=tick,
                        updated_tick=tick,
                    )
                )
            return True, innovation.stage, "Innovation formally validated and established as a reliable procedure"

        return False, current, "Innovation already at terminal validation stage"

    def adapt_tool(
        self,
        creator_uid: str,
        tool_id: str,
        new_task: str,
        agent_skill: float,
        tick: int = 0,
    ) -> CreativeInnovation:
        """Adapt an existing tool for an unscripted secondary task."""
        innovation_id = f"tool_adapt_{uuid4().hex[:8]}"
        name = f"Adapted {tool_id} for {new_task}"
        feasibility = min(0.90, 0.50 + agent_skill * 0.40)

        return CreativeInnovation(
            innovation_id=innovation_id,
            name=name,
            description=f"Repurposed tool '{tool_id}' to execute '{new_task}' through mechanical adaptation",
            stage=InnovationStage.DESIGN,
            creator_uid=str(creator_uid),
            domains_combined=["toolmaking", "practical_trades"],
            contributing_concepts=[tool_id, new_task],
            required_skills={"skill_technical": 0.3},
            required_materials={},
            required_tools=[tool_id],
            labor_ticks_required=4,
            physical_feasibility=feasibility,
            economic_viability=0.80,
            tool_adaptation_note=f"Tool '{tool_id}' modified for '{new_task}'",
            created_tick=tick,
        )

    def modify_procedure_with_substitute(
        self,
        creator_uid: str,
        procedure_name: str,
        standard_material: str,
        substitute_material: str,
        substitution_feasibility: float,
        tick: int = 0,
    ) -> CreativeInnovation:
        """Modify an existing procedural recipe by substituting a scarce material."""
        innovation_id = f"proc_mod_{uuid4().hex[:8]}"
        name = f"Modified {procedure_name} ({substitute_material} substitute)"

        return CreativeInnovation(
            innovation_id=innovation_id,
            name=name,
            description=f"Alternative recipe substituting scarce '{standard_material}' with accessible '{substitute_material}'",
            stage=InnovationStage.HYPOTHESIS,
            creator_uid=str(creator_uid),
            domains_combined=["resource_engineering", "material_science"],
            contributing_concepts=[standard_material, substitute_material],
            required_skills={"skill_practical": 0.35},
            required_materials={substitute_material: 1.5},
            required_tools=[],
            labor_ticks_required=6,
            physical_feasibility=substitution_feasibility,
            economic_viability=0.75,
            alternative_resource_usage_note=f"Replaced {standard_material} with {substitute_material}",
            created_tick=tick,
        )
