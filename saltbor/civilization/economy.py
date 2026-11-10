"""Economic Civilization Evolution Engine for SALTBOR Phase 1.0.

Models long-term productive structure, intergenerational wealth and business mobility:
- Economic sectors: agriculture, cattle, fishing, trade, informal commerce, manufacturing, construction, transport, tourism, education, health, services, tech.
- Dynamics: structural diversification, capital accumulation, business succession/inheritance, intergenerational debt or mobility, productivity shocks.
- Non-linear: recognizes economic regression, structural bottlenecks, informal resilience vs formalization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from saltbor.core.types import Tick


class EconomicSector(str, Enum):
    AGRICULTURE = "agriculture"
    LIVESTOCK = "livestock"
    FISHING = "fishing"
    COMMERCE = "commerce"
    INFORMAL_COMMERCE = "informal_commerce"
    MANUFACTURING = "manufacturing"
    CONSTRUCTION = "construction"
    TRANSPORT = "transport"
    TOURISM = "tourism"
    EDUCATION = "education"
    HEALTH = "health"
    SERVICES = "services"
    TECHNOLOGY = "technology"
    FAMILY_ENTERPRISE = "family_enterprise"


@dataclass
class Enterprise:
    enterprise_id: str
    name: str
    sector: EconomicSector
    founder_id: str
    owner_id: str
    capital: float
    labor_count: int = 1
    productivity_index: float = 1.0  # multiplier
    generation_inherited: int = 0
    active: bool = True
    location: str = "general"


@dataclass
class IntergenerationalWealthRecord:
    family_id: str
    generation: int
    inherited_capital: float
    accumulated_debt: float
    primary_sector: EconomicSector
    transferred_skills: List[str] = field(default_factory=list)


class EconomicCivilizationEngine:
    """Manages structural economic development, multi-sector production, enterprise lifecycle and intergenerational transfers."""

    def __init__(self) -> None:
        self.enterprises: Dict[str, Enterprise] = {}
        self.wealth_history: Dict[str, List[IntergenerationalWealthRecord]] = {}
        self.sector_production: Dict[EconomicSector, float] = {sec: 100.0 for sec in EconomicSector}
        self.total_capital: float = 1000.0

    def establish_enterprise(
        self,
        name: str,
        sector: EconomicSector,
        founder_id: str,
        initial_capital: float,
        location: str = "general",
    ) -> Enterprise:
        ent_id = f"ent_{uuid4().hex[:8]}"
        ent = Enterprise(
            enterprise_id=ent_id,
            name=name,
            sector=sector,
            founder_id=founder_id,
            owner_id=founder_id,
            capital=max(10.0, initial_capital),
            labor_count=1,
            productivity_index=1.0,
            generation_inherited=0,
            active=True,
            location=location,
        )
        self.enterprises[ent_id] = ent
        self.total_capital += ent.capital
        return ent

    def inherit_enterprise(
        self,
        enterprise_id: str,
        heir_id: str,
        transferred_capital_fraction: float = 0.85,
    ) -> Optional[Enterprise]:
        """Transfer enterprise ownership across generations with potential capital dissipation/taxation."""
        if enterprise_id not in self.enterprises:
            return None
        ent = self.enterprises[enterprise_id]
        if not ent.active:
            return None

        ent.owner_id = heir_id
        ent.capital *= max(0.2, min(1.0, transferred_capital_fraction))
        ent.generation_inherited += 1
        # Skill/adaptation might temporarily fluctuate upon inheritance
        ent.productivity_index = max(0.5, ent.productivity_index * 0.95)
        return ent

    def record_intergenerational_wealth(
        self,
        family_id: str,
        generation: int,
        inherited_capital: float,
        accumulated_debt: float,
        primary_sector: EconomicSector,
        skills: Optional[List[str]] = None,
    ) -> IntergenerationalWealthRecord:
        record = IntergenerationalWealthRecord(
            family_id=family_id,
            generation=generation,
            inherited_capital=inherited_capital,
            accumulated_debt=accumulated_debt,
            primary_sector=primary_sector,
            transferred_skills=skills or [],
        )
        self.wealth_history.setdefault(family_id, []).append(record)
        return record

    def simulate_economic_cycle(self, productivity_shock: float = 1.0) -> Dict[str, float]:
        """Advances production, distributes returns, and adjusts sector vitality."""
        output_by_sector: Dict[str, float] = {}
        for ent in self.enterprises.values():
            if not ent.active:
                continue
            # Output depends on capital, labor, productivity and macro shock
            output = math.sqrt(max(1.0, ent.capital)) * ent.labor_count * ent.productivity_index * productivity_shock
            ent.capital += (output * 0.15) - 5.0  # re-investment minus depreciation/living costs
            if ent.capital <= 0:
                ent.active = False
                ent.capital = 0.0
            else:
                output_by_sector[ent.sector.value] = output_by_sector.get(ent.sector.value, 0.0) + output
        return output_by_sector
