"""Unit and integration tests for Phase 0.6 Commodity Money & Payment-in-Kind."""

import pytest
from saltbor.economy.commodity.money import STANDARD_MAIZE, STANDARD_CACAO
from saltbor.economy.commodity.payment_in_kind import InKindPaymentEngine
from saltbor.economy.credit.engine import CreditEngine
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.population.human import SyntheticHuman


def test_commodity_money_conversions():
    # 1 grain unit = $2.0 currency value
    assert STANDARD_MAIZE.convert_to_currency(10.0) == 20.0
    assert STANDARD_MAIZE.convert_from_currency(20.0) == 10.0


def test_payment_in_kind_loan_installment():
    credit = CreditEngine()
    inkind = InKindPaymentEngine()

    lender = SyntheticHuman.create(name="Lender Antonio", serial=1, age=45.0, seed=1)
    debtor = SyntheticHuman.create(name="Debtor Mateo", serial=2, age=28.0, seed=2)

    lender.physical_state.money = 100.0
    debtor.physical_state.money = 0.0

    # Ensure both humans have inventories
    lender.inventory = Inventory(capacity_volume=100.0)
    debtor.inventory = Inventory(capacity_volume=100.0)

    # Debtor holds 20 units of grain
    debtor.inventory.add(InventoryItem(item_type=ItemType.GRAIN, quantity=20.0, unit=UnitType.BUSHEL))

    loan = credit.issue_interpersonal_loan(
        loan_id="loan_test",
        lender=lender,
        borrower=debtor,
        principal=20.0,
        term_ticks=96,
        current_tick=1,
    )
    assert loan is not None

    # Debtor drains liquidity
    debtor.physical_state.money = 0.0

    # Pay installment in kind (appraised at $2.0 per unit)
    settled = inkind.settle_loan_installment_in_kind(
        loan=loan,
        debtor=debtor,
        lender=lender,
        item_type=ItemType.GRAIN,
        max_quantity_to_offer=10.0,
        unit_valuation=2.0,
        current_tick=24,
    )
    assert settled > 5.0
    assert loan.balance_remaining < 16.0
    assert debtor.inventory.get_quantity(ItemType.GRAIN) < 20.0
    assert lender.inventory.get_quantity(ItemType.GRAIN) > 2.0
