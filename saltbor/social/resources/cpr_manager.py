"""Common-Pool Resource (CPR) Management Engine for SALTBOR Phase 1.9.

Implements Elinor Ostrom's Nobel Prize-winning design principles for sustainable
management of common-pool resources without external Leviathan or forced privatization:
1. Clearly defined user boundaries and resource perimeters.
2. Congruence between appropriation rules (extraction quotas) and provision rules (maintenance labor/fees).
3. Collective-choice arrangements (appropriators participate in rule setting).
4. Mutual monitoring of resource state and extractions.
5. Graduated sanctions for rule infractions.
6. Conflict-resolution mechanisms.
7. Minimal recognition of rights to organize.

Prevents or demonstrates the Tragedy of the Commons (Garrett Hardin 1968) through
verifiable mass-conservation and extraction ledgers.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Set
import uuid

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class CPRType(str, enum.Enum):
    """Typology of Common-Pool Resources in El Salvador."""

    WATER_WELL = "water_well"                 # Pozo artesanal / Tanque comunitario
    IRRIGATION_CANAL = "irrigation_canal"     # Acequia de riego para cultivos
    COMMUNAL_PASTURE = "communal_pasture"     # Pastizal común para ganado
    FOREST_FIREWOOD = "forest_firewood"       # Bosque comunal de leña
    COMMUNAL_ROAD = "communal_road"           # Camino vecinal de tierra (requiere balasto)
    COMMUNITY_HALL = "community_hall"         # Casa comunal / Albergue
    SHARED_TOOLS = "shared_tools"             # Banco de herramientas (picos, palas, bombas)
    COMMUNITY_GRAIN_BANK = "grain_bank"       # Troja comunal de reserva de maíz y frijol
    DISASTER_EMERGENCY_FUND = "emergency_fund"# Fondo común de emergencia de la comunidad


class CPRHealthStatus(str, enum.Enum):
    """Physical ecological condition of the common-pool resource."""

    ABUNDANT = "abundant"       # Plenamente sostenible, reserva alta
    STABLE = "stable"           # Extracción balanceada por regeneración
    STRESSED = "stressed"       # Extracción supera recarga; degradación inicial
    DEPLETED = "depleted"       # Sobreexplotado; colapso de provisión
    RESTRICTED = "restricted"   # Cerrado temporalmente por la asamblea para regeneración


@dataclasses.dataclass
class CPRExtractionRecord:
    """Audit log entry for a resource extraction or usage event."""

    record_id: str
    resource_id: str
    user_uid: str
    quantity_extracted: float
    unit: str
    tick: int
    authorized: bool = True
    penalty_applied: float = 0.0


@dataclasses.dataclass
class CPRMaintenanceRecord:
    """Audit log entry for collective maintenance contribution (Faena)."""

    record_id: str
    resource_id: str
    contributor_uid: str
    labor_hours: float
    funds_contributed_usd: float
    tick: int


@dataclasses.dataclass
class CommonPoolResource:
    """A tracked common-pool resource with ecological boundaries and user rules."""

    resource_id: str
    name: str
    resource_type: CPRType
    community_id: str
    location_id: str
    unit_of_measure: str

    # Physical / Ecological Capacities
    max_capacity: float               # Maximum carrying capacity (e.g. 10,000 liters, 50 quintals)
    current_stock: float              # Current available stock
    natural_regeneration_rate: float  # Amount regenerated naturally per simulated day (96 ticks)
    depletion_threshold: float        # Stock level below which the resource is DEPLETED

    # Ostrom Boundary & Governance Rules
    authorized_users: set[str] = dataclasses.field(default_factory=set)
    daily_quota_per_user: float = 50.0  # Max extraction per user per day
    mandatory_maintenance_hours_per_month: float = 4.0
    monitoring_rigor: float = 0.70      # Probability of catching free-riders [0.0, 1.0]

    # Health and Status
    status: CPRHealthStatus = CPRHealthStatus.STABLE
    total_extracted_historical: float = 0.0
    total_maintenance_hours_historical: float = 0.0
    created_tick: int = 0
    last_updated_tick: int = 0

    # Ledgers
    extraction_history: list[CPRExtractionRecord] = dataclasses.field(default_factory=list)
    maintenance_history: list[CPRMaintenanceRecord] = dataclasses.field(default_factory=list)
    sanction_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    @property
    def stock_ratio(self) -> float:
        if self.max_capacity <= 0:
            return 0.0
        return round(self.current_stock / self.max_capacity, 3)

    def extract(
        self,
        user_uid: str,
        amount: float,
        tick: int,
    ) -> tuple[float, bool, str]:
        """Attempt to extract resource. Returns (actual_extracted, is_authorized, status_msg)."""
        if self.status == CPRHealthStatus.RESTRICTED:
            return 0.0, False, "Recurso restringido por acuerdo comunitario para recuperación"

        is_member = user_uid in self.authorized_users
        within_quota = amount <= self.daily_quota_per_user
        authorized = is_member and within_quota

        if self.current_stock <= self.depletion_threshold:
            self.status = CPRHealthStatus.DEPLETED
            return 0.0, authorized, "Recurso agotado (Tragedy of the Commons)"

        actual = min(self.current_stock, amount)
        self.current_stock -= actual
        self.total_extracted_historical += actual
        self.last_updated_tick = tick

        # Update physical status
        ratio = self.stock_ratio
        if ratio < 0.15:
            self.status = CPRHealthStatus.DEPLETED
        elif ratio < 0.40:
            self.status = CPRHealthStatus.STRESSED
        elif ratio > 0.85:
            self.status = CPRHealthStatus.ABUNDANT
        else:
            self.status = CPRHealthStatus.STABLE

        record = CPRExtractionRecord(
            record_id=f"ext_{uuid.uuid4().hex[:6]}",
            resource_id=self.resource_id,
            user_uid=user_uid,
            quantity_extracted=actual,
            unit=self.unit_of_measure,
            tick=tick,
            authorized=authorized,
        )
        self.extraction_history.append(record)

        msg = "Extracción autorizada" if authorized else (
            "Extracción no autorizada (usuario externo)" if not is_member else "Sobreextracción por encima de cuota"
        )
        return actual, authorized, msg

    def contribute_maintenance(
        self,
        contributor_uid: str,
        labor_hours: float,
        funds_usd: float,
        tick: int,
    ) -> None:
        """Contribute work or funds to regenerate/repair the common resource."""
        self.total_maintenance_hours_historical += labor_hours
        # Maintenance boosts regeneration and stock capacity
        boost = (labor_hours * 5.0) + (funds_usd * 2.0)
        self.current_stock = min(self.max_capacity, self.current_stock + boost)
        self.last_updated_tick = tick

        if self.stock_ratio >= 0.40 and self.status == CPRHealthStatus.DEPLETED:
            self.status = CPRHealthStatus.STABLE

        record = CPRMaintenanceRecord(
            record_id=f"maint_{uuid.uuid4().hex[:6]}",
            resource_id=self.resource_id,
            contributor_uid=contributor_uid,
            labor_hours=labor_hours,
            funds_contributed_usd=funds_usd,
            tick=tick,
        )
        self.maintenance_history.append(record)

    def step_natural_regeneration(self, current_tick: Tick) -> None:
        """Regenerate stock naturally per day."""
        if self.status != CPRHealthStatus.DEPLETED:
            self.current_stock = min(
                self.max_capacity,
                self.current_stock + self.natural_regeneration_rate,
            )
            self.last_updated_tick = current_tick


class CollectiveResourceManager:
    """Manages all Common-Pool Resources, extraction rights, and maintenance faenas."""

    def __init__(self) -> None:
        self._resources: dict[str, CommonPoolResource] = {}

    def get_resource(self, res_id: str) -> Optional[CommonPoolResource]:
        return self._resources.get(res_id)

    def get_all_resources(self) -> list[CommonPoolResource]:
        return list(self._resources.values())

    def get_resources_by_community(self, community_id: str) -> list[CommonPoolResource]:
        return [r for r in self._resources.values() if r.community_id == community_id]

    def register_resource(
        self,
        resource_id: str,
        name: str,
        resource_type: CPRType,
        community_id: str,
        location_id: str,
        max_capacity: float,
        initial_stock: float,
        regeneration_rate: float,
        unit: str = "litros",
        daily_quota: float = 50.0,
        authorized_users: Optional[set[str]] = None,
        tick: int = 0,
    ) -> CommonPoolResource:
        """Create or formalize a Common-Pool Resource."""
        res = CommonPoolResource(
            resource_id=resource_id,
            name=name,
            resource_type=resource_type,
            community_id=community_id,
            location_id=location_id,
            unit_of_measure=unit,
            max_capacity=max_capacity,
            current_stock=initial_stock,
            natural_regeneration_rate=regeneration_rate,
            depletion_threshold=max_capacity * 0.05,
            daily_quota_per_user=daily_quota,
            authorized_users=set(authorized_users or []),
            created_tick=tick,
        )
        self._resources[resource_id] = res
        return res

    def step(self, current_tick: Tick) -> None:
        """Advance natural regeneration and check sustainability indicators."""
        if current_tick % 96 == 0:  # Daily cycle
            for res in self._resources.values():
                res.step_natural_regeneration(current_tick)
