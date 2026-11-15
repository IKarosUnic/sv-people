"""Verifiable Economic Ledger for SALTBOR Generalized Territorial Scenarios.

Enforces absolute accounting conservation via double-entry bookkeeping:
- Every economic event creates balanced debit and credit entries: sum(debit) == sum(credit).
- Strict separation of:
    1. Liquid Cash (USD currency)
    2. Physical Goods / Inventory (maize, beans, medicines, etc.)
    3. Informal Credit / Fiado (receivables & payables)
    4. Capital / Equity & Operational Expenses / Revenues
- Zero money created out of thin air:
    * Total circulating currency is strictly conserved across all agents and firms.
    * Exogenous injections (e.g. municipal emergency disaster grants or external remittances)
      must be explicitly recorded with verified concept and entity provenance.
- Complete audit trail with transaction hash / ID, tick, domain, and entity identifiers.
"""

from __future__ import annotations

import collections
import dataclasses
import enum
from typing import Any, Dict, List, Optional, Set, Tuple


class AccountType(str, enum.Enum):
    """Standard accounting classifications."""
    ASSET_CASH = "ASSET_CASH"                      # Liquid USD currency
    ASSET_INVENTORY = "ASSET_INVENTORY"            # Physical commodities valued at cost
    ASSET_RECEIVABLE = "ASSET_RECEIVABLE"          # Fiado or commercial credit owed to entity
    LIABILITY_PAYABLE = "LIABILITY_PAYABLE"        # Fiado or debt owed to another entity
    EQUITY = "EQUITY"                              # Net worth / owner's capital
    REVENUE = "REVENUE"                            # Income earned from sales or wages
    EXPENSE = "EXPENSE"                            # Costs incurred for consumption or operations


class TransactionConcept(str, enum.Enum):
    """Categorized economic exchange concepts."""
    INITIAL_CAPITAL = "INITIAL_CAPITAL"
    WAGE_PAYMENT = "WAGE_PAYMENT"
    FOOD_PURCHASE_CASH = "FOOD_PURCHASE_CASH"
    FOOD_PURCHASE_FIADO = "FOOD_PURCHASE_FIADO"
    FIADO_REPAYMENT = "FIADO_REPAYMENT"
    WHOLESALE_PURCHASE = "WHOLESALE_PURCHASE"
    FREIGHT_TRANSPORT_PAYMENT = "FREIGHT_TRANSPORT_PAYMENT"
    OUT_OF_POCKET_MEDICAL = "OUT_OF_POCKET_MEDICAL"
    BUSINESS_OVERHEAD = "BUSINESS_OVERHEAD"
    MUNICIPAL_EMERGENCY_GRANT = "MUNICIPAL_EMERGENCY_GRANT"
    MUNICIPAL_INFRASTRUCTURE_WAGE = "MUNICIPAL_INFRASTRUCTURE_WAGE"
    EXTERNAL_REMITTANCE = "EXTERNAL_REMITTANCE"


@dataclasses.dataclass
class TransactionEntry:
    """A single leg of a double-entry transaction."""
    account_id: str
    entity_id: str
    account_type: AccountType
    debit: float   # Increase in Assets/Expenses, or decrease in Liabilities/Equity/Revenue
    credit: float  # Increase in Liabilities/Equity/Revenue, or decrease in Assets/Expenses


@dataclasses.dataclass
class EconomicTransaction:
    """An immutable, balanced double-entry transaction record."""
    tx_id: str
    tick: int
    concept: TransactionConcept
    originating_domain: str
    description: str
    entries: List[TransactionEntry]
    physical_units: Dict[str, float] = dataclasses.field(default_factory=dict)  # e.g. {"maize_lb": 10.0}

    @property
    def total_debit(self) -> float:
        return round(sum(e.debit for e in self.entries), 4)

    @property
    def total_credit(self) -> float:
        return round(sum(e.credit for e in self.entries), 4)

    @property
    def is_balanced(self) -> bool:
        return abs(self.total_debit - self.total_credit) < 1e-4


