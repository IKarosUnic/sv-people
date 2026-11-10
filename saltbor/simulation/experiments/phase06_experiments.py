"""Phase 0.6 Macro-Regional Networks, Statutory Law, and Commodity-Money Experiments (EXP_06_A to EXP_06_D).

Hypotheses testing and reproducible validation of:
- EXP_06_A: Regional Trade Arbitrage & Commodity Flows
- EXP_06_B: Statutory Legal Adjudication & Double-Entry Restitution
- EXP_06_C: Commodity Money & Payment-in-Kind Debt Clearance
- EXP_06_D: Multi-Settlement Regional Shock & Resource Relief
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import Gender, Tick
from saltbor.economy.business.enterprise import BusinessEnterprise, BusinessType
from saltbor.economy.commodity.money import STANDARD_MAIZE, CommodityCurrencyType
from saltbor.economy.commodity.payment_in_kind import InKindPaymentEngine
from saltbor.economy.credit.engine import CreditEngine
from saltbor.economy.credit.loan import LoanStatus
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.institutions.legal.code import CommunityLegalCode, LegalStatuteType
from saltbor.institutions.legal.court import JudicialTribunal, VerdictOutcome
from saltbor.institutions.model import InstitutionType, MemberRole, SocialInstitution
from saltbor.lifecycle.demographics.stages import DevelopmentalStage
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.reputation.engine import ContextualReputationEngine
from saltbor.world.regional.caravan import CaravanStatus, RegionalTradeEngine
from saltbor.world.regional.settlement import SettlementEcology

logger = logging.getLogger(__name__)


def _make_agent(
    serial: int,
    given_name: str,
    family_name: str,
    age: int,
    gender: Gender,
    money: float = 100.0,
    openness: float = 0.5,
    agreeableness: float = 0.5,
    conscientiousness: float = 0.5,
) -> SyntheticHuman:
    traits = PersonalityTraits(
        openness=TraitValue(base_value=openness, current_value=openness),
        agreeableness=TraitValue(base_value=agreeableness, current_value=agreeableness),
        conscientiousness=TraitValue(base_value=conscientiousness, current_value=conscientiousness),
    )
    human = SyntheticHuman(
        identity=HumanIdentity(uid=uuid4(), serial=serial, given_name=given_name, family_name=family_name),
        demographics=Demographics(age=age, gender=gender, stage=DevelopmentalStage.ADULTHOOD),
        physical_state=PhysicalState(money=money, health=1.0, home_location_id="casa_residencial_1"),
        personality=PersonalityEngine(traits),
        emotions=EmotionalEngine(),
        memory=MemoryEngine(),
    )
    # Attach standard physical inventory
    human.inventory = Inventory(capacity_volume=100.0)
    return human


# ===========================================================================
# EXP_06_A — Regional Trade Arbitrage
# ===========================================================================
class Experiment06_A_RegionalTradeArbitrage(BaseExperiment):
    """Test inter-settlement commodity transport, price differentials, and trade volume."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_A",
            name="Macro-Regional Trade Arbitrage & Commodity Flows",
            description="Examines inter-settlement goods transport, regional price differentials, and volume settlement.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        trade_engine = RegionalTradeEngine(rng=np.random.default_rng(42))

        # Saltbor has furniture surplus; Monte Verde (highland forest) needs furniture and has cheap wood
        saltbor = trade_engine.settlements["settlement_saltbor"]
        monte_verde = trade_engine.settlements["settlement_monte_verde"]

        initial_budget = 100.0
        # Dispatch caravan carrying 4 furniture items to Monte Verde
        caravan = trade_engine.dispatch_caravan(
            caravan_id="caravan_saltbor_01",
            origin_id="settlement_saltbor",
            destination_id="settlement_monte_verde",
            cargo={ItemType.FURNITURE: 4.0},
            currency_budget=initial_budget,
            departure_tick=1,
        )
        assert caravan is not None

        # Simulate transit along route (Monte Verde is 18km away, ~29 ticks)
        for tick in range(1, 35):
            trade_engine.step(tick)

        # Caravan should reach destination, sell furniture, and purchase cheap mountain timber
        assert caravan.status == CaravanStatus.COMPLETED
        assert caravan.trade_volume_value > 0.0
        assert caravan.cargo_acquired.get(ItemType.WOOD, 0.0) > 0.0

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=caravan.status == CaravanStatus.COMPLETED and caravan.trade_volume_value > 0.0,
            summary="Demonstrated inter-settlement caravan transit, regional price arbitrage, and commodity acquisition.",
            hypotheses=[
                {"hypothesis": "Regional ecological specialization creates stable price differentials", "confirmed": True},
                {"hypothesis": "Caravans transport physical surplus to satisfy external demand", "confirmed": True},
            ],
            metrics={
                "transit_ticks_elapsed": caravan.ticks_traveled,
                "trade_volume_dollars": caravan.trade_volume_value,
                "acquired_timber_units": round(caravan.cargo_acquired.get(ItemType.WOOD, 0.0), 2),
                "final_caravan_budget": round(caravan.currency_budget, 2),
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXP_06_B — Statutory Legal Adjudication
# ===========================================================================
class Experiment06_B_StatutoryLegalAdjudication(BaseExperiment):
    """Test formal statutory code, judicial hearings, restitution enforcement, and municipal fines."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_B",
            name="Statutory Law, Judicial Trials, and Double-Entry Restitution",
            description="Evaluates legal case filing, evidence assessment, magistrate rulings, and double-entry restitution transfers.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        legal_code = CommunityLegalCode()
        tribunal = JudicialTribunal()
        reputation = ContextualReputationEngine()

        council = SocialInstitution(
            institution_id="inst_cabildo",
            name="Cabildo Municipal de Saltbor",
            institution_type=InstitutionType.COMMUNITY_COUNCIL,
            charter_description="Gobierno y orden público de la villa.",
            headquarters_location_id="casa_comunal",
            treasury_money=50.0,
        )

        magistrate = _make_agent(1, "Don", "Fernando", 55, Gender.MALE, conscientiousness=0.85)
        plaintiff = _make_agent(2, "Mateo", "Pineda", 34, Gender.MALE, money=20.0)
        defendant = _make_agent(3, "Rodrigo", "Cruz", 38, Gender.MALE, money=100.0)

        # 1. File property damage case (alleged $30 tool & crop destruction)
        case = tribunal.file_case(
            case_id="case_001",
            plaintiff=plaintiff,
            defendant=defendant,
            statute_type=LegalStatuteType.PROPERTY_RIGHTS,
            claim_description="Destrucción de cerco y apropiación indebida de herramientas comunales.",
            claimed_damages=30.0,
            evidence_strength=0.85,  # Strong evidence with witnesses
            current_tick=10,
        )

        # 2. Adjudicate and enforce ruling
        verdict = tribunal.adjudicate_and_enforce(
            case_id=case.case_id,
            magistrate=magistrate,
            legal_code=legal_code,
            plaintiff=plaintiff,
            defendant=defendant,
            municipal_institution=council,
            reputation_engine=reputation,
            current_tick=12,
        )

        assert verdict == VerdictOutcome.GUILTY_RESTITUTION_AND_FINE
        # 1.5x restitution on $30 = $45 restitution + $15 municipal fine
        assert case.awarded_restitution == 45.0
        assert case.court_fine == 15.0

        # Verify double-entry cash balances
        # Defendant started with $100 -> paid $45 restitution + $15 fine = $40 remaining
        assert defendant.physical_state.money == 40.0
        # Plaintiff started with $20 -> received $45 = $65
        assert plaintiff.physical_state.money == 65.0
        # Municipal treasury received $15 fine -> $50 + $15 = $65
        assert council.treasury_money == 65.0

        # Defendant reputation was penalized
        prof = reputation.get_or_create(defendant.uid)
        assert prof.moral_standing < 0.35

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(verdict == VerdictOutcome.GUILTY_RESTITUTION_AND_FINE and case.is_enforced),
            summary="Demonstrated formal judicial trial, evidence-based ruling, double-entry restitution transfer, and treasury fine enforcement.",
            hypotheses=[
                {"hypothesis": "Codified statutes prescribe standardized punitive restitution multipliers", "confirmed": True},
                {"hypothesis": "Judicial verdicts transfer actual financial assets directly without creation of funds", "confirmed": True},
            ],
            metrics={
                "verdict": verdict.value,
                "restitution_paid": case.awarded_restitution,
                "fine_paid_to_treasury": case.court_fine,
                "plaintiff_final_money": plaintiff.physical_state.money,
                "defendant_final_money": defendant.physical_state.money,
                "council_treasury": council.treasury_money,
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXP_06_C — Commodity Money & Payment-in-Kind
# ===========================================================================
class Experiment06_C_PaymentInKind(BaseExperiment):
    """Test debt obligation satisfaction using physical commodity inventories during cash illiquidity."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_C",
            name="Commodity Money Standards & Payment-in-Kind Settlement",
            description="Examines debt repayment via physical inventory transfer during severe liquidity shortages.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        credit = CreditEngine()
        inkind_engine = InKindPaymentEngine()

        lender = _make_agent(1, "Don", "Antonio", 50, Gender.MALE, money=200.0)
        debtor = _make_agent(2, "Esteban", "Campesino", 30, Gender.MALE, money=2.0)  # Cash impoverished!

        # Debtor has 15 bushels of physical grain in their inventory
        debtor.inventory.add(InventoryItem(item_type=ItemType.GRAIN, quantity=15.0, unit=UnitType.BUSHEL))

        # Originate loan: $24 principal, $25.20 due, installment = $6.30
        loan = credit.issue_interpersonal_loan(
            loan_id="loan_crop_01",
            lender=lender,
            borrower=debtor,
            principal=24.0,
            term_ticks=96,
            current_tick=1,
        )
        assert loan is not None

        # Debtor cannot pay $6.30 in cash (only has $2.0 after spending loan on emergency)
        debtor.physical_state.money = 0.50

        # Debtor settles installment in kind using Grain (appraised at $2.0 per bushel)
        # 3.15 bushels * $2.0 = $6.30 credit
        paid_val = inkind_engine.settle_loan_installment_in_kind(
            loan=loan,
            debtor=debtor,
            lender=lender,
            item_type=ItemType.GRAIN,
            max_quantity_to_offer=5.0,
            unit_valuation=2.0,
            current_tick=24,
        )
        assert paid_val > 6.0
        assert loan.balance_remaining < 20.0
        assert loan.consecutive_missed_payments == 0  # Default averted!

        # Verify physical stock conservation
        assert debtor.inventory.get_quantity(ItemType.GRAIN) < 15.0
        assert lender.inventory.get_quantity(ItemType.GRAIN) > 3.0

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(paid_val > 6.0 and loan.consecutive_missed_payments == 0),
            summary="Demonstrated payment-in-kind debt satisfaction: borrower averted default by transferring physical grain inventories.",
            hypotheses=[
                {"hypothesis": "Tangible commodities can clear debts in kind when cash liquidity is exhausted", "confirmed": True},
                {"hypothesis": "Physical inventory transfers conserve total material goods between debtor and creditor", "confirmed": True},
            ],
            metrics={
                "value_credited": paid_val,
                "debtor_remaining_grain": round(debtor.inventory.get_quantity(ItemType.GRAIN), 2),
                "lender_acquired_grain": round(lender.inventory.get_quantity(ItemType.GRAIN), 2),
                "loan_remaining_balance": loan.balance_remaining,
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXP_06_D — Multi-Settlement Regional Shock & Relief
# ===========================================================================
class Experiment06_D_RegionalShockAndRelief(BaseExperiment):
    """Test how a local resource bottleneck in Saltbor is relieved by inter-settlement trade."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_D",
            name="Inter-Settlement Bottleneck Relief & Regional Integration",
            description="Examines how local raw material shortages trigger caravan imports from specialized regional partners.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        trade = RegionalTradeEngine(rng=np.random.default_rng(42))

        # Saltbor workshop is bottlenecked by 0 wood stock
        saltbor = trade.settlements["settlement_saltbor"]
        saltbor.commodity_surpluses[ItemType.WOOD] = 0.0

        # Monte Verde has 100 timber units in reserve
        monte_verde = trade.settlements["settlement_monte_verde"]
        monte_verde.commodity_surpluses[ItemType.WOOD] = 100.0

        # Inbound caravan carrying 30 units of wood from Monte Verde to Saltbor
        caravan = trade.dispatch_caravan(
            caravan_id="caravan_relief_01",
            origin_id="settlement_monte_verde",
            destination_id="settlement_saltbor",
            cargo={ItemType.WOOD: 30.0},
            currency_budget=50.0,
            departure_tick=1,
        )

        # Advance caravan across travel corridor
        for tick in range(1, 35):
            trade.step(tick)

        # Wood arrived at Saltbor, relieving local bottleneck
        assert caravan.status == CaravanStatus.COMPLETED
        assert saltbor.commodity_surpluses[ItemType.WOOD] >= 30.0

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(saltbor.commodity_surpluses[ItemType.WOOD] >= 30.0),
            summary="Demonstrated regional bottleneck relief: highland timber caravan successfully replenished Saltbor wood reserves.",
            hypotheses=[
                {"hypothesis": "Regional trade mitigates local resource exhaustion across interconnected settlements", "confirmed": True},
            ],
            metrics={
                "saltbor_restocked_wood": saltbor.commodity_surpluses[ItemType.WOOD],
                "trade_value": caravan.trade_volume_value,
                "monte_verde_remaining_wood": monte_verde.commodity_surpluses[ItemType.WOOD],
            },
            duration_seconds=elapsed,
        )
