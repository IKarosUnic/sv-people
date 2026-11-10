"""
Phase 0.7 Advanced Reasoning, General Problem Solving & Metacognition Unit Tests.

Covers:
- Epistemic Interface & Contradiction Detection
- Deductive Reasoning Engine (Modus Tollens, Transitive Syllogisms)
- Inductive Reasoning Engine (Pattern Extraction & Adaptation)
- Abductive Reasoning Engine (Hypothesis Ranking & Discriminant Testing)
- Causal Reasoning Engine (Confounders & Multi-hop Paths)
- Analogical Reasoning Engine (Schema Mapping & Contextual Caveats)
- Counterfactual Reasoning Engine (Episodic Segregation & Regret/Relief)
- Hypothetical Reasoning Engine (Future Projection & Post-facto Verification)
- General Problem Solving Engine (14-Step Problem Solving Trace)
- Metacognitive Self-Audit (K/U/B/R/S) & Calibrated Confidence
- Creative Combination Engine (7-Stage Progression & Feasibility Gates)
- Curiosity & Exploration Engine (Physical, Social, Intellectual Drivers)
- Functional Cognitive Brain Architecture Deliberation
- GOAP Epistemic Bounded Planning
"""

import pytest
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.cognition.epistemic.beliefs import EpistemicBelief, BeliefType
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.reasoning.deductive import DeductiveReasoningEngine
from saltbor.cognition.reasoning.inductive import InductiveReasoningEngine
from saltbor.cognition.reasoning.abductive import AbductiveReasoningEngine, ExplanationHypothesis
from saltbor.cognition.reasoning.causal import (
    AdvancedCausalReasoningEngine,
    CausalLink,
    CausalRelationStatus,
)
from saltbor.cognition.reasoning.analogical import AdvancedAnalogicalReasoningEngine
from saltbor.cognition.reasoning.counterfactual import CounterfactualReasoningEngine
from saltbor.cognition.reasoning.hypothetical import HypotheticalReasoningEngine
from saltbor.cognition.reasoning.engine import AdvancedReasoningEngine
from saltbor.cognition.problem_solving.problem import Problem, StrategyType, ProblemOutcome
from saltbor.cognition.problem_solving.engine import ProblemSolvingEngine
from saltbor.cognition.metacognition.self_audit import MetacognitiveAuditor
from saltbor.cognition.metacognition.confidence import CalibratedConfidenceEstimator
from saltbor.cognition.creativity.engine import CreativeCombinationEngine, InnovationStage
from saltbor.cognition.curiosity.engine import CuriosityEngine, ExplorationModality
from saltbor.cognition.architecture.brain import CognitiveBrainArchitecture
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.autonomy.engine import AutonomyEngine
from saltbor.cognition.planning.goap import GOAPPlanner, ActionDefinition, WorldState


def test_epistemic_interface_and_contradictions():
    """Verify epistemic interface manages beliefs, detects contradictions, and evaluates sources."""
    kg = IndividualKnowledgeGraph(human_uid="agent_epistemic_01")
    interface = EpistemicInterface(human_uid="agent_epistemic_01", knowledge_graph=kg)

    # Add contradictory beliefs
    b1 = EpistemicBelief(
        belief_id="bel_01",
        subject="well_water",
        predicate="quality",
        object_val="safe",
        belief_type=BeliefType.TESTIMONY,
        confidence=0.8,
        source_type="testimony",
        evidence_items=["merchant_bob said so"],
    )
    b2 = EpistemicBelief(
        belief_id="bel_02",
        subject="well_water",
        predicate="quality",
        object_val="contaminated",
        belief_type=BeliefType.OBSERVED_FACT,
        confidence=0.9,
        source_type="observation",
        evidence_items=["direct observation of sickness"],
    )
    interface.register_belief(b1)
    interface.register_belief(b2)

    # Detect contradictions
    contradictions = interface.detect_contradictions()
    assert len(contradictions) >= 1
    c = contradictions[0]
    assert c["subject"] == "well_water"

    # Source credibility
    cred = interface.evaluate_source_reliability("testimony")
    assert 0.0 <= cred <= 1.0

    # Missing info
    missing = interface.identify_missing_information(
        required_elements=["grain_storage_temperature", "pest_control"]
    )
    assert "pest_control" in missing
    assert "grain_storage_temperature" in missing