class VerifiableEconomicLedger:
    """Maintains double-entry journal, entity balances, and absolute conservation auditing."""

    def __init__(self) -> None:
        self.transactions: List[EconomicTransaction] = []
        # entity_id -> account_type -> balance
        self._entity_balances: Dict[str, Dict[AccountType, float]] = collections.defaultdict(
            lambda: collections.defaultdict(float)
        )
        self.initial_currency_pool: float = 0.0
        self.exogenous_currency_inflows: float = 0.0

    def record_transaction(
        self,
        concept: TransactionConcept,
        originating_domain: str,
        description: str,
        entries: List[TransactionEntry],
        tick: int,
        physical_units: Optional[Dict[str, float]] = None,
    ) -> EconomicTransaction:
        """Validate double-entry balance and append transaction to the immutable ledger."""
        tx_id = f"tx_eco_{len(self.transactions) + 1:07d}"
        tx = EconomicTransaction(
            tx_id=tx_id,
            tick=tick,
            concept=concept,
            originating_domain=originating_domain,
            description=description,
            entries=entries,
            physical_units=physical_units or {},
        )

        if not tx.is_balanced:
            raise ValueError(
                f"Double-entry accounting violation in tx '{tx_id}': total debit ${tx.total_debit:.4f} != total credit ${tx.total_credit:.4f}"
            )

        # Update entity ledger balances
        for entry in entries:
            # Asset & Expense increase with debit, decrease with credit
            if entry.account_type in (AccountType.ASSET_CASH, AccountType.ASSET_INVENTORY, AccountType.ASSET_RECEIVABLE, AccountType.EXPENSE):
                delta = entry.debit - entry.credit
            else:
                # Liability, Equity & Revenue increase with credit, decrease with debit
                delta = entry.credit - entry.debit
            self._entity_balances[entry.entity_id][entry.account_type] += delta

        if concept in (TransactionConcept.MUNICIPAL_EMERGENCY_GRANT, TransactionConcept.EXTERNAL_REMITTANCE):
            # Track explicit permitted exogenous inflows
            inflow = sum(e.debit for e in entries if e.account_type == AccountType.ASSET_CASH and e.entity_id != "treasury_municipal")
            self.exogenous_currency_inflows += inflow

        self.transactions.append(tx)
        return tx

    def get_entity_balance(self, entity_id: str, account_type: AccountType) -> float:
        """Return the current balance for an entity's specific account."""
        return round(self._entity_balances[entity_id].get(account_type, 0.0), 2)

    def get_total_circulating_currency(self, exclude_entities: Optional[Set[str]] = None) -> float:
        """Sum total ASSET_CASH held by all entities in the economy."""
        exclude = exclude_entities or set()
        total = 0.0
        for ent_id, accts in self._entity_balances.items():
            if ent_id not in exclude:
                cash = accts.get(AccountType.ASSET_CASH, 0.0)
                if cash > 0:
                    total += cash
        return round(total, 2)

    def verify_accounting_conservation(self) -> Tuple[bool, str, Dict[str, float]]:
        """Verify absolute conservation of monetary currency across the economic ledger."""
        total_cash = 0.0
        total_receivables = 0.0
        total_payables = 0.0

        for ent_id, accts in self._entity_balances.items():
            total_cash += accts.get(AccountType.ASSET_CASH, 0.0)
            total_receivables += accts.get(AccountType.ASSET_RECEIVABLE, 0.0)
            total_payables += accts.get(AccountType.LIABILITY_PAYABLE, 0.0)

        # Informally: all Fiado receivables must equal all Fiado payables!
        credit_market_balanced = abs(total_receivables - total_payables) < 1e-3

        # Currency conservation: Current cash must equal initial currency + logged inflows
        expected_cash = self.initial_currency_pool + self.exogenous_currency_inflows
        cash_conserved = abs(total_cash - expected_cash) < 1e-2

        is_valid = credit_market_balanced and cash_conserved

        message = (
            f"Conservation Verified: Cash total=${total_cash:.2f} (expected=${expected_cash:.2f}), "
            f"Receivables=${total_receivables:.2f}, Payables=${total_payables:.2f}"
            if is_valid
            else f"CONSERVATION VIOLATION: Cash total=${total_cash:.2f} != expected=${expected_cash:.2f} "
                 f"or Receivables=${total_receivables:.2f} != Payables=${total_payables:.2f}"
        )

        metrics = {
            "total_cash": round(total_cash, 2),
            "expected_cash": round(expected_cash, 2),
            "total_receivables": round(total_receivables, 2),
            "total_payables": round(total_payables, 2),
            "credit_market_diff": round(abs(total_receivables - total_payables), 4),
            "cash_conservation_diff": round(abs(total_cash - expected_cash), 4),
        }
        return is_valid, message, metrics

    # =========================================================================
    # High-level Economic Actions with Guaranteed Double-Entry Balance
    # =========================================================================

    def record_wage_payment(
        self,
        employer_id: str,
        worker_id: str,
        amount_usd: float,
        tick: int,
        concept: TransactionConcept = TransactionConcept.WAGE_PAYMENT,
        description: str = "Agricultural day labor wage",
    ) -> EconomicTransaction:
        """Worker earns wage paid by employer."""
        entries = [
            TransactionEntry(f"{employer_id}_cash", employer_id, AccountType.ASSET_CASH, debit=0.0, credit=amount_usd),
            TransactionEntry(f"{employer_id}_wage_expense", employer_id, AccountType.EXPENSE, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{worker_id}_cash", worker_id, AccountType.ASSET_CASH, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{worker_id}_wage_revenue", worker_id, AccountType.REVENUE, debit=0.0, credit=amount_usd),
        ]
        return self.record_transaction(
            concept=concept,
            originating_domain="economy",
            description=description,
            entries=entries,
            tick=tick,
        )

    def record_retail_food_purchase_cash(
        self,
        buyer_id: str,
        tiendita_id: str,
        amount_usd: float,
        cost_of_goods_usd: float,
        commodity: str,
        quantity_lb: float,
        tick: int,
    ) -> EconomicTransaction:
        """Buyer (individual or household) buys food from tiendita with cash."""
        entries = [
            # Buyer leg
            TransactionEntry(f"{buyer_id}_cash", buyer_id, AccountType.ASSET_CASH, debit=0.0, credit=amount_usd),
            TransactionEntry(f"{buyer_id}_food_expense", buyer_id, AccountType.EXPENSE, debit=amount_usd, credit=0.0),
            # Tiendita revenue leg
            TransactionEntry(f"{tiendita_id}_cash", tiendita_id, AccountType.ASSET_CASH, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{tiendita_id}_sales_revenue", tiendita_id, AccountType.REVENUE, debit=0.0, credit=amount_usd),
            # Tiendita inventory cost leg
            TransactionEntry(f"{tiendita_id}_cogs", tiendita_id, AccountType.EXPENSE, debit=cost_of_goods_usd, credit=0.0),
            TransactionEntry(f"{tiendita_id}_inventory", tiendita_id, AccountType.ASSET_INVENTORY, debit=0.0, credit=cost_of_goods_usd),
        ]
        return self.record_transaction(
            concept=TransactionConcept.FOOD_PURCHASE_CASH,
            originating_domain="commerce",
            description=f"Purchase of {quantity_lb} lb {commodity} with cash",
            entries=entries,
            tick=tick,
            physical_units={commodity: quantity_lb},
        )

    def record_retail_food_purchase_fiado(
        self,
        buyer_id: str,
        tiendita_id: str,
        amount_usd: float,
        cost_of_goods_usd: float,
        commodity: str,
        quantity_lb: float,
        tick: int,
    ) -> EconomicTransaction:
        """Buyer (individual or household) takes food on informal credit (fiado) from tiendita.

        NOTE: Tiendita liquid cash does NOT decrease!
        Inventory decreases at cost, tiendita records a Fiado Receivable,
        and buyer records a Fiado Payable (liability).
        """
        entries = [
            # Buyer incurs food expense and records liability (payable)
            TransactionEntry(f"{buyer_id}_food_expense", buyer_id, AccountType.EXPENSE, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{buyer_id}_fiado_payable", buyer_id, AccountType.LIABILITY_PAYABLE, debit=0.0, credit=amount_usd),
            # Tiendita records fiado asset receivable and sales revenue
            TransactionEntry(f"{tiendita_id}_fiado_receivable", tiendita_id, AccountType.ASSET_RECEIVABLE, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{tiendita_id}_sales_revenue", tiendita_id, AccountType.REVENUE, debit=0.0, credit=amount_usd),
            # Tiendita inventory decreases
            TransactionEntry(f"{tiendita_id}_cogs", tiendita_id, AccountType.EXPENSE, debit=cost_of_goods_usd, credit=0.0),
            TransactionEntry(f"{tiendita_id}_inventory", tiendita_id, AccountType.ASSET_INVENTORY, debit=0.0, credit=cost_of_goods_usd),
        ]
        return self.record_transaction(
            concept=TransactionConcept.FOOD_PURCHASE_FIADO,
            originating_domain="commerce",
            description=f"Informal fiado credit purchase of {quantity_lb} lb {commodity}",
            entries=entries,
            tick=tick,
            physical_units={commodity: quantity_lb},
        )

    def record_fiado_repayment(
        self,
        debtor_id: str,
        creditor_id: str,
        amount_usd: float,
        tick: int,
    ) -> EconomicTransaction:
        """Debtor repays fiado balance to tiendita in cash."""
        entries = [
            # Debtor cash decreases, liability decreases
            TransactionEntry(f"{debtor_id}_cash", debtor_id, AccountType.ASSET_CASH, debit=0.0, credit=amount_usd),
            TransactionEntry(f"{debtor_id}_fiado_payable", debtor_id, AccountType.LIABILITY_PAYABLE, debit=amount_usd, credit=0.0),
            # Creditor cash increases, receivable asset decreases
            TransactionEntry(f"{creditor_id}_cash", creditor_id, AccountType.ASSET_CASH, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{creditor_id}_fiado_receivable", creditor_id, AccountType.ASSET_RECEIVABLE, debit=0.0, credit=amount_usd),
        ]
        return self.record_transaction(
            concept=TransactionConcept.FIADO_REPAYMENT,
            originating_domain="commerce",
            description="Repayment of informal fiado debt",
            entries=entries,
            tick=tick,
        )

    def record_out_of_pocket_medical(
        self,
        buyer_id: str,
        pharmacy_id: str,
        amount_usd: float,
        tick: int,
        description: str = "Out-of-pocket chronic hypertension medication",
    ) -> EconomicTransaction:
        """Individual or household pays pharmacy for emergency medicines."""
        entries = [
            TransactionEntry(f"{buyer_id}_cash", buyer_id, AccountType.ASSET_CASH, debit=0.0, credit=amount_usd),
            TransactionEntry(f"{buyer_id}_medical_expense", buyer_id, AccountType.EXPENSE, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{pharmacy_id}_cash", pharmacy_id, AccountType.ASSET_CASH, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{pharmacy_id}_pharmacy_revenue", pharmacy_id, AccountType.REVENUE, debit=0.0, credit=amount_usd),
        ]
        return self.record_transaction(
            concept=TransactionConcept.OUT_OF_POCKET_MEDICAL,
            originating_domain="healthcare",
            description=description,
            entries=entries,
            tick=tick,
        )

    def record_wholesale_replenishment(
        self,
        retailer_id: str,
        wholesaler_id: str,
        transporter_id: str,
        goods_cost_usd: float,
        freight_fee_usd: float,
        commodity: str,
        quantity_lb: float,
        tick: int,
    ) -> EconomicTransaction:
        """Retailer purchases inventory from regional wholesaler and pays transporter."""
        total_payment = goods_cost_usd + freight_fee_usd
        entries = [
            # Retailer pays total cash, acquires inventory asset at total delivered cost
            TransactionEntry(f"{retailer_id}_cash", retailer_id, AccountType.ASSET_CASH, debit=0.0, credit=total_payment),
            TransactionEntry(f"{retailer_id}_inventory", retailer_id, AccountType.ASSET_INVENTORY, debit=total_payment, credit=0.0),
            # Wholesaler receives goods cash and records wholesale revenue
            TransactionEntry(f"{wholesaler_id}_cash", wholesaler_id, AccountType.ASSET_CASH, debit=goods_cost_usd, credit=0.0),
            TransactionEntry(f"{wholesaler_id}_revenue", wholesaler_id, AccountType.REVENUE, debit=0.0, credit=goods_cost_usd),
            # Transporter receives freight fee and records transport revenue
            TransactionEntry(f"{transporter_id}_cash", transporter_id, AccountType.ASSET_CASH, debit=freight_fee_usd, credit=0.0),
            TransactionEntry(f"{transporter_id}_freight_revenue", transporter_id, AccountType.REVENUE, debit=0.0, credit=freight_fee_usd),
        ]
        return self.record_transaction(
            concept=TransactionConcept.WHOLESALE_PURCHASE,
            originating_domain="commerce",
            description=f"Wholesale replenishment: {quantity_lb} lb {commodity} + freight",
            entries=entries,
            tick=tick,
            physical_units={commodity: quantity_lb},
        )

    def record_municipal_grant_or_workfare(
        self,
        beneficiary_id: str,
        treasury_id: str,
        amount_usd: float,
        tick: int,
        is_workfare: bool = True,
        description: str = "Municipal road rehabilitation workfare stipend",
    ) -> EconomicTransaction:
        """Government / Municipal program pays emergency stipend or workfare wage."""
        concept = (
            TransactionConcept.MUNICIPAL_INFRASTRUCTURE_WAGE
            if is_workfare
            else TransactionConcept.MUNICIPAL_EMERGENCY_GRANT
        )
        entries = [
            TransactionEntry(f"{treasury_id}_cash", treasury_id, AccountType.ASSET_CASH, debit=0.0, credit=amount_usd),
            TransactionEntry(f"{treasury_id}_public_expense", treasury_id, AccountType.EXPENSE, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{beneficiary_id}_cash", beneficiary_id, AccountType.ASSET_CASH, debit=amount_usd, credit=0.0),
            TransactionEntry(f"{beneficiary_id}_grant_revenue", beneficiary_id, AccountType.REVENUE, debit=0.0, credit=amount_usd),
        ]
        return self.record_transaction(
            concept=concept,
            originating_domain="governance",
            description=description,
            entries=entries,
            tick=tick,
        )
