"""Multi-Generational Evolution and Demographics Bridge for SALTBOR Phase 1.0.

Bridges biological lifecycle, reproduction, genetics, mortality, and households with civilization-scale cohorts:
- Tracking generational cohorts (Gen 0, Gen 1, Gen 2, etc.).
- Lineage tree tracing and family reorganization upon death/maturation.
- Knowledge and trait transmission without genetic determinism.
- High-efficiency multi-decade demographic aging without full per-tick cognitive execution.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from saltbor.core.types import Tick
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph, GenealogyRecord
from saltbor.population.human import SyntheticHuman


@dataclass
class FamilyLineage:
    family_id: str
    surname: str
    founder_ids: List[str]
    generation_depth: int = 1
    total_members_count: int = 2
    living_members_count: int = 2
    primary_settlement_id: Optional[str] = None
    accumulated_traditions: List[str] = field(default_factory=list)


@dataclass
class IndividualGenerationRecord:
    human_id: str
    generation_index: int
    birth_year: float
    death_year: Optional[float] = None
    parent_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)
    transmitted_skills: List[str] = field(default_factory=list)
    living: bool = True


class MultiGenerationalEngine:
    """Manages generational cohorts, lineage evolution, and population turnover."""

    def __init__(self, genealogy: Optional[GenealogicalGraph] = None) -> None:
        self.genealogy = genealogy or GenealogicalGraph()
        self.lineages: Dict[str, FamilyLineage] = {}
        self.records: Dict[str, IndividualGenerationRecord] = {}

    def register_founder(
        self,
        human_id: str,
        surname: str,
        birth_year: float = 2000.0,
        settlement_id: Optional[str] = None,
    ) -> IndividualGenerationRecord:
        record = IndividualGenerationRecord(
            human_id=human_id,
            generation_index=0,
            birth_year=birth_year,
            living=True,
        )
        self.records[human_id] = record

        fam_id = f"fam_{surname.lower()}_{uuid4().hex[:6]}"
        lineage = FamilyLineage(
            family_id=fam_id,
            surname=surname,
            founder_ids=[human_id],
            generation_depth=1,
            total_members_count=1,
            living_members_count=1,
            primary_settlement_id=settlement_id,
        )
        self.lineages[fam_id] = lineage
        return record

    def birth_descendant(
        self,
        child_id: str,
        parent_a_id: str,
        parent_b_id: Optional[str],
        birth_year: float,
        inherited_skills: Optional[List[str]] = None,
    ) -> IndividualGenerationRecord:
        parent_rec = self.records.get(parent_a_id)
        gen = (parent_rec.generation_index + 1) if parent_rec else 1

        rec = IndividualGenerationRecord(
            human_id=child_id,
            generation_index=gen,
            birth_year=birth_year,
            parent_ids=[p for p in (parent_a_id, parent_b_id) if p],
            transmitted_skills=inherited_skills or [],
            living=True,
        )
        self.records[child_id] = rec

        if parent_rec:
            parent_rec.children_ids.append(child_id)

        # Update family lineage depth
        for lineage in self.lineages.values():
            if parent_a_id in lineage.founder_ids or any(p in self.records for p in lineage.founder_ids):
                lineage.total_members_count += 1
                lineage.living_members_count += 1
                lineage.generation_depth = max(lineage.generation_depth, gen + 1)
                break

        return rec

    def record_death(self, human_id: str, death_year: float) -> bool:
        if human_id not in self.records:
            return False
        rec = self.records[human_id]
        rec.living = False
        rec.death_year = death_year

        # Update lineage living count
        for lineage in self.lineages.values():
            if human_id in lineage.founder_ids or rec.generation_index < lineage.generation_depth:
                lineage.living_members_count = max(0, lineage.living_members_count - 1)
        return True

    def get_generation_cohort(self, generation_index: int) -> List[IndividualGenerationRecord]:
        return [r for r in self.records.values() if r.generation_index == generation_index]
