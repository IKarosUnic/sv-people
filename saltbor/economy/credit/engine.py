"""Credit and debt management engine with double-entry conservation and risk modeling."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.economy.credit.loan import LoanContract, LoanStatus, LoanType
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class CreditEngine:
    """Manages credit origination, repayments, default enforcement, and debt restructuring.

    Guarantees strict monetary conservation: loans transfer funds directly from
    lender reserves to borrower accounts, and repayments return funds directly
    to lenders.
    """

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.loans: dict[str, LoanContract] = {}
        # Track borrower credit history: human_uid -> {"paid": int, "defaulted": int}
        self.repayment_history: dict[HumanID, dict[str, int]] = {}

    def get_borrower_loans(self, borrower_uid: HumanID) -> list[LoanContract]:
        return [l for l in self.loans.values() if l.borrower_uid == borrower_uid]

    def get_active_debt(self, borrower_uid: HumanID) -> float:
        return sum(
            l.balance_remaining
            for l in self.get_borrower_loans(borrower_uid)
            if l.status in (LoanStatus.ACTIVE, LoanStatus.RESTRUCTURED)
        )

    def evaluate_creditworthiness(
        self,
        borrower: SyntheticHuman,
        requested_amount: float,
        lender_trust: float = 0.5,
        lender_affinity: float = 0.5,
    ) -> tuple[bool, float, str]:
        """Evaluate loan request viability and determine interest rate based on risk.

        Returns (approved: bool, risk_adjusted_interest_rate: float, reason: str).
        """
        active_debt = self.get_active_debt(borrower.uid)
        current_funds = borrower.physical_state.money
        history = self.repayment_history.get(borrower.uid, {"paid": 0, "defaulted": 0})

        # Severe default history blocks credit
        if history["defaulted"] >= 2 and history["paid"] < history["defaulted"] * 2:
            return False, 0.0, "High default risk: borrower has unpaid historical defaults"

        # Over-leverage check: active debt > 3x liquid assets
        if active_debt + requested_amount > max(60.0, current_funds * 3.5):
            return False, 0.0, "Over-leveraged: proposed debt burden exceeds repayment capacity"

        # Base rate
        base_rate = 0.04  # 4%
        # Risk premium based on debt-to-funds ratio
        debt_ratio = active_debt / max(1.0, current_funds)
        risk_premium = min(0.15, debt_ratio * 0.05)

        # Relational discount: high trust reduces rate
        rel_discount = (lender_trust - 0.5) * 0.04 if lender_trust > 0.5 else (0.5 - lender_trust) * 0.06

        final_rate = max(0.01, round(base_rate + risk_premium - rel_discount, 4))
        return True, final_rate, "Credit approved under prudent risk assessment"

    def issue_interpersonal_loan(
        self,
        loan_id: str,
        lender: SyntheticHuman,
        borrower: SyntheticHuman,
        principal: float,
        term_ticks: int = 192,
        current_tick: Tick = 0,
        trust_in_borrower: float = 0.6,
        affinity_for_borrower: float = 0.5,
    ) -> Optional[LoanContract]:
        """Originate an interpersonal loan transferring cash directly between individuals."""
        if principal <= 0.0:
            return None

        # Verify lender solvency
        if lender.physical_state.money < principal:
            logger.info("Lender %s possesses insufficient liquidity ($%.2f < $%.2f)", lender.name, lender.physical_state.money, principal)
            return None

        approved, rate, reason = self.evaluate_creditworthiness(
            borrower, principal, trust_in_borrower, affinity_for_borrower
        )
        if not approved:
            logger.info("Loan declined for %s: %s", borrower.name, reason)
            return None

        # Execute direct cash transfer (double-entry conservation)
        lender.physical_state.money -= principal
        borrower.physical_state.money += principal

        total_due = round(principal * (1.0 + rate), 2)
        installments_count = max(1, term_ticks // 24)
        installment = round(total_due / installments_count, 2)

        loan = LoanContract(
            loan_id=loan_id,
            borrower_uid=borrower.uid,
            lender_uid=lender.uid,
            loan_type=LoanType.INFORMAL_PERSONAL,
            principal=principal,
            interest_rate=rate,
            total_due=total_due,
            balance_remaining=total_due,
            issued_tick=current_tick,
            term_ticks=term_ticks,
            due_tick=current_tick + term_ticks,
            installment_frequency_ticks=24,
            installment_amount=installment,
            status=LoanStatus.ACTIVE,
        )
        self.loans[loan_id] = loan
        logger.info("Loan %s issued: %s lent $%.2f to %s at %.1f%% interest.", loan_id, lender.name, principal, borrower.name, rate * 100)
        return loan

    def issue_institutional_loan(
        self,
        loan_id: str,
        institution_id: str,
        institution_treasury: dict[str, Any],
        borrower: SyntheticHuman,
        principal: float,
        term_ticks: int = 288,
        interest_rate: float = 0.05,
        current_tick: Tick = 0,
    ) -> Optional[LoanContract]:
        """Issue commercial or cooperative credit backed by an institutional treasury."""
        if principal <= 0.0 or institution_treasury.get("money", 0.0) < principal:
            return None

        # Deduct from treasury, credit borrower
        institution_treasury["money"] -= principal
        borrower.physical_state.money += principal

        total_due = round(principal * (1.0 + interest_rate), 2)
        installments_count = max(1, term_ticks // 24)
        installment = round(total_due / installments_count, 2)

        loan = LoanContract(
            loan_id=loan_id,
            borrower_uid=borrower.uid,
            lender_uid=None,
            lender_institution_id=institution_id,
            loan_type=LoanType.COOPERATIVE,
            principal=principal,
            interest_rate=interest_rate,
            total_due=total_due,
            balance_remaining=total_due,
            issued_tick=current_tick,
            term_ticks=term_ticks,
            due_tick=current_tick + term_ticks,
            installment_frequency_ticks=24,
            installment_amount=installment,
            status=LoanStatus.ACTIVE,
        )
        self.loans[loan_id] = loan
        return loan

    def process_installment_payment(
        self,
        loan_id: str,
        borrower: SyntheticHuman,
        lender: Optional[SyntheticHuman],
        institution_treasury: Optional[dict[str, Any]],
        amount: float,
        current_tick: Tick,
    ) -> float:
        """Process an installment payment with double-entry funds conservation."""
        loan = self.loans.get(loan_id)
        if not loan or loan.is_settled:
            return 0.0

        available = min(amount, borrower.physical_state.money)
        if available <= 0.0:
            is_def = loan.register_missed_payment(current_tick)
            if is_def:
                hist = self.repayment_history.setdefault(borrower.uid, {"paid": 0, "defaulted": 0})
                hist["defaulted"] += 1
                logger.warning("Loan %s DEFAULTED by borrower %s", loan_id, borrower.name)
            return 0.0

        paid = loan.record_payment(available, current_tick)
        borrower.physical_state.money = round(borrower.physical_state.money - paid, 2)

        # Credit lender or institution
        if lender is not None:
            lender.physical_state.money = round(lender.physical_state.money + paid, 2)
        elif institution_treasury is not None:
            institution_treasury["money"] = round(institution_treasury.get("money", 0.0) + paid, 2)

        if loan.status == LoanStatus.PAID_OFF:
            hist = self.repayment_history.setdefault(borrower.uid, {"paid": 0, "defaulted": 0})
            hist["paid"] += 1
            logger.info("Loan %s FULLY SATISFIED by %s", loan_id, borrower.name)

        return paid

    def renegotiate_debt(
        self,
        loan_id: str,
        additional_ticks: int = 192,
        concession_interest_rate: float = 0.02,
        current_tick: Tick = 0,
    ) -> bool:
        """Restructure an active delinquent loan to prevent bankruptcy."""
        loan = self.loans.get(loan_id)
        if not loan or loan.status == LoanStatus.PAID_OFF:
            return False

        loan.restructure(concession_interest_rate, additional_ticks, current_tick)
        logger.info("Loan %s successfully restructured with extended due tick %d", loan_id, loan.due_tick)
        return True
