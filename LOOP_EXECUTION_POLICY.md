# SALTBOR MULTI-AGENT LOOP EXECUTION POLICY

## 1. Overview & Core Execution Directives

This document specifies the operational rules, state machines, and fail-safe protocols governing multi-agent loops in **SALTBOR**. 

**Primary Mandate**: All multi-agent workflows must terminate deterministically within a bounded number of iterations, execute under explicit token and time budgets, and never enter an infinite loop.

---

## 2. Canonical Development Loop Architecture

The standard SALTBOR development cycle follows an orchestrated, closed-loop pipeline with automated review and remediation:

```mermaid
sequenceDiagram
    autonumber
    participant O as Orchestrator (Pro)
    participant R as Research Agent (Pro)
    participant W as Writer Agent (Flash Lite)
    participant I as Implementation Agent (Flash)
    participant A as Auditor Agent (Flash/Pro)

    O->>R: Inquire Domain Literature / Algorithm State of the Art (if required)
    R-->>O: Structured Theoretical Evaluation
    O->>W: Request Formal Technical Specification
    W-->>O: Typed Specification JSON (Requirements & Acceptance Criteria)
    O->>I: Dispatch Implementation Task (Spec + Constraints)
    
    loop Review-and-Fix Cycle (Max 3 Iterations)
        I->>I: Author Code & Unit Tests in Sandbox
        I->>A: Submit Code, Tests & Complexity Notes
        A->>A: Independent Audit (Conservation, Edge Cases, Pytest Run)
        alt Audit APPROVED
            A-->>O: Certification APPROVED + Checks Passed
        else Audit REJECTED & Iteration < 3
            A-->>I: Detailed Rejection Feedback (Defect List & Edge Cases)
            Note over I: Implement Fix & Rerun Sandboxed Tests
        else Audit REJECTED & Iteration >= 3
            A-->>O: Failure Notification: Max Iterations Exceeded
            Note over O: Trigger Failure Protocol / Human Escalation
        end
    end

    alt Workflow Certified
        O->>O: Run Full Regression Suite (660+ tests)
        O->>O: Update Graphify Knowledge Graph
        O-->>User: Present Verified Deliverable & Test Evidence
    else Workflow Failed
        O->>O: Rollback Sandboxed Changes
        O-->>User: Detailed Failure Report & Architectural Blocker Analysis
    end
```

---

## 3. Loop Termination & Convergence Guarantees

To mathematically prevent non-terminating loops, the orchestration engine enforces four immutable convergence controls:

### 3.1 Hard Iteration Bounding (`max_iterations = 3`)
- Under no circumstances may an Implementation-Auditor cycle exceed **3 iterations**.
- **Iteration 1**: Initial implementation against formal specification.
- **Iteration 2**: Targeted remediation addressing specific defects identified by the Auditor.
- **Iteration 3**: Final resolution turn. If the Auditor rejects the third attempt, the loop halts immediately with status `FAILED_MAX_ITERATIONS`.

### 3.2 Time & Execution Quotas (`with_budget`)
Every dynamic workflow must wrap agent calls with the native `with_budget` primitive:
- Maximum execution time per turn: **180 seconds**.
- Maximum cumulative pipeline time: **600 seconds** (10 minutes).
- If a timeout occurs, `BudgetExceeded` is caught, the active agent is terminated, and the coordinator initiates rollback.

### 3.3 Strict Progress Invariants
On each fix turn, the Implementation Agent must submit a `fix_summary` explaining how each numbered item from the Auditor's feedback was resolved. If the Auditor determines that the feedback was ignored or that previously passing checks were broken (regression), the task is escalated immediately to Tier 3 (`pro`) or terminated.

---

## 4. Execution Patterns: Sequential vs. Parallel

```mermaid
graph TD
    subgraph Sequential Execution [Pattern A: Sequential Pipeline]
        S1[Research] --> S2[Writer] --> S3[Implementation] --> S4[Auditor]
    end

    subgraph Parallel Execution [Pattern B: Disjoint Parallel Fan-Out]
        P0[Orchestrator Partitioning]
        P0 -->|Module A / branch-A| P1[Implementer A]
        P0 -->|Module B / branch-B| P2[Implementer B]
        P0 -->|Module C / branch-C| P3[Implementer C]
        P1 --> J[Join & Conflict Audit]
        P2 --> J
        P3 --> J
    end
```

### 4.1 Sequential Execution Rules
Sequential pipelines are mandatory when:
- Tasks exhibit linear dependencies (e.g. specification must precede coding; coding must precede auditing).
- Changes touch core simulation loops (`SimulationRunner`, `EventBus`, database schema).

### 4.2 Parallel Execution & Collision Prevention
Antigravity's `parallel(items, fn)` enables concurrent agent execution, subject to strict isolation rules:
1. **Disjoint Target Sets**: Parallel execution is only permitted when agents modify completely distinct files or modules. Two agents must **never** edit the same file simultaneously.
2. **Workspace Isolation Modes**:
   - `workspace="branch"`: Each parallel agent receives an isolated git clone.
   - `workspace="share"`: Agents share the repository through a dedicated worktree.
   - `workspace="inherit"`: Read-only tasks (e.g. parallel code audits across 10 modules).
3. **Merge Conflict Verification**: Before merging parallel branches into `main`, the Orchestrator runs static conflict detection and regression testing.

---

## 5. Multi-Turn State Retention vs. Stateless Agents

Antigravity dynamic workflows support two operational agent modes:

### 5.1 Stateless Single-Turn Agents (`await agent(...)`)
Used for independent tasks where past conversation context is not required:
- Writer generating a specification from prompt arguments.
- Research agent surveying a specific paper or algorithm.
- Initial implementation from scratch.

### 5.2 Stateful Multi-Turn Agents (`a = agent(...)` then `await a(...)`)
Used for Review-and-Fix loops where retaining the conversational history of previous findings is critical:
```python
# The Auditor retains context across turns to verify fix fidelity
auditor = agent(
    prompt="You are an uncompromising QA Auditor for SALTBOR.",
    role="Auditor Agent",
    model="flash"
)

# Turn 1: Initial Audit
verdict_turn1 = await auditor(audit_prompt, schema=auditor_schema)

if verdict_turn1["status"] == "REJECTED":
    # Turn 2: Re-evaluation of the fix against earlier findings
    verdict_turn2 = await auditor(re_audit_prompt, schema=auditor_schema)
```
Stateful retention prevents the Auditor from repeating solved issues or forgetting previous edge-case discoveries.

---

## 6. Safety & Rollback Protocol

1. **Working Copy Cleanliness**: No agent may commence work if `git status` reports uncommitted user changes, unless operating in an isolated `workspace="branch"`.
2. **Atomic Rollback**: If a workflow fails or is aborted:
   - All temporary files in `scratch/` are purged.
   - The isolated git branch is deleted without touching the user's working copy.
   - An incident record is written to the run log.
3. **Never Fake Success**: An agent or workflow must never claim tests passed without actual execution stdout containing `=== N passed in X.XXs ===`.
