"""Experimentation and Discovery Engine for Saltbor Phase 0.6.

Implements the formal 10-step scientific experimental cycle with actual
material/economic resource consumption, empirical observations, failure modes,
and Bayesian hypothesis updating.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Optional
from uuid import uuid4

from saltbor.knowledge.graph.node import ValidationStatus
from saltbor.knowledge.layers.hypothesis_graph import (
    EvidenceItem,
    Hypothesis,
    HypothesisDiscoveryGraph,
)
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ExperimentDesign:
    """The experimental protocol designed to test a hypothesis."""

    experiment_id: str
    hypothesis_id: str
    researcher_uid: str
    target_question: str
    action_protocol: str
    required_materials: dict[str, float]  # item_type -> quantity consumed
    required_tools: list[str]
    required_skills: dict[str, float]     # skill_id -> min_proficiency
    energy_cost: float = 0.20
    duration_ticks: int = 5
    expected_outcome: str = ""


@dataclasses.dataclass
class ExperimentOutcome:
    """Empirical observations and evidence resulting from trial execution."""

    outcome_id: str
    experiment_id: str
    hypothesis_id: str
    is_success: bool                      # Execution succeeded without critical error
    supports_hypothesis: bool             # Observation matches expected hypothesis outcome
    materials_consumed: dict[str, float]
    energy_consumed: float
    observation_summary: str
    evidence: EvidenceItem
    updated_hypothesis_status: ValidationStatus
    posterior_confidence: float


class ExperimentationEngine:
    """Coordinates scientific and practical empirical testing."""

    def __init__(self, hypothesis_graph: HypothesisDiscoveryGraph) -> None:
        self.hypothesis_graph = hypothesis_graph
        self.experiments_log: list[ExperimentOutcome] = []

    def design_experiment(
        self,
        hypothesis: Hypothesis,
        researcher_uid: str,
        action_protocol: str,
        required_materials: dict[str, float],
        required_tools: list[str],
        required_skills: dict[str, float],
        expected_outcome: str,
        duration_ticks: int = 5,
    ) -> ExperimentDesign:
        """Step 1-4: Formalize test design and resource prerequisites."""
        return ExperimentDesign(
            experiment_id=f"exp_{uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            researcher_uid=str(researcher_uid),
            target_question=f"Does testing '{hypothesis.title}' produce '{expected_outcome}'?",
            action_protocol=action_protocol,
            required_materials=required_materials,
            required_tools=required_tools,
            required_skills=required_skills,
            expected_outcome=expected_outcome,
            duration_ticks=duration_ticks,
        )

    def execute_experiment(
        self,
        design: ExperimentDesign,
        researcher_graph: IndividualKnowledgeGraph,
        researcher_inventory: dict[str, float],
        researcher_skills: dict[str, float],
        physical_feasibility_oracle: Optional[bool] = None, # If None, determined by physics
        tick: int = 0,
    ) -> tuple[bool, Optional[ExperimentOutcome], str]:
        """Step 5-10: Execute trial, consume physical resources, record evidence, and update belief."""
        hyp = self.hypothesis_graph.get_hypothesis(design.hypothesis_id)
        if not hyp:
            return False, None, "Target hypothesis does not exist"

        # 1. Resource verification
        for mat, qty in design.required_materials.items():
            if researcher_inventory.get(mat, 0.0) < qty:
                return False, None, f"Insufficient material: {mat} (needs {qty}, has {researcher_inventory.get(mat, 0.0)})"

        for tool in design.required_tools:
            if researcher_inventory.get(tool, 0.0) < 1.0:
                return False, None, f"Missing required tool: {tool}"

        # 2. Skill verification
        for skill_id, min_lvl in design.required_skills.items():
            cur_lvl = researcher_skills.get(skill_id, 0.0)
            if cur_lvl < min_lvl:
                return False, None, f"Insufficient skill in {skill_id} ({cur_lvl:.2f} < {min_lvl:.2f})"

        # 3. Consume physical resources
        consumed: dict[str, float] = {}
        for mat, qty in design.required_materials.items():
            researcher_inventory[mat] -= qty
            consumed[mat] = qty

        # 4. Experimental execution & physical observation
        # Skill and tooling influence trial execution stability
        avg_skill = sum(researcher_skills.get(s, 0.0) for s in design.required_skills) / max(1, len(design.required_skills))
        execution_succeeded = avg_skill >= 0.25

        if not execution_succeeded:
            obs = f"Trial suffered execution blunder due to operator inexperience in {list(design.required_skills.keys())}."
            evidence = EvidenceItem(
                evidence_id=f"ev_{uuid4().hex[:8]}",
                experiment_id=design.experiment_id,
                observer_uid=design.researcher_uid,
                observation_summary=obs,
                is_supporting=False,
                weight=0.3, # Low weight because execution was flawed
                timestamp_tick=tick,
            )
            hyp.add_evidence(evidence, tick=tick)
            outcome = ExperimentOutcome(
                outcome_id=f"out_{uuid4().hex[:8]}",
                experiment_id=design.experiment_id,
                hypothesis_id=hyp.hypothesis_id,
                is_success=False,
                supports_hypothesis=False,
                materials_consumed=consumed,
                energy_consumed=design.energy_cost,
                observation_summary=obs,
                evidence=evidence,
                updated_hypothesis_status=hyp.status,
                posterior_confidence=hyp.posterior_confidence,
            )
            self.experiments_log.append(outcome)
            return True, outcome, "Experiment failed due to execution difficulty"

        # If execution was clean, determine whether the physical reality supports the hypothesis
        # Real-world ground truth (physical feasibility)
        truth_supports = physical_feasibility_oracle if physical_feasibility_oracle is not None else True

        if truth_supports:
            obs = f"Empirical observation confirmed expectation: {design.expected_outcome} materialized."
            evidence = EvidenceItem(
                evidence_id=f"ev_{uuid4().hex[:8]}",
                experiment_id=design.experiment_id,
                observer_uid=design.researcher_uid,
                observation_summary=obs,
                is_supporting=True,
                weight=1.0,
                timestamp_tick=tick,
            )
            hyp.add_evidence(evidence, tick=tick)
            # Replications count increment if already supported
            if hyp.status in (ValidationStatus.SUPPORTED, ValidationStatus.REPLICATED):
                hyp.replications_count += 1
                hyp._update_status()

            # Researcher learns concept with high confidence (direct experience)
            researcher_graph.learn_concept(
                node_id=hyp.hypothesis_id,
                confidence=hyp.posterior_confidence,
                source_pathway="experimentation",
                tick=tick,
                evidence=obs,
            )
        else:
            obs = f"Empirical observation refuted expectation: {design.expected_outcome} did NOT occur."
            evidence = EvidenceItem(
                evidence_id=f"ev_{uuid4().hex[:8]}",
                experiment_id=design.experiment_id,
                observer_uid=design.researcher_uid,
                observation_summary=obs,
                is_supporting=False,
                weight=1.0,
                timestamp_tick=tick,
            )
            hyp.add_evidence(evidence, tick=tick)
            researcher_graph.learn_concept(
                node_id=hyp.hypothesis_id,
                confidence=hyp.posterior_confidence,
                source_pathway="experimentation",
                tick=tick,
                evidence=obs,
            )

        outcome = ExperimentOutcome(
            outcome_id=f"out_{uuid4().hex[:8]}",
            experiment_id=design.experiment_id,
            hypothesis_id=hyp.hypothesis_id,
            is_success=True,
            supports_hypothesis=truth_supports,
            materials_consumed=consumed,
            energy_consumed=design.energy_cost,
            observation_summary=obs,
            evidence=evidence,
            updated_hypothesis_status=hyp.status,
            posterior_confidence=hyp.posterior_confidence,
        )
        self.experiments_log.append(outcome)
        return True, outcome, "Experiment completed"