def test_deductive_reasoning_engine():
    """Test Deductive Reasoning Engine with Modus Tollens and transitive syllogisms."""
    engine = DeductiveReasoningEngine()
    kg = IndividualKnowledgeGraph(human_uid="agent_deduct_01")

    # Register concepts & dependencies
    kg.learn_concept(node_id="wheat_bread", confidence=0.9)
    kg.learn_concept(node_id="flour", confidence=0.9)
    kg.learn_concept(node_id="grain", confidence=0.9)

    kg.learn_relationship(
        KnowledgeRelationship(
            rel_id="rel_bread_flour",
            source_id="wheat_bread",
            target_id="flour",
            rel_type=RelationshipType.REQUIRES,
        ),
        confidence=0.95,
    )
    kg.learn_relationship(
        KnowledgeRelationship(
            rel_id="rel_flour_grain",
            source_id="flour",
            target_id="grain",
            rel_type=RelationshipType.REQUIRES,
        ),
        confidence=0.95,
    )

    # Modus Tollens: Agent wants to produce bread, but inventory lacks flour
    context_prod = {
        "target_product": "wheat_bread",
        "required_material": "flour",
        "required_quantity": 2.0,
        "inventory": {"flour": 0.0},
    }
    traces = engine.deduce(kg, context=context_prod)
    assert len(traces) >= 1
    t = traces[0]
    assert t.is_negation is True
    assert "cannot craft" in t.conclusion_statement.lower()

    # Transitive Syllogism: wheat_bread -> flour -> grain
    context_trans = {"target_concept": "wheat_bread"}
    traces_trans = engine.deduce(kg, context=context_trans)
    assert any("transitive" in tr.rule_name.lower() for tr in traces_trans)


def test_inductive_reasoning_engine():
    """Test Inductive Reasoning Engine: sample size uncertainty and counter-evidence degradation."""
    engine = InductiveReasoningEngine(regularizer_k=3.0, min_observations=2)

    # 3 observations of high bread demand on Saturday
    for _ in range(3):
        engine.record_observation(condition="market_day==Saturday", outcome="high_sales")

    patterns = engine.evaluate_expectation(condition="market_day==Saturday", min_confidence=0.1)
    assert len(patterns) >= 1
    pat = patterns[0]
    assert pat.total_observations == 3
    # Uncertainty is preserved due to small sample size
    initial_conf = pat.confidence
    assert initial_conf < 0.85

    # Add 10 more positive observations
    for _ in range(10):
        pat.update_with_observation("high_sales")
    assert pat.confidence > initial_conf
    peak_conf = pat.confidence

    # Add counter-evidence (degradation)
    for _ in range(15):
        pat.update_with_observation("low_sales")
    assert pat.confidence < peak_conf


def test_abductive_reasoning_engine():
    """Test Abductive Reasoning: ranking candidate explanations and applying discriminant tests."""
    engine = AbductiveReasoningEngine()

    hyps = engine.generate_explanations(anomaly_key="decrease_in_customers")
    assert len(hyps) >= 3

    ranked = engine.compare_and_rank(hyps)
    initial_top = ranked[0]
    initial_top_score = initial_top.composite_score

    # Apply discriminant test: new competition confirmed
    differentiated = engine.differentiate_with_evidence(
        hypotheses=hyps,
        tested_cause="new_competition",
        evidence_found="New merchant stall opened selling identical pottery",
        supports_cause=True,
    )
    final_top = differentiated[0]
    assert final_top.candidate_cause == "new_competition"
    assert final_top.composite_score > initial_top_score


