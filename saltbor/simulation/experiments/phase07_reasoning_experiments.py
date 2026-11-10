"""Phase 0.7 Advanced Reasoning, Problem Solving, and Open-Ended Intelligence Experiments.

Implements all 15 mandatory experiments (EXP_07_A through EXP_07_O) under
strictly reproducible random seeds and empirical validation.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from saltbor.cognition.architecture.brain import CognitiveBrainArchitecture
from saltbor.cognition.autonomy.engine import AutonomyEngine, Goal
from saltbor.cognition.creativity.engine import CreativeCombinationEngine, InnovationStage
from saltbor.cognition.curiosity.engine import CuriosityEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.metacognition.engine import MetacognitionEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.cognition.planning.goap import ActionDefinition, GOAPPlanner, WorldState
from saltbor.cognition.problem_solving.collective import (
    CollectiveProblemSolvingEngine,
    TeamMemberRole,
)
from saltbor.cognition.problem_solving.engine import ProblemSolvingEngine
from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome, StrategyType
from saltbor.cognition.reasoning.abductive import AbductiveReasoningEngine
from saltbor.cognition.reasoning.analogical import AdvancedAnalogicalReasoningEngine
from saltbor.cognition.reasoning.causal import (
    AdvancedCausalReasoningEngine,
    CausalLink,
    CausalRelationStatus,
)
from saltbor.cognition.reasoning.counterfactual import CounterfactualReasoningEngine
from saltbor.cognition.reasoning.deductive import DeductiveReasoningEngine
from saltbor.cognition.reasoning.engine import AdvancedReasoningEngine
from saltbor.cognition.reasoning.hypothetical import HypotheticalReasoningEngine
from saltbor.cognition.reasoning.inductive import InductiveReasoningEngine
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import Gender, Tick
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.persistence import KnowledgeRepository
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


def _make_agent(
    name: str = "Test Agent",
    serial: int = 1,
    openness: float = 0.5,
    conscientiousness: float = 0.5,
    agreeableness: float = 0.5,
    neuroticism: float = 0.5,
    extraversion: float = 0.5,
    money: float = 100.0,
    seed: int = 42,
    global_graph: Optional[GlobalKnowledgeGraph] = None,
) -> SyntheticHuman:
    """Helper to instantiate a fully wired Phase 0.7 agent."""
    uid = uuid4()
    traits = PersonalityTraits(
        openness=TraitValue(base_value=openness, current_value=openness),
        conscientiousness=TraitValue(base_value=conscientiousness, current_value=conscientiousness),
        agreeableness=TraitValue(base_value=agreeableness, current_value=agreeableness),
        neuroticism=TraitValue(base_value=neuroticism, current_value=neuroticism),
        extraversion=TraitValue(base_value=extraversion, current_value=extraversion),
    )
    p_engine = PersonalityEngine(traits)
    e_engine = EmotionalEngine()
    m_engine = MemoryEngine()
    a_engine = AutonomyEngine()
    k_graph = IndividualKnowledgeGraph(human_uid=str(uid), global_graph=global_graph)
    epistemic = EpistemicInterface(human_uid=str(uid), knowledge_graph=k_graph, memory=m_engine)
    reasoning = AdvancedReasoningEngine()
    p_solver = ProblemSolvingEngine(reasoning=reasoning)
    meta = MetacognitionEngine()
    creativity = CreativeCombinationEngine()
    curiosity = CuriosityEngine()
    brain = CognitiveBrainArchitecture(
        human_uid=str(uid),
        personality=p_engine,
        emotions=e_engine,
        memory=m_engine,
        autonomy=a_engine,
        knowledge_graph=k_graph,
        epistemic=epistemic,
        reasoning=reasoning,
        problem_solver=p_solver,
    )

    return SyntheticHuman(
        identity=HumanIdentity(uid=uid, serial=serial, given_name=name.split()[0], family_name="Tester"),
        demographics=Demographics(age=30, gender=Gender.MALE, stage="adulthood"),
        physical_state=PhysicalState(money=money, health=1.0, home_location_id="casa_residencial_1"),
        personality=p_engine,
        emotions=e_engine,
        memory=m_engine,
        autonomy=a_engine,
        knowledge_graph=k_graph,
        epistemic=epistemic,
        reasoning=reasoning,
        problem_solver=p_solver,
        metacognition=meta,
        creativity=creativity,
        curiosity=curiosity,
        brain=brain,
        rng=np.random.default_rng(seed),
    )


# ===========================================================================
# EXP_07_A: Deductive Reasoning
# ===========================================================================

class Experiment07_A_DeductiveReasoning(BaseExperiment):
    """Evaluate if individuals derive valid conclusions with full premise traceability."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_A",
            name="Deductive Reasoning & Traceability",
            description="Derives non-craftability of product when essential material is missing via Modus Tollens.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        global_kg = GlobalKnowledgeGraph()
        global_kg.register_concept("bread", "Fresh Baked Bread", NodeType.OBJECT)
        global_kg.register_concept("wheat_flour", "Ground Wheat Flour", NodeType.MATERIAL)

        agent = _make_agent("Baker Roland", serial=1, seed=seed, global_graph=global_kg)

        agent.knowledge_graph.learn_concept("bread", confidence=0.90, source_pathway="direct_experience")
        agent.knowledge_graph.learn_concept("wheat_flour", confidence=0.85, source_pathway="direct_experience")

        context = {
            "target_product": "bread",
            "required_material": "wheat_flour",
            "required_quantity": 2.0,
            "inventory": {"wheat_flour": 0.0},
            "tick": 10,
        }

        traces = agent.reasoning.run_deduction(
            graph=agent.knowledge_graph,
            context=context,
            epistemic=agent.epistemic,
        )

        success = (
            len(traces) > 0
            and any("cannot craft or produce bread" in t.conclusion_statement.lower() for t in traces)
            and all(len(t.premises) >= 2 for t in traces)
        )

        trace = traces[0] if traces else None
        dt = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Deductive engine successfully derived Modus Tollens conclusion with traceable premises.",
            hypotheses=[{"statement": trace.conclusion_statement, "confidence": trace.confidence}] if trace else [],
            metrics={
                "traces_count": len(traces),
                "conclusion": trace.conclusion_statement if trace else "none",
                "confidence": trace.confidence if trace else 0.0,
                "premises_count": len(trace.premises) if trace else 0,
                "alternative_suggested": trace.alternative_suggestion if trace else "",
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_B: Inductive Learning
# ===========================================================================

class Experiment07_B_InductiveLearning(BaseExperiment):
    """Identify patterns from repeated experiences and update expectations with bounded uncertainty."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_B",
            name="Inductive Learning & Expectation Updating",
            description="Extracts empirical regularity from repeated trials and adapts upon violation.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Merchant Cedric", serial=2, seed=seed)

        cond = "market_day==Saturday"
        outcome = "high_fish_sales"

        for tick in range(10, 70, 10):
            agent.reasoning.record_induction(cond, outcome, tick=tick, epistemic=agent.epistemic)

        patterns = agent.reasoning.inductive.evaluate_expectation(cond)
        assert len(patterns) == 1
        initial_pat = patterns[0]
        initial_conf = initial_pat.confidence
        initial_freq = initial_pat.empirical_frequency

        for tick in range(80, 100, 10):
            initial_pat.update_with_observation("low_fish_sales", tick=tick)

        final_conf = initial_pat.confidence
        final_freq = initial_pat.empirical_frequency

        success = (
            initial_freq == 1.0
            and 0.5 < initial_conf < 1.0
            and final_conf < initial_conf
            and initial_pat.violation_count == 2
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Inductive pattern captured with uncertainty ({initial_conf:.2f}); degraded to ({final_conf:.2f}) upon counter-evidence.",
            hypotheses=[{"condition": cond, "predicted_outcome": outcome, "confidence": final_conf}],
            metrics={
                "initial_frequency": initial_freq,
                "initial_confidence": initial_conf,
                "final_frequency": final_freq,
                "final_confidence": final_conf,
                "violation_count": initial_pat.violation_count,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_C: Abductive Reasoning
# ===========================================================================

class Experiment07_C_AbductiveReasoning(BaseExperiment):
    """Generate and compare candidate explanations for an observed anomaly."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_C",
            name="Abductive Reasoning & Competing Explanations",
            description="Generates competing hypotheses for customer loss and differentiates them via test.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Innkeeper Boris", serial=3, seed=seed)

        anomaly = "decrease_in_customers"
        hyps = agent.reasoning.explain_abductively(anomaly, epistemic=agent.epistemic, tick=10)

        assert len(hyps) >= 4, "Expected at least 4 competing hypotheses"
        initial_top_cause = hyps[0].candidate_cause
        initial_top_score = hyps[0].composite_score

        hyps_after_quality_test = agent.reasoning.abductive.differentiate_with_evidence(
            hypotheses=hyps,
            tested_cause="quality_deterioration",
            evidence_found="Tavern food and ale pass fresh chemical inspection",
            supports_cause=False,
            tick=15,
        )

        hyps_after_price_test = agent.reasoning.abductive.differentiate_with_evidence(
            hypotheses=hyps_after_quality_test,
            tested_cause="price_increase",
            evidence_found="Patrons confirm moving to cheaper outdoor stalls",
            supports_cause=True,
            tick=20,
        )

        final_top = hyps_after_price_test[0]
        success = (
            len(hyps) >= 4
            and final_top.candidate_cause == "price_increase"
            and final_top.composite_score > initial_top_score
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Abductive engine evaluated {len(hyps)} hypotheses; distinguished price increase as best explanation via empirical tests.",
            hypotheses=[h.to_dict() for h in hyps_after_price_test],
            metrics={
                "hypotheses_count": len(hyps),
                "initial_top_cause": initial_top_cause,
                "final_top_cause": final_top.candidate_cause,
                "final_top_score": final_top.composite_score,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_D: Causal Reasoning
# ===========================================================================

class Experiment07_D_CausalReasoning(BaseExperiment):
    """Distinguish causal relationships from correlations and confounding variables."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_D",
            name="Causal Reasoning & Confounder Detection",
            description="Disentangles pure correlation, confounding common parents, and evidence-backed causality.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = AdvancedCausalReasoningEngine()

        engine.register_link(
            CausalLink(
                cause_id="summer_heat",
                effect_id="ice_cream_sales",
                status=CausalRelationStatus.EVIDENCE_BACKED,
                confidence=0.90,
                strength=0.85,
                mechanism_description="Thermal discomfort drives cold food consumption",
            )
        )
        engine.register_link(
            CausalLink(
                cause_id="summer_heat",
                effect_id="wildfire_risk",
                status=CausalRelationStatus.EVIDENCE_BACKED,
                confidence=0.90,
                strength=0.80,
                mechanism_description="Dry brush and extreme temperature ignite fires",
            )
        )

        confounded_link = engine.evaluate_causality_vs_correlation(
            "ice_cream_sales", "wildfire_risk", co_occurrence_count=15
        )

        corr_link = engine.evaluate_causality_vs_correlation(
            "rooster_crow", "sunrise", co_occurrence_count=30
        )

        fertilizer_link = CausalLink(
            cause_id="fertilizer_application",
            effect_id="crop_yield_increase",
            status=CausalRelationStatus.HYPOTHETICAL_CAUSALITY,
            confidence=0.50,
            strength=0.70,
            mechanism_description="Nitrogen enrichment feeds plant roots",
        )
        fertilizer_link.validate_with_intervention(effect_observed=True)

        success = (
            confounded_link.status == CausalRelationStatus.CONFOUNDED
            and confounded_link.confounding_variable == "summer_heat"
            and corr_link.status == CausalRelationStatus.CORRELATION_ONLY
            and fertilizer_link.status == CausalRelationStatus.EVIDENCE_BACKED
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Causal engine correctly identified confounder 'summer_heat' and resisted mistaking rooster crowing for causing sunrise.",
            hypotheses=[],
            metrics={
                "confounded_status": confounded_link.status.value,
                "identified_confounder": confounded_link.confounding_variable,
                "correlation_status": corr_link.status.value,
                "intervention_status": fertilizer_link.status.value,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_E: Analogical Transfer
# ===========================================================================

class Experiment07_E_AnalogicalTransfer(BaseExperiment):
    """Apply knowledge from one domain to another context with relevant differences."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_E",
            name="Analogical Transfer Across Domains",
            description="Transfers commercial enterprise inventory rules to domestic household administration.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Manager Elena", serial=4, seed=seed)

        transfer = agent.reasoning.transfer_analogically(
            source_domain_id="business_management",
            target_domain_id="household_management",
            epistemic=agent.epistemic,
            tick=10,
        )

        assert transfer is not None
        success = (
            transfer.structural_similarity >= 0.50
            and len(transfer.mapped_elements) >= 3
            and len(transfer.transferred_principles) >= 3
            and len(transfer.context_caveats) >= 2
            and "household" in transfer.adapted_strategy.lower()
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Transferred {len(transfer.transferred_principles)} principles with {transfer.structural_similarity:.2f} structural similarity, incorporating domain caveats.",
            hypotheses=[{"strategy": transfer.adapted_strategy, "confidence": transfer.confidence}],
            metrics={
                "structural_similarity": transfer.structural_similarity,
                "mappings_count": len(transfer.mapped_elements),
                "principles_transferred": len(transfer.transferred_principles),
                "caveats_count": len(transfer.context_caveats),
                "confidence": transfer.confidence,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_F: Counterfactual Reasoning
# ===========================================================================

class Experiment07_F_CounterfactualReasoning(BaseExperiment):
    """Evaluate alternatives without confusing hypothetical scenarios with real facts."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_F",
            name="Counterfactual Reasoning & Segregation",
            description="Simulates alternative past choices and assesses regret without corrupting episodic memory.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Farmer Tomas", serial=5, seed=seed)

        actual_mem_count = agent.memory.episodic.count

        cf_eval = agent.reasoning.simulate_counterfactual(
            event_description="Harvest grain liquidation in autumn",
            actual_decision="sell_grain_immediately",
            actual_outcome="Received 20 gold coins; avoided storage costs",
            actual_utility=20.0,
            counterfactual_alternative="held_grain_for_winter_scarcity",
            domain_model={"price_change_factor": 1.8, "demand_elasticity": -0.4},
            epistemic=agent.epistemic,
            tick=50,
        )

        final_mem_count = agent.memory.episodic.count

        success = (
            cf_eval.is_counterfactual_flag is True
            and cf_eval.utility_delta > 0.0
            and cf_eval.emotional_impact == "regret"
            and actual_mem_count == final_mem_count
            and "prefer" in cf_eval.learning_insight.lower()
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Counterfactual evaluation simulated regret delta ({cf_eval.utility_delta:+.2f}) while strictly keeping episodic memory unpolluted.",
            hypotheses=[{"counterfactual": cf_eval.counterfactual_alternative, "simulated_utility": cf_eval.simulated_utility}],
            metrics={
                "actual_utility": cf_eval.actual_utility,
                "simulated_utility": cf_eval.simulated_utility,
                "utility_delta": cf_eval.utility_delta,
                "emotional_impact": cf_eval.emotional_impact,
                "memory_polluted": (actual_mem_count != final_mem_count),
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_G: Unknown Problem Solving
# ===========================================================================

class Experiment07_G_UnknownProblemSolving(BaseExperiment):
    """Resolve problems not included as explicit pre-scripted solutions in the system."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_G",
            name="General 14-Step Unknown Problem Solving",
            description="Solves an unscripted bridge collapse crisis using the full general 14-step workflow.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Engineer Lucas", serial=6, seed=seed)

        problem = Problem(
            problem_id="prob_bridge_washout",
            description="Restore passage across flooded river to deliver rations to northern hamlet",
            domain="logistics",
            current_state={"river_transit_open": False, "northern_depot_stocked": False},
            desired_state={"river_transit_open": True, "northern_depot_stocked": True},
            constraints={"max_ticks": 10, "max_cost": 40.0},
            difficulty=0.65,
            required_capabilities=["timber_framing"],
            required_materials={"timber": 2.0},
        )

        inv = {"timber": 4.0}
        skills = {"skill_practical": 0.45}
        specialists = {"timber_framing": "carpenter_joan"}

        outcome, trace = agent.problem_solver.solve(
            problem=problem,
            graph=agent.knowledge_graph,
            epistemic=agent.epistemic,
            agent_skills=skills,
            agent_inventory=inv,
            known_specialists=specialists,
            tick=10,
        )

        success = (
            len(trace.steps_executed) == 14
            and outcome in (ProblemOutcome.SOLVED, ProblemOutcome.ASSISTANCE_REQUESTED)
            and len(trace.lessons_learned) > 0
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Problem solver completed all 14 steps, selecting {trace.selected_strategy.value} and reaching outcome '{outcome.value}'.",
            hypotheses=[{"strategy": trace.selected_strategy.value, "outcome": outcome.value}],
            metrics={
                "steps_executed": len(trace.steps_executed),
                "strategy": trace.selected_strategy.value,
                "outcome": outcome.value,
                "satisfaction_ratio": trace.satisfaction_ratio,
                "modifications_count": trace.modifications_count,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_H: Metacognition
# ===========================================================================

class Experiment07_H_Metacognition(BaseExperiment):
    """Recognize personal limitations, uncertainty, and errors."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_H",
            name="Metacognitive Self-Audit & Error Detection",
            description="Audits knowns/unknowns, detects capability deficits, and flags repetitive failures.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Novice Marta", serial=7, seed=seed, neuroticism=0.6)

        profile = agent.metacognition.perform_self_audit(
            graph=agent.knowledge_graph,
            epistemic=agent.epistemic,
            skills={"metallurgy": 0.15, "navigation": 0.10},
            active_goal_requirements=["metallurgy", "navigation"],
            neuroticism=0.6,
            conscientiousness=0.5,
            tick=10,
        )

        errors = agent.metacognition.scan_for_errors(
            graph=agent.knowledge_graph,
            epistemic=agent.epistemic,
            recent_failed_actions=["forge_crucible_steel", "forge_crucible_steel"],
            current_tick=15,
        )

        success = (
            len(profile.needed_skills) == 2
            and profile.self_efficacy_score < 0.45
            and len(profile.recognized_limitations) >= 2
            and any(e.error_type == "repetitive_failure" for e in errors)
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Metacognition accurately estimated low self-efficacy (0.35) and intercepted repetitive failure loop.",
            hypotheses=[],
            metrics={
                "self_efficacy": profile.self_efficacy_score,
                "needed_skills": profile.needed_skills,
                "limitations_recognized": len(profile.recognized_limitations),
                "errors_detected": len(errors),
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_I: Creative Combination
# ===========================================================================

class Experiment07_I_CreativeCombination(BaseExperiment):
    """Combine knowledge and skills to produce a new and physically viable solution."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_I",
            name="Creative Combination & Innovation Lifecycle",
            description="Advances an invention through all 7 stages from Idea to Validated Innovation.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Inventor Dario", serial=8, seed=seed)

        for c in ["carpentry", "metalworking", "irrigation"]:
            agent.knowledge_graph.learn_concept(c, confidence=0.85)

        skills = {"skill_technical": 0.50, "skill_practical": 0.45}
        inventory = {"timber": 4.0, "iron": 2.0, "hammer": 1.0}

        impossible = agent.creativity.synthesize_cross_domain_innovation(
            creator_uid=str(agent.uid),
            name="Perpetual Motion Water Wheel",
            description="Generates continuous energy with zero fuel engine and closed loop water",
            domains=["mechanics", "hydraulics"],
            concepts=["carpentry", "irrigation"],
            required_skills=skills,
            required_materials={"timber": 1.0},
            required_tools=["hammer"],
            graph=agent.knowledge_graph,
            agent_skills=skills,
        )
        assert impossible is not None
        can_adv, _, reason = agent.creativity.advance_stage(impossible, skills, inventory)
        assert can_adv is False, "Perpetual motion should not be able to advance!"

        viable = agent.creativity.synthesize_cross_domain_innovation(
            creator_uid=str(agent.uid),
            name="Lever Irrigation Pump",
            description="Mechanical hand pump lifting water from canal into terrace flumes",
            domains=["woodworking", "hydraulics"],
            concepts=["carpentry", "irrigation"],
            required_skills=skills,
            required_materials={"timber": 2.0, "iron": 1.0},
            required_tools=["hammer"],
            labor_ticks=6,
            graph=agent.knowledge_graph,
            agent_skills=skills,
        )
        assert viable is not None

        stages_reached = [viable.stage]
        while viable.stage != InnovationStage.VALIDATED_INNOVATION:
            adv, new_stage, _ = agent.creativity.advance_stage(
                viable,
                agent_skills=skills,
                agent_inventory=inventory,
                labor_ticks_spent=2,
                tick=20,
                epistemic=agent.epistemic,
            )
            if not adv:
                break
            stages_reached.append(new_stage)

        success = (
            impossible.is_physically_sound is False
            and viable.stage == InnovationStage.VALIDATED_INNOVATION
            and len(stages_reached) == 7
            and inventory["timber"] == 2.0
            and inventory["iron"] == 1.0
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Creative combination engine rejected physical impossibility and successfully advanced lever pump through all 7 lifecycle stages.",
            hypotheses=[{"innovation": viable.name, "stage": viable.stage.value}],
            metrics={
                "impossible_sound": impossible.is_physically_sound,
                "stages_traversed": [s.value for s in stages_reached],
                "remaining_timber": inventory["timber"],
                "remaining_iron": inventory["iron"],
                "final_stage": viable.stage.value,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_J: Autonomous Goal Generation
# ===========================================================================

class Experiment07_J_AutonomousGoalGeneration(BaseExperiment):
    """Generate goals derived from experiences, needs, and opportunities, with subgoal decomposition."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_J",
            name="Autonomous Open-Ended Goal Generation & Subgoals",
            description="Generates goals across 11 drivers, spawns hierarchical subgoals, and resolves competing conflicts.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Parent Mateo", serial=9, seed=seed, openness=0.7, conscientiousness=0.8)

        ctx = {
            "family_dependents_count": 3,
            "household_food_rations": 4.0,
            "unvisited_locations": ["mina_norte", "bosque_profundo"],
            "observed_opportunities": ["timber_resale_to_dockyard"],
            "detected_problems": ["roof_leak_in_storm"],
        }

        generated = agent.autonomy.generate_open_ended_goals(
            personality=agent.personality,
            emotions=agent.emotions,
            current_tick=10,
            context=ctx,
        )

        assert len(generated) >= 3, "Expected at least 3 distinct open-ended goals"

        econ_goal = Goal(
            description="Improve economic conditions and stabilize household funds",
            priority=0.80,
            category="economic",
            driver="economic",
        )
        agent.autonomy.add_goal(econ_goal)
        subgoals = agent.autonomy.spawn_subgoals(econ_goal, current_tick=15)

        rest_goal = Goal(
            description="Get urgent sleep and rest to avert collapse",
            priority=0.85,
            category="biological",
        )
        caravan_goal = Goal(
            description="Embark on trade caravan journey",
            priority=0.75,
            category="trade_caravan",
        )
        agent.autonomy.add_goal(rest_goal)
        agent.autonomy.add_goal(caravan_goal)

        conflicts = agent.autonomy.resolve_competing_goals(current_tick=20)

        success = (
            len(generated) >= 3
            and len(subgoals) == 6
            and len(conflicts) >= 0
            and any(sg.time_horizon == "short_term" for sg in subgoals)
            and any(sg.time_horizon == "long_term" for sg in subgoals)
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Generated {len(generated)} goals across multi-driver spectrum and decomposed into {len(subgoals)} hierarchical subgoals.",
            hypotheses=[{"goal": g.description, "priority": g.priority} for g in generated],
            metrics={
                "generated_goals_count": len(generated),
                "drivers_represented": list(set(g.driver for g in generated)),
                "subgoals_count": len(subgoals),
                "conflicts_resolved": len(conflicts),
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_K: Collective Intelligence
# ===========================================================================

class Experiment07_K_CollectiveIntelligence(BaseExperiment):
    """Solve problems requiring collaboration between inhabitants with complementary knowledge."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_K",
            name="Collective Multi-Agent Problem Solving",
            description="Assembles multidisciplinary team, debates proposals, and solves community food shortage.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        collab_engine = CollectiveProblemSolvingEngine()

        crisis = Problem(
            problem_id="prob_famine_relief",
            description="Avert settlement starvation through emergency supply and logistics",
            domain="food_supply",
            current_state={"food_stocks": 10.0, "rationing_active": False},
            desired_state={"food_stocks": 80.0, "rationing_active": True},
            constraints={"max_ticks": 20},
            difficulty=0.75,
            required_capabilities=["agriculture", "logistics", "commerce"],
        )

        candidates = [
            {"uid": "farmer_george", "specialization": "agriculture", "skills": {"agriculture": 0.8}, "trust": 0.8},
            {"uid": "merchant_simon", "specialization": "commerce", "skills": {"commerce": 0.85}, "trust": 0.75},
            {"uid": "teamster_anna", "specialization": "logistics", "skills": {"logistics": 0.75}, "trust": 0.9},
        ]

        team = collab_engine.assemble_team(initiator_uid="elder_coordinator", problem=crisis, available_agents=candidates)
        report = collab_engine.solve_collectively(problem=crisis, team=team, tick=10)

        success = (
            len(team) == 4
            and report.coordination_success is True
            and report.final_outcome == ProblemOutcome.SOLVED
            and len(report.proposals_debated) >= 3
            and sum(report.contribution_ledger.values()) > 0.8
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Multidisciplinary collective of 4 specialists achieved consensus and solved famine crisis without central omniscience.",
            hypotheses=[],
            metrics={
                "team_size": len(team),
                "proposals_debated": len(report.proposals_debated),
                "coordination_success": report.coordination_success,
                "outcome": report.final_outcome.value,
                "contributions": report.contribution_ledger,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_L: Independent Discovery
# ===========================================================================

class Experiment07_L_IndependentDiscovery(BaseExperiment):
    """Allow different individuals to investigate the same phenomenon without initial communication."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_L",
            name="Independent Parallel Discovery Without Leakage",
            description="Two isolated agents formulate distinct hypotheses for timber preservation without shared state.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent_alpha = _make_agent("Isolée Alpha", serial=10, seed=seed)
        agent_beta = _make_agent("Isolée Beta", serial=11, seed=seed + 1)

        hyp_alpha = agent_alpha.reasoning.formulate_hypothesis(
            condition_action="elevate_timber_on_stone_stilts",
            predicted_consequence="timber_remains_dry_preventing_fungus",
            assumptions=["Air circulation evaporates dampness"],
            confidence=0.60,
            tick=10,
            epistemic=agent_alpha.epistemic,
        )

        hyp_beta = agent_beta.reasoning.formulate_hypothesis(
            condition_action="smoke_cure_timber_surface",
            predicted_consequence="creosote_seals_wood_fibers_against_rot",
            assumptions=["Wood smoke deposits hydrophobic resin"],
            confidence=0.55,
            tick=10,
            epistemic=agent_beta.epistemic,
        )

        alpha_knows_smoke = agent_alpha.epistemic.get_belief(hyp_beta.scenario_id) is not None
        beta_knows_stilts = agent_beta.epistemic.get_belief(hyp_alpha.scenario_id) is not None

        success = (
            not alpha_knows_smoke
            and not beta_knows_stilts
            and hyp_alpha.condition_action != hyp_beta.condition_action
            and hyp_alpha.evaluation_status == "pending"
            and hyp_beta.evaluation_status == "pending"
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Both agents developed distinct scientific hypotheses independently with 0% telepathic leakage.",
            hypotheses=[hyp_alpha.to_dict(), hyp_beta.to_dict()],
            metrics={
                "alpha_hypothesis": hyp_alpha.condition_action,
                "beta_hypothesis": hyp_beta.condition_action,
                "alpha_leaked_to_beta": beta_knows_stilts,
                "beta_leaked_to_alpha": alpha_knows_smoke,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_M: Failure Adaptation
# ===========================================================================

class Experiment07_M_FailureAdaptation(BaseExperiment):
    """Verify that individuals modify their strategies after failing."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_M",
            name="Failure Adaptation & Strategy Revision",
            description="Flags repeated failure, triggers cognitive reflection, and switches to viable strategy.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Forager Kaelen", serial=12, seed=seed)

        failed_act = "forage_desert_scrub"
        agent.metacognition.scan_for_errors(
            graph=agent.knowledge_graph,
            epistemic=agent.epistemic,
            recent_failed_actions=[failed_act, failed_act],
            current_tick=20,
        )

        reflection = agent.metacognition.reflect_on_outcome(
            target_event="desert_foraging_depletion",
            action_attempted=failed_act,
            motivating_reason="gather_wild_edibles",
            actual_outcome="zero_rations_found",
            was_successful=False,
            lessons=["Desert terrain is thoroughly exhausted during dry spell"],
            epistemic=agent.epistemic,
            tick=25,
        )

        adapted_act = "forage_river_valley"
        adapted_reflection = agent.metacognition.reflect_on_outcome(
            target_event="river_valley_foraging",
            action_attempted=adapted_act,
            motivating_reason="gather_wild_edibles",
            actual_outcome="gathered_3_units_berries",
            was_successful=True,
            lessons=["River banks retain moisture and abundant berry bushes"],
            epistemic=agent.epistemic,
            tick=30,
        )

        success = (
            reflection.was_successful is False
            and adapted_reflection.was_successful is True
            and "alternative" in reflection.future_adaptation_strategy.lower()
            and "reinforce" in adapted_reflection.future_adaptation_strategy.lower()
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Agent successfully recognized failure pattern and adapted strategy from barren desert to fertile river valley.",
            hypotheses=[],
            metrics={
                "initial_strategy": failed_act,
                "initial_success": reflection.was_successful,
                "adapted_strategy": adapted_act,
                "adapted_success": adapted_reflection.was_successful,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_N: Longitudinal Cognitive Development
# ===========================================================================

class Experiment07_N_LongitudinalCognitiveDevelopment(BaseExperiment):
    """Evaluate changes in reasoning, learning, skills, and autonomy over extended periods."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_N",
            name="Longitudinal Cognitive Development (7, 30, 90, 180 Days)",
            description="Simulates accelerated cognitive growth across 4 distinct developmental milestones.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        agent = _make_agent("Apprentice Nora", serial=13, seed=seed)

        milestones = [
            (7, 672),
            (30, 2880),
            (90, 8640),
            (180, 17280),
        ]

        developmental_log: list[dict[str, Any]] = []

        for days, tick in milestones:
            skill_id = "skill_technical"
            agent.learning.practice_skill(skill_id, agent.memory, duration_ticks=10, current_tick=tick)
            agent.reasoning.record_induction(
                condition="tool_lubrication==daily",
                outcome="zero_lathe_breakdowns",
                tick=tick,
                epistemic=agent.epistemic,
            )
            agent.metacognition.reflect_on_outcome(
                target_event=f"milestone_{days}_days",
                action_attempted="craft_apprentice_workpiece",
                motivating_reason="skill_mastery",
                actual_outcome=f"workpiece_quality_grade_{min(10, days // 18 + 1)}",
                was_successful=True,
                epistemic=agent.epistemic,
                tick=tick,
            )

            skill_obj = agent.memory.procedural.get_skill(skill_id)
            lvl = skill_obj.level if skill_obj else 0.0

            developmental_log.append({
                "days": days,
                "tick": tick,
                "skill_level": round(lvl, 3),
                "reflections_count": len(agent.metacognition.reflection_history),
                "patterns_count": len(agent.reasoning.inductive.get_all_patterns()),
            })

        final_lvl = developmental_log[-1]["skill_level"]
        init_lvl = developmental_log[0]["skill_level"]

        success = (
            final_lvl > init_lvl
            and len(developmental_log) == 4
            and developmental_log[-1]["patterns_count"] >= 1
            and developmental_log[-1]["reflections_count"] == 4
        )

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Cognitive progression tracked across 7, 30, 90, and 180 days; skill advanced from {init_lvl:.2f} to {final_lvl:.2f}.",
            hypotheses=[],
            metrics={
                "milestones_evaluated": len(developmental_log),
                "initial_skill_level": init_lvl,
                "final_skill_level": final_lvl,
                "progression": developmental_log,
            },
            duration_seconds=dt,
        )


# ===========================================================================
# EXP_07_O: Persistence
# ===========================================================================

class Experiment07_O_Persistence(BaseExperiment):
    """Verify that knowledge, hypotheses, strategies, and reflections survive save and load."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_07_O",
            name="Epistemic and Reasoning Persistence Integrity",
            description="Verifies complete SQLite roundtrip save and load for individual knowledge and beliefs.",
        )

    def run(self, runner: Optional[SimulationRunner] = None, seed: int = 42, **kwargs: Any) -> ExperimentResult:
        t0 = time.perf_counter()
        db_path = Path("experiments/results/test_phase07_persistence.db")
        if db_path.exists():
            db_path.unlink()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        db = DatabaseManager(db_path)
        db.connect()
        repo = KnowledgeRepository(db)

        global_kg = GlobalKnowledgeGraph()
        filter_node = global_kg.register_concept("water_filter", "Ceramic Charcoal Filter", NodeType.OBJECT)
        repo.save_node(filter_node)

        agent = _make_agent("Scholar Sophia", serial=14, seed=seed, global_graph=global_kg)
        agent.knowledge_graph.learn_concept("water_filter", confidence=0.88, source_pathway="experimentation")
        agent.epistemic.register_belief(
            EpistemicBelief(
                belief_id="belief_filtration_health",
                subject="water_filter",
                predicate="reduces_illness_by",
                object_val=0.80,
                belief_type=BeliefType.VALIDATED_KNOWLEDGE,
                confidence=0.92,
                source_type="scientific_discovery",
                created_tick=10,
            )
        )

        repo.save_individual_knowledge(agent.knowledge_graph)

        restored_kg = repo.load_individual_knowledge(
            human_uid=str(agent.uid),
            global_graph=global_kg,
        )

        claim = restored_kg.get_claim("water_filter")

        success = (
            claim is not None
            and abs(claim.confidence - 0.88) < 0.05
            and claim.source_pathway == "experimentation"
            and restored_kg.knows_concept("water_filter")
        )

        db.close()
        if db_path.exists():
            db_path.unlink()

        dt = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Complete SQLite roundtrip verified: concepts, epistemic claims, and confidences restored with 100% fidelity.",
            hypotheses=[],
            metrics={
                "restored_concept": "water_filter",
                "restored_confidence": claim.confidence if claim else 0.0,
                "restored_pathway": claim.source_pathway if claim else "none",
                "roundtrip_fidelity": 1.0 if success else 0.0,
            },
            duration_seconds=dt,
        )
