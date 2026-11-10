"""Codified statutory law: community legal codes, precedents, and standardized sanctions."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import Tick


class LegalStatuteType(enum.Enum):
    """Categorization of formal community laws in Saltbor."""

    PROPERTY_RIGHTS = "property_rights"            # Encroachment, timber theft, water diversion
    CONTRACT_ENFORCEMENT = "contract_enforcement"  # Loan default, broken delivery agreements
    THEFT_RESTITUTION = "theft_restitution"        # Stealing inventory, livestock, or tools
    LABOR_AND_WAGES = "labor_and_wages"            # Unpaid wages, hazardous negligence
    CIVIC_ORDER = "civic_order"                    # Fighting, public disturbance, festival sabotage


@dataclass
class LegalStatute:
    """A formal codified statute enacted by community councils or established through precedent."""

    statute_id: str
    title: str
    statute_type: LegalStatuteType
    description: str
    enacted_tick: Tick
    prescribed_fine: float = 10.0           # Mandatory fine payable to town treasury
    restitution_multiplier: float = 1.0     # 1.0 = full repayment; 1.5 = punitive damages (150%)
    reputation_penalty: float = 0.20        # Moral/financial standing reduction if found guilty
    precedent_origin_dispute_id: Optional[str] = None


class CommunityLegalCode:
    """The body of active statutory laws governing Saltbor."""

    def __init__(self) -> None:
        self.statutes: dict[str, LegalStatute] = {}
        self._initialize_baseline_laws()

    def _initialize_baseline_laws(self) -> None:
        """Establish baseline customary statutes."""
        self.statutes["law_debt_restitution"] = LegalStatute(
            statute_id="law_debt_restitution",
            title="Estatuto de Cumplimiento de Contratos y Deuda",
            statute_type=LegalStatuteType.CONTRACT_ENFORCEMENT,
            description="Todo préstamo impago con mora grave faculta al embargo o dación en pago por el monto total más 10% de recargo.",
            enacted_tick=1,
            prescribed_fine=5.0,
            restitution_multiplier=1.1,
            reputation_penalty=0.25,
        )
        self.statutes["law_property_integrity"] = LegalStatute(
            statute_id="law_property_integrity",
            title="Estatuto de Protección de Bienes e Inmuebles",
            statute_type=LegalStatuteType.PROPERTY_RIGHTS,
            description="La apropiación indebida o daño de herramientas y cultivos exige restitución del 150% del daño comprobado.",
            enacted_tick=1,
            prescribed_fine=15.0,
            restitution_multiplier=1.5,
            reputation_penalty=0.30,
        )

    def enact_statute(self, statute: LegalStatute) -> None:
        """Add or update a statute in the codified legal corpus."""
        self.statutes[statute.statute_id] = statute

    def get_statute_for_type(self, statute_type: LegalStatuteType) -> Optional[LegalStatute]:
        for s in self.statutes.values():
            if s.statute_type == statute_type:
                return s
        return None
