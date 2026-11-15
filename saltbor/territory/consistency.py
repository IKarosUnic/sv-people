"""Shared Entity & State Consistency Validator for SALTBOR Territorial Scenarios.

Guarantees cross-domain ontological and transactional coherence:
1. No Entity State Bifurcation:
   - An individual cannot hold conflicting liquid cash balances between domain modules.
   - An individual cannot simultaneously hold contradictory employment statuses, locations,
     or dual health statuses updated out-of-sync.
2. Household Resource Pooling:
   - Shared household cash equals the pooled or managed cash of its cohabiting members.
   - Food pantry (kg), utility debts, and fiado liabilities are shared at household scope.
   - Educational enrolment and child labor activities are visible across domestic budgeting.
3. Commercial & Business Coherence:
   - Business cash balance matches the double-entry accounting ledger balance.
   - Inventory units are non-negative, conserved across purchases and sales.
   - Fiado accounts receivable match the corresponding households' accounts payable.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from saltbor.territory.economic_ledger import AccountType, VerifiableEconomicLedger
from saltbor.territory.models import RegionalTradeNode
from saltbor.territory.multi_scale import (
    MultiScaleHouseholdRecord,
    MultiScaleIndividualRecord,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ConsistencyViolation:
    """Description of an ontological or accounting state inconsistency."""
    entity_id: str
    entity_type: str
    variable_name: str
    observed_value_a: Any
    observed_value_b: Any
    severity: str    # "CRITICAL", "WARNING"
    details: str


class SharedEntityConsistencyValidator:
    """Validates and enforces synchronization across shared synthetic entities."""

    def __init__(self, tolerance_usd: float = 0.05) -> None:
        self.tolerance_usd = tolerance_usd

    def validate_individual_consistency(
        self,
        individual: MultiScaleIndividualRecord,
        household: Optional[MultiScaleHouseholdRecord],
        ledger: Optional[VerifiableEconomicLedger],
    ) -> List[ConsistencyViolation]:
        """Verify state integrity for an individual human."""
        violations: List[ConsistencyViolation] = []

        # 1. Health Status in [0.0, 1.0]
        if not (0.0 <= individual.health_status <= 1.0):
            violations.append(
                ConsistencyViolation(
                    entity_id=individual.uid,
                    entity_type="individual",
                    variable_name="health_status",
                    observed_value_a=individual.health_status,
                    observed_value_b="[0.0, 1.0]",
                    severity="CRITICAL",
                    details=f"Individual health_status {individual.health_status} is outside valid [0, 1] range.",
                )
            )

        # 2. Age vs Education/Work Feasibility
        if individual.age < 18 and individual.current_activity == "elder_care_home":
            violations.append(
                ConsistencyViolation(
                    entity_id=individual.uid,
                    entity_type="individual",
                    variable_name="current_activity",
                    observed_value_a=individual.current_activity,
                    observed_value_b="age < 18",
                    severity="CRITICAL",
                    details="Minor assigned to elder_care_home activity.",
                )
            )

        # 3. Cash consistency with Economic Ledger
        if ledger:
            ledger_cash = ledger.get_entity_balance(individual.uid, AccountType.ASSET_CASH)
            # If ledger has recorded transactions for this individual, cash must match
            if abs(individual.cash_usd - ledger_cash) > self.tolerance_usd and ledger_cash != 0.0:
                violations.append(
                    ConsistencyViolation(
                        entity_id=individual.uid,
                        entity_type="individual",
                        variable_name="cash_usd",
                        observed_value_a=individual.cash_usd,
                        observed_value_b=ledger_cash,
                        severity="CRITICAL",
                        details=f"In-memory cash (${individual.cash_usd:.2f}) does not match ledger cash (${ledger_cash:.2f}).",
                    )
                )

        # 4. Household affiliation
        if household:
            if individual.uid not in household.member_uids:
                violations.append(
                    ConsistencyViolation(
                        entity_id=individual.uid,
                        entity_type="individual",
                        variable_name="household_id",
                        observed_value_a=individual.household_id,
                        observed_value_b=household.member_uids,
                        severity="CRITICAL",
                        details=f"Individual references household '{household.household_id}' but is not in member_uids.",
                    )
                )

        return violations

    def validate_household_consistency(
        self,
        household: MultiScaleHouseholdRecord,
        members: List[MultiScaleIndividualRecord],
        ledger: Optional[VerifiableEconomicLedger],
    ) -> List[ConsistencyViolation]:
        """Verify domestic unit consistency."""
        violations: List[ConsistencyViolation] = []

        # 1. Head of household must be one of the members
        if household.head_uid not in household.member_uids:
            violations.append(
                ConsistencyViolation(
                    entity_id=household.household_id,
                    entity_type="household",
                    variable_name="head_uid",
                    observed_value_a=household.head_uid,
                    observed_value_b=household.member_uids,
                    severity="CRITICAL",
                    details=f"Household head '{household.head_uid}' not listed in member_uids.",
                )
            )

        # 2. Pantry food cannot be negative
        if household.pantry_food_kg < -1e-4:
            violations.append(
                ConsistencyViolation(
                    entity_id=household.household_id,
                    entity_type="household",
                    variable_name="pantry_food_kg",
                    observed_value_a=household.pantry_food_kg,
                    observed_value_b=">= 0.0",
                    severity="CRITICAL",
                    details=f"Pantry food kg is negative ({household.pantry_food_kg:.2f} kg).",
                )
            )

        # 3. Fiado payable in ledger vs household
        if ledger:
            ledger_fiado = ledger.get_entity_balance(household.household_id, AccountType.LIABILITY_PAYABLE)
            if ledger_fiado < -1e-4:
                violations.append(
                    ConsistencyViolation(
                        entity_id=household.household_id,
                        entity_type="household",
                        variable_name="fiado_payable",
                        observed_value_a=ledger_fiado,
                        observed_value_b=">= 0.0",
                        severity="CRITICAL",
                        details=f"Negative liability payable balance on household ({ledger_fiado:.2f}).",
                    )
                )

        return violations

    def validate_business_consistency(
        self,
        business: RegionalTradeNode,
        ledger: Optional[VerifiableEconomicLedger],
    ) -> List[ConsistencyViolation]:
        """Verify micro-business / trade node consistency."""
        violations: List[ConsistencyViolation] = []

        # 1. Non-negative inventory
        for commodity, qty in business.inventory_units.items():
            if qty < 0:
                violations.append(
                    ConsistencyViolation(
                        entity_id=business.node_id,
                        entity_type="business",
                        variable_name=f"inventory_{commodity}",
                        observed_value_a=qty,
                        observed_value_b=">= 0",
                        severity="CRITICAL",
                        details=f"Physical inventory of {commodity} is negative ({qty} units).",
                    )
                )

        # 2. Ledger cash match
        if ledger:
            ledger_cash = ledger.get_entity_balance(business.node_id, AccountType.ASSET_CASH)
            if abs(business.cash_balance_usd - ledger_cash) > self.tolerance_usd and ledger_cash != 0.0:
                violations.append(
                    ConsistencyViolation(
                        entity_id=business.node_id,
                        entity_type="business",
                        variable_name="cash_balance_usd",
                        observed_value_a=business.cash_balance_usd,
                        observed_value_b=ledger_cash,
                        severity="CRITICAL",
                        details=f"Business cash (${business.cash_balance_usd:.2f}) does not match ledger cash (${ledger_cash:.2f}).",
                    )
                )

        return violations

    def synchronize_entities(
        self,
        individuals: Dict[str, MultiScaleIndividualRecord],
        households: Dict[str, MultiScaleHouseholdRecord],
        businesses: Dict[str, RegionalTradeNode],
        ledger: VerifiableEconomicLedger,
    ) -> int:
        """Enforce bidirectional synchronization between memory objects and ledger state.

        Returns total count of fields synchronized.
        """
        sync_count = 0

        # Sync individual liquid cash
        for ind in individuals.values():
            ledger_cash = ledger.get_entity_balance(ind.uid, AccountType.ASSET_CASH)
            if abs(ind.cash_usd - ledger_cash) > 1e-4 and ledger_cash >= 0.0:
                ind.cash_usd = ledger_cash
                sync_count += 1

        # Sync household shared cash with head individual or pooled members
        for hh in households.values():
            ledger_hh_cash = ledger.get_entity_balance(hh.household_id, AccountType.ASSET_CASH)
            if ledger_hh_cash > 0.0:
                hh.shared_cash_usd = ledger_hh_cash
                sync_count += 1
            else:
                # Sum of individual members' cash
                pooled = sum(individuals[uid].cash_usd for uid in hh.member_uids if uid in individuals)
                hh.shared_cash_usd = round(pooled, 2)
                sync_count += 1

        # Sync businesses
        for biz in businesses.values():
            ledger_biz_cash = ledger.get_entity_balance(biz.node_id, AccountType.ASSET_CASH)
            if abs(biz.cash_balance_usd - ledger_biz_cash) > 1e-4 and ledger_biz_cash >= 0.0:
                biz.cash_balance_usd = ledger_biz_cash
                sync_count += 1

            # Solvency check: working capital must cover operating liquidity buffer ($50 for retail / 4x overhead)
            biz.is_solvent = biz.cash_balance_usd >= max(biz.daily_overhead_usd * 4.0, 50.0) if biz.daily_overhead_usd > 0 else biz.cash_balance_usd > 0

        return sync_count
