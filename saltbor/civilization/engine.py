"""Civilization Evolution Engine for SALTBOR Phase 1.11.

Master orchestrator of civilization emergence, longitudinal trajectories, and multi-generational evolution:
- Multi-attribute state: Identity, territory, population, demographics, constituent settlements,
  institutions, economy, governance, culture, knowledge, diplomacy, and environmental interactions.
- Non-scripted emergence: Growth, Stability, Expansion, Fragmentation, Adaptation, Crisis, Decline,
  Recovery, Transformation.
- Avoids mandatory teleology, predetermined stages, or guaranteed civilizational success/collapse.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import numpy as np

from saltbor.civilization.economy import EconomicCivilizationEngine, EconomicSector
from saltbor.civilization.history import HistoricalCategory, HistoricalMemoryEngine
from saltbor.civilization.interaction import MultiSocietyInteractionEngine, RelationType
from saltbor.civilization.migration import MigrationDynamicsEngine, MigrationReason
from saltbor.civilization.multigenerational import MultiGenerationalEngine
from saltbor.civilization.resilience import CivilizationResilienceEngine, CrisisType
from saltbor.civilization.settlement import Settlement, SettlementEvolutionEngine, SettlementType
from saltbor.civilization.society_vector import SocietalIdentityVector
from saltbor.civilization.stratification import SocialStratificationEngine
from saltbor.civilization.technology import KnowledgeDomain, TechnologicalEvolutionEngine
from saltbor.core.types import Tick


class CivilizationPhase(str, Enum):
    """Broad phases for backward compatibility."""
    EMERGING = "emerging"
    GROWING = "growing"
    CONSOLIDATED = "consolidated"
    EXPANDING = "expanding"
    TRANSFORMING = "transforming"
    FRAGMENTED = "fragmented"
    DECLINING = "declining"
    RECOVERED = "recovered"
    EXTINCT = "extinct"


class CivilizationCondition(str, Enum):
    """Descriptive, analytical civilization conditions (derived from observable variables).
    
    A society can exhibit multiple conditions simultaneously (e.g. GROWTH and ENVIRONMENTAL_DEGRADATION).
    """
    GROWTH = "growth"
    STABILITY = "stability"
    EXPANSION = "expansion"
    FRAGMENTATION = "fragmentation"
    ADAPTATION = "adaptation"
    CRISIS = "crisis"
    DECLINE = "decline"
    RECOVERY = "recovery"
    TRANSFORMATION = "transformation"
    HIGH_INEQUALITY = "high_inequality"
    ENVIRONMENTAL_PRESSURE = "environmental_pressure"
    KNOWLEDGE_EXPANSION = "knowledge_expansion"
    KNOWLEDGE_RECESSION = "knowledge_recession"


@dataclass
class CivilizationState:
    civilization_id: str
    name: str
    phase: CivilizationPhase = CivilizationPhase.EMERGING
    conditions: Set[CivilizationCondition] = field(default_factory=lambda: {CivilizationCondition.GROWTH})
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
    ecological_stress: float = 0.20  # 0.0 to 1.0
    gini_wealth: float = 0.35  # 0.0 to 1.0
    total_gdp_production: float = 500.0
    active_crises: List[str] = field(default_factory=list)

    def to_identity_vector(self) -> SocietalIdentityVector:
        """Derive an 18-variable SocietalIdentityVector from the current state."""
        return SocietalIdentityVector(
            society_id=self.civilization_id,
            society_name=self.name,
            population=self.population_count,
            total_production_units=self.total_gdp_production,
            wealth_gini=self.gini_wealth,
            community_cohesion=self.cohesion_index,
            retained_knowledge_count=len(self.known_technologies),
            ecological_habitability=max(0.0, 1.0 - self.ecological_stress),
        )


class CivilizationEvolutionEngine:
    """Master orchestrator coordinating demographic, settlement, historical, economic,
    technological, cultural, and environmental sub-engines over generational time horizons.
    """

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng(42)
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
        self.multigenerational = MultiGenerationalEngine()

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
            conditions={CivilizationCondition.GROWTH, CivilizationCondition.STABILITY},
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
        """Advances civilization history, economy, ecology, and emergent state transition."""
        if civ_id not in self.civilizations:
            raise KeyError(f"Civilization {civ_id} not found")
        civ = self.civilizations[civ_id]
        if not civ.active:
            return civ

        civ.current_year += delta_years

        # Aggregate total population across constituent settlements
        total_pop = sum(
            self.settlements.settlements[s_id].population_count
            for s_id in civ.settlement_ids
            if s_id in self.settlements.settlements
        )
        civ.population_count = total_pop

        # Economic cycle
        self.economy.simulate_economic_cycle()
        civ.total_gdp_production = sum(self.economy.sector_production.values())

        # Update emergent analytical conditions
        civ.conditions = self._compute_emergent_conditions(civ, delta_years, current_tick)

        # Map emergent conditions to overall backward-compatible phase
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
        elif CivilizationCondition.FRAGMENTATION in civ.conditions:
            civ.phase = CivilizationPhase.FRAGMENTED
        elif CivilizationCondition.CRISIS in civ.conditions:
            civ.phase = CivilizationPhase.DECLINING
        elif CivilizationCondition.RECOVERY in civ.conditions:
            civ.phase = CivilizationPhase.RECOVERED
        elif CivilizationCondition.TRANSFORMATION in civ.conditions:
            civ.phase = CivilizationPhase.TRANSFORMING
        elif total_pop > 100 and civ.cohesion_index > 0.6 and len(civ.settlement_ids) > 2:
            civ.phase = CivilizationPhase.EXPANDING
        elif total_pop > 40 and civ.phase == CivilizationPhase.EMERGING:
            civ.phase = CivilizationPhase.GROWING
        else:
            civ.phase = CivilizationPhase.CONSOLIDATED

        return civ

    def _compute_emergent_conditions(
        self,
        civ: CivilizationState,
        delta_years: float,
        current_tick: Tick,
    ) -> Set[CivilizationCondition]:
        """Analytically determine all concurrent civilization conditions from observable variables."""
        conditions: Set[CivilizationCondition] = set()
        pop = civ.population_count

        # 1. Population Dynamics
        if pop > 50:
            conditions.add(CivilizationCondition.GROWTH)
        elif pop > 0 and pop < 15:
            conditions.add(CivilizationCondition.DECLINE)

        # 2. Stability vs Cohesion
        if civ.cohesion_index >= 0.65 and pop >= 20:
            conditions.add(CivilizationCondition.STABILITY)
        elif civ.cohesion_index < 0.30:
            conditions.add(CivilizationCondition.FRAGMENTATION)
            if CivilizationCondition.FRAGMENTATION not in civ.conditions:
                self.history.record_ground_truth(
                    category=HistoricalCategory.CONFLICT,
                    tick=current_tick,
                    year=civ.current_year,
                    location=civ.territory_name,
                    actors=[civ.name],
                    title="Fragmentación Social Interna",
                    description="Pérdida crítica de cohesión comunitaria produce fisuras y polarización.",
                    significance=0.8,
                )

        # 3. Territorial Expansion
        if len(civ.settlement_ids) >= 3 and pop > 80:
            conditions.add(CivilizationCondition.EXPANSION)

        # 4. Environmental Stress
        if civ.ecological_stress > 0.60:
            conditions.add(CivilizationCondition.ENVIRONMENTAL_PRESSURE)
            if civ.ecological_stress > 0.85:
                conditions.add(CivilizationCondition.CRISIS)

        # 5. Inequality
        if civ.gini_wealth >= 0.50:
            conditions.add(CivilizationCondition.HIGH_INEQUALITY)

        # 6. Adaptation & Recovery
        if civ.active_crises and civ.cohesion_index > 0.55:
            conditions.add(CivilizationCondition.ADAPTATION)
        elif not civ.active_crises and CivilizationCondition.CRISIS in civ.conditions:
            conditions.add(CivilizationCondition.RECOVERY)

        # 7. Knowledge Evolution
        known_count = len(civ.known_technologies)
        if known_count >= 5:
            conditions.add(CivilizationCondition.KNOWLEDGE_EXPANSION)

        return conditions

    def step_daily(self, current_tick: Tick) -> None:
        """Called daily at midnight (tick_of_day == 0) to synchronize civilization micro-dynamics."""
        for civ in self.civilizations.values():
            if not civ.active:
                continue
            # Synchronize population from active settlements
            civ.population_count = sum(
                self.settlements.settlements[s_id].population_count
                for s_id in civ.settlement_ids
                if s_id in self.settlements.settlements
            )

    def fragment_civilization(
        self,
        civ_id: str,
        new_name: str,
        separating_settlement_ids: List[str],
    ) -> CivilizationState:
        """Splits off settlements into a newly emerged autonomous society."""
        if civ_id not in self.civilizations:
            raise KeyError(f"Civilization {civ_id} not found")
        parent = self.civilizations[civ_id]

        new_civ_id = f"civ_{uuid4().hex[:8]}"
        new_civ = CivilizationState(
            civilization_id=new_civ_id,
            name=new_name,
            phase=CivilizationPhase.FRAGMENTED,
            conditions={CivilizationCondition.FRAGMENTATION},
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
