"""Cognitive Plasticity, Skill Transfer & Divergence Dynamics for SALTBOR Phase 1.3 (Section 5).

Implements:
- Non-linear practice curves with diminishing returns.
- Cognitive retention, forgetting, and disuse decay (Ebbinghaus-style power decay).
- Cross-skill transfer (positive synergy) and cognitive interference (negative transfer).
- Real cognitive costs: mental energy expenditure, attention limits, cognitive fatigue.
- Socio-ecological deprivation penalties: malnutrition and chronic poverty impairing capacity.
- Individual divergence dynamics from identical or near-identical initial conditions.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.cognition.development.profile import CognitiveCapability, CognitiveProfile


@dataclasses.dataclass
class SkillDomainTransferMatrix:
    """Inter-domain transfer and interference coefficients."""

    # Positive synergies between related domains
    synergies: dict[tuple[str, str], float] = dataclasses.field(default_factory=lambda: {
        ("agriculture", "botany"): 0.35,
        ("botany", "herbal_medicine"): 0.40,
        ("commerce", "accounting"): 0.45,
        ("commerce", "negotiation"): 0.35,
        ("masonry", "architecture"): 0.30,
        ("pottery", "sculpture"): 0.40,
        ("fishing", "navigation"): 0.35,
        ("cooking", "nixtamalization"): 0.50,
    })

    # Negative interference (competing motor programs or conflicting epistemic heuristics)
    interferences: dict[tuple[str, str], float] = dataclasses.field(default_factory=lambda: {
        ("rapid_speculation", "meticulous_craftsmanship"): 0.25,
        ("rigid_traditionalism", "radical_experimentation"): 0.30,
        ("informal_barter", "formal_double_entry_bookkeeping"): 0.20,
    })

    def get_transfer_coefficient(self, source_domain: str, target_domain: str) -> float:
        pair = (source_domain, target_domain)
        rev_pair = (target_domain, source_domain)
        if pair in self.synergies:
            return self.synergies[pair]
        if rev_pair in self.synergies:
            return self.synergies[rev_pair]
        return 0.0

    def get_interference_penalty(self, active_domain: str, secondary_domain: str) -> float:
        pair = (active_domain, secondary_domain)
        rev_pair = (secondary_domain, active_domain)
        if pair in self.interferences:
            return self.interferences[pair]
        if rev_pair in self.interferences:
            return self.interferences[rev_pair]
        return 0.0


class CognitivePlasticityEngine:
    """Orchestrates plastic cognitive changes, acquisition costs, transfer, and interference."""

    def __init__(self, transfer_matrix: Optional[SkillDomainTransferMatrix] = None) -> None:
        self.transfer_matrix = transfer_matrix or SkillDomainTransferMatrix()

    def calculate_practice_gain(
        self,
        current_proficiency: float,
        practice_hours: float,
        relevance_capability_level: float,
        working_memory_level: float,
        procedural_learning_level: float,
        fatigue: float = 0.0,
        deprivation_penalty: float = 0.0,
    ) -> float:
        """Compute non-linear proficiency delta via log-power practice curve.

        Headroom: (1.0 - current_proficiency)
        Cognitive bandwidth: procedural_learning * (1 - fatigue) * (1 - deprivation)
        """
        headroom = max(0.01, 1.0 - current_proficiency)
        bandwidth = (
            0.50 * procedural_learning_level
            + 0.30 * working_memory_level
            + 0.20 * relevance_capability_level
        )
        effective_bandwidth = bandwidth * (1.0 - 0.40 * fatigue) * (1.0 - deprivation_penalty)
        effective_bandwidth = max(0.10, effective_bandwidth)

        # Base practice formula with diminishing marginal returns
        # As proficiency approaches 1.0, identical hours yield progressively smaller deltas
        gain = 0.04 * (practice_hours ** 0.65) * effective_bandwidth * (headroom ** 1.2)
        return min(headroom, max(0.0005, gain))

    def calculate_disuse_atrophy(
        self,
        current_proficiency: float,
        elapsed_days_inactive: float,
        retention_capability_level: float,
        is_overlearned: bool = False,
    ) -> float:
        """Calculate skill or knowledge atrophy from prolonged inactivity (Ebbinghaus-inspired).

        Overlearned skills (proficiency > 0.85 with extensive practice) resist decay strongly.
        """
        if elapsed_days_inactive < 3.0:
            return 0.0

        retention_shield = min(0.95, 0.40 + 0.60 * retention_capability_level)
        if is_overlearned:
            retention_shield = min(0.99, retention_shield + 0.15)

        decay_rate = (1.0 - retention_shield) * 0.02
        time_factor = math.log1p(elapsed_days_inactive - 2.0)
        atrophy = current_proficiency * decay_rate * time_factor
        return min(current_proficiency - 0.05, max(0.0, atrophy))

    def compute_cross_domain_transfer(
        self,
        practiced_domain: str,
        target_domain: str,
        practice_xp: float,
    ) -> float:
        """Calculate positive transfer XP spillover to a related domain."""
        coeff = self.transfer_matrix.get_transfer_coefficient(practiced_domain, target_domain)
        if coeff <= 0.0:
            return 0.0
        return practice_xp * coeff

    def compute_interference_loss(
        self,
        active_domain: str,
        prior_domain: str,
    ) -> float:
        """Calculate negative cognitive interference between incompatible procedures."""
        penalty = self.transfer_matrix.get_interference_penalty(active_domain, prior_domain)
        return penalty * 0.05

    def compute_divergence_metric(
        self,
        profile_a: CognitiveProfile,
        profile_b: CognitiveProfile,
    ) -> dict[str, float]:
        """Quantify multi-dimensional cognitive divergence between two individuals.

        Computes:
        - Euclidean distance (L2) in 14-dimensional capability space.
        - Manhattan distance (L1).
        - Maximum capability disparity.
        """
        caps = list(CognitiveCapability)
        vec_a = np.array([profile_a.capabilities[c].current_level for c in caps])
        vec_b = np.array([profile_b.capabilities[c].current_level for c in caps])

        diff = vec_a - vec_b
        l2_dist = float(np.linalg.norm(diff))
        l1_dist = float(np.sum(np.abs(diff)))
        max_disparity = float(np.max(np.abs(diff)))

        return {
            "l2_distance": round(l2_dist, 4),
            "l1_distance": round(l1_dist, 4),
            "max_disparity": round(max_disparity, 4),
        }