def test_causal_reasoning_engine():
    """Test Causal Reasoning: distinguish correlation vs causation, multi-hop tracing, confounders."""
    engine = AdvancedCausalReasoningEngine()

    # Heat -> Ice cream; Heat -> Drownings
    link1 = CausalLink(
        cause_id="summer_heat",
        effect_id="ice_cream_sales",
        status=CausalRelationStatus.EVIDENCE_BACKED,
        confidence=0.85,
        strength=0.8,
        mechanism_description="Hot weather stimulates cold food purchases",
    )
    link2 = CausalLink(
        cause_id="summer_heat",
        effect_id="river_drownings",
        status=CausalRelationStatus.EVIDENCE_BACKED,
        confidence=0.80,
        strength=0.7,
        mechanism_description="Hot weather increases swimming volume",
    )
    engine.register_link(link1)
    engine.register_link(link2)

    # Confounder detection
    confounder = engine.identify_confounder("ice_cream_sales", "river_drownings")
    assert confounder == "summer_heat"

    # Evaluate co-occurrence without mechanism
    evaluated = engine.evaluate_causality_vs_correlation(
        "ice_cream_sales", "river_drownings", co_occurrence_count=12
    )
    assert evaluated.status == CausalRelationStatus.CONFOUNDED

    # Multi-hop trace: drought -> crop_failure -> bread_shortage
    engine.register_link(
        CausalLink(
            cause_id="drought",
            effect_id="crop_failure",
            status=CausalRelationStatus.EVIDENCE_BACKED,
            confidence=0.9,
            strength=0.85,
            mechanism_description="Water deficit kills crops",
        )
    )
    engine.register_link(
        CausalLink(
            cause_id="crop_failure",
            effect_id="bread_shortage",
            status=CausalRelationStatus.EVIDENCE_BACKED,
            confidence=0.85,
            strength=0.8,
            mechanism_description="Grain deficit stops flour mills",
        )
    )
    paths = engine.trace_impacts("drought")
    shortage_path = next((p for p in paths if p.target_effect_id == "bread_shortage"), None)
    assert shortage_path is not None
    assert shortage_path.hop_count == 2
    assert shortage_path.is_purely_causal is True


def test_analogical_reasoning_engine():
    """Test Analogical Reasoning: structural mapping and boundary caveats."""
    engine = AdvancedAnalogicalReasoningEngine()

    transfer = engine.transfer_knowledge(
        source_domain_id="business_management",
        target_domain_id="household_management",
    )
    assert transfer is not None
    assert transfer.structural_similarity >= 0.5
    assert len(transfer.transferred_principles) >= 1
    # Domain differences must be acknowledged
    assert len(transfer.context_caveats) >= 1


def test_counterfactual_reasoning_engine():
    """Test Counterfactual Reasoning: evaluating past alternative decisions without memory pollution."""
    engine = CounterfactualReasoningEngine()

    eval_result = engine.evaluate_counterfactual(
        event_description="Grain market trading",
        actual_decision="sold_all_wheat_early",
        actual_outcome="earned 10 silver coins",
        actual_utility=10.0,
        counterfactual_alternative="held_grain_and_set_higher_price",
        domain_model={"price_change_factor": 1.4, "demand_elasticity": -0.3},
    )

    assert eval_result.utility_delta != 0.0
    assert eval_result.emotional_impact in ["regret", "relief", "indifference"]
    assert eval_result.is_counterfactual_flag is True
    assert eval_result.learning_insight != ""


def test_hypothetical_reasoning_engine():
    """Test Hypothetical Reasoning: projecting forward scenarios and checking post-facto."""
    engine = HypotheticalReasoningEngine()

    scenario = engine.formulate_scenario(
        condition_action="hire_apprentice_smith",
        predicted_consequence="increase_forge_production_by_50_percent",
        assumptions=["sufficient_charcoal_stocks", "raw_iron_available"],
        confidence=0.65,
        expected_utility_delta=15.0,
    )
    assert scenario.evaluation_status == "pending"

    # Resolve post-facto with actual outcome
    resolved = engine.resolve_scenario(
        scenario_id=scenario.scenario_id,
        actual_outcome="production output expanded by 55%",
        is_confirmed=True,
    )
    assert resolved is not None
    assert resolved.evaluation_status == "confirmed"
    assert resolved.confidence > 0.65


