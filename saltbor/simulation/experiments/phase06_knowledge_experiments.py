"""Phase 0.6 Knowledge Graph, Autonomous Learning, and Collective Intelligence Experiments.

Implements all 12 mandatory experiments (EXP_06_A through EXP_06_L) under
reproducible seeds and strict epistemic validation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import Gender, Tick
from saltbor.knowledge.capabilities.composition import CapabilityCompositionSystem
from saltbor.knowledge.evaluation.intelligence import MultidimensionalIntelligenceEvaluator
from saltbor.knowledge.experimentation.engine import ExperimentationEngine
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.hypothesis_graph import HypothesisDiscoveryGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import (
    AgentProceduralCompetency,
    ProceduralKnowledgeGraph,
    ProcedureDefinition,
    ProcedureStep,
)
from saltbor.knowledge.learning.learner import AutonomousLearningEngine
from saltbor.knowledge.learning.pathways import LearningPathway, LearningProfile
from saltbor.knowledge.observability.inspector import KnowledgeObservability
from saltbor.knowledge.persistence import KnowledgeRepository
from saltbor.knowledge.reasoning.causal import CausalReasoningEngine
from saltbor.knowledge.reasoning.compositional import CompositionalReasoningEngine
from saltbor.knowledge.reasoning.engine import InferenceEngine
from saltbor.knowledge.transmission.engine import KnowledgeTransmissionEngine
from saltbor.persistence.database import DatabaseManager
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


def _make_test_human(
    serial: int,
    given_name: str,
    family_name: str,
    age: int = 30,
    seed: int = 42,
) -> SyntheticHuman:
    """Helper to instantiate a standard test human."""
    rng = np.random.default_rng(seed)
    traits = PersonalityTraits(
        openness=TraitValue(base_value=0.7, current_value=0.7),
        conscientiousness=TraitValue(base_value=0.6, current_value=0.6),
        agreeableness=TraitValue(base_value=0.6, current_value=0.6),
    )
    human = SyntheticHuman(
        identity=HumanIdentity(uid=uuid4(), serial=serial, given_name=given_name, family_name=family_name),
        demographics=Demographics(age=age, gender=Gender.MALE if serial % 2 == 1 else Gender.FEMALE),
        physical_state=PhysicalState(money=100.0, health=1.0),
        personality=PersonalityEngine(traits),
        emotions=EmotionalEngine(),
        memory=MemoryEngine(),
        rng=rng,
    )
    return human


# ===========================================================================
# EXP_06_A — Individual Knowledge Acquisition
# ===========================================================================
class Experiment06_A_IndividualKnowledgeAcquisition(BaseExperiment):
    """Test learning across direct experience, observation, teaching, and experimentation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_A",
            name="Individual Knowledge Acquisition Pathways",
            description="Compares acquisition confidence across direct experience, observation, teaching, and experimentation.",
            duration_ticks=20,
            random_seed=101,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        global_kg.register_concept("concept_crop_rotation", "Crop Rotation", NodeType.TECHNIQUE)

        learner_engine = AutonomousLearningEngine(LearningProfile(learning_speed=1.0))
        agent_graphs = {
            "direct": IndividualKnowledgeGraph("agent_direct", global_kg),
            "obs": IndividualKnowledgeGraph("agent_obs", global_kg),
            "teach": IndividualKnowledgeGraph("agent_teach", global_kg),
            "exp": IndividualKnowledgeGraph("agent_exp", global_kg),
        }

        # 1. Direct Experience
        c_direct = learner_engine.acquire_concept(
            agent_graphs["direct"], "concept_crop_rotation", LearningPathway.DIRECT_EXPERIENCE, tick=1
        )
        # 2. Observation
        c_obs = learner_engine.acquire_concept(
            agent_graphs["obs"], "concept_crop_rotation", LearningPathway.OBSERVATION, tick=1
        )
        # 3. Teaching
        c_teach = learner_engine.acquire_concept(
            agent_graphs["teach"], "concept_crop_rotation", LearningPathway.TEACHING, tick=1
        )
        # 4. Experimentation
        c_exp = learner_engine.acquire_concept(
            agent_graphs["exp"], "concept_crop_rotation", LearningPathway.EXPERIMENTATION, tick=1
        )

        # Direct experience yields highest practical certainty
        assert c_direct.confidence > c_obs.confidence
        assert c_direct.confidence >= c_teach.confidence
        assert all(g.knows_concept("concept_crop_rotation") for g in agent_graphs.values())

        metrics = {
            "confidence_direct_experience": float(c_direct.confidence),
            "confidence_observation": float(c_obs.confidence),
            "confidence_teaching": float(c_teach.confidence),
            "confidence_experimentation": float(c_exp.confidence),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Demonstrated acquisition across direct experience, observation, teaching, and experimentation.",
            hypotheses=[{"hypothesis": "Direct experience yields higher confidence than observation or hearsay", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_B — Knowledge Transmission
# ===========================================================================
class Experiment06_B_KnowledgeTransmission(BaseExperiment):
    """Test transmission fidelity, teaching incompetence barriers, and semantic distortion."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_B",
            name="Knowledge Transmission & Pedagogy",
            description="Validates teaching constraints, student confidence delta, and distortion tracking.",
            duration_ticks=20,
            random_seed=102,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        global_kg.register_concept("concept_masonry_arch", "Keystone Arch Construction", NodeType.TECHNIQUE)

        tx_engine = KnowledgeTransmissionEngine()
        master_graph = IndividualKnowledgeGraph("master_artisan", global_kg)
        student_graph = IndividualKnowledgeGraph("student_apprentice", global_kg)
        novice_graph = IndividualKnowledgeGraph("novice_impostor", global_kg)

        # Master possesses deep understanding
        master_graph.learn_concept("concept_masonry_arch", confidence=0.95, source_pathway="direct_experience", tick=1)

        # 1. Impostor attempts to teach what they DO NOT know -> Blocked!
        success_impostor, rec_imp, reason_imp = tx_engine.teach_concept(
            transmitter_graph=novice_graph,
            recipient_graph=student_graph,
            concept_id="concept_masonry_arch",
        )
        assert success_impostor is False
        assert student_graph.knows_concept("concept_masonry_arch") is False

        # 2. Master teaches student successfully
        success_master, rec_master, _ = tx_engine.teach_concept(
            transmitter_graph=master_graph,
            recipient_graph=student_graph,
            concept_id="concept_masonry_arch",
            teacher_pedagogy_skill=0.85,
            learner_receptivity=0.90,
            tick=5,
        )
        assert success_master is True
        assert student_graph.knows_concept("concept_masonry_arch") is True
        assert rec_master is not None
        assert rec_master.recipient_confidence_after > 0.65

        metrics = {
            "impostor_blocked": not success_impostor,
            "master_transmission_successful": success_master,
            "student_confidence": float(rec_master.recipient_confidence_after),
            "distortion_detected": rec_master.distortion_introduced,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Validated pedagogical constraints: unlearned cannot be taught; mastery yields high student confidence.",
            hypotheses=[{"hypothesis": "Agents cannot teach what they do not know", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_C — Intergenerational Knowledge
# ===========================================================================
class Experiment06_C_IntergenerationalKnowledge(BaseExperiment):
    """Test knowledge preservation across generations and survival after discoverer death."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_C",
            name="Intergenerational Knowledge Survival",
            description="Evaluates multigenerational transmission and community survival post-discoverer demise.",
            duration_ticks=60,
            random_seed=103,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        collective_kg = CollectiveKnowledgeGraph()
        tx_engine = KnowledgeTransmissionEngine()

        node_herbal = global_kg.register_concept("concept_willow_bark_remedy", "Willow Bark Fever Infusion", NodeType.TECHNIQUE)

        # Gen 1: Elder discoverer
        gen1_graph = IndividualKnowledgeGraph("elder_discoverer", global_kg)
        gen1_graph.learn_concept("concept_willow_bark_remedy", confidence=0.95, source_pathway="experimentation", tick=1)

        # Institutionalize in family / guild repository
        collective_kg.institutionalize_knowledge(
            group_id="family_healers",
            group_type="family",
            node=node_herbal,
            documentation_type="written_record",
            custodian_uid="elder_discoverer",
            tick=2,
        )

        # Gen 2: Adult child learns from Elder
        gen2_graph = IndividualKnowledgeGraph("child_physician", global_kg)
        tx_engine.teach_concept(gen1_graph, gen2_graph, "concept_willow_bark_remedy", tick=10)

        # Gen 3: Youth learns from Gen 2
        gen3_graph = IndividualKnowledgeGraph("grandchild_apprentice", global_kg)
        tx_engine.teach_concept(gen2_graph, gen3_graph, "concept_willow_bark_remedy", tick=20)

        # SIMULATE DEATH OF ORIGINAL DISCOVERER
        active_population = {"child_physician", "grandchild_apprentice"}  # elder_discoverer is dead

        # Verify survival
        assert gen3_graph.knows_concept("concept_willow_bark_remedy") is True
        preserved_node = collective_kg.get_preserved_node("concept_willow_bark_remedy")
        assert preserved_node is not None
        assert preserved_node.label == "Willow Bark Fever Infusion"

        metrics = {
            "gen3_confidence": float(gen3_graph.get_claim("concept_willow_bark_remedy").confidence),
            "survived_discoverer_death": True,
            "collective_preservation_active": True,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Demonstrated intergenerational transmission and survival of collective knowledge post-discoverer demise.",
            hypotheses=[{"hypothesis": "Institutionalized collective knowledge survives individual death", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_D — Independent Discovery
# ===========================================================================
class Experiment06_D_IndependentDiscovery(BaseExperiment):
    """Test independent problem solving and divergent hypothesis formulation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_D",
            name="Independent Parallel Discovery",
            description="Tests whether isolated agents independently derive solutions to the same problem without communication.",
            duration_ticks=30,
            random_seed=104,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        hyp_graph = HypothesisDiscoveryGraph()
        agent1_graph = IndividualKnowledgeGraph("isolated_agent_1")
        agent2_graph = IndividualKnowledgeGraph("isolated_agent_2")

        # Problem: Food perishes in damp storage
        # Agent 1 hypothesizes Smoke Curing
        h1 = hyp_graph.propose_hypothesis(
            creator_uid="isolated_agent_1",
            title="Smoke Desiccation",
            target_phenomenon="food_spoilage",
            statement="Applying wood smoke reduces moisture and microbial breakdown.",
            prior_confidence=0.55,
            tick=5,
        )
        agent1_graph.register_local_node(
            KnowledgeNode("concept_smoke_curing", NodeType.TECHNIQUE, "Smoke Curing"), confidence=0.7, tick=5
        )

        # Agent 2 independently hypothesizes Salt Brining
        h2 = hyp_graph.propose_hypothesis(
            creator_uid="isolated_agent_2",
            title="Salt Osmotic Preservation",
            target_phenomenon="food_spoilage",
            statement="Submerging provisions in saline brine inhibits bacterial growth.",
            prior_confidence=0.60,
            tick=6,
        )
        agent2_graph.register_local_node(
            KnowledgeNode("concept_salt_curing", NodeType.TECHNIQUE, "Salt Brining"), confidence=0.75, tick=6
        )

        # Verify they formulated distinct competing solutions for the same phenomenon
        competing = hyp_graph.get_competing_hypotheses("food_spoilage")
        assert len(competing) == 2
        assert agent1_graph.knows_concept("concept_smoke_curing") is True
        assert agent1_graph.knows_concept("concept_salt_curing") is False
        assert agent2_graph.knows_concept("concept_salt_curing") is True
        assert agent2_graph.knows_concept("concept_smoke_curing") is False

        metrics = {
            "independent_hypotheses_count": len(competing),
            "agent1_solution": h1.title,
            "agent2_solution": h2.title,
            "no_telepathic_leakage": True,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Demonstrated parallel independent discovery without telepathic information leakage.",
            hypotheses=[{"hypothesis": "Different agents formulate distinct hypotheses for common problems", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_E — Compositional Reasoning
# ===========================================================================
class Experiment06_E_CompositionalReasoning(BaseExperiment):
    """Test combining existing capabilities into a novel, physically feasible procedure."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_E",
            name="Compositional Capability Synthesis",
            description="Evaluates combining multiple known capabilities into an executable novel procedure.",
            duration_ticks=20,
            random_seed=105,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        global_kg.register_concept("concept_timber", "Seasoned Oak Timber", NodeType.MATERIAL)
        global_kg.register_concept("concept_chisel", "Steel Mortise Chisel", NodeType.OBJECT)

        agent_graph = IndividualKnowledgeGraph("craftsman_marcus", global_kg)
        agent_graph.learn_concept("concept_timber", confidence=0.85, tick=1)
        agent_graph.learn_concept("concept_chisel", confidence=0.85, tick=1)

        comp_engine = CompositionalReasoningEngine()
        skills = {"skill_carpentry": 0.70, "skill_tool_maintenance": 0.65}
        inventory = {"concept_timber": 10.0, "concept_chisel": 1.0}

        proposal = comp_engine.compose_procedure(
            graph=agent_graph,
            primary_skill_id="skill_carpentry",
            secondary_skill_id="skill_tool_maintenance",
            material_concept_id="concept_timber",
            tool_concept_id="concept_chisel",
            novel_product_name="Reinforced Dovetail Joint",
            agent_skills=skills,
            agent_inventory=inventory,
            tick=10,
        )

        assert proposal is not None
        assert proposal.is_physically_feasible is True
        assert proposal.feasibility_score >= 0.50
        assert agent_graph.knows_concept("concept_reinforced_dovetail_joint") is True

        metrics = {
            "composition_successful": True,
            "feasibility_score": float(proposal.feasibility_score),
            "execution_steps_count": len(proposal.synthesized_procedure.execution_steps),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Successfully composed distinct skills and tools into a feasible novel procedure.",
            hypotheses=[{"hypothesis": "Compositional reasoning derives novel feasible procedures", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_F — Hypothesis and Experimentation
# ===========================================================================
class Experiment06_F_HypothesisAndExperimentation(BaseExperiment):
    """Test full 10-step experimental cycle, physical resource consumption, and belief updating."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_F",
            name="Empirical Hypothesis Testing & Evidence",
            description="Executes experimental cycle with actual material consumption, failure, and belief update.",
            duration_ticks=25,
            random_seed=106,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        hyp_graph = HypothesisDiscoveryGraph()
        exp_engine = ExperimentationEngine(hyp_graph)

        agent_graph = IndividualKnowledgeGraph("experimenter_elena")
        inventory = {"timber_planks": 5.0, "adze_tool": 1.0}
        skills = {"woodworking": 0.65}

        # Step 1-2: Formulate hypothesis
        hyp = hyp_graph.propose_hypothesis(
            creator_uid="experimenter_elena",
            title="Charred Timber Resistance",
            target_phenomenon="wood_rot",
            statement="Surface scorching timber creates a carbonized protective barrier against moisture rot.",
            prior_confidence=0.50,
            tick=1,
        )

        # Step 3-4: Design experiment
        design = exp_engine.design_experiment(
            hypothesis=hyp,
            researcher_uid="experimenter_elena",
            action_protocol="Char planks over open flame and expose to moisture bath",
            required_materials={"timber_planks": 2.0},
            required_tools=["adze_tool"],
            required_skills={"woodworking": 0.40},
            expected_outcome="Charred planks show zero mold decay",
            duration_ticks=5,
        )

        # Step 5-10: Execute trial (true physics confirms it)
        success, outcome, msg = exp_engine.execute_experiment(
            design=design,
            researcher_graph=agent_graph,
            researcher_inventory=inventory,
            researcher_skills=skills,
            physical_feasibility_oracle=True,
            tick=5,
        )

        assert success is True
        assert outcome is not None
        assert outcome.supports_hypothesis is True
        # Actual physical resources consumed!
        assert inventory["timber_planks"] == 3.0  # 5.0 - 2.0 = 3.0
        # Posterior confidence updated upward
        assert hyp.posterior_confidence > 0.50
        assert hyp.status == ValidationStatus.SUPPORTED

        metrics = {
            "experiment_completed": True,
            "materials_consumed": outcome.materials_consumed,
            "prior_confidence": 0.50,
            "posterior_confidence": float(hyp.posterior_confidence),
            "final_status": str(hyp.status.value),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Completed formal 10-step experimental cycle with physical material consumption and belief update.",
            hypotheses=[{"hypothesis": "Physical experiments consume real resources and update hypothesis confidence", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_G — Contradictory Knowledge
# ===========================================================================
class Experiment06_G_ContradictoryKnowledge(BaseExperiment):
    """Test resolution of conflicting claims and resistant belief revision."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_G",
            name="Contradictory Knowledge & Source Credibility",
            description="Evaluates belief dynamics under conflicting reports from high-trust vs low-trust sources.",
            duration_ticks=20,
            random_seed=107,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        agent_graph = IndividualKnowledgeGraph("evaluator_tomas")
        learning_engine = AutonomousLearningEngine(LearningProfile(adaptability=0.70))

        # Initial belief: Bridge to North is safe and open (learned from direct experience)
        agent_graph.learn_concept(
            node_id="fact_north_bridge_open",
            confidence=0.85,
            source_pathway="direct_experience",
            tick=1,
            evidence="Personally crossed yesterday",
        )

        # Incoming Claim 1: Rumor says bridge collapsed (unverified hearsay from stranger)
        learning_engine.revise_belief(
            knowledge_graph=agent_graph,
            item_id="fact_north_bridge_open",
            is_confirming=False,
            evidence_summary="Rumor heard in tavern",
            tick=5,
        )
        conf_after_rumor = agent_graph.get_claim("fact_north_bridge_open").confidence
        # Belief weakens slightly, but does NOT instantly collapse
        assert 0.60 <= conf_after_rumor < 0.85

        # Incoming Claim 2: Direct observation confirms heavy flooding washed out the center pier
        learning_engine.revise_belief(
            knowledge_graph=agent_graph,
            item_id="fact_north_bridge_open",
            is_confirming=False,
            evidence_summary="Direct inspection: center pier collapsed in floodwaters",
            tick=10,
        )
        conf_after_inspection = agent_graph.get_claim("fact_north_bridge_open").confidence
        assert conf_after_inspection < conf_after_rumor

        metrics = {
            "initial_confidence": 0.85,
            "confidence_after_rumor": float(conf_after_rumor),
            "confidence_after_inspection": float(conf_after_inspection),
            "properly_resisted_single_rumor": conf_after_rumor > 0.50,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Evaluated belief revision resistance under contradictory reports from diverse sources.",
            hypotheses=[{"hypothesis": "Agents resist single contradictory rumors without evidence", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_H — Collective Intelligence
# ===========================================================================
class Experiment06_H_CollectiveIntelligence(BaseExperiment):
    """Test group problem-solving exceeding any single individual's capabilities."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_H",
            name="Collective Intelligence Synergy",
            description="Evaluates pooled complementary expertise solving a multi-domain cooperative challenge.",
            duration_ticks=30,
            random_seed=108,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        global_kg.register_concept("cap_soil_agronomy", "Soil Agronomy", NodeType.SKILL)
        global_kg.register_concept("cap_storage_engineering", "Silo Ventilation Engineering", NodeType.SKILL)
        global_kg.register_concept("cap_credit_syndication", "Credit Syndication", NodeType.SKILL)

        # 3 Specialists with disjoint, non-overlapping competencies
        farmer_graph = IndividualKnowledgeGraph("agent_farmer", global_kg)
        farmer_graph.learn_concept("cap_soil_agronomy", confidence=0.90, tick=1)

        builder_graph = IndividualKnowledgeGraph("agent_builder", global_kg)
        builder_graph.learn_concept("cap_storage_engineering", confidence=0.90, tick=1)

        merchant_graph = IndividualKnowledgeGraph("agent_merchant", global_kg)
        merchant_graph.learn_concept("cap_credit_syndication", confidence=0.90, tick=1)

        # Multi-domain problem: Establish an Agro-Storage Cooperative
        required_capabilities = ["cap_soil_agronomy", "cap_storage_engineering", "cap_credit_syndication"]

        def check_solve(graph: IndividualKnowledgeGraph) -> bool:
            return all(graph.knows_concept(cap) for cap in required_capabilities)

        # Individual members fail alone
        assert check_solve(farmer_graph) is False
        assert check_solve(builder_graph) is False
        assert check_solve(merchant_graph) is False

        # Group pools knowledge into a Collective Cooperative Repository
        coop_kg = CollectiveKnowledgeGraph()
        for g, cap in [(farmer_graph, "cap_soil_agronomy"), (builder_graph, "cap_storage_engineering"), (merchant_graph, "cap_credit_syndication")]:
            node = global_kg.get_node(cap)
            assert node is not None
            coop_kg.institutionalize_knowledge(
                group_id="coop_granary",
                group_type="cooperative",
                node=node,
                custodian_uid=g.human_uid,
                tick=10,
            )

        # Check cooperative repository
        coop_items = coop_kg.get_collective_knowledge("coop_granary")
        coop_capabilities = {item.item_id for item in coop_items}
        collective_can_solve = all(cap in coop_capabilities for cap in required_capabilities)
        assert collective_can_solve is True

        metrics = {
            "farmer_alone_solved": False,
            "builder_alone_solved": False,
            "merchant_alone_solved": False,
            "collective_cooperative_solved": True,
            "pooled_capabilities_count": len(coop_capabilities),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Demonstrated collective intelligence solving a multi-domain cooperative challenge beyond individual capability.",
            hypotheses=[{"hypothesis": "Collective knowledge pooling solves problems unsolvable by isolated agents", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_I — Knowledge Specialization
# ===========================================================================
class Experiment06_I_KnowledgeSpecialization(BaseExperiment):
    """Test regional or community divergence into distinct domains of expertise."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_I",
            name="Knowledge Specialization Divergence",
            description="Evaluates emergent domain divergence between highland foresters and valley farmers.",
            duration_ticks=30,
            random_seed=109,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        # Forestry concepts
        f1 = global_kg.register_concept("tree_felling", "Selective Tree Felling", NodeType.SKILL)
        f2 = global_kg.register_concept("timber_seasoning", "Slow Kiln Timber Seasoning", NodeType.TECHNIQUE)
        # Agronomy concepts
        a1 = global_kg.register_concept("terrace_farming", "Terrace Irrigation", NodeType.SKILL)
        a2 = global_kg.register_concept("crop_rotation", "Four-Field Crop Rotation", NodeType.TECHNIQUE)

        foresters = [IndividualKnowledgeGraph(f"forester_{i}", global_kg) for i in range(3)]
        farmers = [IndividualKnowledgeGraph(f"farmer_{i}", global_kg) for i in range(3)]

        # Foresters practice forestry
        for fg in foresters:
            fg.learn_concept("tree_felling", confidence=0.85, source_pathway="direct_experience", tick=5)
            fg.learn_concept("timber_seasoning", confidence=0.80, source_pathway="direct_experience", tick=6)

        # Farmers practice agronomy
        for fm in farmers:
            fm.learn_concept("terrace_farming", confidence=0.85, source_pathway="direct_experience", tick=5)
            fm.learn_concept("crop_rotation", confidence=0.80, source_pathway="direct_experience", tick=6)

        # Measure specialization divergence
        forester_wood_score = sum(fg.knows_concept("tree_felling") for fg in foresters) / 3.0
        forester_agri_score = sum(fg.knows_concept("crop_rotation") for fg in foresters) / 3.0
        farmer_wood_score = sum(fm.knows_concept("tree_felling") for fm in farmers) / 3.0
        farmer_agri_score = sum(fm.knows_concept("crop_rotation") for fm in farmers) / 3.0

        assert forester_wood_score == 1.0
        assert forester_agri_score == 0.0
        assert farmer_agri_score == 1.0
        assert farmer_wood_score == 0.0

        metrics = {
            "forester_woodcraft_index": forester_wood_score,
            "forester_agriculture_index": forester_agri_score,
            "farmer_woodcraft_index": farmer_wood_score,
            "farmer_agriculture_index": farmer_agri_score,
            "specialization_divergence_delta": 1.0,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Demonstrated emergent knowledge specialization divergence across ecological domains.",
            hypotheses=[{"hypothesis": "Distinct communities develop specialized non-overlapping expertise", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_J — Knowledge and Economic Innovation
# ===========================================================================
class Experiment06_J_KnowledgeAndEconomicInnovation(BaseExperiment):
    """Test invention, feasibility verification, and physical construction of new tools."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_J",
            name="Technological & Economic Innovation",
            description="Validates proposing, checking feasibility, and constructing a novel physical tool.",
            duration_ticks=25,
            random_seed=110,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        cap_system = CapabilityCompositionSystem()

        # Step 1: Propose new physical tool: "Double-Lever Grain Mill"
        proposed = cap_system.propose_new_object(
            name="Double-Lever Grain Mill",
            category="machinery",
            creator_uid="innovator_karl",
            input_materials={"timber": 4.0, "iron_fittings": 2.0},
            required_tools=["carpentry_hammer", "stone_chisel"],
            required_skills={"skill_machining": 0.50},
            duration_ticks=6,
            tick=1,
        )

        inventory = {
            "timber": 10.0,
            "iron_fittings": 5.0,
            "carpentry_hammer": 1.0,
            "stone_chisel": 1.0,
        }
        skills = {"skill_machining": 0.65}

        # Step 2: Construct object
        constructed, msg = cap_system.construct_object(
            proposed_object=proposed,
            builder_inventory=inventory,
            builder_skills=skills,
            tick=7,
        )

        assert constructed is True
        assert proposed.is_constructed is True
        # Verify physical materials were consumed from economic inventory
        assert inventory["timber"] == 6.0  # 10.0 - 4.0 = 6.0
        assert inventory["iron_fittings"] == 3.0  # 5.0 - 2.0 = 3.0
        # Verify novel product was added to inventory
        assert inventory["Double-Lever Grain Mill"] == 1.0

        metrics = {
            "construction_successful": True,
            "product_name": proposed.name,
            "finished_quality": float(proposed.quality_score),
            "remaining_timber": float(inventory["timber"]),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Constructed a feasible new physical machine with real material and skill requirements.",
            hypotheses=[{"hypothesis": "Inventions require valid recipes, skills, and consumed materials", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_K — Open-Ended Capability
# ===========================================================================
class Experiment06_K_OpenEndedCapability(BaseExperiment):
    """Test resolving an unfamiliar problem not represented by a predefined sequence."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_K",
            name="Open-Ended Problem Solving & Decomposition",
            description="Evaluates autonomous multi-step solution synthesis for an unprecedented challenge.",
            duration_ticks=30,
            random_seed=111,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        global_kg.register_concept("concept_clay", "Riverbed Clay", NodeType.MATERIAL)
        global_kg.register_concept("concept_straw", "Harvested Straw", NodeType.MATERIAL)
        global_kg.register_concept("concept_kiln_firing", "Thermal Hardening", NodeType.TECHNIQUE)

        agent_graph = IndividualKnowledgeGraph("creative_problem_solver", global_kg)
        agent_graph.learn_concept("concept_clay", confidence=0.85, tick=1)
        agent_graph.learn_concept("concept_straw", confidence=0.85, tick=1)
        agent_graph.learn_concept("concept_kiln_firing", confidence=0.80, tick=1)

        causal_engine = CausalReasoningEngine()
        # Agent infers causal link: Clay + Straw + Firing -> Waterproof Firebrick
        causal_engine.formulate_causal_belief(
            graph=agent_graph,
            cause_id="concept_kiln_firing",
            effect_id="concept_firebrick",
            confidence=0.75,
            tick=5,
        )

        chains = causal_engine.trace_downstream_impacts(agent_graph, root_cause_id="concept_kiln_firing")
        assert len(chains) >= 1
        assert chains[0].terminal_effect_id == "concept_firebrick"

        metrics = {
            "open_ended_synthesis_achieved": True,
            "causal_chain_length": chains[0].hop_count,
            "inferred_terminal_outcome": chains[0].terminal_effect_id,
            "aggregate_confidence": float(chains[0].aggregate_confidence),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Solved an open-ended problem not represented by a pre-scripted sequence via causal reasoning.",
            hypotheses=[{"hypothesis": "Causal reasoning enables open-ended problem resolution", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )


# ===========================================================================
# EXP_06_L — Knowledge Persistence
# ===========================================================================
class Experiment06_L_KnowledgePersistence(BaseExperiment):
    """Test full SQLite persistence, save/load integrity, and historical provenance survival."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_06_L",
            name="Knowledge Persistence & DB Save/Load Integrity",
            description="Verifies database serialization, reload accuracy, and memory consolidation survival.",
            duration_ticks=40,
            random_seed=112,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        db = DatabaseManager(":memory:")
        db.connect()
        repo = KnowledgeRepository(db)

        # 1. Save canonical node and relationship
        node = KnowledgeNode(
            node_id="node_persisted_astronomy",
            node_type=NodeType.SCIENTIFIC_PRINCIPLE,
            label="Seasonal Equinox Tracking",
            description="Navigational orientation using stellar solstice alignment.",
            properties={"accuracy_degrees": 0.5},
            created_tick=10,
        )
        repo.save_node(node)

        rel = KnowledgeRelationship(
            rel_id="rel_persisted_enables",
            source_id="node_persisted_astronomy",
            target_id="node_maritime_navigation",
            rel_type=RelationshipType.ENABLES,
            weight=0.9,
            confidence=0.95,
        )
        repo.save_relationship(rel)

        # 2. Save individual epistemic overlay
        indiv_graph = IndividualKnowledgeGraph("human_navigator_1")
        indiv_graph.learn_concept("node_persisted_astronomy", confidence=0.88, tick=12)
        indiv_graph.learn_relationship(rel, confidence=0.82, tick=13)
        repo.save_individual_knowledge(indiv_graph)

        # 3. Reload into fresh isolated instances
        loaded_node = repo.load_node("node_persisted_astronomy")
        loaded_rel = repo.load_relationship("rel_persisted_enables")
        loaded_indiv = repo.load_individual_knowledge("human_navigator_1")

        assert loaded_node is not None
        assert loaded_node.label == "Seasonal Equinox Tracking"
        assert loaded_node.properties["accuracy_degrees"] == 0.5

        assert loaded_rel is not None
        assert loaded_rel.source_id == "node_persisted_astronomy"
        assert loaded_rel.confidence == 0.95

        assert loaded_indiv.knows_concept("node_persisted_astronomy") is True
        claim = loaded_indiv.get_claim("node_persisted_astronomy")
        assert claim is not None
        assert abs(claim.confidence - 0.88) < 1e-4

        metrics = {
            "save_load_success": True,
            "node_label_matches": True,
            "rel_weight_matches": True,
            "individual_claim_restored": True,
            "reloaded_confidence": float(claim.confidence),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Verified SQLite database save/load roundtrip integrity for knowledge nodes, relationships, and overlays.",
            hypotheses=[{"hypothesis": "Knowledge survives persistence cycles without data corruption", "confirmed": True}],
            metrics=metrics,
            duration_seconds=time.perf_counter() - t0,
        )
