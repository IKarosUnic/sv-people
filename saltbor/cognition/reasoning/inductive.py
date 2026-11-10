"""Inductive Reasoning Engine for Saltbor Phase 0.7 (Section 2.2).

Detects empirical patterns from repeated observations and experiences,
formulates probabilistic expectations with bounded certainty, and updates
patterns as new observations accumulate or violate previous expectations.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface


@dataclasses.dataclass
class ObservationRecord:
    """An episodic observation of conditions and observed outcome."""

    condition_key: str                  # e.g., 'market_day==Saturday', 'weather==rainy'
    observed_outcome: str               # e.g., 'high_bread_sales', 'low_foot_traffic'
    outcome_value: float = 1.0          # Numerical magnitude or binary occurrence
    tick: int = 0


@dataclasses.dataclass
class InductivePattern:
    """An empirical regularity derived from repeated observations."""

    pattern_id: str
    condition: str                      # Antecedent condition
    predicted_outcome: str              # Consequent outcome
    total_observations: int             # Total times condition occurred
    matching_observations: int          # Times condition led to predicted outcome
    confidence: float                   # Epistemic certainty in [0.0, 1.0] (never 1.0)
    last_observed_tick: int = 0
    violation_count: int = 0
    notes: str = ""

    @property
    def empirical_frequency(self) -> float:
        if self.total_observations == 0:
            return 0.0
        return self.matching_observations / self.total_observations

    def update_with_observation(
        self,
        actual_outcome: str,
        tick: int = 0,
        regularizer_k: float = 3.0,
    ) -> float:
        """Update pattern upon observing condition again."""
        self.total_observations += 1
        self.last_observed_tick = tick

        if actual_outcome == self.predicted_outcome:
            self.matching_observations += 1
        else:
            self.violation_count += 1

        # Inductive confidence formula: frequency * (n / (n + k))
        # Preserves uncertainty: small n -> low confidence even if 100% match
        freq = self.empirical_frequency
        sample_factor = self.total_observations / (self.total_observations + regularizer_k)
        self.confidence = max(0.1, min(0.92, freq * sample_factor))

        if self.violation_count > self.matching_observations:
            self.notes = "Pattern degrading: more violations than confirmations"
        else:
            self.notes = f"Pattern validated across {self.total_observations} trials (freq={freq:.2f})"

        return self.confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "condition": self.condition,
            "predicted_outcome": self.predicted_outcome,
            "total_observations": self.total_observations,
            "matching_observations": self.matching_observations,
            "violations": self.violation_count,
            "empirical_frequency": round(self.empirical_frequency, 3),
            "confidence": round(self.confidence, 3),
            "notes": self.notes,
        }


class InductiveReasoningEngine:
    """Discovers empirical regularities from episodic experience history."""

    def __init__(self, regularizer_k: float = 3.0, min_observations: int = 3) -> None:
        self.regularizer_k = regularizer_k
        self.min_observations = min_observations
        # Key: (condition, outcome) -> InductivePattern
        self._patterns: dict[tuple[str, str], InductivePattern] = {}
        # Observation history
        self._history: list[ObservationRecord] = []

    def record_observation(
        self,
        condition: str,
        outcome: str,
        value: float = 1.0,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Optional[InductivePattern]:
        """Record an observation and update or create an inductive pattern."""
        rec = ObservationRecord(
            condition_key=condition,
            observed_outcome=outcome,
            outcome_value=value,
            tick=tick,
        )
        self._history.append(rec)

        key = (condition, outcome)
        if key in self._patterns:
            pat = self._patterns[key]
            pat.update_with_observation(outcome, tick=tick, regularizer_k=self.regularizer_k)
        else:
            # Check how many times condition has appeared in history
            cond_records = [r for r in self._history if r.condition_key == condition]
            matches = [r for r in cond_records if r.observed_outcome == outcome]
            n_total = len(cond_records)
            n_match = len(matches)

            freq = n_match / max(1, n_total)
            sample_factor = n_total / (n_total + self.regularizer_k)
            conf = max(0.1, min(0.90, freq * sample_factor))

            pat = InductivePattern(
                pattern_id=f"induct_{uuid4().hex[:8]}",
                condition=condition,
                predicted_outcome=outcome,
                total_observations=n_total,
                matching_observations=n_match,
                confidence=conf,
                last_observed_tick=tick,
                violation_count=n_total - n_match,
                notes=f"Formulated from {n_total} observed instances",
            )
            self._patterns[key] = pat

        # If pattern meets threshold, register as an epistemic expectation belief
        if pat.total_observations >= self.min_observations and epistemic:
            belief = EpistemicBelief(
                belief_id=pat.pattern_id,
                subject=condition,
                predicate="inductively_predicts",
                object_val=outcome,
                belief_type=BeliefType.INFERENCE,
                confidence=pat.confidence,
                source_type="inductive_learning",
                created_tick=tick,
                updated_tick=tick,
                evidence_items=[f"Observed {pat.matching_observations}/{pat.total_observations} times"],
            )
            epistemic.register_belief(belief)

        return pat

    def evaluate_expectation(
        self,
        condition: str,
        min_confidence: float = 0.35,
    ) -> list[InductivePattern]:
        """Retrieve inductive patterns predicting consequences of this condition."""
        matches: list[InductivePattern] = []
        for (c, _), pat in self._patterns.items():
            if c == condition and pat.confidence >= min_confidence and pat.total_observations >= self.min_observations:
                matches.append(pat)
        matches.sort(key=lambda p: p.confidence, reverse=True)
        return matches

    def get_all_patterns(self) -> list[InductivePattern]:
        return list(self._patterns.values())
