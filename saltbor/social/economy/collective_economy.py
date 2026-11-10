"""Collective Economy and Enterprise Engine for Saltbor Phase 0.9.

Models collective business ventures: agricultural cooperatives, family pupuserías,
market vendor collectives, pooled inventories, bulk purchasing, dividend distribution,
and rotating informal credit (cuchubales / fiado).
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.core.types import HumanID, LocationID, Tick

logger = logging.getLogger(__name__)


class CollectiveOrgType(str, enum.Enum):
    """Typology of collective economic organizations."""

    AGRICULTURAL_COOP = "agricultural_coop"     # E.g., Cooperativa Cafetalera / Granos Basicos
    FAMILY_ENTERPRISE = "family_enterprise"     # E.g., Pupuseria Familiar Doña Rosa
    MARKET_ASSOCIATION = "market_association"   # E.g., Asociacion de Vendedoras del Mercado Central
    SAVINGS_CIRCLE = "savings_circle"           # E.g., Cuchubal / Tanda Vecinal
    PRODUCER_GUILD = "producer_guild"           # E.g., Gremio de Panificadores


@dataclasses.dataclass
class EconomicMemberShare:
    """An individual member's capital share and role in the collective enterprise."""

    human_uid: str
    role: str = "member" # "admin", "producer", "vendor", "member"
    equity_ratio: float = 0.20 # Share of profits/dividends
    invested_capital: float = 50.0
    accumulated_dividends: float = 0.0


@dataclasses.dataclass
class CollectiveEnterprise:
    """A persistent collective economic organization."""

    org_id: str
    name: str
    org_type: CollectiveOrgType
    location_id: Optional[str]
    created_tick: int = 0

    # Treasury & Inventories
    treasury_usd: float = 100.0
    shared_inventory: dict[str, float] = dataclasses.field(default_factory=dict) # item_name -> quantity
    total_revenue_earned: float = 0.0

    # Membership & Shares
    members: dict[str, EconomicMemberShare] = dataclasses.field(default_factory=dict)

    # Debts & Obligations
    collective_debt_usd: float = 0.0
    is_active: bool = True

    def deposit_capital(self, member_uid: str, amount_usd: float) -> None:
        """Member injects funds into collective treasury."""
        if member_uid in self.members:
            self.members[member_uid].invested_capital += amount_usd
        self.treasury_usd += amount_usd

    def record_production_output(self, item_name: str, quantity: float, production_cost: float = 0.0) -> None:
        """Add newly produced goods to collective inventory."""
        self.treasury_usd = max(0.0, self.treasury_usd - production_cost)
        self.shared_inventory[item_name] = self.shared_inventory.get(item_name, 0.0) + quantity

    def sell_goods(self, item_name: str, quantity: float, unit_price: float) -> float:
        """Sell goods from pooled stock at negotiated market price."""
        available = self.shared_inventory.get(item_name, 0.0)
        actual_qty = min(available, quantity)
        if actual_qty <= 0.0:
            return 0.0

        revenue = round(actual_qty * unit_price, 2)
        self.shared_inventory[item_name] -= actual_qty
        self.treasury_usd += revenue
        self.total_revenue_earned += revenue
        return revenue

    def distribute_dividends(self, total_dividend_pool: float) -> dict[str, float]:
        """Disburse profits to members proportionally based on equity ratios."""
        if total_dividend_pool > self.treasury_usd:
            total_dividend_pool = self.treasury_usd

        payouts: dict[str, float] = {}
        if not self.members or total_dividend_pool <= 0:
            return payouts

        for uid, share in self.members.items():
            payout = round(total_dividend_pool * share.equity_ratio, 2)
            share.accumulated_dividends += payout
            payouts[uid] = payout

        self.treasury_usd -= sum(payouts.values())
        return payouts


class CollectiveEconomyEngine:
    """Coordinates collective enterprises, bulk purchasing, cooperatives, and credit circles."""

    def __init__(self) -> None:
        self._enterprises: dict[str, CollectiveEnterprise] = {}

    def get_enterprise(self, org_id: str) -> Optional[CollectiveEnterprise]:
        return self._enterprises.get(org_id)

    def get_all_enterprises(self, active_only: bool = True) -> list[CollectiveEnterprise]:
        if not active_only:
            return list(self._enterprises.values())
        return [e for e in self._enterprises.values() if e.is_active]

    def create_enterprise(
        self,
        name: str,
        org_type: CollectiveOrgType,
        founder_uids: list[str | HumanID],
        initial_treasury: float = 100.0,
        location_id: Optional[str] = None,
        tick: int = 0,
    ) -> CollectiveEnterprise:
        """Establish a collective enterprise."""
        org_id = f"ent_{org_type.value[:4]}_{uuid.uuid4().hex[:6]}"
        ent = CollectiveEnterprise(
            org_id=org_id,
            name=name,
            org_type=org_type,
            location_id=location_id,
            created_tick=tick,
            treasury_usd=initial_treasury,
        )

        n = max(1, len(founder_uids))
        equal_equity = round(1.0 / n, 4)
        for i, uid in enumerate(founder_uids):
            role = "admin" if i == 0 else "producer"
            ent.members[str(uid)] = EconomicMemberShare(
                human_uid=str(uid),
                role=role,
                equity_ratio=equal_equity,
                invested_capital=initial_treasury / n,
            )

        self._enterprises[org_id] = ent
        logger.info("Formed collective enterprise '%s' with %d partners", name, len(founder_uids))
        return ent

    def bulk_purchase_supplies(
        self,
        org_id: str,
        item_name: str,
        quantity: float,
        wholesale_unit_cost: float,
    ) -> bool:
        """Purchase production supplies at bulk discount."""
        ent = self.get_enterprise(org_id)
        if not ent:
            return False

        total_cost = round(quantity * wholesale_unit_cost, 2)
        if ent.treasury_usd < total_cost:
            return False

        ent.treasury_usd -= total_cost
        ent.shared_inventory[item_name] = ent.shared_inventory.get(item_name, 0.0) + quantity
        return True

    def dissolve_enterprise(self, org_id: str) -> dict[str, float]:
        """Liquidate enterprise, settle debts, and return remaining capital to members."""
        ent = self.get_enterprise(org_id)
        if not ent or not ent.is_active:
            return {}

        remaining_cash = max(0.0, ent.treasury_usd - ent.collective_debt_usd)
        payouts = ent.distribute_dividends(remaining_cash)
        ent.is_active = False
        return payouts
