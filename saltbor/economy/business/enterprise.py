"""Business enterprises: ownership, employment, production capacity, operating costs, and solvency."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from saltbor.core.types import HumanID, LocationID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.economy.production.recipe import ProductionRecipe

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class BusinessType(enum.Enum):
    """Sector of commercial or artisanal enterprise."""

    CARPENTRY_WORKSHOP = "carpentry_workshop"
    DINING_COMEDOR = "dining_comedor"
    AGRICULTURAL_FARM = "agricultural_farm"
    MARKET_STALL = "market_stall"
    CONSTRUCTION_MASONRY = "construction_masonry"
    TEXTILE_CLOTHING = "textile_clothing"


class BusinessStatus(enum.Enum):
    """Solvency and operating status of an enterprise."""

    ACTIVE = "active"          # Open, operating profitably or breaking even
    DISTRESSED = "distressed"  # Revenue below operating expenses, running down cash reserves
    INSOLVENT = "insolvent"    # Exhausted liquidity, unable to meet payroll
    CLOSED = "closed"          # Liquidated or dissolved


@dataclass
class FinancialPeriodRecord:
    """Income statement and balance sheet snapshot for an operating period."""

    period_tick: Tick
    revenue: float
    payroll_expenses: float
    material_costs: float
    other_operating_costs: float
    net_profit: float
    closing_cash: float
    inventory_valuation: float


@dataclass
class BusinessEnterprise:
    """A commercial firm with an owner, payroll, physical inventory, and real financial ledger."""

    business_id: str
    name: str
    business_type: BusinessType
    owner_uid: HumanID
    location_id: LocationID

    # Capital, Liquidity, and Inventory
    cash_reserve: float = 150.0
    inventory: Inventory = field(default_factory=lambda: Inventory(capacity_volume=200.0))
    accumulated_debt: float = 0.0

    # Operational Capacity and Employees
    employees: dict[HumanID, float] = field(default_factory=dict)  # worker_uid -> wage_per_day
    max_employees: int = 4
    operating_cost_per_day: float = 10.0  # rent, tool wear, upkeep
    reputation: float = 0.5               # 0.0 to 1.0 (customer trust and quality)
    status: BusinessStatus = BusinessStatus.ACTIVE

    # Retail Catalog & Output Pricing
    retail_prices: dict[ItemType, float] = field(default_factory=dict)
    recipes_supported: list[str] = field(default_factory=list)

    # Historical Accounting
    financial_history: list[FinancialPeriodRecord] = field(default_factory=list)
    total_lifetime_revenue: float = 0.0
    total_lifetime_expenses: float = 0.0

    @property
    def employee_count(self) -> int:
        return len(self.employees)

    def hire_worker(self, worker: SyntheticHuman, daily_wage: float = 15.0) -> bool:
        """Hire a new employee if capacity permits and business is solvent."""
        if self.status in (BusinessStatus.INSOLVENT, BusinessStatus.CLOSED):
            return False
        if len(self.employees) >= self.max_employees:
            return False

        self.employees[worker.uid] = daily_wage
        worker.demographics.occupation = f"Empleado en {self.name}"
        worker.physical_state.work_location_id = self.location_id
        logger.info("Business %s hired %s at $%.2f/day wage.", self.name, worker.name, daily_wage)
        return True

    def dismiss_worker(self, worker_uid: HumanID) -> bool:
        """Lay off an employee to reduce payroll costs."""
        if worker_uid in self.employees:
            del self.employees[worker_uid]
            logger.info("Business %s laid off employee %s.", self.name, worker_uid)
            return True
        return False

    def sell_product(
        self,
        item_type: ItemType,
        quantity: float,
        buyer: SyntheticHuman,
        current_tick: Tick,
    ) -> float:
        """Direct consumer sale from business inventory to buyer."""
        unit_price = self.retail_prices.get(item_type, 5.0)
        total_cost = unit_price * quantity

        if buyer.physical_state.money < total_cost:
            # Insufficient funds: buyer cannot complete transaction
            return 0.0

        available_stock = self.inventory.get_quantity(item_type)
        if available_stock < quantity:
            # Shortage: partial fill or unmet
            return 0.0

        # Transfer goods and currency
        extracted = self.inventory.remove(item_type, quantity)
        if not extracted:
            return 0.0

        buyer.physical_state.money -= total_cost
        self.cash_reserve += total_cost
        self.total_lifetime_revenue += total_cost

        # Buyer receives goods
        buyer_inv = getattr(buyer, "inventory", None)
        if buyer_inv and isinstance(buyer_inv, Inventory):
            buyer_inv.add(extracted)

        return total_cost

    def execute_daily_accounting_cycle(
        self,
        current_tick: Tick,
        population_registry: Any,
    ) -> FinancialPeriodRecord:
        """Execute end-of-day payroll, operating expense deduction, and solvency evaluation."""
        payroll = 0.0
        # Disburse wages directly to employees
        for emp_uid, wage in list(self.employees.items()):
            emp = population_registry.get_optional(emp_uid)
            if emp:
                if self.cash_reserve >= wage:
                    self.cash_reserve -= wage
                    emp.physical_state.money += wage
                    payroll += wage
                else:
                    # Inability to pay wage triggers employee departure
                    logger.warning("Business %s missed wage payment to %s; employee resigns.", self.name, emp.name)
                    del self.employees[emp_uid]

        # Deduct fixed overhead costs
        overhead = self.operating_cost_per_day
        self.cash_reserve -= overhead
        self.total_lifetime_expenses += (payroll + overhead)

        # Evaluate financial status
        if self.cash_reserve < -50.0:
            self.status = BusinessStatus.INSOLVENT
            # Fire remaining staff
            self.employees.clear()
            logger.error("Business %s is INSOLVENT with negative balance $%.2f", self.name, self.cash_reserve)
        elif self.cash_reserve < 20.0:
            self.status = BusinessStatus.DISTRESSED
        else:
            self.status = BusinessStatus.ACTIVE

        # Calculate approximate inventory valuation
        inv_value = sum(
            self.retail_prices.get(item.item_type, 3.0) * item.quantity
            for item in self.inventory._items.values()
        )

        record = FinancialPeriodRecord(
            period_tick=current_tick,
            revenue=round(payroll + overhead + self.cash_reserve, 2),
            payroll_expenses=round(payroll, 2),
            material_costs=0.0,
            other_operating_costs=round(overhead, 2),
            net_profit=round(self.cash_reserve, 2),
            closing_cash=round(self.cash_reserve, 2),
            inventory_valuation=round(inv_value, 2),
        )
        self.financial_history.append(record)
        return record


class BusinessRegistry:
    """Manages active businesses, commercial entries, expansions, and liquidations."""

    def __init__(self) -> None:
        self._businesses: dict[str, BusinessEnterprise] = {}

    def register(self, biz: BusinessEnterprise) -> None:
        self._businesses[biz.business_id] = biz

    def get(self, business_id: str) -> Optional[BusinessEnterprise]:
        return self._businesses.get(business_id)

    def get_by_owner(self, owner_uid: HumanID) -> list[BusinessEnterprise]:
        return [b for b in self._businesses.values() if b.owner_uid == owner_uid]

    def get_all(self) -> list[BusinessEnterprise]:
        return list(self._businesses.values())

    def get_active(self) -> list[BusinessEnterprise]:
        return [b for b in self._businesses.values() if b.status != BusinessStatus.CLOSED]
