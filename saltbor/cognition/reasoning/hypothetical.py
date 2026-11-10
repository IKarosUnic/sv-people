"""Hypothetical Reasoning Engine for Saltbor Phase 0.7 (Section 2.7).

Formulates prospective future scenarios that have not yet occurred
("If I raise the price, demand might drop; if I hire an assistant, production capacity increases"),
storing predictions for subsequent empirical verification against actual future states.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface


@dataclasses.dataclass
class HypotheticalScenario:
    """A prospective future scenario prediction."""

    scenario_id: str
    condition_action: str               # e.g., 'raise_price_by_20_percent'
    predicted_consequence: str          # e.g., 'demand_decreases_by_15_percent'
    assumptions: list[str]
    confidence: float                   # Epistemic confidence in prospective claim
    expected_utility_delta: float       # Predicted utility change
    evaluation_status: str = "pending"  # 'pending', 'confirmed', 'refuted'
    actual_outcome: Optional[str] = None
    created_tick: int = 0
    resolved_tick: Optional[int] = None

    def resolve(self, actual_outcome: str, is_confirmed: bool, tick: int = 0) -> None:
        """Resolve hypothesis against observed real outcome."""
        self.actual_outcome = actual_outcome
        self.resolved_tick = tick
        if is_confirmed:
            self.evaluation_status = "confirmed"
            self.confidence = min(0.95, self.confidence + 0.25)
        else:
            self.evaluation_status = "refuted"
            self.confidence = max(0.05, self.confidence - 0.35)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "condition_action": self.condition_action,
            "prediction": self.predicted_consequence,
            "assumptions": self.assumptions,
            "confidence": round(self.confidence, 3),
            "expected_utility_delta": round(self.expected_utility_delta, 3),
            "status": self.evaluation_status,
            "actual_outcome": self.actual_outcome,
        }


class HypotheticalReasoningEngine:
    """Projects prospective hypothetical scenarios and validates them post-facto."""

    def __init__(self) -> None:
        self._scenarios: dict[str, HypotheticalScenario] = {}

    def formulate_scenario(
        self,
        condition_action: str,
        predicted_consequence: str,
        assumptions: Optional[list[str]] = None,
        confidence: float = 0.50,
        expected_utility_delta: float = 0.0,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> HypotheticalScenario:
        """Formulate a future prospective hypothetical scenario."""
        scenario_id = f"hypothet_{uuid4().hex[:8]}"
        scenario = HypotheticalScenario(
            scenario_id=scenario_id,
            condition_action=condition_action,
            predicted_consequence=predicted_consequence,
            assumptions=assumptions or [],
            confidence=confidence,
            expected_utility_delta=expected_utility_delta,
            evaluation_status="pending",
            created_tick=tick,
        )
        self._scenarios[scenario_id] = scenario

        if epistemic:
            belief = EpistemicBelief(
                belief_id=scenario_id,
                subject=condition_action,
                predicate="hypothetically_causes",
                object_val=predicted_consequence,
                belief_type=BeliefType.HYPOTHESIS,
                confidence=confidence,
                source_type="hypothetical_reasoning",
                created_tick=tick,
                updated_tick=tick,
                evidence_items=assumptions or [],
                validation_status="untested",
            )
            epistemic.register_belief(belief)

        return scenario

    def resolve_scenario(
        self,
        scenario_id: str,
        actual_outcome: str,
        is_confirmed: bool,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Optional[HypotheticalScenario]:
        """Resolve a previously formulated prospective scenario when its outcome is observed."""
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            return None

        scenario.resolve(actual_outcome=actual_outcome, is_confirmed=is_confirmed, tick=tick)

        if epistemic:
            epistemic.update_belief_with_evidence(
                belief_id_or_concept=scenario_id,
                evidence=f"Observed outcome: {actual_outcome}",
                is_supporting=is_confirmed,
                evidence_weight=1.2,
                tick=tick,
            )

        return scenario

    def get_pending_scenarios(self) -> list[HypotheticalScenario]:
        return [s for s in self._scenarios.values() if s.evaluation_status == "pending"]

    def get_all_scenarios(self) -> list[HypotheticalScenario]:
        return list(self._scenarios.values())
