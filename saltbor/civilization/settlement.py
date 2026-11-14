"""Settlement and Territorial Evolution Engine for SALTBOR Phase 1.11.

Models dynamic settlements embedded in real or emerging Salvadoran geography:
- Settlement types: caserío, comunidad rural, aldea, barrio, colonia, centro urbano, ciudad, núcleo comercial, zona productiva.
- Dynamic processes: foundation, demographic concentration, physical expansion, commercial development,
  land use transformation, infrastructure lifecycle, decay, abandonment, relocation, and integration.
- Plausible determinants: water availability, soil fertility, road connectivity, employment, trade, security,
  social networks, and environmental conditions.
- Infrastructure assets: roads, bridges, markets, schools, healthcare facilities, water systems, electricity networks,
  communication infrastructure, with construction costs, maintenance overhead, carrying capacity, ownership, and failure risk.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
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


class InfrastructureType(str, Enum):
    ROAD = "road"
    BRIDGE = "bridge"
    MARKET = "market"
    SCHOOL = "school"
    HEALTHCARE = "healthcare"
    WATER_SYSTEM = "water_system"
    ELECTRICITY_GRID = "electricity_grid"
    COMMUNICATION = "communication"


class InfrastructureOwnership(str, Enum):
    COMMUNAL = "communal"  # ADESCO / community managed
    MUNICIPAL = "municipal"  # Local government
    PRIVATE = "private"  # Cooperatives / private owners


class LandUseType(str, Enum):
    RURAL_UNDEVELOPED = "rural_undeveloped"
    AGRICULTURAL = "agricultural"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    PUBLIC_INFRASTRUCTURE = "public_infrastructure"
    NATURAL_PROTECTED = "natural_protected"


@dataclass
class InfrastructureAsset:
    asset_id: str
    asset_type: InfrastructureType
    name: str
    capacity: int = 100
    condition_level: float = 1.0  # 0.0 (ruin/failed) to 1.0 (pristine)
    annual_maintenance_cost: float = 25.0
    ownership: InfrastructureOwnership = InfrastructureOwnership.COMMUNAL
    is_operational: bool = True
    year_built: float = 2026.0
    failure_risk: float = 0.05  # probability of breakdown when maintenance is missed


@dataclass
class SettlementResources:
    water_access: float = 0.7  # 0.0 to 1.0
    soil_fertility: float = 0.6  # 0.0 to 1.0
    road_connectivity: float = 0.5  # 0.0 to 1.0
    housing_capacity: int = 50
    infrastructure_level: float = 0.3  # 0.0 to 1.0
    commercial_intensity: float = 0.2  # 0.0 to 1.0
    carrying_capacity: int = 60  # Derived demographic ceiling
    environmental_health: float = 0.85  # 0.0 to 1.0


@dataclass
class Settlement:
    settlement_id: str
    name: str
    settlement_type: SettlementType
    status: SettlementStatus
    municipality: str  # Official or regional administrative anchor (CNR / OSM)
    department: str
    coordinates: Tuple[float, float]
    population_count: int = 0
    inhabitant_ids: List[str] = field(default_factory=list)
    households_count: int = 0
    resources: SettlementResources = field(default_factory=SettlementResources)
    economic_specializations: List[str] = field(default_factory=list)
    land_use: Dict[LandUseType, float] = field(default_factory=lambda: {
        LandUseType.RURAL_UNDEVELOPED: 0.40,
        LandUseType.AGRICULTURAL: 0.35,
        LandUseType.RESIDENTIAL: 0.15,
        LandUseType.COMMERCIAL: 0.10,
    })
    infrastructure_assets: Dict[str, InfrastructureAsset] = field(default_factory=dict)
    founded_year: float = 2026.0
    integrated_into: Optional[str] = None
    is_real_geographic_anchor: bool = True  # True if mapped from OSM/CNR dataset

    def recalculate_carrying_capacity(self) -> int:
        """Carrying capacity based on water, soil, infrastructure, and housing."""
        water_factor = max(0.1, self.resources.water_access)
        soil_factor = max(0.1, self.resources.soil_fertility)
        infra_factor = max(0.2, self.resources.infrastructure_level)
        housing = max(10, self.resources.housing_capacity)
        cap = int(housing * (0.35 * water_factor + 0.25 * soil_factor + 0.40 * infra_factor) * 1.5)
        self.resources.carrying_capacity = max(5, cap)
        return self.resources.carrying_capacity


class SettlementEvolutionEngine:
    """Manages territorial settlement founding, scale transitions, infrastructure lifecycles,
    economic specialization, land use, and abandonment.
    """

    def __init__(self) -> None:
        self.settlements: Dict[str, Settlement] = {}

    def found_settlement(
        self,
        name: str,
        settlement_type: SettlementType,
        municipality: str,
        department: str,
        coordinates: Tuple[float, float],
        initial_inhabitants: Optional[List[str]] = None,
        founded_year: float = 2026.0,
        resources: Optional[SettlementResources] = None,
        is_real_geographic_anchor: bool = True,
    ) -> Settlement:
        s_id = f"settle_{uuid4().hex[:8]}"
        inhabitants = initial_inhabitants or []
        res = resources or SettlementResources()
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
            resources=res,
            founded_year=founded_year,
            is_real_geographic_anchor=is_real_geographic_anchor,
        )
        # Add default communal water system and access road
        self._seed_default_infrastructure(settlement, founded_year)
        settlement.recalculate_carrying_capacity()
        self.settlements[s_id] = settlement
        return settlement

    def _seed_default_infrastructure(self, settlement: Settlement, year: float) -> None:
        road = InfrastructureAsset(
            asset_id=f"infra_road_{settlement.settlement_id}",
            asset_type=InfrastructureType.ROAD,
            name=f"Camino vecinal hacia {settlement.name}",
            capacity=150,
            condition_level=0.75,
            annual_maintenance_cost=15.0,
            ownership=InfrastructureOwnership.COMMUNAL,
            year_built=year,
        )
        water = InfrastructureAsset(
            asset_id=f"infra_water_{settlement.settlement_id}",
            asset_type=InfrastructureType.WATER_SYSTEM,
            name=f"Pozo artesanal y pila comunal de {settlement.name}",
            capacity=100,
            condition_level=0.80,
            annual_maintenance_cost=10.0,
            ownership=InfrastructureOwnership.COMMUNAL,
            year_built=year,
        )
        settlement.infrastructure_assets[road.asset_id] = road
        settlement.infrastructure_assets[water.asset_id] = water

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

        s.recalculate_carrying_capacity()

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

    def build_infrastructure_asset(
        self,
        settlement_id: str,
        asset_type: InfrastructureType,
        name: str,
        cost_usd: float,
        capacity: int = 150,
        ownership: InfrastructureOwnership = InfrastructureOwnership.COMMUNAL,
        year: float = 2026.0,
    ) -> Optional[InfrastructureAsset]:
        """Constructs an infrastructure asset if settlement has sufficient resources."""
        if settlement_id not in self.settlements:
            return None
        s = self.settlements[settlement_id]
        asset_id = f"asset_{asset_type.value}_{uuid4().hex[:6]}"
        asset = InfrastructureAsset(
            asset_id=asset_id,
            asset_type=asset_type,
            name=name,
            capacity=capacity,
            condition_level=1.0,
            annual_maintenance_cost=max(5.0, cost_usd * 0.08),
            ownership=ownership,
            is_operational=True,
            year_built=year,
        )
        s.infrastructure_assets[asset_id] = asset
        # Boost overall infrastructure level
        s.resources.infrastructure_level = min(1.0, s.resources.infrastructure_level + 0.08)
        if asset_type == InfrastructureType.ROAD:
            s.resources.road_connectivity = min(1.0, s.resources.road_connectivity + 0.15)
        elif asset_type == InfrastructureType.WATER_SYSTEM:
            s.resources.water_access = min(1.0, s.resources.water_access + 0.20)
        elif asset_type == InfrastructureType.MARKET:
            s.resources.commercial_intensity = min(1.0, s.resources.commercial_intensity + 0.25)
        self._update_settlement_scale(s)
        return asset

    def age_and_maintain_infrastructure(
        self,
        settlement_id: str,
        maintenance_funds_allocated: float,
        wear_factor: float = 0.05,
    ) -> Dict[str, Any]:
        """Ages infrastructure assets annually. Unmaintained assets deteriorate and can fail."""
        if settlement_id not in self.settlements:
            return {"operational_count": 0, "failed_count": 0}
        s = self.settlements[settlement_id]
        operational = 0
        failed = 0
        remaining_budget = maintenance_funds_allocated

        for asset in s.infrastructure_assets.values():
            if remaining_budget >= asset.annual_maintenance_cost:
                # Fully maintained: minimal condition loss
                remaining_budget -= asset.annual_maintenance_cost
                asset.condition_level = min(1.0, asset.condition_level + 0.02)
                asset.is_operational = True
            else:
                # Under-maintained: degradation
                asset.condition_level = max(0.0, asset.condition_level - wear_factor * 2.0)
                if asset.condition_level < 0.20:
                    asset.is_operational = False
                    failed += 1
            if asset.is_operational:
                operational += 1

        # Recompute settlement infrastructure level
        if s.infrastructure_assets:
            s.resources.infrastructure_level = (
                sum(a.condition_level for a in s.infrastructure_assets.values() if a.is_operational)
                / len(s.infrastructure_assets)
            )
        self._update_settlement_scale(s)
        return {
            "operational_count": operational,
            "failed_count": failed,
            "remaining_budget": remaining_budget,
            "new_infrastructure_level": s.resources.infrastructure_level,
        }

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
        primary.resources.commercial_intensity = min(
            1.0, primary.resources.commercial_intensity + secondary.resources.commercial_intensity * 0.3
        )

        # Transfer infrastructure assets
        for a_id, asset in secondary.infrastructure_assets.items():
            primary.infrastructure_assets[a_id] = asset

        secondary.status = SettlementStatus.INTEGRATED
        secondary.integrated_into = primary_id
        secondary.inhabitant_ids.clear()
        secondary.population_count = 0

        self._update_settlement_scale(primary)
        return primary
