"""Comprehensive automated unit test suite for Saltbor Phase 0.6 Knowledge Architecture."""

import pytest
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.graph.engine import KnowledgeGraphEngine
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph, EpistemicClaim
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import (
    ProceduralKnowledgeGraph,
    ProcedureDefinition,
    ProcedureStep,
    AgentProceduralCompetency,
)
from saltbor.knowledge.layers.hypothesis_graph import (
    HypothesisDiscoveryGraph,
    Hypothesis,
    EvidenceItem,
)
from saltbor.knowledge.learning.pathways import LearningPathway, LearningProfile
from saltbor.knowledge.learning.learner import AutonomousLearningEngine
from saltbor.knowledge.transmission.engine import KnowledgeTransmissionEngine
from saltbor.knowledge.reasoning.rules import InferenceRule, RuleBasedInferenceEngine
from saltbor.knowledge.reasoning.causal import CausalReasoningEngine
from saltbor.knowledge.reasoning.compositional import CompositionalReasoningEngine
from saltbor.knowledge.reasoning.analogical import AnalogicalReasoningEngine
from saltbor.knowledge.reasoning.engine import InferenceEngine, ReasoningBudget
from saltbor.knowledge.experimentation.engine import ExperimentationEngine
from saltbor.knowledge.capabilities.composition import CapabilityCompositionSystem
from saltbor.knowledge.integration.memory_bridge import KnowledgeMemoryBridge
from saltbor.knowledge.integration.decision_bridge import KnowledgeDecisionBridge
from saltbor.cognition.planning.goap import ActionDefinition
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.knowledge.observability.inspector import KnowledgeObservability
from saltbor.knowledge.evaluation.intelligence import MultidimensionalIntelligenceEvaluator
from saltbor.knowledge.persistence import KnowledgeRepository
from saltbor.persistence.database import DatabaseManager


# ===========================================================================
# 1. Graph Core & Engine Tests
# ===========================================================================

def test_knowledge_graph_engine_crud_and_indexing():
    kg = KnowledgeGraphEngine("TestGraph")
    n1 = KnowledgeNode("n1", NodeType.CONCEPT, "Concept 1", properties={"val": 10})
    n2 = KnowledgeNode("n2", NodeType.MATERIAL, "Material 2")
    kg.add_node(n1)
    kg.add_node(n2)

    assert kg.node_count == 2
    assert kg.get_node("n1").label == "Concept 1"
    assert len(kg.get_nodes_by_type(NodeType.CONCEPT)) == 1

    rel = KnowledgeRelationship("r1", "n1", "n2", RelationshipType.PRODUCES, weight=2.0)
    kg.add_relationship(rel)

    assert kg.relationship_count == 1
    assert len(kg.get_out_relationships("n1")) == 1
    assert len(kg.get_in_relationships("n2")) == 1
    assert kg.get_neighbors("n1")[0].node_id == "n2"

    # Multi-hop traversal and shortest path
    n3 = KnowledgeNode("n3", NodeType.OBJECT, "Object 3")
    kg.add_node(n3)
    kg.add_relationship(KnowledgeRelationship("r2", "n2", "n3", RelationshipType.USED_FOR))

    traversals = kg.traverse_multi_hop("n1", max_depth=2)
    visited_ids = [t[0] for t in traversals]
    assert "n2" in visited_ids
    assert "n3" in visited_ids

    path = kg.find_shortest_path("n1", "n3")
    assert path is not None
    assert len(path) == 2

    # Subgraph extraction
    sub = kg.extract_subgraph("n2", radius=1)
    assert sub.has_node("n1") is True
    assert sub.has_node("n2") is True
    assert sub.has_node("n3") is True


# ===========================================================================
# 2. Multi-Layer Knowledge Representation Tests
# ===========================================================================

def test_global_vs_individual_bounded_epistemics():
    global_kg = GlobalKnowledgeGraph()
    global_kg.register_concept("secret_physics_law", "Quantum Mechanics", NodeType.SCIENTIFIC_PRINCIPLE)
    global_kg.register_concept("common_wood", "Pine Wood", NodeType.MATERIAL)

    agent_kg = IndividualKnowledgeGraph("agent_007", global_kg)
    # Agent learns common_wood but NOT secret_physics_law
    agent_kg.learn_concept("common_wood", confidence=0.8, tick=1)

    assert agent_kg.knows_concept("common_wood") is True
    assert agent_kg.knows_concept("secret_physics_law") is False
    assert agent_kg.get_concept("secret_physics_law") is None


