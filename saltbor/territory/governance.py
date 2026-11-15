"""Collaborative Governance & Institutional Permissions Engine for SALTBOR Phase 1.14.

Coordinates multi-actor collaborative territorial governance:
- 9 Authorized Governance Roles:
  Citizen, Business Owner, ADESCO Community Leader, Researcher, Educator,
  Health Worker, Municipal Administrator, Ministry Official, NGO Coordinator.
- Capabilities:
  Submitting community needs, authoring versioned proposals, multi-stage approval workflows,
  deliberative conflict resolution, participatory evaluation.
- Multi-Stage Lifecycle:
  DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> IN_EXECUTION -> COMPLETED (or REJECTED).
- Enforces:
  Role-Based Access Control (RBAC), Geographic boundary jurisdiction, Institutional permissions,
  Immutable audit trails.
- Safety Boundary:
  No autonomous public policy enactment. Distinguishes simulated interventions from real actions.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from saltbor.domain.models import DataProvenanceTier
from saltbor.territory.models import (
    CollaborativeProposal,
    GovernanceAuditEntry,
    GovernanceRole,
    ProjectApprovalStatus,
)

logger = logging.getLogger(__name__)


# Permissions matrix mapping GovernanceRole to allowed actions
ROLE_GOVERNANCE_PERMISSIONS: Dict[GovernanceRole, Set[str]] = {
    GovernanceRole.CITIZEN: {
        "submit_need",
        "submit_proposal",
        "view_approved_proposals",
        "view_public_projects",
    },
    GovernanceRole.BUSINESS_OWNER: {
        "submit_need",
        "submit_proposal",
        "view_approved_proposals",
        "view_public_projects",
        "bid_project_contract",
    },
    GovernanceRole.COMMUNITY_LEADER_ADESCO: {
        "submit_need",
        "submit_proposal",
        "endorse_community_proposal",
        "view_approved_proposals",
        "view_public_projects",
        "participate_conflict_deliberation",
    },
    GovernanceRole.RESEARCHER: {
        "submit_need",
        "submit_proposal",
        "view_approved_proposals",
        "view_public_projects",
        "run_scenario_simulation",
        "evaluate_impact_assessment",
    },
    GovernanceRole.EDUCATIONAL_REPRESENTATIVE: {
        "submit_need",
        "submit_proposal",
        "endorse_education_proposal",
        "view_approved_proposals",
    },
    GovernanceRole.HEALTHCARE_REPRESENTATIVE: {
        "submit_need",
        "submit_proposal",
        "endorse_health_proposal",
        "view_approved_proposals",
    },
    GovernanceRole.MUNICIPAL_ADMINISTRATOR: {
        "submit_need",
        "submit_proposal",
        "review_proposal",
        "approve_municipal_proposal",
        "reject_municipal_proposal",
        "execute_approved_project",
        "resolve_conflict",
        "view_approved_proposals",
        "view_audit_trail",
    },
    GovernanceRole.GOVERNMENT_MINISTRY_OFFICIAL: {
        "submit_need",
        "submit_proposal",
        "review_proposal",
        "approve_municipal_proposal",
        "approve_national_proposal",
        "reject_municipal_proposal",
        "reject_national_proposal",
        "execute_approved_project",
        "resolve_conflict",
        "view_approved_proposals",
        "view_audit_trail",
    },
    GovernanceRole.NONPROFIT_COORDINATOR: {
        "submit_need",
        "submit_proposal",
        "co-sponsor_proposal",
        "view_approved_proposals",
    },
}


class CollaborativeGovernanceEngine:
    """Manages multi-stakeholder proposals, territorial authorization, and deliberative governance."""

    def __init__(self) -> None:
        self.proposals: Dict[str, CollaborativeProposal] = {}
        self.audit_log: List[GovernanceAuditEntry] = []
        self.user_jurisdictions: Dict[str, Dict[str, Any]] = {}  # actor_id -> {role, department, municipality}
        self._seed_default_governance_actors()

    def register_actor(
        self,
        actor_id: str,
        role: GovernanceRole,
        department_code: str,
        municipality_id: Optional[str] = None,
    ) -> None:
        """Register an actor with specific territorial jurisdiction."""
        self.user_jurisdictions[actor_id] = {
            "role": role,
            "department_code": department_code,
            "municipality_id": municipality_id,
        }

    def check_authorization(
        self,
        actor_id: str,
        action: str,
        target_department: Optional[str] = None,
        target_municipality: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Verify role capability and geographic jurisdiction."""
        actor = self.user_jurisdictions.get(actor_id)
        if not actor:
            return False, f"Actor '{actor_id}' is not registered in governance directory"

        role = actor["role"]
        allowed_actions = ROLE_GOVERNANCE_PERMISSIONS.get(role, set())
        if action not in allowed_actions:
            return False, f"Role '{role.value}' does not possess permission for action '{action}'"

        # Check geographic boundary permissions for approvals
        if action in ("approve_municipal_proposal", "reject_municipal_proposal"):
            if role == GovernanceRole.MUNICIPAL_ADMINISTRATOR:
                if target_municipality and actor["municipality_id"] != target_municipality:
                    return False, f"Jurisdiction breach: Administrator for {actor['municipality_id']} cannot govern {target_municipality}"
            elif role == GovernanceRole.GOVERNMENT_MINISTRY_OFFICIAL:
                # National ministry officials have department/national scope
                pass

        return True, "Authorized"

    # =========================================================================
    # Proposal Authoring, Review & Approval Lifecycle
    # =========================================================================

    def submit_proposal(
        self,
        actor_id: str,
        title: str,
        description: str,
        project_type: str,
        target_department_code: str,
        target_municipality_id: str,
        requested_budget_usd: float,
        is_simulated_intervention: bool = True,
        tick: int = 0,
    ) -> Tuple[bool, str, Optional[CollaborativeProposal]]:
        """Submit a new territorial project proposal."""
        auth, reason = self.check_authorization(actor_id, "submit_proposal")
        if not auth:
            self._log_audit(tick, actor_id, GovernanceRole.CITIZEN, "submit_proposal_rejected", "none", {"reason": reason}, False)
            return False, reason, None

        actor = self.user_jurisdictions[actor_id]
        pid = f"prop_{uuid4().hex[:8]}"
        proposal = CollaborativeProposal(
            proposal_id=pid,
            title=title,
            description=description,
            proposer_id=actor_id,
            proposer_role=actor["role"],
            target_department_code=target_department_code,
            target_municipality_id=target_municipality_id,
            project_type=project_type,
            requested_budget_usd=requested_budget_usd,
            status=ProjectApprovalStatus.SUBMITTED,
            version=1,
            versions_history=[{"version": 1, "tick": tick, "description": description, "budget": requested_budget_usd}],
            is_simulated_intervention=is_simulated_intervention,
        )
        self.proposals[pid] = proposal

        self._log_audit(
            tick=tick,
            actor_id=actor_id,
            actor_role=actor["role"],
            action="submit_proposal",
            target_id=pid,
            details={"title": title, "budget": requested_budget_usd, "target_muni": target_municipality_id},
            authorized=True,
        )
        return True, "Proposal submitted for institutional review", proposal

    def review_and_decide_proposal(
        self,
        reviewer_id: str,
        proposal_id: str,
        decision: str,  # "APPROVE", "REJECT", "REQUEST_REVISION"
        notes: str = "",
        tick: int = 0,
    ) -> Tuple[bool, str]:
        """Municipal or Ministry review of a territorial proposal."""
        prop = self.proposals.get(proposal_id)
        if not prop:
            return False, f"Proposal '{proposal_id}' not found"

        action = "approve_municipal_proposal" if decision == "APPROVE" else "reject_municipal_proposal"
        auth, reason = self.check_authorization(
            actor_id=reviewer_id,
            action=action,
            target_department=prop.target_department_code,
            target_municipality=prop.target_municipality_id,
        )
        if not auth:
            actor_role = self.user_jurisdictions.get(reviewer_id, {}).get("role", GovernanceRole.CITIZEN)
            self._log_audit(tick, reviewer_id, actor_role, "review_decision_denied", proposal_id, {"reason": reason}, False)
            return False, reason

        actor = self.user_jurisdictions[reviewer_id]
        if decision == "APPROVE":
            prop.status = ProjectApprovalStatus.APPROVED
            prop.approval_signatures[actor["role"].value] = reviewer_id
        elif decision == "REJECT":
            prop.status = ProjectApprovalStatus.REJECTED
            prop.rejection_reasons.append(notes)
        else:
            prop.status = ProjectApprovalStatus.UNDER_REVIEW
            prop.conflicts_identified.append(notes)

        self._log_audit(
            tick=tick,
            actor_id=reviewer_id,
            actor_role=actor["role"],
            action=f"proposal_{decision.lower()}",
            target_id=proposal_id,
            details={"decision": decision, "notes": notes},
            authorized=True,
        )
        return True, f"Proposal {decision} recorded successfully"

    def resolve_proposal_conflict(
        self,
        resolver_id: str,
        proposal_id: str,
        amended_budget_usd: float,
        compromise_notes: str,
        tick: int = 0,
    ) -> Tuple[bool, str]:
        """Deliberative conflict resolution creating a new version of the proposal."""
        prop = self.proposals.get(proposal_id)
        if not prop:
            return False, "Proposal not found"

        auth, reason = self.check_authorization(resolver_id, "resolve_conflict")
        if not auth:
            return False, reason

        prop.version += 1
        prop.requested_budget_usd = amended_budget_usd
        prop.versions_history.append({
            "version": prop.version,
            "tick": tick,
            "resolver_id": resolver_id,
            "notes": compromise_notes,
            "amended_budget": amended_budget_usd,
        })
        prop.status = ProjectApprovalStatus.UNDER_REVIEW

        self._log_audit(
            tick=tick,
            actor_id=resolver_id,
            actor_role=self.user_jurisdictions[resolver_id]["role"],
            action="resolve_conflict_new_version",
            target_id=proposal_id,
            details={"version": prop.version, "notes": compromise_notes},
            authorized=True,
        )
        return True, f"Proposal amended to version {prop.version} through deliberative consensus"

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return chronological immutable audit entries."""
        return [dataclasses.asdict(e) for e in self.audit_log[-limit:]]

    def _log_audit(
        self,
        tick: int,
        actor_id: str,
        actor_role: GovernanceRole,
        action: str,
        target_id: str,
        details: Dict[str, Any],
        authorized: bool,
    ) -> None:
        entry = GovernanceAuditEntry(
            entry_id=f"audit_{len(self.audit_log)+1:06d}",
            timestamp_tick=tick,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            target_id=target_id,
            details=details,
            authorized=authorized,
        )
        self.audit_log.append(entry)

    def _seed_default_governance_actors(self) -> None:
        """Seed representative authorized actors across administrative tiers."""
        # 1. Municipal Administrator: San Salvador Centro (SS01)
        self.register_actor(
            actor_id="admin_muni_ss_centro",
            role=GovernanceRole.MUNICIPAL_ADMINISTRATOR,
            department_code="SS",
            municipality_id="SS01",
        )

        # 2. Municipal Administrator: Chalatenango (CH01)
        self.register_actor(
            actor_id="admin_muni_chalatenango",
            role=GovernanceRole.MUNICIPAL_ADMINISTRATOR,
            department_code="CH",
            municipality_id="CH01",
        )

        # 3. National Ministry Official: MOP / MINSAL (National jurisdiction)
        self.register_actor(
            actor_id="official_ministry_mop",
            role=GovernanceRole.GOVERNMENT_MINISTRY_OFFICIAL,
            department_code="SS",
            municipality_id=None,
        )

        # 4. ADESCO Community Leader: Canton El Tamarindo (Usulután)
        self.register_actor(
            actor_id="leader_adesco_tamarindo",
            role=GovernanceRole.COMMUNITY_LEADER_ADESCO,
            department_code="US",
            municipality_id="US01",
        )

        # 5. Local Citizen
        self.register_actor(
            actor_id="citizen_ss_01",
            role=GovernanceRole.CITIZEN,
            department_code="SS",
            municipality_id="SS01",
        )
