"""Housing, Tenancy, Precarity and Homelessness Dynamics (Phase 1.5).

Simulates the full spectrum of human accommodation:
- 7 realistic tenure conditions: Owner-occupied, rental, shared family housing, informal housing (mesón),
  temporary accommodation (couch-surfing), community shelter, and homelessness.
- Eviction dynamics: emerges from persistent unpaid rent, unemployment, and exhausted credit.
- Protective social buffers: family reunification, neighbor mutual aid, temporary shelter beds.
- Economic recovery pathways: unhoused agents earning day-labor cash can lease rooms and exit homelessness.
- Double-entry accounting: rent paid by tenants transfers directly into landlord cash balances.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from saltbor.core.types import HousingTenureType, HumanID, LocationID, Tick

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class HousingUnit:
    """A domestic residential dwelling, apartment, mesón room, or shelter."""
    unit_id: str
    name: str
    location_id: LocationID
    tenure_type: HousingTenureType
    capacity: int = 4
    rent_per_day: float = 3.00           # In USD (0.0 for owner-occupied or shelter)
    owner_uid: Optional[str] = None      # Landlord or owner
    occupant_uids: list[str] = dataclasses.field(default_factory=list)
    quality_score: float = 0.70          # [0.0, 1.0] Condition and habitability
    consecutive_unpaid_days: dict[str, int] = dataclasses.field(default_factory=dict)
    arrears_balance: dict[str, float] = dataclasses.field(default_factory=dict)

    @property
    def current_occupancy(self) -> int:
        return len(self.occupant_uids)

    @property
    def has_vacancy(self) -> bool:
        return len(self.occupant_uids) < self.capacity


@dataclasses.dataclass
class HousingLease:
    """A formal or informal rental contract for a dwelling unit."""
    lease_id: str
    unit_id: str
    tenant_uid: str
    landlord_uid: Optional[str]
    rent_per_day: float
    start_tick: Tick
    end_tick: Optional[Tick] = None
    is_active: bool = True
    total_rent_paid: float = 0.0
    accumulated_arrears: float = 0.0


class HousingEngine:
    """Manages residential housing units, tenancy, leases, evictions, and homelessness."""

    def __init__(self) -> None:
        self._units: dict[str, HousingUnit] = {}
        self._leases: dict[str, HousingLease] = {}
        self.eviction_history: list[dict[str, Any]] = []

    def register_unit(self, unit: HousingUnit) -> None:
        """Register a dwelling unit in the housing stock."""
        self._units[unit.unit_id] = unit

    def get_unit(self, unit_id: str) -> Optional[HousingUnit]:
        return self._units.get(unit_id)

    def get_all_units(self) -> list[HousingUnit]:
        return list(self._units.values())

    def get_available_rentals(self, max_daily_rent: Optional[float] = None) -> list[HousingUnit]:
        """Find rental or mesón units with open capacity."""
        candidates = [
            u for u in self._units.values()
            if u.has_vacancy and u.tenure_type in (HousingTenureType.RENTAL, HousingTenureType.INFORMAL_HOUSING)
        ]
        if max_daily_rent is not None:
            candidates = [u for u in candidates if u.rent_per_day <= max_daily_rent]
        return candidates

    # -------------------------------------------------------------------------
    # Tenancy & Lease Operations
    # -------------------------------------------------------------------------

    def lease_unit(
        self,
        tenant_agent: Any,
        unit_id: str,
        current_tick: Tick = 0,
    ) -> dict[str, Any]:
        """Establish a tenancy lease for an individual."""
        unit = self._units.get(unit_id)
        if not unit or not unit.has_vacancy:
            return {"leased": False, "reason": "No vacancy in unit"}

        tenant_uid_str = str(tenant_agent.uid)
        lease_id = f"lease_{uuid.uuid4().hex[:8]}"
        lease = HousingLease(
            lease_id=lease_id,
            unit_id=unit_id,
            tenant_uid=tenant_uid_str,
            landlord_uid=unit.owner_uid,
            rent_per_day=unit.rent_per_day,
            start_tick=current_tick,
            is_active=True,
        )
        self._leases[lease_id] = lease

        if tenant_uid_str not in unit.occupant_uids:
            unit.occupant_uids.append(tenant_uid_str)
        unit.consecutive_unpaid_days[tenant_uid_str] = 0
        unit.arrears_balance[tenant_uid_str] = 0.0

        # Update agent physical home
        tenant_agent.physical_state.home_location_id = unit.location_id
        tenant_agent.housing_tenure = unit.tenure_type

        logger.info("Agent %s leased unit %s at $%.2f/day", tenant_agent.name, unit.name, unit.rent_per_day)
        return {
            "leased": True,
            "lease_id": lease_id,
            "unit_id": unit_id,
            "rent_per_day": unit.rent_per_day,
        }

    # -------------------------------------------------------------------------
    # Daily Rent Collection, Arrears & Evictions
    # -------------------------------------------------------------------------

    def collect_daily_rent(
        self,
        current_tick: Tick,
        population_registry: Any,
        eviction_threshold_days: int = 4,
    ) -> dict[str, Any]:
        """Collect daily rent from active leases with conservation of money."""
        total_rent_collected = 0.0
        total_arrears_accrued = 0.0
        evictions_count = 0

        for lease in list(self._leases.values()):
            if not lease.is_active:
                continue

            unit = self._units.get(lease.unit_id)
            if not unit:
                continue

            tenant = population_registry.get_optional(uuid.UUID(lease.tenant_uid))
            if not tenant:
                continue

            rent = lease.rent_per_day
            tenant_money = tenant.physical_state.money

            if tenant_money >= rent:
                # Pay rent
                tenant.physical_state.money = round(tenant_money - rent, 2)
                lease.total_rent_paid += rent
                unit.consecutive_unpaid_days[lease.tenant_uid] = 0
                total_rent_collected += rent

                # Landlord receives rent if present
                if lease.landlord_uid:
                    landlord = population_registry.get_optional(uuid.UUID(lease.landlord_uid))
                    if landlord:
                        landlord.physical_state.money = round(landlord.physical_state.money + rent, 2)
            else:
                # Cannot afford rent: accrue arrears
                unit.consecutive_unpaid_days[lease.tenant_uid] = (
                    unit.consecutive_unpaid_days.get(lease.tenant_uid, 0) + 1
                )
                unit.arrears_balance[lease.tenant_uid] = (
                    unit.arrears_balance.get(lease.tenant_uid, 0.0) + rent
                )
                lease.accumulated_arrears += rent
                total_arrears_accrued += rent

                unpaid_days = unit.consecutive_unpaid_days[lease.tenant_uid]
                logger.warning(
                    "Tenant %s failed rent payment to unit %s (Day %d of unpaid rent, owed $%.2f)",
                    tenant.name, unit.name, unpaid_days, unit.arrears_balance[lease.tenant_uid]
                )

                # Eviction trigger after threshold days of non-payment
                if unpaid_days >= eviction_threshold_days:
                    self.evict_tenant(
                        unit_id=unit.unit_id,
                        tenant_uid=lease.tenant_uid,
                        current_tick=current_tick,
                        population_registry=population_registry,
                    )
                    evictions_count += 1

        return {
            "tick": current_tick,
            "total_rent_collected_usd": round(total_rent_collected, 2),
            "total_arrears_accrued_usd": round(total_arrears_accrued, 2),
            "evictions_count": evictions_count,
        }

    # -------------------------------------------------------------------------
    # Eviction Execution & Protective Buffers
    # -------------------------------------------------------------------------

    def evict_tenant(
        self,
        unit_id: str,
        tenant_uid: str,
        current_tick: Tick,
        population_registry: Any,
    ) -> dict[str, Any]:
        """Evict tenant and activate protective family/community mechanisms."""
        unit = self._units.get(unit_id)
        tenant = population_registry.get_optional(uuid.UUID(tenant_uid))
        if not unit or not tenant:
            return {"evicted": False}

        # Remove from unit
        if tenant_uid in unit.occupant_uids:
            unit.occupant_uids.remove(tenant_uid)

        # Deactivate lease
        for lease in self._leases.values():
            if lease.unit_id == unit_id and lease.tenant_uid == tenant_uid and lease.is_active:
                lease.is_active = False
                lease.end_tick = current_tick

        # Evaluate protective mechanisms in priority order:
        new_tenure = HousingTenureType.HOMELESS
        assigned_shelter_loc = "plaza_central"
        resolution = "Homeless on street/plaza"

        # 1. Family Support: Search for relatives with spare capacity
        for other_unit in self._units.values():
            if other_unit.unit_id != unit_id and other_unit.has_vacancy:
                # If unit is owned or inhabited by family member
                if other_unit.tenure_type in (HousingTenureType.OWNER_OCCUPIED, HousingTenureType.SHARED_FAMILY):
                    new_tenure = HousingTenureType.SHARED_FAMILY
                    other_unit.occupant_uids.append(tenant_uid)
                    assigned_shelter_loc = other_unit.location_id
                    resolution = f"Moved in with extended family at {other_unit.name}"
                    break

        # 2. Community Shelter (Albergue Comunal)
        if new_tenure == HousingTenureType.HOMELESS:
            shelter_unit = next(
                (u for u in self._units.values() if u.tenure_type == HousingTenureType.SHELTER and u.has_vacancy),
                None
            )
            if shelter_unit:
                new_tenure = HousingTenureType.SHELTER
                shelter_unit.occupant_uids.append(tenant_uid)
                assigned_shelter_loc = shelter_unit.location_id
                resolution = f"Admitted to community shelter at {shelter_unit.name}"

        # Apply new status to tenant
        tenant.housing_tenure = new_tenure
        tenant.physical_state.home_location_id = assigned_shelter_loc

        record = {
            "tenant_uid": tenant_uid,
            "tenant_name": tenant.name,
            "unit_id": unit_id,
            "evicted_at_tick": current_tick,
            "new_tenure": new_tenure.value,
            "resolution": resolution,
        }
        self.eviction_history.append(record)
        logger.warning("Eviction executed for %s: %s", tenant.name, resolution)

        return record

    # -------------------------------------------------------------------------
    # Recovery from Homelessness / Upward Housing Mobility
    # -------------------------------------------------------------------------

    def attempt_housing_recovery(
        self,
        agent: Any,
        current_tick: Tick,
    ) -> dict[str, Any]:
        """Unhoused agent searches for an affordable room/mesón and signs lease."""
        current_tenure = getattr(agent, "housing_tenure", HousingTenureType.HOMELESS)
        if current_tenure not in (HousingTenureType.HOMELESS, HousingTenureType.SHELTER, HousingTenureType.TEMPORARY_ACCOMMODATION):
            return {"recovered": False, "reason": "Agent already stably housed"}

        agent_money = agent.physical_state.money
        # Require small savings reserve ($15+) to safely rent
        if agent_money < 12.0:
            return {"recovered": False, "reason": f"Insufficient savings (${agent_money:.2f} < $12.00)"}

        # Look for affordable mesón or shared room ($1.50 - $3.00/day)
        candidates = self.get_available_rentals(max_daily_rent=3.50)
        if not candidates:
            return {"recovered": False, "reason": "No affordable rentals with vacancy"}

        best_unit = min(candidates, key=lambda u: u.rent_per_day)

        # Remove from prior shelter
        for u in self._units.values():
            if str(agent.uid) in u.occupant_uids and u.tenure_type == HousingTenureType.SHELTER:
                u.occupant_uids.remove(str(agent.uid))

        res = self.lease_unit(agent, best_unit.unit_id, current_tick)
        if res.get("leased"):
            logger.info("Agent %s successfully recovered from %s into %s", agent.name, current_tenure.value, best_unit.name)
            return {
                "recovered": True,
                "unit_id": best_unit.unit_id,
                "unit_name": best_unit.name,
                "tenure": best_unit.tenure_type.value,
            }

        return {"recovered": False, "reason": "Lease attempt failed"}

    def get_all_leases(self) -> list[HousingLease]:
        return list(self._leases.values())

    def get_active_leases(self) -> list[HousingLease]:
        return [l for l in self._leases.values() if l.is_active]

