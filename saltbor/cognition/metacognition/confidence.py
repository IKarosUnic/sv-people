"""Calibrated Confidence Estimation for Saltbor Phase 0.7 (Section 5).

Estimates well-calibrated epistemic confidence combining:
1. Information pathway quality (direct experience > experiment > teaching > observation > rumor).
2. Quantity of accumulated empirical evidence and verification count.
3. Prior personal experience and domain familiarity.
4. Source credibility discounting for social testimonies.
5. Internal logical consistency and absence of active contradictions.
6. Contextual stability.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional


PATHWAY_RELIABILITY_WEIGHTS: dict[str, float] = {
    "direct_experience": 0.95,
    "experimentation": 0.90,
    "formal_deduction": 0.90,
    "apprenticeship": 0.85,
    "teaching": 0.80,
    "reading_records": 0.75,
    "problem_solving": 0.75,
    "environmental_exploration": 0.70,
    "observation": 0.65,
    "inductive_learning": 0.65,
    "analogical_transfer": 0.60,
    "abductive_reasoning": 0.55,
    "social_imitation": 0.50,
    "testimony": 0.45,
    "dialogue": 0.45,
    "rumor": 0.30,
}


@dataclasses.dataclass
class ConfidenceAudit:
    """Breakdown of factors contributing to calibrated confidence."""

    calibrated_confidence: float        # [0.0, 1.0]
    pathway_base_weight: float
    evidence_boost: float
    experience_boost: float
    source_discount: float
    contradiction_penalty: float
    justification: str


class CalibratedConfidenceEstimator:
    """Computes soundly calibrated confidence for claims, beliefs, and hypotheses."""

    @staticmethod
    def estimate(
        pathway: str,
        verification_count: int = 1,
        supporting_evidence_count: int = 0,
        contradiction_count: int = 0,
        source_credibility: float = 1.0,
        domain_experience_level: float = 0.5,
        has_internal_contradiction: bool = False,
    ) -> ConfidenceAudit:
        """Calculate calibrated confidence score with transparent attribution."""
        base_path = PATHWAY_RELIABILITY_WEIGHTS.get(pathway.lower(), 0.50)

        # Evidence scaling (diminishing returns)
        total_evidence = max(0, verification_count - 1) + supporting_evidence_count
        evidence_boost = min(0.30, total_evidence * 0.06)

        # Domain experience factor
        experience_boost = (domain_experience_level - 0.5) * 0.15

        # Source discounting for external testimonies
        source_discount = 1.0
        if "testimony" in pathway or "dialogue" in pathway or "rumor" in pathway:
            source_discount = max(0.2, min(1.0, source_credibility))

        # Contradiction penalties
        contra_penalty = min(0.60, contradiction_count * 0.20)
        if has_internal_contradiction:
            contra_penalty = max(contra_penalty, 0.35)

        raw_score = (base_path + evidence_boost + experience_boost) * source_discount - contra_penalty
        final_confidence = max(0.02, min(0.98, raw_score))

        justification = (
            f"Pathway '{pathway}' (base={base_path:.2f}), evidence=+{evidence_boost:.2f}, "
            f"experience=+{experience_boost:.2f}, source_discount={source_discount:.2f}, "
            f"contra_penalty=-{contra_penalty:.2f}"
        )

        return ConfidenceAudit(
            calibrated_confidence=final_confidence,
            pathway_base_weight=base_path,
            evidence_boost=evidence_boost,
            experience_boost=experience_boost,
            source_discount=source_discount,
            contradiction_penalty=contra_penalty,
            justification=justification,
        )
