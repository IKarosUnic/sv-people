"""Multidimensional Intelligence and Competency Evaluation Framework for Saltbor Phase 0.6.

Evaluates synthetic individuals across 15 non-reducible epistemic and cognitive
dimensions, avoiding single-number IQ reductions.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.learning.pathways import LearningProfile
from saltbor.knowledge.transmission.engine import KnowledgeTransmissionEngine


@dataclasses.dataclass
class MultidimensionalIntelligenceReport:
    """Quantitative diagnostics across the 15 simulated cognitive dimensions."""

    human_uid: str
    # 1. Acquisition & Retention
    learning_speed: float
    knowledge_retention: float
    # 2. Reasoning & Problem Solving
    logical_reasoning: float
    causal_reasoning: float
    analogical_reasoning: float
    problem_solving_ability: float
    knowledge_composition: float
    # 3. Scientific & Discovery
    hypothesis_generation: float
    experimental_ability: float
    error_correction: float
    # 4. Social & Pedagogical
    teaching_effectiveness: float
    knowledge_transmission: float
    adaptability: float
    # 5. Practical Competence & Transfer
    practical_skill_acquisition: float
    domain_knowledge_transfer: float
    # Aggregated Categorical Profiles (NOT a single IQ number)
    knowledge_quantity_score: float
    knowledge_quality_score: float
    reasoning_ability_score: float
    practical_competence_score: float
    learning_potential_score: float
    creative_capability_score: float


class MultidimensionalIntelligenceEvaluator:
    """Evaluates an agent's multidimensional cognitive performance."""

    @staticmethod
    def evaluate_individual(
        graph: IndividualKnowledgeGraph,
        profile: LearningProfile,
        transmission_engine: Optional[KnowledgeTransmissionEngine] = None,
        experiment_trials_conducted: int = 0,
        experiment_successes: int = 0,
    ) -> MultidimensionalIntelligenceReport:
        """Compute the 15-dimensional diagnostic report for an agent."""
        # Calculate derived metrics from actual activity
        known_nodes = graph.all_known_nodes()
        node_claims = list(graph._node_claims.values())

        # Quality: ratio of high-confidence, non-misconceptions
        valid_claims = [c for c in node_claims if not c.is_misconception and not c.is_forgotten]
        quality_ratio = len(valid_claims) / max(1, len(node_claims))
        mean_conf = sum(c.confidence for c in valid_claims) / max(1, len(valid_claims))

        # Experimental ability
        exp_score = (experiment_successes / max(1, experiment_trials_conducted)) if experiment_trials_conducted > 0 else profile.analytical_reasoning

        # Teaching metrics
        teach_eff = profile.communication_ability
        tx_volume = 0.5
        if transmission_engine:
            student_records = [tx for tx in transmission_engine.history if tx.immediate_transmitter_uid == graph.human_uid]
            if student_records:
                avg_delta = sum(tx.recipient_confidence_after - tx.recipient_confidence_before for tx in student_records) / len(student_records)
                teach_eff = max(0.1, min(1.0, 0.4 + avg_delta * 1.5))
                tx_volume = min(1.0, len(student_records) * 0.2)

        # 15 dimensions
        dim_learning_speed = profile.learning_speed
        dim_retention = profile.memory_retention
        dim_logical = profile.analytical_reasoning
        dim_causal = min(1.0, profile.analytical_reasoning * 1.1)
        dim_analogical = min(1.0, (profile.analytical_reasoning + profile.curiosity) / 2.0)
        dim_prob_solving = min(1.0, (profile.analytical_reasoning + profile.persistence) / 2.0)
        dim_composition = min(1.0, (profile.practical_aptitude + profile.analytical_reasoning) / 2.0)
        dim_hyp_gen = profile.curiosity
        dim_exp_ability = exp_score
        dim_err_corr = profile.adaptability
        dim_teach_eff = teach_eff
        dim_tx_score = tx_volume
        dim_adapt = profile.adaptability
        dim_practical = profile.practical_aptitude
        dim_domain_transfer = min(1.0, (profile.analytical_reasoning + profile.curiosity) * 0.5)

        # Categorical synthesis
        qty_score = min(1.0, len(known_nodes) / 25.0)
        qual_score = quality_ratio * mean_conf
        reason_score = (dim_logical + dim_causal + dim_analogical + dim_prob_solving) / 4.0
        prac_score = dim_practical
        learn_potential = (dim_learning_speed + dim_retention + profile.curiosity) / 3.0
        creative_score = (dim_composition + dim_hyp_gen + dim_analogical) / 3.0

        return MultidimensionalIntelligenceReport(
            human_uid=graph.human_uid,
            learning_speed=dim_learning_speed,
            knowledge_retention=dim_retention,
            logical_reasoning=dim_logical,
            causal_reasoning=dim_causal,
            analogical_reasoning=dim_analogical,
            problem_solving_ability=dim_prob_solving,
            knowledge_composition=dim_composition,
            hypothesis_generation=dim_hyp_gen,
            experimental_ability=dim_exp_ability,
            error_correction=dim_err_corr,
            teaching_effectiveness=dim_teach_eff,
            knowledge_transmission=dim_tx_score,
            adaptability=dim_adapt,
            practical_skill_acquisition=dim_practical,
            domain_knowledge_transfer=dim_domain_transfer,
            knowledge_quantity_score=qty_score,
            knowledge_quality_score=qual_score,
            reasoning_ability_score=reason_score,
            practical_competence_score=prac_score,
            learning_potential_score=learn_potential,
            creative_capability_score=creative_score,
        )