def test_procedural_four_state_distinction():
    comp = AgentProceduralCompetency("proc_blacksmithing")
    # State 1: Knowing that it exists
    comp.knows_existence = True
    assert comp.can_perform is False

    # State 2: Knowing how it works
    comp.knows_mechanism = True
    assert comp.can_perform is False

    # State 3: Knowing how to perform it (procedure sequence)
    comp.knows_procedure = True
    assert comp.can_perform is True

    # State 4: Practical execution feasibility
    proc = ProcedureDefinition(
        procedure_id="proc_blacksmithing",
        name="Forge Iron Blade",
        domain="metallurgy",
        description="Heat, hammer, quench",
        prerequisite_concepts=["iron", "anvil"],
        required_skills={"blacksmithing": 0.50},
        required_tools=["anvil", "hammer"],
        input_materials={"iron": 2.0},
        output_products={"blade": 1.0},
        execution_steps=[],
    )

    # Missing tools and skills
    feasible, msg = comp.evaluate_execution_feasibility(
        agent_skills={"blacksmithing": 0.20},
        agent_inventory_items={"iron": 5.0, "hammer": 1.0},
        procedure=proc,
    )
    assert feasible is False
    assert "Insufficient skill" in msg


# ===========================================================================
# 3. Learning & Pedagogy Tests
# ===========================================================================

def test_autonomous_learning_engine_and_decay():
    profile = LearningProfile(learning_speed=1.2, memory_retention=0.80)
    learner = AutonomousLearningEngine(profile)
    graph = IndividualKnowledgeGraph("student_1")

    claim = learner.acquire_concept(graph, "basic_math", LearningPathway.TEACHING, tick=1)
    assert claim.confidence > 0.50
    assert graph.knows_concept("basic_math") is True

    # Check cognitive decay
    forgotten = graph.apply_decay(elapsed_ticks=20000, retention_rate=0.20)
    assert forgotten >= 1
    assert graph.knows_concept("basic_math") is False


def test_knowledge_transmission_engine():
    tx = KnowledgeTransmissionEngine()
    g_teacher = IndividualKnowledgeGraph("teacher_1")
    g_student = IndividualKnowledgeGraph("student_1")

    # Teacher does not know astronomy -> blocked!
    success, _, err = tx.teach_concept(g_teacher, g_student, "astronomy")
    assert success is False
    assert "does not know" in err

    # Teacher learns and transmits
    g_teacher.learn_concept("astronomy", confidence=0.90, source_pathway="direct_experience")
    success, rec, _ = tx.teach_concept(g_teacher, g_student, "astronomy", teacher_pedagogy_skill=0.8)
    assert success is True
    assert g_student.knows_concept("astronomy") is True
    assert rec.recipient_confidence_after > 0.5


# ===========================================================================
# 4. Reasoning & Inference Tests
# ===========================================================================

def test_rule_based_inference():
    rule_engine = RuleBasedInferenceEngine()
    rule = InferenceRule(
        rule_id="r_fire",
        name="Combustion Rule",
        antecedent_concept_ids=["dry_kindling", "spark"],
        required_relationships=[],
        consequent_node_generator=lambda g: KnowledgeNode("concept_fire", NodeType.CONCEPT, "Fire"),
        confidence_factor=0.90,
        explanation="Kindling plus spark yields fire",
    )
    rule_engine.register_rule(rule)

    graph = IndividualKnowledgeGraph("primitive_man")
    graph.learn_concept("dry_kindling", confidence=0.8)
    # Only 1 antecedent known -> No inference
    inferred = rule_engine.infer(graph)
    assert len(inferred) == 0

    # Learn spark -> Inferred!
    graph.learn_concept("spark", confidence=0.8)
    inferred = rule_engine.infer(graph)
    assert len(inferred) == 1
    assert graph.knows_concept("concept_fire") is True


