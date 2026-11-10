"""Civilization Evolution Engine for SALTBOR Phase 1.0.

Core orchestrator of civilization-level emergence, multidimensional trajectory, and life-cycle:
- Multi-attribute state: Identity, territory, population, demographics, constituent settlements, institutions, economy, governance, culture, knowledge, diplomacy.
- Evolution processes: Formation, growth, consolidation, territorial expansion, institutional reform, diversification, fragmentation, integration, decline, collapse, recovery.
- Non-linear: avoids mandatory teleology or deterministic progress stages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from saltbor.civilization.economy import EconomicCivilizationEngine, EconomicSector
from saltbor.civilization.history import HistoricalCategory, HistoricalMemoryEngine
from saltbor.civilization.interaction import MultiSocietyInteractionEngine, RelationType
from saltbor.civilization.migration import MigrationDynamicsEngine, MigrationReason
from saltbor.civilization.resilience import CivilizationResilienceEngine, CrisisType
from saltbor.civilization.settlement import Settlement, SettlementEvolutionEngine, SettlementType
from saltbor.civilization.stratification import SocialStratificationEngine
from saltbor.civilization.technology import KnowledgeDomain, TechnologicalEvolutionEngine
from saltbor.core.types import Tick


class CivilizationPhase(str, Enum):
    EMERGING = "emerging"
    GROWING = "growing"
    CONSOLIDATED = "consolidated"
    EXPANDING = "expanding"
    TRANSFORMING = "transforming"
    FRAGMENTED = "fragmented"
    DECLINING = "declining"
    RECOVERED = "recovered"
    EXTINCT = "extinct"


@dataclass
class CivilizationState:
    civilization_id: str
    name: str
    phase: CivilizationPhase = CivilizationPhase.EMERGING
    territory_name: str = "El Salvador"
    population_count: int = 0
    settlement_ids: List[str] = field(default_factory=list)
    institution_ids: List[str] = field(default_factory=list)
    founded_year: float = 2026.0
    current_year: float = 2026.0
    collective_identity: str = "Sociedad Cuscatleca"
    cohesion_index: float = 0.7  # 0.0 to 1.0
    cultural_traits: Dict[str, float] = field(default_factory=dict)
    known_technologies: Set[str] = field(default_factory=set)
    active: bool = True


class CivilizationEvolutionEngine:
    """Master orchestrator integrating demographic, institutional, historical, settlement, economic, and technological engines."""

    def __init__(self) -> None:
        self.civilizations: Dict[str, CivilizationState] = {}
        # Integrated sub-engines
        self.history = HistoricalMemoryEngine()
        self.settlements = SettlementEvolutionEngine()
        self.migration = MigrationDynamicsEngine()
        self.economy = EconomicCivilizationEngine()
        self.technology = TechnologicalEvolutionEngine()
        self.stratification = SocialStratificationEngine()
        self.resilience = CivilizationResilienceEngine()
        self.interactions = MultiSocietyInteractionEngine()

    def found_civilization(
        self,
        name: str,
        territory: str = "El Salvador",
        initial_year: float = 2026.0,
        initial_settlement_name: str = "San Salvador Central",
    ) -> CivilizationState:
        civ_id = f"civ_{uuid4().hex[:8]}"
        civ = CivilizationState(
            civilization_id=civ_id,
            name=name,
            phase=CivilizationPhase.EMERGING,
            territory_name=territory,
            founded_year=initial_year,
            current_year=initial_year,
            collective_identity=name,
        )

        # Initial settlement
        init_settle = self.settlements.found_settlement(
            name=initial_settlement_name,
            settlement_type=SettlementType.CENTRO_URBANO,
            municipality="San Salvador Centro",
            department="San Salvador",
            coordinates=(13.6929, -89.2182),
            founded_year=initial_year,
        )
        civ.settlement_ids.append(init_settle.settlement_id)
        self.civilizations[civ_id] = civ

        # Record foundation in historical memory
        self.history.record_ground_truth(
            category=HistoricalCategory.FOUNDATION,
            tick=0,
            year=initial_year,
            location=init_settle.name,
            actors=[civ.name],
            title=f"Fundación de {civ.name}",
            description=f"Se establece la comunidad inicial en {init_settle.name}.",
            significance=0.9,
        )
        self.history.form_cultural_narrative(civ_id, f"hist_{civ_id}", framing="heroic")
        self.interactions.register_society(civ_id)
        return civ

    def evolve_step(self, civ_id: str, delta_years: float = 1.0, current_tick: Tick = 0) -> CivilizationState:
        """Advances civilization history, economy, and state transition."""
        if civ_id not in self.civilizations:
            raise KeyError(f"Civilization {civ_id} not found")
        civ = self.civilizations[civ_id]
        if not civ.active:
            return civ

        civ.current_year += delta_years

        # Aggregate total population across constituent settlements
        total_pop = sum(self.settlements.settlements[s_id].population_count for s_id in civ.settlement_ids if s_id in self.settlements.settlements)
        civ.population_count = total_pop

        # Economic cycle
        self.economy.simulate_economic_cycle()

        # Phase transitions based on emergence
        if total_pop == 0 and len(civ.settlement_ids) > 0 and civ.current_year - civ.founded_year > 5:
            civ.phase = CivilizationPhase.EXTINCT
            civ.active = False
            self.history.record_ground_truth(
                category=HistoricalCategory.DEMOGRAPHIC_CHANGE,
                tick=current_tick,
                year=civ.current_year,
                location=civ.territory_name,
                actors=[civ.name],
                title=f"Desaparición de {civ.name}",
                description="La sociedad ha colapsado o su población se ha dispersado completamente.",
                significance=0.95,
            )
        elif civ.cohesion_index < 0.25 and civ.phase != CivilizationPhase.FRAGMENTED:
            civ.phase = CivilizationPhase.FRAGMENTED
            self.history.record_ground_truth(
                category=HistoricalCategory.CONFLICT,
                tick=current_tick,
                year=civ.current_year,
                location=civ.territory_name,
                actors=[civ.name],
                title="Fragmentación Social",
                description="Pérdida crítica de cohesión interna produce fragmentación en facciones.",
                significance=0.8,
            )
        elif total_pop > 100 and civ.cohesion_index > 0.6 and len(civ.settlement_ids) > 2:
            civ.phase = CivilizationPhase.EXPANDING
        elif total_pop > 40 and civ.phase == CivilizationPhase.EMERGING:
            civ.phase = CivilizationPhase.GROWING

        return civ

    def fragment_civilization(self, civ_id: str, new_name: str, separating_settlement_ids: List[str]) -> CivilizationState:
        """Splits off settlements into a newly emerged autonomous society."""
        if civ_id not in self.civilizations:
            raise KeyError(f"Civilization {civ_id} not found")
        parent = self.civilizations[civ_id]

        new_civ_id = f"civ_{uuid4().hex[:8]}"
        new_civ = CivilizationState(
            civilization_id=new_civ_id,
            name=new_name,
            phase=CivilizationPhase.FRAGMENTED,
            territory_name=parent.territory_name,
            founded_year=parent.current_year,
            current_year=parent.current_year,
            collective_identity=new_name,
            settlement_ids=[s for s in separating_settlement_ids if s in parent.settlement_ids],
        )

        for s_id in new_civ.settlement_ids:
            parent.settlement_ids.remove(s_id)

        parent.cohesion_index = max(0.2, parent.cohesion_index - 0.2)
        self.civilizations[new_civ_id] = new_civ

        self.history.record_ground_truth(
            category=HistoricalCategory.ORGANIZATION_CHANGE,
            tick=0,
            year=parent.current_year,
            location=parent.territory_name,
            actors=[parent.name, new_civ.name],
            title=f"Fragmentación y nacimiento de {new_name}",
            description=f"La comunidad se divide; {new_name} emerge como nueva entidad autónoma.",
            significance=0.85,
        )

        self.interactions.establish_relation(parent.civilization_id, new_civ_id, RelationType.TENSION, trust=0.3)
        return new_civ
