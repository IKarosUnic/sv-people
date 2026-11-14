"""Unit tests for SALTBOR Multi-Agent Orchestration Contracts and Schemas.

Validates that schemas, role boundaries, model routing, and convergence invariants
comply with AGENTS.md, AGENT_ORCHESTRATION_ARCHITECTURE.md, and MODEL_ROUTING_POLICY.md.
"""

import pytest
from orchestration.schemas import (
    AgentRole,
    ComplexityTier,
    AuditStatus,
    TaskSpecification,
    ImplementationDeliverable,
    AuditorReport,
    WorkflowRunMetrics,
)


def test_agent_roles_enumeration():
    """Verify all 5 canonical roles are present."""
    roles = {r.value for r in AgentRole}
    expected = {"orchestrator", "writer", "implementation", "research", "auditor"}
    assert roles == expected


def test_complexity_tier_mapping():
    """Verify complexity tiers map to valid Antigravity model identifiers (pro excluded; Gemini 3.8 Flash High used)."""
    assert ComplexityTier.LOW.value == "flash_lite"
    assert ComplexityTier.MODERATE.value == "flash"
    assert ComplexityTier.HIGH.value == "inherit"
    assert ComplexityTier.CRITICAL.value == "gemini-3.8-flash-high"


def test_task_specification_validation():
    """Verify TaskSpecification contract validation."""
    spec = TaskSpecification(
        spec_title="Economic Conservation Audit Engine",
        summary="Audit accounting transactions for zero balance leak",
        requirements=["Verify sum delta balances equals zero", "Reject negative money creation"],
        acceptance_criteria=["Zero tolerance epsilon 1e-9", "Pytest pass rate 100%"]
    )
    assert len(spec.requirements) == 2
    assert len(spec.acceptance_criteria) == 2
    assert "Economic" in spec.spec_title


def test_implementation_deliverable_contract():
    """Verify ImplementationDeliverable holds code, tests, and complexity notes."""
    deliverable = ImplementationDeliverable(
        target_file="saltbor/core/conservation.py",
        function_code="def verify_zero_sum(deltas): return abs(sum(deltas)) < 1e-9",
        unit_test_code="def test_zero_sum(): assert verify_zero_sum([10.0, -10.0])",
        tests_passed=True,
        complexity_notes="O(N) time, O(1) auxiliary space"
    )
    assert deliverable.tests_passed is True
    assert deliverable.target_file == "saltbor/core/conservation.py"


def test_auditor_report_contract():
    """Verify AuditorReport handles APPROVED, REJECTED, and conservation checks."""
    report_approved = AuditorReport(
        status=AuditStatus.APPROVED,
        feedback="Code satisfies all edge cases and conservation laws.",
        checks_passed=["Zero-sum accounting", "Unicode normalization", "100% Pytest pass"],
        conservation_verified=True,
        security_risks_detected=[]
    )
    assert report_approved.status == AuditStatus.APPROVED
    assert report_approved.conservation_verified is True

    report_rejected = AuditorReport(
        status=AuditStatus.REJECTED,
        feedback="Detected balance leak in dues collection.",
        checks_passed=["Unicode handling"],
        conservation_verified=False,
        security_risks_detected=["Unverified balance addition"]
    )
    assert report_rejected.status == AuditStatus.REJECTED
    assert report_rejected.conservation_verified is False


def test_workflow_metrics_and_loop_invariants():
    """Verify WorkflowRunMetrics tracking and hard iteration bounds."""
    metrics = WorkflowRunMetrics(
        run_id="run-test-01",
        total_turns=3,
        total_tokens={"input_tokens": 5000, "output_tokens": 1200, "total_tokens": 6200},
        elapsed_seconds=14.5,
        status="COMPLETED",
        remediations_count=1
    )
    assert metrics.total_turns <= 3, "Workflow exceeded maximum iteration bound of 3!"
    assert metrics.remediations_count == 1
