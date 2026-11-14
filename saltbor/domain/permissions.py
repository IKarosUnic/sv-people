"""Territorial and Organizational Permission Engine for SALTBOR.

Enforces role-based access control (RBAC), geographic bounding scopes,
institutional affiliations, approval workflows, and audit history:

Roles:
- CITIZEN
- BUSINESS_OWNER
- BUSINESS_ADMINISTRATOR
- PROPERTY_ADMINISTRATOR
- RESEARCHER
- EDUCATIONAL_INSTITUTION
- HEALTHCARE_INSTITUTION
- MUNICIPAL_ADMINISTRATOR
- GOVERNMENT_INSTITUTION
- PLATFORM_ADMINISTRATOR

Approval Lifecycle:
DRAFT -> PROPOSED -> UNDER_REVIEW -> APPROVED -> ACTIVE (or REJECTED)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from saltbor.domain.models import (
    ApprovalStatus,
    AuditAction,
    PermissionType,
    UserRole,
    UserSubject,
    WorldLayerType,
)

logger = logging.getLogger(__name__)


# Default Role-to-Permissions Mapping
ROLE_CAPABILITIES: Dict[UserRole, Set[Tuple[PermissionType, WorldLayerType]]] = {
    UserRole.CITIZEN: {
        (PermissionType.READ, WorldLayerType.LAYER_A_BASE),
        (PermissionType.READ, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.READ, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.READ, WorldLayerType.LAYER_D_INTERVENTIONS),
    },
    UserRole.BUSINESS_OWNER: {
        (PermissionType.READ, WorldLayerType.LAYER_A_BASE),
        (PermissionType.READ, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.READ, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.READ, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.CREATE, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.EDIT, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.DELETE, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.CREATE, WorldLayerType.LAYER_D_INTERVENTIONS),
    },
    UserRole.RESEARCHER: {
        (PermissionType.READ, WorldLayerType.LAYER_A_BASE),
        (PermissionType.READ, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.READ, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.READ, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.CREATE, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.EDIT, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.DELETE, WorldLayerType.LAYER_D_INTERVENTIONS),
    },
    UserRole.MUNICIPAL_ADMINISTRATOR: {
        (PermissionType.READ, WorldLayerType.LAYER_A_BASE),
        (PermissionType.READ, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.READ, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.READ, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.CREATE, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.EDIT, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.DELETE, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.CREATE, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.EDIT, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.DELETE, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.ADMINISTER, WorldLayerType.LAYER_B_WORLD),
    },
    UserRole.PLATFORM_ADMINISTRATOR: {
        (PermissionType.READ, WorldLayerType.LAYER_A_BASE),
        (PermissionType.READ, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.READ, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.READ, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.CREATE, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.EDIT, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.DELETE, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.CREATE, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.EDIT, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.DELETE, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.CREATE, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.EDIT, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.DELETE, WorldLayerType.LAYER_D_INTERVENTIONS),
        (PermissionType.ADMINISTER, WorldLayerType.LAYER_B_WORLD),
        (PermissionType.ADMINISTER, WorldLayerType.LAYER_C_ACTIVITY),
        (PermissionType.ADMINISTER, WorldLayerType.LAYER_D_INTERVENTIONS),
    },
}


class DomainPermissionEngine:
    """Evaluates user authorization, enforces boundaries, and maintains immutable audit history."""

    def __init__(self) -> None:
        self.users: Dict[str, UserSubject] = {}
        self.proposals: Dict[str, Dict[str, Any]] = {}  # proposal_id -> proposal info
        self.audit_log: List[AuditAction] = []
        self._seed_default_users()

    def register_user(self, user: UserSubject) -> None:
        self.users[user.user_id] = user

    def authorize(
        self,
        user_id: str,
        action: PermissionType,
        target_layer: WorldLayerType,
        target_coords: Optional[Tuple[float, float]] = None,
        institution_id: Optional[str] = None,
    ) -> bool:
        """Check if user has permission to execute an action on a target layer within geographical bounds."""
        user = self.users.get(user_id)
        if not user:
            self._log_audit(user_id, action, target_layer, success=False, error="User not registered")
            return False

        # Rule 1: Layer A is universally read-only
        if target_layer == WorldLayerType.LAYER_A_BASE and action != PermissionType.READ:
            self._log_audit(user_id, action, target_layer, success=False, error="Layer A is strictly immutable")
            return False

        # Rule 2: Platform administrator has universal access across B, C, D
        if UserRole.PLATFORM_ADMINISTRATOR in user.roles:
            self._log_audit(user_id, action, target_layer, success=True)
            return True

        # Rule 3: Check role capability matrix
        has_capability = False
        for role in user.roles:
            caps = ROLE_CAPABILITIES.get(role, set())
            if (action, target_layer) in caps:
                has_capability = True
                break

        if not has_capability:
            self._log_audit(user_id, action, target_layer, success=False, error=f"Roles {user.roles} lack {action.value} on {target_layer.value}")
            return False

        # Rule 4: Geographic boundary scope check
        if target_coords and user.geographic_bounds:
            lon, lat = target_coords
            min_lon, min_lat, max_lon, max_lat = user.geographic_bounds
            if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
                self._log_audit(user_id, action, target_layer, success=False, error="Action coordinates outside authorized municipal bounds")
                return False

        # Rule 5: Institutional scope check
        if institution_id and user.institution_id and institution_id != user.institution_id:
            if UserRole.GOVERNMENT_INSTITUTION not in user.roles:
                self._log_audit(user_id, action, target_layer, success=False, error="Action outside authorized institutional scope")
                return False

        self._log_audit(user_id, action, target_layer, success=True)
        return True

    # =========================================================================
    # Approval Workflow Lifecycle
    # =========================================================================

    def submit_proposal(
        self,
        user_id: str,
        title: str,
        target_layer: WorldLayerType,
        proposed_feature_data: Dict[str, Any],
        rationale: str,
    ) -> Dict[str, Any]:
        """Submit a proposed intervention or public project for municipal/institutional review."""
        prop_id = f"prop_{uuid4().hex[:8]}"
        proposal = {
            "proposal_id": prop_id,
            "creator_id": user_id,
            "title": title,
            "target_layer": target_layer.value,
            "proposed_feature_data": proposed_feature_data,
            "rationale": rationale,
            "status": ApprovalStatus.PROPOSED.value,
            "created_at": time.time(),
            "reviewers": [],
            "review_notes": [],
        }
        self.proposals[prop_id] = proposal
        logger.info("Proposal %s ('%s') submitted by %s", prop_id, title, user_id)
        return proposal

    def review_proposal(
        self,
        reviewer_id: str,
        proposal_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        comment: str = "",
    ) -> bool:
        """Review and approve/reject a proposal. Requires Municipal or Platform Admin role."""
        rev = self.users.get(reviewer_id)
        if not rev:
            return False

        is_authorized_reviewer = any(
            r in (UserRole.MUNICIPAL_ADMINISTRATOR, UserRole.PLATFORM_ADMINISTRATOR, UserRole.GOVERNMENT_INSTITUTION)
            for r in rev.roles
        )
        if not is_authorized_reviewer:
            logger.warning("User %s unauthorized to review proposals.", reviewer_id)
            return False

        prop = self.proposals.get(proposal_id)
        if not prop:
            return False

        new_status = ApprovalStatus.APPROVED.value if decision == "APPROVED" else ApprovalStatus.REJECTED.value
        prop["status"] = new_status
        prop["reviewers"].append(reviewer_id)
        prop["review_notes"].append({"reviewer": reviewer_id, "decision": decision, "comment": comment, "time": time.time()})
        return True

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return chronological audit trail of all access control checks."""
        return [dataclasses.asdict(a) for a in self.audit_log[-limit:]]

    def _log_audit(
        self,
        user_id: str,
        action: PermissionType,
        layer: WorldLayerType,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        self.audit_log.append(
            AuditAction(
                audit_id=f"audit_{uuid4().hex[:8]}",
                user_id=user_id,
                action_type=action,
                target_resource_id=layer.value,
                target_layer=layer,
                success=success,
                error_message=error,
            )
        )

    def _seed_default_users(self) -> None:
        """Seed representative accounts."""
        self.register_user(
            UserSubject(
                user_id="citizen_juan",
                name="Juan Perez",
                roles=[UserRole.CITIZEN],
            )
        )
        self.register_user(
            UserSubject(
                user_id="entrepreneur_carmen",
                name="Carmen Gonzalez",
                roles=[UserRole.BUSINESS_OWNER],
            )
        )
        self.register_user(
            UserSubject(
                user_id="alcaldia_san_salvador",
                name="Alcaldía Municipal de San Salvador Centro",
                roles=[UserRole.MUNICIPAL_ADMINISTRATOR],
                geographic_bounds=(-89.260, 13.660, -89.170, 13.740),
            )
        )
        self.register_user(
            UserSubject(
                user_id="researcher_dr_santos",
                name="Dr. Roberto Santos",
                roles=[UserRole.RESEARCHER],
                institution_id="universidad_ues",
            )
        )
        self.register_user(
            UserSubject(
                user_id="admin",
                name="System Administrator",
                roles=[UserRole.PLATFORM_ADMINISTRATOR],
            )
        )
