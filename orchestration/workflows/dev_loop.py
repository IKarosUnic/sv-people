"""SALTBOR Reusable Dynamic Development Loop Workflow.

Execution mode: Antigravity Dynamic Workflow (run_workflow tool).
Implements: Orchestrator -> [Research] -> Writer -> Implementation -> Auditor -> [Review-and-Fix Loop] -> Final Release.
"""

# Read workflow arguments
task_desc = args.get("task_description", "Implement a utility helper in SALTBOR")
target_subsystem = args.get("target_subsystem", "core")
max_iterations = int(args.get("max_iterations", 3))
enable_research = bool(args.get("enable_research", False))

phase("Phase 1 - Grounding & Specification")
log(f"Initiating Development Loop for: {task_desc}")
log(f"Target Subsystem: {target_subsystem} | Max Iterations: {max_iterations}")

# Optional Research Phase
research_notes = ""
if enable_research:
    phase("Phase 1A - Research & Theoretical Grounding")
    log("Dispatching Research Agent (model='inherit' -> Gemini 3.8 Flash High)...")
    research_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "algorithms": {"type": "array", "items": {"type": "string"}},
            "tradeoffs": {"type": "string"}
        },
        "required": ["summary", "algorithms", "tradeoffs"]
    }
    research_prompt = f"Conduct technical research on {task_desc} in the context of SALTBOR {target_subsystem}. Outline algorithms and trade-offs."
    research_res = await agent(
        prompt=research_prompt,
        schema=research_schema,
        role="Research Agent",
        model="inherit"
    )
    research_notes = f"\nResearch Findings:\n{research_res['summary']}\nRecommended Algorithms: {research_res['algorithms']}"
    log("Research phase completed.")

# Phase 2 - Writer Agent (flash_lite)
phase("Phase 2 - Technical Specification")
log("Dispatching Writer Agent (model='flash_lite')...")
writer_schema = {
    "type": "object",
    "properties": {
        "spec_title": {"type": "string"},
        "summary": {"type": "string"},
        "requirements": {"type": "array", "items": {"type": "string"}},
        "acceptance_criteria": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["spec_title", "summary", "requirements", "acceptance_criteria"]
}

writer_prompt = f"""You are the SALTBOR Writer Agent. Create a strict technical specification for:
Task: {task_desc}
Subsystem: {target_subsystem}
{research_notes}

Provide spec_title, summary, 3-5 concrete requirements, and 3 explicit acceptance criteria."""

spec = await agent(
    prompt=writer_prompt,
    schema=writer_schema,
    role="Writer Agent",
    model="flash_lite"
)
log(f"Specification finalized: {spec['spec_title']}")

# Phase 3 - Implementation & Review-and-Fix Loop
phase("Phase 3 - Implementation & Quality Audit Loop")

impl_schema = {
    "type": "object",
    "properties": {
        "target_file": {"type": "string"},
        "function_code": {"type": "string"},
        "unit_test_code": {"type": "string"},
        "tests_passed": {"type": "boolean"},
        "complexity_notes": {"type": "string"},
        "fix_summary": {"type": "string"}
    },
    "required": ["target_file", "function_code", "unit_test_code", "tests_passed", "complexity_notes"]
}

auditor_schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["APPROVED", "REJECTED", "ESCALATED"]},
        "feedback": {"type": "string"},
        "checks_passed": {"type": "array", "items": {"type": "string"}},
        "conservation_verified": {"type": "boolean"},
        "security_risks_detected": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["status", "feedback", "checks_passed", "conservation_verified", "security_risks_detected"]
}

# Stateful Auditor preserves context across inspection rounds
auditor = agent(
    prompt=f"You are the independent QA & Invariant Auditor for SALTBOR ({target_subsystem}). Evaluate code against specifications and conservation laws. Reject any edge-case omissions or accounting discrepancies.",
    role="Auditor Agent",
    model="flash"
)

iteration = 0
approved = False
feedback = "Initial implementation round."
last_impl = None

while iteration < max_iterations and not approved:
    iteration += 1
    phase(f"Iteration {iteration} - Code Implementation")
    
    # Model routing: escalate to 'inherit' (Gemini 3.8 Flash High) if failed previous attempt
    impl_model = "inherit" if iteration >= 3 else "flash"
    log(f"Running Implementation Agent (Turn {iteration}, model='{impl_model}')...")
    
    impl_prompt = f"""Specification:
Title: {spec['spec_title']}
Summary: {spec['summary']}
Requirements: {spec['requirements']}
Acceptance Criteria: {spec['acceptance_criteria']}

Feedback from Previous Audit:
{feedback}

Implement production code and comprehensive pytest unit tests. Verify in sandbox and return code and tests."""

    last_impl = await agent(
        prompt=impl_prompt,
        schema=impl_schema,
        role=f"Implementation Agent (Round {iteration})",
        model=impl_model
    )
    log(f"Implementation complete. Sandbox tests passed: {last_impl['tests_passed']}")

    phase(f"Iteration {iteration} - Independent Audit")
    log("Auditing implementation against acceptance criteria...")
    audit_prompt = f"""Audit this implementation:
Target File: {last_impl['target_file']}
Function Code:
{last_impl['function_code']}

Unit Tests:
{last_impl['unit_test_code']}

Verify:
1. All specification requirements are met.
2. Edge cases (empty input, unicode, type bounds, precision) are covered.
3. Accounting conservation is strictly respected.
4. Pytest suite tests the actual behaviors."""

    audit_res = await auditor(audit_prompt, auditor_schema)
    log(f"Audit Verdict (Round {iteration}): {audit_res['status']}")
    
    if audit_res["status"] == "APPROVED":
        approved = True
        log("Deliverable successfully certified by Auditor!")
        break
    else:
        feedback = audit_res["feedback"]
        log(f"Rejection Feedback: {feedback[:200]}...")

phase("Phase 4 - Final Review & Resource Accounting")
usage = tokens_used()
log(f"Total Workflow Execution Tokens: {usage}")

if approved:
    log("RESULT: WORKFLOW SUCCESS - Ready for integration into SALTBOR.")
    print("STATUS: SUCCESS")
else:
    log(f"RESULT: WORKFLOW FAILED - Reached maximum iterations ({max_iterations}) without auditor certification.")
    print("STATUS: FAILED_MAX_ITERATIONS")