def test_causal_reasoning_engine():
    causal = CausalReasoningEngine()
    graph = IndividualKnowledgeGraph("meteorologist")
    graph.learn_concept("drought", confidence=0.9)
    graph.learn_concept("crop_loss", confidence=0.9)
    graph.learn_concept("famine", confidence=0.9)

    rel1 = KnowledgeRelationship("r_c1", "drought", "crop_loss", RelationshipType.CAUSES, weight=0.9)
    rel2 = KnowledgeRelationship("r_c2", "crop_loss", "famine", RelationshipType.CAUSES, weight=0.8)
    graph.learn_relationship(rel1, confidence=0.85)
    graph.learn_relationship(rel2, confidence=0.80)

    chains = causal.trace_downstream_impacts(graph, root_cause_id="drought")
    assert len(chains) == 2
    famine_chain = next(c for c in chains if c.terminal_effect_id == "famine")
    assert famine_chain.hop_count == 2
    assert famine_chain.aggregate_confidence > 0.50


def test_analogical_reasoning_engine():
    analogical = AnalogicalReasoningEngine()
    hyp_graph = HypothesisDiscoveryGraph()
    graph = IndividualKnowledgeGraph("inventor")

    n1 = KnowledgeNode("concept_salted_meat", NodeType.OBJECT, "Salted Pork", properties={"preserves": True, "organic": True})
    n2 = KnowledgeNode("concept_timber_logs", NodeType.OBJECT, "Oak Timber", properties={"organic": True})
    graph.register_local_node(n1, confidence=0.9)
    graph.register_local_node(n2, confidence=0.9)

    mapping = analogical.perform_analogical_transfer(
        graph=graph,
        hypothesis_graph=hyp_graph,
        source_concept_id="concept_salted_meat",
        target_concept_id="concept_timber_logs",
    )
    assert mapping is not None
    assert mapping.structural_similarity_score > 0.0
    assert mapping.generated_hypothesis.status == ValidationStatus.PROPOSED


# ===========================================================================
# 5. Integration, Decision & Memory Tests
# ===========================================================================

def test_knowledge_decision_bridge_action_filtering():
    bridge = KnowledgeDecisionBridge()
    graph = IndividualKnowledgeGraph("adventurer")
    graph.learn_concept("skill_swimming", confidence=0.8)

    act1 = ActionDefinition("act_cross_river", "Swim River", preconditions={}, effects={}, required_capabilities=["skill_swimming"])
    act2 = ActionDefinition("act_fly_air", "Hang Glider", preconditions={}, effects={}, required_capabilities=["skill_aerodynamics"])

    exec_acts, blocked = bridge.filter_executable_actions([act1, act2], graph)
    assert len(exec_acts) == 1
    assert exec_acts[0].action_id == "act_cross_river"
    assert len(blocked) == 1
    assert blocked[0][0].action_id == "act_fly_air"

    # Formulate epistemic goal
    options = bridge.formulate_epistemic_inquiry_goals(blocked, graph, known_experts={"skill_aerodynamics": "expert_leonardo"})
    assert len(options) == 1
    assert options[0].suggested_strategy == "seek_mentor"
    assert options[0].target_expert_uid == "expert_leonardo"


def test_knowledge_memory_bridge():
    bridge = KnowledgeMemoryBridge()
    mem = MemoryEngine()
    bridge.sync_concept_to_semantic_memory("c1", "Concept One", 0.9, "observation", mem, tick=1)
    fact = mem.semantic.get("fact_c1")
    assert fact is not None
    assert fact.confidence == 0.9

    bridge.record_learning_episode(mem, "Learned pottery today", 0.7, tick=5)
    assert len(mem.episodic.get_all(include_dormant=True)) == 1


# ===========================================================================
# 6. Observability & Multidimensional Evaluation Tests
# ===========================================================================

def test_observability_and_multidimensional_evaluation():
    graph = IndividualKnowledgeGraph("scholar_1")
    graph.learn_concept("logic", confidence=0.95)
    graph.learn_concept("history", confidence=0.85)

    profile = LearningProfile(learning_speed=1.1, analytical_reasoning=0.85, curiosity=0.80)
    report = MultidimensionalIntelligenceEvaluator.evaluate_individual(graph, profile)

    assert report.logical_reasoning == 0.85
    assert report.learning_speed == 1.1
    assert report.reasoning_ability_score > 0.7
    assert report.knowledge_quantity_score > 0.0

    # Observability profile
    obs_profile = KnowledgeObservability.inspect_individual(graph)
    assert obs_profile.known_concepts_count == 2
    assert obs_profile.mean_confidence > 0.85