def test_problem_solving_engine_14_steps():
    """Verify General Problem Solving Engine executes all 14 steps."""
    engine = ProblemSolvingEngine()
    kg = IndividualKnowledgeGraph(human_uid="solver_agent_01")
    kg.learn_concept(node_id="forestry", confidence=0.8)

    problem = Problem(
        problem_id="prob_fuel_exhaustion",
        description="Gather Winter Firewood",
        domain="survival",
        current_state={"firewood": 0.0},
        desired_state={"firewood": 10.0},
        required_capabilities=["forestry"],
        required_materials={},
        constraints={"daylight_hours": 8.0},
        urgency=0.7,
        difficulty=0.5,
    )

    outcome, trace = engine.solve(
        problem=problem,
        graph=kg,
        agent_skills={"forestry": 0.7},
        agent_inventory={"axe": 1.0},
    )

    assert len(trace.steps_executed) == 14
    assert trace.problem_id == "prob_fuel_exhaustion"
    assert outcome in [
        ProblemOutcome.SOLVED,
        ProblemOutcome.PARTIALLY_SOLVED,
        ProblemOutcome.ASSISTANCE_REQUESTED,
        ProblemOutcome.FAILED,
        ProblemOutcome.INSUFFICIENT_CAPABILITY,
    ]


def test_metacognitive_self_audit_and_confidence():
    """Verify Metacognitive self-audit computes K/U/B/R/S and penalizes overconfidence."""
    kg = IndividualKnowledgeGraph(human_uid="meta_agent_01")
    kg.learn_concept(node_id="foraging", confidence=0.8)

    profile = MetacognitiveAuditor.audit(
        graph=kg,
        skills={"foraging": 0.8},
        active_goal_requirements=["foraging", "blacksmithing"],
    )

    assert profile.known_concepts_count >= 1
    assert "blacksmithing" in profile.needed_skills
    assert 0.0 <= profile.self_efficacy_score <= 1.0

    # Calibrated confidence estimator
    audit_high = CalibratedConfidenceEstimator.estimate(
        pathway="direct_experience",
        verification_count=3,
        supporting_evidence_count=2,
        contradiction_count=0,
    )
    assert audit_high.calibrated_confidence > 0.80

    audit_low = CalibratedConfidenceEstimator.estimate(
        pathway="rumor",
        verification_count=0,
        supporting_evidence_count=0,
        contradiction_count=1,
    )
    assert audit_low.calibrated_confidence < 0.45


def test_creative_combination_engine():
    """Verify Creative Combination Engine 7-stage lifecycle and physical feasibility checks."""
    engine = CreativeCombinationEngine()
    kg = IndividualKnowledgeGraph(human_uid="creator_01")
    kg.learn_concept(node_id="leather", confidence=0.8)
    kg.learn_concept(node_id="wax", confidence=0.8)

    # Valid combination
    innov = engine.synthesize_cross_domain_innovation(
        creator_uid="creator_01",
        name="Waxed Leather Boots",
        description="Waterproof protective boots treated with apicultural beeswax",
        domains=["leatherworking", "apiculture"],
        concepts=["leather", "wax"],
        required_skills={"leatherworking": 0.5, "apiculture": 0.3},
        required_materials={"leather": 2.0, "wax": 1.0},
        required_tools=["awl"],
        graph=kg,
        agent_skills={"leatherworking": 0.5, "apiculture": 0.3},
    )
    assert innov is not None
    assert innov.stage == InnovationStage.IDEA
    assert innov.is_physically_sound is True

    # Advance through stages
    skills = {"leatherworking": 0.6, "apiculture": 0.4}
    inventory = {"awl": 1.0, "leather": 5.0, "wax": 5.0}

    # IDEA -> HYPOTHESIS
    ok, stage, _ = engine.advance_stage(innov, skills, inventory)
    assert ok and stage == InnovationStage.HYPOTHESIS

    # HYPOTHESIS -> DESIGN
    ok, stage, _ = engine.advance_stage(innov, skills, inventory)
    assert ok and stage == InnovationStage.DESIGN

    # DESIGN -> PROTOTYPE (consumes materials)
    ok, stage, _ = engine.advance_stage(innov, skills, inventory)
    assert ok and stage == InnovationStage.PROTOTYPE

    # PROTOTYPE -> EXPERIMENTATION
    ok, stage, _ = engine.advance_stage(innov, skills, inventory)
    assert ok and stage == InnovationStage.EXPERIMENTATION

    # EXPERIMENTATION -> FUNCTIONAL_SOLUTION (spends labor)
    ok, stage, _ = engine.advance_stage(innov, skills, inventory, labor_ticks_spent=innov.labor_ticks_required)
    assert ok and stage == InnovationStage.FUNCTIONAL_SOLUTION

    # FUNCTIONAL_SOLUTION -> VALIDATED_INNOVATION
    ok, stage, _ = engine.advance_stage(innov, skills, inventory)
    assert ok and stage == InnovationStage.VALIDATED_INNOVATION

    # Physically impossible combination
    impossible = engine.synthesize_cross_domain_innovation(
        creator_uid="creator_01",
        name="Perpetual Energy Wheel",
        description="Perpetual motion device with zero_fuel_engine",
        domains=["mechanics"],
        concepts=["leather"],
        required_skills={"leatherworking": 0.5},
        required_materials={},
        required_tools=[],
        graph=kg,
        agent_skills={"leatherworking": 0.5},
    )
    assert impossible.is_physically_sound is False


