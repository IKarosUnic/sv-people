"""Settlement Evolution Engine for SALTBOR Phase 1.0.

Models dynamic settlements embedded in real or emerging geography:
- Settlement types: caserío, comunidad rural, aldea, barrio, colonia, centro urbano, ciudad, núcleo comercial, zona productiva.
- Dynamic processes: foundation, demographic growth, physical expansion, commercial development, housing, infrastructure, decay, abandonment, relocation, integration.
- Determinants: water, soil, climate, accessibility, roads, employment, trade, housing capacity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SettlementType(str, Enum):
    CASERIO = "caserio"
    COMUNIDAD_RURAL = "comunidad_rural"
    ALDEA = "aldea"
    BARRIO = "barrio"
    COLONIA = "colonia"
    CENTRO_URBANO = "centro_urbano"
    CIUDAD = "ciudad"
    NUCLEO_COMERCIAL = "nucleo_comercial"
    ZONA_PRODUCTIVA = "zona_productiva"


class SettlementStatus(str, Enum):
    EMERGING = "emerging"
    THRIVING = "thriving"
    STAGNANT = "stagnant"
    DECAYING = "decaying"
    ABANDONED = "abandoned"
    INTEGRATED = "integrated"


@dataclass
class SettlementResources:
    water_access: float = 0.7  # 0.0 to 1.0
    soil_fertility: float = 0.6  # 0.0 to 1.0
    road_connectivity: float = 0.5  # 0.0 to 1.0
    housing_capacity: int = 50
    infrastructure_level: float = 0.3  # 0.0 to 1.0
    commercial_intensity: float = 0.2  # 0.0 to 1.0


@dataclass
class Settlement:
    settlement_id: str
    name: str
    settlement_type: SettlementType
    status: SettlementStatus
    municipality: str  # Official or regional administrative anchor
    department: str
    coordinates: tuple[float, float]
    population_count: int = 0
    inhabitant_ids: List[str] = field(default_factory=list)
    households_count: int = 0
    resources: SettlementResources = field(default_factory=SettlementResources)
    economic_specializations: List[str] = field(default_factory=list)
    founded_year: float = 2026.0
    integrated_into: Optional[str] = None


class SettlementEvolutionEngine:
    """Manages territorial settlement growth, decline, specialization, and integration."""

    def __init__(self) -> None:
        self.settlements: Dict[str, Settlement] = {}

    def found_settlement(
        self,
        name: str,
        settlement_type: SettlementType,
        municipality: str,
        department: str,
        coordinates: tuple[float, float],
        initial_inhabitants: Optional[List[str]] = None,
        founded_year: float = 2026.0,
        resources: Optional[SettlementResources] = None,
    ) -> Settlement:
        s_id = f"settle_{uuid4().hex[:8]}"
        inhabitants = initial_inhabitants or []
        settlement = Settlement(
            settlement_id=s_id,
            name=name,
            settlement_type=settlement_type,
            status=SettlementStatus.EMERGING,
            municipality=municipality,
            department=department,
            coordinates=coordinates,
            population_count=len(inhabitants),
            inhabitant_ids=list(inhabitants),
            households_count=max(1, len(inhabitants) // 3) if inhabitants else 0,
            resources=resources or SettlementResources(),
            founded_year=founded_year,
        )
        self.settlements[s_id] = settlement
        return settlement

    def add_inhabitant(self, settlement_id: str, human_id: str) -> bool:
        if settlement_id not in self.settlements:
            return False
        s = self.settlements[settlement_id]
        if human_id not in s.inhabitant_ids:
            s.inhabitant_ids.append(human_id)
            s.population_count = len(s.inhabitant_ids)
            s.households_count = max(1, s.population_count // 3)
            self._update_settlement_scale(s)
            return True
        return False

    def remove_inhabitant(self, settlement_id: str, human_id: str) -> bool:
        if settlement_id not in self.settlements:
            return False
        s = self.settlements[settlement_id]
        if human_id in s.inhabitant_ids:
            s.inhabitant_ids.remove(human_id)
            s.population_count = len(s.inhabitant_ids)
            s.households_count = max(0, s.population_count // 3)
            self._update_settlement_scale(s)
            return True
        return False

    def _update_settlement_scale(self, s: Settlement) -> None:
        """Emergent type and status transition based on population, infrastructure, ecology, and commerce.
        
        Supports non-linear developmental trajectories: growth, stagnation, decay, regression, and abandonment.
        """
        pop = s.population_count
        infra = s.resources.infrastructure_level
        comm = s.resources.commercial_intensity
        water = s.resources.water_access
        soil = s.resources.soil_fertility

        if pop == 0:
            s.status = SettlementStatus.ABANDONED
            return

        is_decaying = (
            water < 0.25
            or soil < 0.20
            or (infra < 0.15 and pop < 20)
        )
        is_stagnant = (
            water <= 0.40
            or (comm < 0.20 and infra < 0.35 and pop < 40)
        )

        if pop < 15:
            s.settlement_type = SettlementType.CASERIO
            if is_decaying:
                s.status = SettlementStatus.DECAYING
            elif is_stagnant:
                s.status = SettlementStatus.STAGNANT
            else:
                s.status = SettlementStatus.THRIVING
        elif pop < 50:
            s.settlement_type = SettlementType.COMUNIDAD_RURAL if soil > 0.5 else SettlementType.ALDEA
            if is_decaying:
                s.status = SettlementStatus.DECAYING
            elif is_stagnant and pop < 25:
                s.status = SettlementStatus.STAGNANT
            else:
                s.status = SettlementStatus.THRIVING
        elif pop < 200:
            if is_decaying:
                s.settlement_type = SettlementType.ALDEA
                s.status = SettlementStatus.DECAYING
            elif comm > 0.6:
                s.settlement_type = SettlementType.NUCLEO_COMERCIAL
                s.status = SettlementStatus.THRIVING
            else:
                s.settlement_type = SettlementType.BARRIO if infra > 0.5 else SettlementType.ALDEA
                s.status = SettlementStatus.THRIVING
        elif pop < 800:
            if is_decaying:
                s.settlement_type = SettlementType.BARRIO
                s.status = SettlementStatus.DECAYING
            else:
                s.settlement_type = SettlementType.CENTRO_URBANO if infra > 0.6 else SettlementType.COLONIA
                s.status = SettlementStatus.THRIVING
        else:
            if is_decaying:
                s.settlement_type = SettlementType.CENTRO_URBANO
                s.status = SettlementStatus.DECAYING
            else:
                s.settlement_type = SettlementType.CIUDAD
                s.status = SettlementStatus.THRIVING

    def develop_infrastructure(self, settlement_id: str, investment: float) -> float:
        if settlement_id not in self.settlements:
            return 0.0
        s = self.settlements[settlement_id]
        delta = investment * 0.1
        s.resources.infrastructure_level = min(1.0, s.resources.infrastructure_level + delta)
        s.resources.housing_capacity += int(investment * 20)
        s.resources.road_connectivity = min(1.0, s.resources.road_connectivity + delta * 0.5)
        self._update_settlement_scale(s)
        return s.resources.infrastructure_level

    def integrate_settlements(self, primary_id: str, secondary_id: str) -> Optional[Settlement]:
        """Integrate smaller settlement into expanding urban/commercial hub."""
        if primary_id not in self.settlements or secondary_id not in self.settlements:
            return None
        primary = self.settlements[primary_id]
        secondary = self.settlements[secondary_id]

        for inh in secondary.inhabitant_ids:
            if inh not in primary.inhabitant_ids:
                primary.inhabitant_ids.append(inh)

        primary.population_count = len(primary.inhabitant_ids)
        primary.households_count += secondary.households_count
        primary.resources.housing_capacity += secondary.resources.housing_capacity
        primary.resources.commercial_intensity = min(1.0, primary.resources.commercial_intensity + secondary.resources.commercial_intensity * 0.3)

        secondary.status = SettlementStatus.INTEGRATED
        secondary.integrated_into = primary_id
        secondary.inhabitant_ids.clear()
        secondary.population_count = 0

        self._update_settlement_scale(primary)
        return primary
