"""Loan contracts, terms, repayment schedules, and status tracking."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from saltbor.core.types import HumanID, Tick


class LoanType(enum.Enum):
    """Categorization of credit contracts in the economy."""

    INFORMAL_PERSONAL = "informal_personal"  # Interpersonal loan between friends/family
    HOUSEHOLD = "household"                  # Household sustenance or emergency loan
    COMMERCIAL_BUSINESS = "commercial_business" # Working capital or equipment investment
    COOPERATIVE = "cooperative"              # Mutual lending fund credit


class LoanStatus(enum.Enum):
    """Status lifecycle of a credit contract."""

    ACTIVE = "active"          # In good standing, payments being made
    PAID_OFF = "paid_off"      # Fully satisfied with principal and interest
    DEFAULTED = "defaulted"    # Delinquent beyond forgiveness window
    RESTRUCTURED = "restructured" # Renegotiated terms (extended term / lowered interest)


@dataclass
class LoanPayment:
    """Historical record of an installment payment."""

    tick: Tick
    amount: float
    principal_portion: float
    interest_portion: float
    remaining_balance: float


@dataclass
class LoanContract:
    """A formal or informal credit contract governed by double-entry conservation."""

    loan_id: str
    borrower_uid: HumanID
    lender_uid: Optional[HumanID]       # None if lender is an institutional fund / cooperative
    lender_institution_id: Optional[str] = None
    loan_type: LoanType = LoanType.INFORMAL_PERSONAL

    # Principal & Interest
    principal: float = 50.0
    interest_rate: float = 0.05         # 5% total interest over term
    total_due: float = 52.5             # principal * (1.0 + interest_rate)
    balance_remaining: float = 52.5
    collateral_description: Optional[str] = None
    collateral_value: float = 0.0

    # Term & Schedule
    issued_tick: Tick = 0
    term_ticks: int = 192               # e.g. 2 simulated days (192 ticks)
    due_tick: Tick = 192
    installment_frequency_ticks: int = 24 # Installment due every 6 hours
    installment_amount: float = 6.56

    # Status and History
    status: LoanStatus = LoanStatus.ACTIVE
    consecutive_missed_payments: int = 0
    total_missed_payments: int = 0
    max_missed_before_default: int = 4
    payments: list[LoanPayment] = field(default_factory=list)
    renegotiations_count: int = 0

    @property
    def is_settled(self) -> bool:
        return self.status in (LoanStatus.PAID_OFF, LoanStatus.DEFAULTED)

    def record_payment(self, amount: float, current_tick: Tick) -> float:
        """Apply payment toward remaining loan balance. Returns actual amount applied."""
        if amount <= 0.0 or self.balance_remaining <= 0.0:
            return 0.0

        applied = min(amount, self.balance_remaining)
        # Proportionate principal vs interest split
        interest_fraction = self.interest_rate / (1.0 + self.interest_rate) if self.interest_rate > 0 else 0.0
        interest_paid = applied * interest_fraction
        principal_paid = applied - interest_paid

        self.balance_remaining = round(self.balance_remaining - applied, 2)
        if self.balance_remaining <= 0.01:
            self.balance_remaining = 0.0
            self.status = LoanStatus.PAID_OFF

        self.consecutive_missed_payments = 0
        self.payments.append(
            LoanPayment(
                tick=current_tick,
                amount=applied,
                principal_portion=round(principal_paid, 2),
                interest_portion=round(interest_paid, 2),
                remaining_balance=self.balance_remaining,
            )
        )
        return applied

    def register_missed_payment(self, current_tick: Tick) -> bool:
        """Record missed installment. Returns True if loan has transitioned to DEFAULTED."""
        if self.status != LoanStatus.ACTIVE:
            return False

        self.consecutive_missed_payments += 1
        self.total_missed_payments += 1
        if self.consecutive_missed_payments >= self.max_missed_before_default:
            self.status = LoanStatus.DEFAULTED
            return True
        return False

    def restructure(
        self,
        new_interest_rate: float,
        additional_ticks: int,
        current_tick: Tick,
    ) -> None:
        """Renegotiate contract terms to avoid catastrophic liquidation."""
        self.renegotiations_count += 1
        self.interest_rate = new_interest_rate
        # Recalculate remaining balance with adjusted interest
        self.due_tick = current_tick + additional_ticks
        self.consecutive_missed_payments = 0
        self.status = LoanStatus.RESTRUCTURED
