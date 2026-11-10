"""
Salvadoran Family Remittances Engine (Section 19.4).

Models the critical economic lifeline of international family remittances (remesas):
- Monthly remittance inflows from relatives in the diaspora (EE.UU., etc.)
- Allocation of remittance funds:
  - Food & basic sustenance (~45%)
  - Home improvement: converting adobe/wood/sheet metal to block/concrete (~25%)
  - Education and children's school supplies (~15%)
  - Healthcare and medicine for elderly relatives (~10%)
  - Modest precautionary savings (~5%)
- Behavioral effects: reduced desperation, greater resilience during droughts/temporales,
  and potential reduction in arduous agricultural wage labor if transfers are reliable.
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class HouseholdRemittanceProfile:
    """Remittance metadata for a Salvadoran household."""
    household_id: str
    has_sender_abroad: bool = True
    sender_relation: str = "hijo_en_eeuu"       # "hijo", "hermano", "padre", "tio"
    monthly_transfer_usd: float = 250.0
    reliability_index: float = 0.90             # Probability of transfer arriving each month
    total_lifetime_received_usd: float = 0.0
    housing_quality_score: float = 0.40         # [0.0, 1.0] Increases as funds are invested in block/roof


class RemittanceEngine:
    """Simulates monthly remittance inflows and their multi-sector household impacts."""

    def __init__(self) -> None:
        self._profiles: dict[str, HouseholdRemittanceProfile] = {}

    def register_household_remittance(
        self,
        household_id: str,
        monthly_amount_usd: float = 250.0,
        sender_relation: str = "hijo_en_eeuu",
        reliability: float = 0.90,
    ) -> HouseholdRemittanceProfile:
        """Assign remittance profile to a household."""
        profile = HouseholdRemittanceProfile(
            household_id=household_id,
            has_sender_abroad=True,
            sender_relation=sender_relation,
            monthly_transfer_usd=monthly_amount_usd,
            reliability_index=reliability,
        )
        self._profiles[household_id] = profile
        return profile

    def process_monthly_remittance(
        self,
        household_id: str,
        current_household_cash: float,
        is_emergency_crisis: bool = False,
    ) -> dict[str, Any]:
        """Process arrival of monthly transfer and simulate household budget allocation."""
        profile = self._profiles.get(household_id)
        if not profile or not profile.has_sender_abroad:
            return {
                "received": False,
                "amount_usd": 0.0,
                "allocated_budget": {},
                "final_cash_usd": current_household_cash,
            }

        # Transfer arrives with reliability check
        transfer_amount = profile.monthly_transfer_usd
        if is_emergency_crisis:
            # Senders often send extra emergency money during temporales or sickness
            transfer_amount *= 1.35

        profile.total_lifetime_received_usd += transfer_amount

        # Standard Salvadoran remittance allocation model
        food_sustenance = round(transfer_amount * 0.45, 2)
        housing_improvement = round(transfer_amount * 0.25, 2)
        education_children = round(transfer_amount * 0.15, 2)
        health_elderly = round(transfer_amount * 0.10, 2)
        savings_retain = round(transfer_amount * 0.05, 2)

        # Invest in housing quality (gradual improvement of floor, block walls, zinc roof)
        profile.housing_quality_score = min(0.95, profile.housing_quality_score + 0.02)

        new_total_cash = current_household_cash + transfer_amount

        return {
            "received": True,
            "sender_relation": profile.sender_relation,
            "remittance_amount_usd": round(transfer_amount, 2),
            "allocated_budget": {
                "food_and_subsistence": food_sustenance,
                "housing_construction": housing_improvement,
                "education": education_children,
                "health_and_medicine": health_elderly,
                "savings": savings_retain,
            },
            "new_housing_quality": round(profile.housing_quality_score, 2),
            "total_lifetime_received": round(profile.total_lifetime_received_usd, 2),
            "final_cash_usd": round(new_total_cash, 2),
        }
