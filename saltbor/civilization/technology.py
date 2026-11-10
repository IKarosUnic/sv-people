"""Technological and Knowledge Evolution Engine for SALTBOR Phase 1.0.

Models knowledge acquisition, innovation discovery, empirical constraints, diffusion, and potential loss/recovery:
- Knowledge types: practical, scientific, technical, agricultural, commercial, medical, architectural, organizational, environmental, cultural.
- Innovation steps: need identification, exploration, observation, hypothesis, experiment, solution, validation, transmission, adaptation, refinement.
- Realistic constraints: requires material prerequisites, existing knowledge bases, labor time; non-linear loss and rediscovery.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from saltbor.core.types import Tick


class KnowledgeDomain(str, Enum):
    PRACTICAL = "practical"
    SCIENTIFIC = "scientific"
    TECHNICAL = "technical"
    AGRICULTURAL = "agricultural"
    COMMERCIAL = "commercial"
    MEDICAL = "medical"
    ARCHITECTURAL = "architectural"
    ORGANIZATIONAL = "organizational"
    ENVIRONMENTAL = "environmental"
    CULTURAL = "cultural"


class InnovationStatus(str, Enum):
    HYPOTHESIS = "hypothesis"
    EXPERIMENTING = "experimenting"
    VALIDATED = "validated"
    DIFFUSED = "diffused"
    FORGOTTEN = "forgotten"
    RECOVERED = "recovered"


@dataclass
class TechnologyNode:
    tech_id: str
    name: str
    domain: KnowledgeDomain
    prerequisites: List[str] = field(default_factory=list)
    material_requirements: List[str] = field(default_factory=list)
    discovered_by: Optional[str] = None
    discovered_year: float = 2026.0
    status: InnovationStatus = InnovationStatus.HYPOTHESIS
    productivity_bonus: float = 0.1  # boost when adopted
    known_by_settlements: Set[str] = field(default_factory=set)
    known_by_individuals: Set[str] = field(default_factory=set)


class TechnologicalEvolutionEngine:
    """Manages knowledge synthesis, invention, material constraints, transmission, and recovery."""

    def __init__(self) -> None:
        self.technologies: Dict[str, TechnologyNode] = {}
        self.diffusion_history: List[Dict[str, Any]] = []

    def register_innovation_concept(
        self,
        name: str,
        domain: KnowledgeDomain,
        prerequisites: Optional[List[str]] = None,
        material_requirements: Optional[List[str]] = None,
        productivity_bonus: float = 0.15,
    ) -> TechnologyNode:
        tech_id = f"tech_{uuid4().hex[:8]}"
        tech = TechnologyNode(
            tech_id=tech_id,
            name=name,
            domain=domain,
            prerequisites=prerequisites or [],
            material_requirements=material_requirements or [],
            status=InnovationStatus.HYPOTHESIS,
            productivity_bonus=productivity_bonus,
        )
        self.technologies[tech_id] = tech
        return tech

    def attempt_discovery(
        self,
        tech_id: str,
        innovator_id: str,
        settlement_id: str,
        available_materials: List[str],
        known_tech_ids: Set[str],
        year: float = 2026.0,
    ) -> bool:
        """Attempts to validate a hypothesis based on materials and prerequisites."""
        if tech_id not in self.technologies:
            return False
        tech = self.technologies[tech_id]

        # Check prerequisite technologies
        for prereq in tech.prerequisites:
            if prereq not in known_tech_ids:
                return False

        # Check material availability
        for mat in tech.material_requirements:
            if mat not in available_materials:
                return False

        tech.status = InnovationStatus.VALIDATED
        tech.discovered_by = innovator_id
        tech.discovered_year = year
        tech.known_by_settlements.add(settlement_id)
        tech.known_by_individuals.add(innovator_id)
        return True

    def diffuse_to_settlement(self, tech_id: str, target_settlement_id: str) -> bool:
        if tech_id not in self.technologies:
            return False
        tech = self.technologies[tech_id]
        if tech.status not in (InnovationStatus.VALIDATED, InnovationStatus.DIFFUSED, InnovationStatus.RECOVERED):
            return False
        tech.known_by_settlements.add(target_settlement_id)
        tech.status = InnovationStatus.DIFFUSED
        self.diffusion_history.append({
            "tech_id": tech_id,
            "settlement_id": target_settlement_id,
            "status": tech.status.value,
        })
        return True

    def simulate_knowledge_decay(self, tech_id: str, settlement_id: str) -> bool:
        """Simulates demographic collapse or isolation leading to loss of specialized knowledge."""
        if tech_id not in self.technologies:
            return False
        tech = self.technologies[tech_id]
        if settlement_id in tech.known_by_settlements:
            tech.known_by_settlements.remove(settlement_id)
            if len(tech.known_by_settlements) == 0:
                tech.status = InnovationStatus.FORGOTTEN
            return True
        return False

    def recover_forgotten_knowledge(self, tech_id: str, settlement_id: str) -> bool:
        """Rediscovery via archaeological / archival / intercultural exchange."""
        if tech_id not in self.technologies:
            return False
        tech = self.technologies[tech_id]
        if tech.status == InnovationStatus.FORGOTTEN:
            tech.status = InnovationStatus.RECOVERED
            tech.known_by_settlements.add(settlement_id)
            return True
        return False
