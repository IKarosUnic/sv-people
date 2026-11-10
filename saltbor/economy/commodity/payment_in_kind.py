"""Payment-in-Kind (Dación en pago): debt settlement and trade clearance via physical commodities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import Tick
from saltbor.economy.credit.loan import LoanContract, LoanStatus
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


@dataclass
class InKindSettlementRecord:
    """Historical record of an obligation settled using physical goods."""

    settlement_id: str
    payer_uid: str
    receiver_uid: str
    item_type: ItemType
    quantity_transferred: float
    appraised_value_per_unit: float
    total_credit_value: float
    tick: Tick
    obligation_type: str  # "loan_installment", "market_barter", "court_restitution"


class InKindPaymentEngine:
    """Facilitates debt clearance, restitution, and commercial exchange using physical goods."""

    def __init__(self) -> None:
        self.settlement_records: list[InKindSettlementRecord] = []
        self.total_value_settled_in_kind: float = 0.0

    def settle_loan_installment_in_kind(
        self,
        loan: LoanContract,
        debtor: SyntheticHuman,
        lender: SyntheticHuman,
        item_type: ItemType,
        max_quantity_to_offer: float,
        unit_valuation: float,
        current_tick: Tick,
    ) -> float:
        """Settle a loan installment by transferring physical goods instead of scarce cash currency.

        Double-entry conservation:
        - Goods removed from debtor's inventory.
        - Goods added to lender's inventory.
        - Loan principal/installment credited by the appraised goods value.
        - Zero fiat money is created.
        """
        if loan.is_settled or max_quantity_to_offer <= 0.0 or unit_valuation <= 0.0:
            return 0.0

        debtor_inv = getattr(debtor, "inventory", None)
        if not debtor_inv or not isinstance(debtor_inv, Inventory):
            return 0.0

        available_stock = debtor_inv.get_quantity(item_type)
        if available_stock <= 0.0:
            return 0.0

        # Calculate quantity needed to satisfy remaining balance or target installment
        target_due = min(loan.balance_remaining, loan.installment_amount)
        needed_qty = target_due / unit_valuation
        qty_to_transfer = min(available_stock, max_quantity_to_offer, needed_qty)

        # Remove goods from debtor
        transferred_item = debtor_inv.remove(item_type, qty_to_transfer)
        if not transferred_item:
            return 0.0

        # Transfer goods to lender
        lender_inv = getattr(lender, "inventory", None)
        if lender_inv and isinstance(lender_inv, Inventory):
            lender_inv.add(transferred_item)

        credit_val = round(transferred_item.quantity * unit_valuation, 2)
        paid = loan.record_payment(credit_val, current_tick)

        record = InKindSettlementRecord(
            settlement_id=f"inkind_{len(self.settlement_records)+1}",
            payer_uid=str(debtor.uid),
            receiver_uid=str(lender.uid),
            item_type=item_type,
            quantity_transferred=transferred_item.quantity,
            appraised_value_per_unit=unit_valuation,
            total_credit_value=paid,
            tick=current_tick,
            obligation_type="loan_installment",
        )
        self.settlement_records.append(record)
        self.total_value_settled_in_kind += paid

        logger.info(
            "In-kind debt settlement: %s paid %.2f %s ($%.2f credit) to %s on loan %s",
            debtor.name,
            transferred_item.quantity,
            item_type.value,
            paid,
            lender.name,
            loan.loan_id,
        )
        return paid
