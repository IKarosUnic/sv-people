"""Individual Cognitive Development Engine for SALTBOR Phase 1.3 (Section 3).

Maintains a dynamic, multi-dimensional cognitive profile across 14 differentiated
capabilities. Rejects single-IQ scalar indicators in favor of partially independent
traits subject to cognitive trade-offs, mental budget constraints, environmental
pressures, and developmental life-cycle dynamics.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import math
from typing import Any, Dict, List, Optional
import numpy as np


class CognitiveCapability(str, Enum):
    """The 14 differentiated cognitive capabilities required by SALTBOR Phase 1.3."""

    LOGICAL_REASONING = "logical_reasoning"
    WORKING_MEMORY_CAPACITY = "working_memory_capacity"
    EPISODIC_SEMANTIC_RETENTION = "episodic_semantic_retention"
    CAUSAL_UNDERSTANDING = "causal_understanding"
    PROBLEM_SOLVING_ABILITY = "problem_solving_ability"
    ABSTRACT_THINKING = "abstract_thinking"
    PROCEDURAL_LEARNING = "procedural_learning"
    PATTERN_RECOGNITION = "pattern_recognition"
    COMBINATORIAL_CREATIVITY = "combinatorial_creativity"
    PLANNING_DEPTH = "planning_depth"
    COMMUNICATION_EFFICACY = "communication_efficacy"
    SOCIAL_LEARNING_FIDELITY = "social_learning_fidelity"
    ENVIRONMENTAL_ADAPTABILITY = "environmental_adaptability"
    METACOGNITIVE_ACCURACY = "metacognitive_accuracy"


# Map each capability to its core domain for trade-offs
CAPABILITY_DOMAINS: dict[CognitiveCapability, str] = {
    CognitiveCapability.LOGICAL_REASONING: "analytical",
    CognitiveCapability.WORKING_MEMORY_CAPACITY: "attentional",
    CognitiveCapability.EPISODIC_SEMANTIC_RETENTION: "mnemic",
    CognitiveCapability.CAUSAL_UNDERSTANDING: "analytical",
    CognitiveCapability.PROBLEM_SOLVING_ABILITY: "executive",
    CognitiveCapability.ABSTRACT_THINKING: "analytical",
    CognitiveCapability.PROCEDURAL_LEARNING: "practical",
    CognitiveCapability.PATTERN_RECOGNITION: "perceptual",
    CognitiveCapability.COMBINATORIAL_CREATIVITY: "generative",
    CognitiveCapability.PLANNING_DEPTH: "executive",
    CognitiveCapability.COMMUNICATION_EFFICACY: "social",
    CognitiveCapability.SOCIAL_LEARNING_FIDELITY: "social",
    CognitiveCapability.ENVIRONMENTAL_ADAPTABILITY: "practical",
    CognitiveCapability.METACOGNITIVE_ACCURACY: "reflective",
}


@dataclasses.dataclass
class CapabilityMetric:
    """State of an individual cognitive capability."""

    capability: CognitiveCapability
    base_level: float = 0.50             # Genetic / developmental baseline in [0.05, 1.0]
    current_level: float = 0.50          # Current effective level in [0.05, 1.0]
    practice_ticks: int = 0              # Cumulative time spent engaged in tasks requiring this capability
    last_engaged_tick: int = 0           # Simulation tick when last practiced or taxed
    learning_rate: float = 1.0           # Individual acquisition velocity multiplier
    fatigue: float = 0.0                 # Temporary cognitive fatigue [0.0, 1.0]

    def effective_level(self, deprivation_penalty: float = 0.0) -> float:
        """Effective capacity accounting for fatigue and physical deprivation (hunger, poverty, stress)."""
        level = self.current_level * (1.0 - 0.40 * self.fatigue)
        level = level * (1.0 - deprivation_penalty)
        return max(0.05, min(1.0, level))


@dataclasses.dataclass
class CognitiveProfile:
    """Dynamic, multi-dimensional cognitive profile of an autonomous individual.

    Invariants:
    1. No monolithic IQ; 14 differentiated capabilities.
    2. Zero-sum and sub-additive cognitive budget constraints prevent simultaneous maximums across all 14.
    3. Practice curves follow power law with diminishing returns.
    4. Extended disuse triggers graceful atrophy.
    5. Environmental shocks, chronic stress, and poverty inflict temporary or persistent capacity constraints.
    """

    human_uid: str
    capabilities: dict[CognitiveCapability, CapabilityMetric] = dataclasses.field(default_factory=dict)
    cognitive_budget_capacity: float = 8.40   # Maximum sustainable sum of 14 capabilities (average ~0.60 each)
    chronic_stress: float = 0.0                # Accumulated chronic stress [0.0, 1.0]
    developmental_age_years: float = 25.0      # Biological age influencing fluid vs crystallized balance
    total_learning_experiences: int = 0
    specialization_domain: Optional[str] = None # e.g., 'practical', 'analytical', 'social'

    def __post_init__(self) -> None:
        if not self.capabilities:
            for cap in CognitiveCapability:
                self.capabilities[cap] = CapabilityMetric(
                    capability=cap,
                    base_level=0.50,
                    current_level=0.50,
                )

    @classmethod
    def create_default(
        cls,
        human_uid: str,
        age: float = 25.0,
        rng: Optional[np.random.Generator] = None,
        bias_domain: Optional[str] = None,
    ) -> CognitiveProfile:
        """Instantiate a realistic, slightly heterogeneous cognitive profile."""
        generator = rng or np.random.default_rng()
        profile = cls(human_uid=str(human_uid), developmental_age_years=age)

        for cap in CognitiveCapability:
            domain = CAPABILITY_DOMAINS[cap]
            # Baseline with mild natural variation centered at 0.50, std 0.08
            raw_val = float(generator.normal(0.50, 0.08))
            if bias_domain and domain == bias_domain:
                raw_val += 0.15

            val = max(0.15, min(0.85, raw_val))
            profile.capabilities[cap] = CapabilityMetric(
                capability=cap,
                base_level=val,
                current_level=val,
                practice_ticks=int(generator.integers(10, 50)),
            )

        profile._enforce_budget_constraints()
        return profile

    def get_level(self, cap: CognitiveCapability, deprivation_penalty: float = 0.0) -> float:
        """Query effective level of a capability."""
        if cap in self.capabilities:
            return self.capabilities[cap].effective_level(deprivation_penalty)
        return 0.50

    def get_all_levels(self, deprivation_penalty: float = 0.0) -> dict[str, float]:
        """Return dict of all 14 effective capabilities."""
        return {
            cap.value: self.get_level(cap, deprivation_penalty)
            for cap in CognitiveCapability
        }

    def train_capability(
        self,
        cap: CognitiveCapability,
        effort_intensity: float = 1.0,
        duration_ticks: int = 1,
        current_tick: int = 0,
        plasticity_multiplier: float = 1.0,
    ) -> float:
        """Engage in focused practice or intellectual labor taxing a capability.

        Follows an asymptotic power law of practice with diminishing marginal returns.
        """
        metric = self.capabilities.get(cap)
        if not metric:
            return 0.0

        old_level = metric.current_level
        metric.practice_ticks += duration_ticks
        metric.last_engaged_tick = current_tick
        self.total_learning_experiences += 1

        # Diminishing returns: the higher the capability, the more effort required
        # Headroom: (1.0 - current_level)
        headroom = max(0.01, 1.0 - metric.current_level)
        
        # Plasticity decreases with age for fluid abilities, but crystallized abilities retain plasticity
        age_plasticity = self._get_age_plasticity(cap)
        
        delta = (
            0.008
            * effort_intensity
            * duration_ticks
            * metric.learning_rate
            * plasticity_multiplier
            * age_plasticity
            * headroom
        )

        metric.current_level = min(0.98, metric.current_level + delta)
        
        # Training induces mild domain-specific cognitive fatigue
        metric.fatigue = min(0.40, metric.fatigue + 0.01 * effort_intensity)

        # Enforce budget trade-offs across non-practiced domains if budget is exceeded
        self._enforce_budget_constraints(favored_cap=cap)

        return metric.current_level - old_level

    def rest_and_recover(self, rest_intensity: float = 1.0) -> None:
        """Recover from cognitive fatigue and acute stress."""
        recovery = 0.25 * rest_intensity
        for metric in self.capabilities.values():
            metric.fatigue = max(0.0, metric.fatigue - recovery)
        self.chronic_stress = max(0.0, self.chronic_stress - 0.02 * rest_intensity)

    def apply_disuse_atrophy(self, current_tick: int, threshold_ticks: int = 960) -> dict[str, float]:
        """Gradual capability atrophy caused by prolonged lack of practice.

        Capabilities do not decay below base_level * 0.70.
        """
        atrophied: dict[str, float] = {}
        for cap, metric in self.capabilities.items():
            if metric.last_engaged_tick > 0:
                elapsed = current_tick - metric.last_engaged_tick
                if elapsed > threshold_ticks:
                    days_inactive = (elapsed - threshold_ticks) / 96.0  # 96 ticks per day
                    # Modest decay: ~0.005 per inactive week
                    decay = min(0.15, days_inactive * 0.003)
                    min_floor = max(0.10, metric.base_level * 0.70)
                    if metric.current_level > min_floor:
                        loss = min(decay, metric.current_level - min_floor)
                        metric.current_level -= loss
                        atrophied[cap.value] = loss
        return atrophied

    def apply_environmental_stress(self, stress_impact: float, is_chronic: bool = False) -> None:
        """Environmental hardship, hunger, or conflict taxes working memory and planning."""
        if is_chronic:
            self.chronic_stress = min(1.0, self.chronic_stress + stress_impact * 0.15)
        else:
            for cap in [CognitiveCapability.WORKING_MEMORY_CAPACITY, CognitiveCapability.PLANNING_DEPTH]:
                if cap in self.capabilities:
                    self.capabilities[cap].fatigue = min(1.0, self.capabilities[cap].fatigue + stress_impact * 0.20)

    def _get_age_plasticity(self, cap: CognitiveCapability) -> float:
        """Developmental life-cycle modulation:

        - Youth (age < 20): High fluid plasticity, lower initial crystallized retention.
        - Prime Adulthood (20-55): Balanced plasticity.
        - Senescence (age > 60): Fluid abilities (working memory, processing speed) decline in plasticity,
          while crystallized abilities (causal understanding, semantic retention, metacognition) persist.
        """
        domain = CAPABILITY_DOMAINS[cap]
        age = self.developmental_age_years

        if age < 18:
            return 1.40  # Highly plastic young mind
        elif age <= 50:
            return 1.00  # Stable adult learning
        else:
            # Over 50
            if domain in ("mnemic", "analytical", "reflective"):
                # Crystallized wisdom and causal understanding remain plastic
                return max(0.60, 1.0 - (age - 50) * 0.005)
            else:
                # Fluid processing and rapid working memory slow down
                return max(0.25, 1.0 - (age - 50) * 0.020)

    def _enforce_budget_constraints(self, favored_cap: Optional[CognitiveCapability] = None) -> None:
        """Enforces cognitive budget: an agent cannot master all 14 dimensions simultaneously.

        Specialization leads to trade-offs in unexercised domains.
        """
        current_sum = sum(m.current_level for m in self.capabilities.values())
        if current_sum <= self.cognitive_budget_capacity:
            return

        excess = current_sum - self.cognitive_budget_capacity
        other_caps = [c for c in self.capabilities.keys() if c != favored_cap]
        if not other_caps:
            return

        # Distribute tiny decrement across other capabilities, respecting base floors
        reduction_per_cap = excess / len(other_caps)
        for c in other_caps:
            metric = self.capabilities[c]
            floor = max(0.08, metric.base_level * 0.60)
            if metric.current_level > floor:
                metric.current_level = max(floor, metric.current_level - reduction_per_cap * 0.6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "human_uid": self.human_uid,
            "age": round(self.developmental_age_years, 1),
            "chronic_stress": round(self.chronic_stress, 3),
            "total_experiences": self.total_learning_experiences,
            "capabilities": {
                cap.value: {
                    "base": round(m.base_level, 3),
                    "current": round(m.current_level, 3),
                    "effective": round(m.effective_level(), 3),
                    "practice_ticks": m.practice_ticks,
                    "fatigue": round(m.fatigue, 3),
                }
                for cap, m in self.capabilities.items()
            },
        }
