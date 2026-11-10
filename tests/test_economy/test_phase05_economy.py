"""Unit and integration tests for Phase 0.5 Advanced Economy (Credit, Business, Mobility)."""

import pytest
from saltbor.economy.credit.loan import LoanContract, LoanType, LoanStatus
from saltbor.economy.credit.engine import CreditEngine
from saltbor.economy.business.enterprise import BusinessEnterprise, BusinessType, BusinessStatus, BusinessRegistry
from saltbor.economy.mobility.inequality import EconomicMobilityEngine
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry


def test_loan_contract_and_repayment():
    engine = CreditEngine()
    lender = SyntheticHuman.create(name="Carlos Lender", serial=1, age=45.0, seed=1)
    borrower = SyntheticHuman.create(name="Mateo Borrower", serial=2, age=28.0, seed=2)

    lender.physical_state.money = 200.0
    borrower.physical_state.money = 10.0

    # Issue interpersonal loan
    loan = engine.issue_interpersonal_loan(
        loan_id="loan_test_1",
        lender=lender,
        borrower=borrower,
        principal=50.0,
        term_ticks=96,
        current_tick=100,
    )
    assert loan is not None
    assert lender.physical_state.money == 150.0
    assert borrower.physical_state.money == 60.0
    assert loan.status == LoanStatus.ACTIVE
    assert loan.balance_remaining > 50.0

    # Make repayment installment
    paid = engine.process_installment_payment(
        loan_id=loan.loan_id,
        borrower=borrower,
        lender=lender,
        institution_treasury=None,
        amount=20.0,
        current_tick=105,
    )
    assert paid == 20.0
    assert borrower.physical_state.money == 40.0
    assert lender.physical_state.money == 170.0

    # Restructure loan
    restruct = engine.renegotiate_debt(loan.loan_id, additional_ticks=48, concession_interest_rate=0.02)
    assert restruct is True
    assert loan.status == LoanStatus.RESTRUCTURED
    assert loan.interest_rate == 0.02


def test_business_enterprise_lifecycle():
    owner = SyntheticHuman.create(name="Rosa Owner", serial=3, age=38.0, seed=3)
    worker = SyntheticHuman.create(name="Diego Worker", serial=4, age=24.0, seed=4)
    customer = SyntheticHuman.create(name="Sofia Buyer", serial=5, age=30.0, seed=5)

    owner.physical_state.money = 100.0
    worker.physical_state.money = 10.0
    customer.physical_state.money = 60.0

    enterprise = BusinessEnterprise(
        business_id="biz_carpentry_1",
        name="Saltbor Woodcraft",
        business_type=BusinessType.CARPENTRY_WORKSHOP,
        owner_uid=owner.uid,
        location_id="taller_artesanal",
        cash_reserve=60.0,
        operating_cost_per_day=5.0,
        retail_prices={ItemType.FURNITURE: 25.0},
    )
    assert enterprise.cash_reserve == 60.0

    # Hire worker
    hired = enterprise.hire_worker(worker, daily_wage=12.0)
    assert hired is True
    assert worker.uid in enterprise.employees

    # Stock inventory
    enterprise.inventory.add(InventoryItem(item_type=ItemType.FURNITURE, quantity=2.0, unit=UnitType.PIECE))

    # Consumer sale
    rev = enterprise.sell_product(ItemType.FURNITURE, quantity=1.0, buyer=customer, current_tick=11)
    assert rev == 25.0
    assert enterprise.inventory.get_quantity(ItemType.FURNITURE) == 1.0
    assert customer.physical_state.money == 35.0
    assert enterprise.cash_reserve == 85.0

    # Daily accounting
    pop = PopulationRegistry()
    pop.register(owner)
    pop.register(worker)
    pop.register(customer)
    rec = enterprise.execute_daily_accounting_cycle(current_tick=96, population_registry=pop)
    assert rec.payroll_expenses == 12.0
    assert worker.physical_state.money == 22.0


def test_economic_mobility_and_inequality_metrics():
    mobility = EconomicMobilityEngine()
    humans = []
    wallets = [10.0, 20.0, 40.0, 80.0, 200.0]
    for i, w in enumerate(wallets):
        h = SyntheticHuman.create(name=f"Person {i}", serial=10 + i, age=30.0, seed=i)
        h.physical_state.money = w
        humans.append(h)

    profiles, snapshot = mobility.evaluate_settlement_wealth(humans, current_tick=50)
    assert snapshot.gini_coefficient > 0.25
    assert snapshot.palma_ratio > 0.5
    assert snapshot.quintile_shares[4] > snapshot.quintile_shares[0]
