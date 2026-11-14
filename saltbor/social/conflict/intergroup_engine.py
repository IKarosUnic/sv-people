"""Intergroup and Inter-Organizational Conflict Engine for SALTBOR Phase 1.9.

Models collective disputes between organizations, commercial syndicates, cantones,
and labor groups: strikes, boycotts, territorial friction, water disputes, mediation,
pacts, and contract breaches.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional
import uuid

from saltbor.core.types import Tick

logger = logging.getLogger(__name__)


class IntergroupConflictType(str, enum.Enum):
    """Domains of collective intergroup dispute."""

    TERRITORIAL_BOUNDARY = "territorial_boundary"     # Linderos entre cantones o comunidades
    COMMERCIAL_RIVALRY = "commercial_rivalry"         # Competencia por puestos en mercado / precios
    WATER_RESOURCE = "water_resource"                 # Disputa por turnos de agua de pozo o acequia
    LABOR_STRIKE = "labor_strike"                     # Huelga de jornaleros frente a taller o patrón
    MUNICIPAL_JURISDICTION = "municipal_jurisdiction" # Fricción de competencias entre ADESCO y gobierno
    DEBT_BREACH = "debt_breach"                       # Incumplimiento de crédito inter-asociación


class ConflictTensionStage(str, enum.Enum):
    """Stages of collective conflict escalation."""

    LATENT = "latent"
    GRIEVANCE_FILED = "grievance_filed"
    DIRECT_NEGOTIATION = "direct_negotiation"
    ESCALATED_ACTION = "escalated_action"             # Huelga, boicot o protesta
    MEDIATION = "mediation"                           # Mediación por ADESCO o tribunal
    PACT_ENACTED = "pact_enacted"                     # Acuerdo de paz y cooperación
    BROKEN_PACT = "broken_pact"                       # Ruptura de acuerdo y represalia


@dataclasses.dataclass
class IntergroupDispute:
    """A tracked dispute between two collective organizations or communities."""

    dispute_id: str
    conflict_type: IntergroupConflictType
    initiator_org_id: str
    respondent_org_id: str
    core_grievance: str
    intensity: float = 0.50          # [0.0, 1.0] Tension level
    stage: ConflictTensionStage = ConflictTensionStage.GRIEVANCE_FILED
    mediator_id: Optional[str] = None
    created_tick: int = 0
    resolved_tick: Optional[int] = None

    # Offers and Pacts
    terms_agreed: list[str] = dataclasses.field(default_factory=list)
    compensation_usd: float = 0.0
    history_log: list[str] = dataclasses.field(default_factory=list)

    def escalate(self, boost: float = 0.20, action_type: str = "escalation", tick: int = 0) -> None:
        """Escalate conflict tension (e.g., launching a strike or boycott)."""
        self.intensity = min(1.0, self.intensity + boost)
        self.stage = ConflictTensionStage.ESCALATED_ACTION
        self.history_log.append(f"Tick {tick}: Escalated ({action_type}) to intensity {self.intensity:.2f}")

    def enter_mediation(self, mediator_name: str, tick: int = 0) -> None:
        """Submit dispute to neutral community or judicial mediator."""
        self.mediator_id = mediator_name
        self.stage = ConflictTensionStage.MEDIATION
        self.history_log.append(f"Tick {tick}: Entered mediation under {mediator_name}")

    def sign_compromise_pact(self, terms: list[str], compensation: float = 0.0, tick: int = 0) -> None:
        """Reach formal settlement between conflicting organizations."""
        self.stage = ConflictTensionStage.PACT_ENACTED
        self.terms_agreed = list(terms)
        self.compensation_usd = compensation
        self.intensity = max(0.10, self.intensity - 0.50)
        self.resolved_tick = tick
        self.history_log.append(
            f"Tick {tick}: Compromise pact ENACTED (compensation: ${compensation:.2f}, {len(terms)} terms)"
        )

    def break_pact(self, reason: str, tick: int = 0) -> None:
        """Breach of settlement terms triggering retaliation."""
        self.stage = ConflictTensionStage.BROKEN_PACT
        self.intensity = min(1.0, self.intensity + 0.40)
        self.history_log.append(f"Tick {tick}: Pact BROKEN ({reason}) - Tension renewed")


class IntergroupConflictEngine:
    """Coordinates collective inter-organizational conflict, mediation, and pacts."""

    def __init__(self) -> None:
        self._disputes: dict[str, IntergroupDispute] = {}

    def get_dispute(self, dispute_id: str) -> Optional[IntergroupDispute]:
        return self._disputes.get(dispute_id)

    def get_all_disputes(self, active_only: bool = True) -> list[IntergroupDispute]:
        if not active_only:
            return list(self._disputes.values())
        return [d for d in self._disputes.values() if d.stage != ConflictTensionStage.PACT_ENACTED]

    def initiate_dispute(
        self,
        initiator_org_id: str,
        respondent_org_id: str,
        conflict_type: IntergroupConflictType,
        grievance: str,
        initial_intensity: float = 0.50,
        tick: int = 0,
    ) -> IntergroupDispute:
        """File a formal collective grievance against another organization."""
        disp_id = f"disp_{conflict_type.value[:4]}_{uuid.uuid4().hex[:6]}"
        dispute = IntergroupDispute(
            dispute_id=disp_id,
            conflict_type=conflict_type,
            initiator_org_id=initiator_org_id,
            respondent_org_id=respondent_org_id,
            core_grievance=grievance,
            intensity=initial_intensity,
            created_tick=tick,
        )
        dispute.history_log.append(f"Tick {tick}: Collective grievance filed by {initiator_org_id}")
        self._disputes[disp_id] = dispute
        return dispute

    def step(self, current_tick: Tick) -> None:
        """Periodic cooling of tensions or escalation checks."""
        pass
