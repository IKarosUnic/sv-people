"""Scientific Thinking, Hypothesis Testing & Empirical Discovery for SALTBOR Phase 1.3 (Section 6).

Implements the 8-stage scientific discovery cycle:
OBSERVATION -> QUESTION -> HYPOTHESIS -> EXPERIMENTATION -> RESULT -> EVALUATION -> BELIEF_REVISION -> TRANSMISSION

Key characteristics:
1. No omniscience: agents observe noisy phenomena in their immediate environment.
2. Anomaly detection based on unexpected discrepancies between expectations and observations.
3. Testable hypothesis generation specifying proposed causal directions.
4. Experimental trials subjected to realistic environmental noise, sample size limits, and confounders.
5. Possibility of incorrect conclusions: confirmation bias and small-sample false positives/negatives.
6. Progressive Bayesian belief revision and classification into the 8 epistemic states.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import numpy as np

from saltbor.cognition.development.profile import CognitiveCapability, CognitiveProfile
from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface


class ScientificCycleStage(str, Enum):
    """The 8 formal stages of the scientific thinking cycle."""

    OBSERVATION = "observation"
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    EXPERIMENTATION = "experimentation"
    RESULT = "result"
    EVALUATION = "evaluation"
    BELIEF_REVISION = "belief_revision"
    TRANSMISSION = "transmission"


@dataclasses.dataclass
class ScientificExperiment:
    """An empirical experiment designed by an agent to test a hypothesis."""

    experiment_id: str
    hypothesis_id: str
    target_subject: str
    manipulated_variable: str
    treatment_value: float
    control_value: float
    planned_trials: int = 3
    executed_trials: int = 0
    raw_measurements: list[float] = dataclasses.field(default_factory=list)
    control_measurements: list[float] = dataclasses.field(default_factory=list)
    observed_mean_diff: float = 0.0
    is_completed: bool = False
    is_conclusive: bool = False


@dataclasses.dataclass
class ScientificCycleSession:
    """Traceable state of an active scientific inquiry."""

    session_id: str
    creator_uid: str
    stage: ScientificCycleStage
    observation: str
    question: Optional[str] = None
    hypothesis: Optional[EpistemicBelief] = None
    experiment: Optional[ScientificExperiment] = None
    evaluation_summary: Optional[str] = None
    outcome_status: str = "in_progress" # 'supported', 'refuted', 'inconclusive', 'false_conclusion'
    cycle_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    def log_stage(self, stage: ScientificCycleStage, description: str, data: Optional[dict[str, Any]] = None) -> None:
        self.stage = stage
        self.cycle_history.append({
            "stage": stage.value,
            "description": description,
            "data": data or {},
        })


class ScientificThinkingEngine:
    """Coordinates scientific questioning, experimental testing, and belief revision."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self._sessions: dict[str, ScientificCycleSession] = {}

    def get_all_sessions(self) -> list[ScientificCycleSession]:
        """Return all scientific inquiry sessions."""
        return list(self._sessions.values())

    def get_session(self, session_id: str) -> Optional[ScientificCycleSession]:
        """Retrieve a specific inquiry session."""
        return self._sessions.get(session_id)

    def start_investigation(
        self,
        creator_uid: str,
        observation: str,
        anomaly_detected: bool = True,
        tick: int = 0,
    ) -> ScientificCycleSession:
        """Stage 1: Observation & Anomaly Detection."""
        session = ScientificCycleSession(
            session_id=f"sci_{uuid4().hex[:8]}",
            creator_uid=str(creator_uid),
            stage=ScientificCycleStage.OBSERVATION,
            observation=observation,
        )
        session.log_stage(
            ScientificCycleStage.OBSERVATION,
            f"Observed phenomenon: '{observation}' (anomaly={anomaly_detected})",
            {"tick": tick},
        )
        self._sessions[session.session_id] = session
        return session

    def formulate_question(
        self,
        session: ScientificCycleSession,
        subject: str,
        variable_of_interest: str,
        tick: int = 0,
    ) -> str:
        """Stage 2: Question Formulation."""
        q = f"Why does {variable_of_interest} vary in {subject}?"
        session.question = q
        session.log_stage(ScientificCycleStage.QUESTION, q, {"subject": subject, "variable": variable_of_interest, "tick": tick})
        return q

    def generate_hypothesis(
        self,
        session: ScientificCycleSession,
        subject: str,
        predicate: str,
        proposed_effect: Any,
        prior_confidence: float = 0.50,
        context_tags: Optional[list[str]] = None,
        tick: int = 0,
    ) -> EpistemicBelief:
        """Stage 3: Hypothesis Construction."""
        hyp_id = f"hyp_{uuid4().hex[:8]}"
        hyp = EpistemicBelief(
            belief_id=hyp_id,
            subject=subject,
            predicate=predicate,
            object_val=proposed_effect,
            belief_type=BeliefType.HYPOTHESIS,
            confidence=prior_confidence,
            source_type="scientific_hypothesis",
            source_agent_id=session.creator_uid,
            provenance="autonomous_scientific_inquiry",
            context_tags=context_tags or ["scientific_inquiry"],
            created_tick=tick,
            updated_tick=tick,
            validation_status="provisional",
        )
        session.hypothesis = hyp
        session.log_stage(
            ScientificCycleStage.HYPOTHESIS,
            f"Formulated hypothesis: {subject} {predicate} {proposed_effect}",
            {"confidence": prior_confidence, "tick": tick},
        )
        return hyp

    def design_experiment(
        self,
        session: ScientificCycleSession,
        manipulated_var: str,
        treatment_val: float,
        control_val: float,
        trials: int = 3,
        tick: int = 0,
    ) -> ScientificExperiment:
        """Stage 4: Experiment Design."""
        if not session.hypothesis:
            raise ValueError("Cannot design experiment without active hypothesis.")

        exp = ScientificExperiment(
            experiment_id=f"exp_{uuid4().hex[:8]}",
            hypothesis_id=session.hypothesis.belief_id,
            target_subject=session.hypothesis.subject,
            manipulated_variable=manipulated_var,
            treatment_value=treatment_val,
            control_value=control_val,
            planned_trials=trials,
        )
        session.experiment = exp
        session.log_stage(
            ScientificCycleStage.EXPERIMENTATION,
            f"Designed experiment testing {manipulated_var} across {trials} trials",
            {"treatment": treatment_val, "control": control_val, "tick": tick},
        )
        return exp

    def run_experimental_trials(
        self,
        session: ScientificCycleSession,
        true_causal_effect: float,
        noise_std: float = 0.50,
        confounder_bias: float = 0.0,
        cognitive_profile: Optional[CognitiveProfile] = None,
        tick: int = 0,
    ) -> list[float]:
        """Stage 5: Experiment Execution & Observation of Results.

        Subject to measurement noise and confounders.
        Higher logical reasoning and pattern recognition reduce experimental error.
        """
        exp = session.experiment
        if not exp:
            raise ValueError("No experiment designed.")

        # Cognitive mitigation of measurement error
        skill_mitigation = 1.0
        if cognitive_profile:
            log_reas = cognitive_profile.get_level(CognitiveCapability.LOGICAL_REASONING)
            pat_rec = cognitive_profile.get_level(CognitiveCapability.PATTERN_RECOGNITION)
            skill_mitigation = max(0.40, 1.0 - 0.35 * (log_reas + pat_rec) / 2.0)

        effective_noise = noise_std * skill_mitigation

        for _ in range(exp.planned_trials):
            # Control measurement: baseline centered around 10.0
            ctrl_val = 10.0 + float(self.rng.normal(0.0, effective_noise))
            # Treatment measurement: baseline + true_causal_effect + confounder + noise
            treat_val = 10.0 + true_causal_effect + confounder_bias + float(self.rng.normal(0.0, effective_noise))

            exp.control_measurements.append(ctrl_val)
            exp.raw_measurements.append(treat_val)
            exp.executed_trials += 1

        exp.observed_mean_diff = float(np.mean(exp.raw_measurements) - np.mean(exp.control_measurements))
        exp.is_completed = True

        session.log_stage(
            ScientificCycleStage.RESULT,
            f"Completed {exp.executed_trials} trials: observed delta = {exp.observed_mean_diff:.3f}",
            {"mean_diff": exp.observed_mean_diff, "tick": tick},
        )
        return exp.raw_measurements

    def evaluate_and_revise(
        self,
        session: ScientificCycleSession,
        true_causal_effect: float,
        cognitive_profile: Optional[CognitiveProfile] = None,
        epistemic_interface: Optional[EpistemicInterface] = None,
        tick: int = 0,
    ) -> Tuple[str, EpistemicBelief]:
        """Stage 6 & 7: Evaluation & Belief Revision.

        Revises the hypothesis into one of the 8 epistemic states:
        - VERIFIED_KNOWLEDGE: Supported by strong, low-noise evidence across trials.
        - PROVISIONAL_KNOWLEDGE: Preliminary positive evidence.
        - REFUTED_KNOWLEDGE: Disproven by empirical contradiction.
        - CONTRADICTORY_INFO: Mixed or noisy results.
        - HYPOTHESIS: Inconclusive trials requiring further study.

        Can yield false conclusions if sample size is small ($N=1$ or $2$) or noise is large!
        """
        exp = session.experiment
        hyp = session.hypothesis
        if not exp or not hyp:
            raise ValueError("Incomplete scientific cycle session.")

        diff = exp.observed_mean_diff
        trials = exp.executed_trials

        # Causal understanding modulates critical evaluation threshold
        causal_threshold = 0.35
        if cognitive_profile:
            causal_und = cognitive_profile.get_level(CognitiveCapability.CAUSAL_UNDERSTANDING)
            causal_threshold = max(0.20, 0.50 - 0.30 * causal_und)

        # Statistical significance check
        is_positive = diff > causal_threshold
        is_negative = diff < -causal_threshold
        is_null = abs(diff) <= causal_threshold

        # Detect potential false positive or false negative
        is_truly_causal = true_causal_effect > 0.20

        if is_positive:
            evidence_str = f"Empirical trial (N={trials}): mean gain of {diff:.2f}"
            hyp.update_with_evidence(evidence=evidence_str, is_supporting=True, evidence_weight=math.sqrt(trials) * 0.5, tick=tick)

            if is_truly_causal:
                outcome = "supported"
                if trials >= 4 and len(hyp.contradiction_items) == 0:
                    hyp.belief_type = BeliefType.VERIFIED_KNOWLEDGE
                else:
                    hyp.belief_type = BeliefType.PROVISIONAL_KNOWLEDGE
            else:
                # False positive due to confounder or noise
                outcome = "false_conclusion"
                hyp.belief_type = BeliefType.PROVISIONAL_KNOWLEDGE

        elif is_negative or (is_null and trials >= 3):
            contradiction_str = f"Empirical trial (N={trials}): observed delta {diff:.2f} fails to produce expected effect"
            hyp.update_with_evidence(evidence=contradiction_str, is_supporting=False, evidence_weight=math.sqrt(trials) * 0.5, tick=tick)

            if not is_truly_causal:
                outcome = "refuted"
                hyp.belief_type = BeliefType.REFUTED_KNOWLEDGE
            else:
                outcome = "false_conclusion"
                hyp.belief_type = BeliefType.CONTRADICTORY_INFO

        else:
            outcome = "inconclusive"
            hyp.validation_status = "untested"
            hyp.belief_type = BeliefType.HYPOTHESIS

        session.outcome_status = outcome
        session.evaluation_summary = (
            f"Outcome: {outcome}. Observed delta: {diff:.3f} across {trials} trials. "
            f"Updated belief type to {hyp.belief_type.value} with confidence {hyp.confidence:.3f}."
        )

        session.log_stage(
            ScientificCycleStage.EVALUATION,
            session.evaluation_summary,
            {"outcome": outcome, "belief_type": hyp.belief_type.value, "confidence": hyp.confidence, "tick": tick},
        )
        session.log_stage(
            ScientificCycleStage.BELIEF_REVISION,
            f"Belief '{hyp.belief_id}' updated to {hyp.belief_type.value}",
            {"status": hyp.validation_status, "tick": tick},
        )

        if epistemic_interface:
            epistemic_interface.register_belief(hyp)

        return outcome, hyp

    def prepare_for_transmission(
        self,
        session: ScientificCycleSession,
        recipient_uid: str,
        tick: int = 0,
    ) -> EpistemicBelief:
        """Stage 8: Possible Social Transmission.

        Exports belief with incremented hop count and recorded provenance.
        """
        hyp = session.hypothesis
        if not hyp:
            raise ValueError("No hypothesis to transmit.")

        transmitted_belief = EpistemicBelief(
            belief_id=f"tx_{hyp.belief_id}_{uuid4().hex[:6]}",
            subject=hyp.subject,
            predicate=hyp.predicate,
            object_val=hyp.object_val,
            belief_type=hyp.belief_type,
            confidence=max(0.10, hyp.confidence * 0.90), # Transmission discount
            source_type="social_testimony",
            source_agent_id=session.creator_uid,
            provenance=f"Transmitted from {session.creator_uid} ({hyp.provenance})",
            evidence_items=list(hyp.evidence_items),
            contradiction_items=list(hyp.contradiction_items),
            transmission_lineage=hyp.transmission_lineage + [session.creator_uid],
            hop_count=hyp.hop_count + 1,
            created_tick=tick,
            updated_tick=tick,
            context_tags=list(hyp.context_tags),
            validation_status=hyp.validation_status,
        )

        session.log_stage(
            ScientificCycleStage.TRANSMISSION,
            f"Prepared belief for transmission to agent {recipient_uid} (hop {transmitted_belief.hop_count})",
            {"recipient": recipient_uid, "hop_count": transmitted_belief.hop_count, "tick": tick},
        )
        return transmitted_belief
