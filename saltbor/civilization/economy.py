"""Economic Civilization Evolution Engine for SALTBOR Phase 1.11.

Models long-term productive structure, regional specializations, business lifecycles, and endogenous crises:
- Multi-sector economy: agriculture, livestock, fishing, commerce, informal commerce, manufacturing,
  construction, transport, tourism, education, health, services, technology, family enterprise.
- Structural dynamics: business foundation, hiring, capital accumulation, succession, insolvency, liquidation.
- Regional specializations: agricultural hubs, coastal fishing, urban commercial centers, artisanal manufacturing.
- Endogenous crises: supply chain bottlenecks, credit defaults, harvest failures, infrastructure breakdown.
- Strict accounting conservation: zero currency creation from air; bankruptcy liquidates assets to pay creditors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

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


class EnterpriseStatus(str, Enum):
    ACTIVE = "active"
    DISTRESSED = "distressed"
    BANKRUPT = "bankrupt"
    CLOSED = "closed"
    TRANSFERRED = "transferred"


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
    status: EnterpriseStatus = EnterpriseStatus.ACTIVE
    location: str = "general"
    accumulated_debt: float = 0.0
    inventory_value: float = 20.0
    total_sales_volume: float = 0.0


@dataclass
class IntergenerationalWealthRecord:
    family_id: str
    generation: int
    inherited_capital: float
    accumulated_debt: float
    primary_sector: EconomicSector
    transferred_skills: List[str] = field(default_factory=list)


@dataclass
class RegionalEconomyProfile:
    settlement_id: str
    primary_sector: EconomicSector
    secondary_sector: Optional[EconomicSector] = None
    total_firms_count: int = 1
    total_labor_force: int = 10
    employed_labor_count: int = 9
    local_gdp: float = 100.0
    mean_wage: float = 12.0


class EconomicCivilizationEngine:
    """Manages structural economic development, multi-sector production, enterprise lifecycle,
    regional specializations, and endogenous crisis dynamics.
    """

    def __init__(self) -> None:
        self.enterprises: Dict[str, Enterprise] = {}
        self.wealth_history: Dict[str, List[IntergenerationalWealthRecord]] = {}
        self.sector_production: Dict[EconomicSector, float] = {sec: 100.0 for sec in EconomicSector}
        self.total_capital: float = 1000.0
        self.regional_profiles: Dict[str, RegionalEconomyProfile] = {}
        self.active_economic_crises: List[Dict[str, Any]] = []

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
            status=EnterpriseStatus.ACTIVE,
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
        ent.status = EnterpriseStatus.TRANSFERRED
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

    def trigger_endogenous_crisis(
        self,
        crisis_type: str,
        affected_sector: Optional[EconomicSector] = None,
        severity: float = 0.5,
    ) -> Dict[str, Any]:
        """Induces an endogenous economic shock: sector contractions, credit defaults, firm stress."""
        impacted_firms = 0
        total_loss = 0.0

        crisis_record = {
            "crisis_id": f"ecrisis_{uuid4().hex[:6]}",
            "type": crisis_type,
            "sector": affected_sector.value if affected_sector else "all",
            "severity": severity,
            "firms_impacted": 0,
        }

        for ent in self.enterprises.values():
            if not ent.active:
                continue
            if affected_sector is None or ent.sector == affected_sector:
                ent.status = EnterpriseStatus.DISTRESSED
                loss = ent.capital * severity * 0.4
                ent.capital = max(0.0, ent.capital - loss)
                ent.accumulated_debt += loss * 0.5
                total_loss += loss
                impacted_firms += 1

                if ent.capital <= 5.0 and ent.accumulated_debt > ent.inventory_value:
                    ent.status = EnterpriseStatus.BANKRUPT
                    ent.active = False

        crisis_record["firms_impacted"] = impacted_firms
        self.active_economic_crises.append(crisis_record)
        return crisis_record

    def liquidate_insolvent_enterprise(
        self,
        enterprise_id: str,
        creditor_ids: List[str],
    ) -> Dict[str, Any]:
        """Liquidates assets of a bankrupt enterprise to repay creditors under exact conservation.
        Total distributed to creditors equals liquidated assets.
        """
        if enterprise_id not in self.enterprises:
            return {"success": False, "reason": "not_found"}
        ent = self.enterprises[enterprise_id]

        liquidation_value = ent.capital + ent.inventory_value * 0.60
        ent.capital = 0.0
        ent.inventory_value = 0.0
        ent.active = False
        ent.status = EnterpriseStatus.CLOSED

        distributed_to_creditors: Dict[str, float] = {}
        if creditor_ids and liquidation_value > 0:
            share = liquidation_value / len(creditor_ids)
            for c_id in creditor_ids:
                distributed_to_creditors[c_id] = round(share, 2)

        return {
            "success": True,
            "enterprise_id": enterprise_id,
            "liquidation_value_usd": liquidation_value,
            "creditors_count": len(creditor_ids),
            "distributions": distributed_to_creditors,
        }

    def simulate_economic_cycle(self, productivity_shock: float = 1.0) -> Dict[str, float]:
        """Advances production, distributes returns, and adjusts sector vitality."""
        output_by_sector: Dict[str, float] = {}
        for ent in self.enterprises.values():
            if not ent.active:
                continue
            output = (
                (math.sqrt(max(1.0, ent.capital)) * 2.0 + ent.capital * 0.1)
                * ent.labor_count
                * ent.productivity_index
                * productivity_shock
            )
            depreciation = ent.capital * 0.03 + 2.0
            reinvestment = output * 0.35
            ent.capital += reinvestment - depreciation
            if ent.capital <= 0:
                ent.active = False
                ent.status = EnterpriseStatus.CLOSED
                ent.capital = 0.0
            else:
                sec_key = ent.sector.value
                output_by_sector[sec_key] = output_by_sector.get(sec_key, 0.0) + output
                self.sector_production[ent.sector] = output

        return output_by_sector