def test_curiosity_and_exploration_engine():
    """Verify Curiosity Engine modulates exploration by personality and needs."""
    curiosity = CuriosityEngine()
    personality = PersonalityEngine()
    emotions = EmotionalEngine()

    drive = curiosity.calculate_curiosity_drive(personality, emotions, energy=0.9, hunger=0.1)
    assert 0.0 < drive <= 1.0

    # Starving/exhausted agent
    drive_deprived = curiosity.calculate_curiosity_drive(personality, emotions, energy=0.1, hunger=0.9)
    assert drive_deprived < drive

    targets = curiosity.find_exploration_targets(
        graph=None,
        unvisited_locations=["misty_canyon"],
        known_unmet_peers=[{"uid": "stranger_01", "name": "Boran", "profession": "Stonemason"}],
        unexplained_anomalies=["luminous_cave_moss"],
    )
    assert len(targets) == 3

    selected = curiosity.select_exploration_target(targets, curiosity_drive=0.8, risk_tolerance=0.6)
    assert selected is not None


def test_cognitive_brain_architecture_deliberation():
    """Verify functional cognitive brain integrates fronto-limbic-hippocampal systems."""
    personality = PersonalityEngine()
    emotions = EmotionalEngine()
    memory = MemoryEngine()
    autonomy = AutonomyEngine()
    kg = IndividualKnowledgeGraph(human_uid="brain_01")
    epistemic = EpistemicInterface(human_uid="brain_01", knowledge_graph=kg)
    reasoning = AdvancedReasoningEngine()
    solver = ProblemSolvingEngine(reasoning=reasoning)

    brain = CognitiveBrainArchitecture(
        human_uid="brain_01",
        personality=personality,
        emotions=emotions,
        memory=memory,
        autonomy=autonomy,
        knowledge_graph=kg,
        epistemic=epistemic,
        reasoning=reasoning,
        problem_solver=solver,
    )

    outcome = brain.deliberate(
        current_location_id="home",
        available_candidate_actions=[
            {
                "action_name": "gather_herbs",
                "target_location": "meadow",
                "domain": "foraging",
            }
        ],
        current_tick=1,
    )

    assert outcome is not None
    assert outcome.action_name == "gather_herbs"
    assert outcome.reasoning_summary != ""


def test_goap_epistemic_bounds():
    """Verify GOAP planner validates epistemic bounds before planning."""
    planner = GOAPPlanner(
        available_actions=[
            ActionDefinition(
                action_id="forge_plow",
                name="Forge Iron Plow",
                preconditions={"has_iron": True},
                effects={"has_plow": True},
                required_capabilities=["master_blacksmithing"],
            )
        ]
    )

    kg = IndividualKnowledgeGraph(human_uid="planner_agent")

    # Agent lacks required knowledge
    plan, learned = planner.plan_with_epistemic_bounds(
        initial_state=WorldState({"has_iron": True}),
        goal_conditions={"has_plow": True},
        knowledge_graph=kg,
        allow_epistemic_learning=True,
    )
    assert "master_blacksmithing" in learned
    assert any(a.action_id == "learn_master_blacksmithing" for a in plan)
