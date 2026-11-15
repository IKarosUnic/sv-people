"""Unit tests for CollaborativeGovernanceEngine (Phase 1.14)."""

import pytest
from saltbor.territory.governance import CollaborativeGovernanceEngine
from saltbor.territory.models import GovernanceRole, ProjectApprovalStatus


def test_governance_initialization():
    engine = CollaborativeGovernanceEngine()
    assert len(engine.user_jurisdictions) >= 5


def test_rbac_and_geographic_jurisdiction():
    engine = CollaborativeGovernanceEngine()

    # Citizen cannot review or approve proposals
    auth, reason = engine.check_authorization("citizen_ss_01", "approve_municipal_proposal")
    assert auth is False
    assert "does not possess permission" in reason

    # Municipal admin can approve proposals in their OWN municipality (SS01)
    auth_muni, _ = engine.check_authorization(
        actor_id="admin_muni_ss_centro",
        action="approve_municipal_proposal",
        target_department="SS",
        target_municipality="SS01",
    )
    assert auth_muni is True

    # Municipal admin CANNOT approve proposals in another municipality (CH01)!
    auth_breach, breach_reason = engine.check_authorization(
        actor_id="admin_muni_ss_centro",
        action="approve_municipal_proposal",
        target_department="CH",
        target_municipality="CH01",
    )
    assert auth_breach is False
    assert "Jurisdiction breach" in breach_reason


def test_proposal_lifecycle_and_conflict_resolution():
    engine = CollaborativeGovernanceEngine()

    # 1. Citizen submits proposal in San Salvador Centro
    ok, msg, prop = engine.submit_proposal(
        actor_id="citizen_ss_01",
        title="Parque Infantil Comunitario",
        description="Rehabilitate neighborhood sports park",
        project_type="public_recreational_space",
        target_department_code="SS",
        target_municipality_id="SS01",
        requested_budget_usd=15000.0,
        tick=10,
    )
    assert ok is True
    assert prop is not None
    assert prop.status == ProjectApprovalStatus.SUBMITTED

    # 2. Deliberative conflict resolution creates version 2
    res_ok, res_msg = engine.resolve_proposal_conflict(
        resolver_id="admin_muni_ss_centro",
        proposal_id=prop.proposal_id,
        amended_budget_usd=12000.0,
        compromise_notes="Adjusted playground equipment costs to fit municipal fiscal budget",
        tick=15,
    )
    assert res_ok is True
    assert prop.version == 2
    assert prop.requested_budget_usd == 12000.0

    # 3. Municipal admin approves proposal
    appr_ok, appr_msg = engine.review_and_decide_proposal(
        reviewer_id="admin_muni_ss_centro",
        proposal_id=prop.proposal_id,
        decision="APPROVE",
        notes="Approved under 2024 municipal development plan",
        tick=20,
    )
    assert appr_ok is True
    assert prop.status == ProjectApprovalStatus.APPROVED

    # 4. Verify immutable audit log
    audit_trail = engine.get_audit_trail(limit=10)
    assert len(audit_trail) >= 3
    assert all(e["authorized"] for e in audit_trail)
