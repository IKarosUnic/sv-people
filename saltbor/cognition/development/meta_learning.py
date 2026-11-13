"""Learning to Learn (Meta-Learning) Engine for SALTBOR Phase 1.3 (Section 4).

Implements second-order cognitive adaptation:
- Tracks the empirical efficacy of distinct learning strategies per individual.
- Detects recurring errors and plateaus in skill and knowledge acquisition.
- Compares strategies based on historical performance.
- Autonomously pivots between study and experimentation methods.
- Recognizes when external mentorship or peer assistance is necessary.
- Detects strategy obsolescence and develops personalized heuristics.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import math
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.cognition.development.profile import CognitiveCapability, CognitiveProfile


class LearningStrategy(str, Enum):
    """The distinct learning and exploration modalities available to an agent."""

    OBSERVATION = "observation"                     # Social modeling of skilled peers
    DELIBERATE_PRACTICE = "deliberate_practice"     # Solo repetition, targeted refinement
    FORMAL_INSTRUCTION = "formal_instruction"       # Guided pedagogy under an expert/teacher
    TRIAL_AND_ERROR = "trial_and_error"             # Unguided empirical exploration
    PEER_COLLABORATION = "peer_collaboration"       # Joint problem solving and exchange
    ANALOGICAL_INFERENCE = "analogical_inference"   # Cross-domain schema transfer


@dataclasses.dataclass
class StrategyRecord:
    """Historical track record of a learning strategy's performance for this agent."""

    strategy: LearningStrategy
    attempts_count: int = 0
    success_count: int = 0
    total_xp_gained: float = 0.0
    total_ticks_invested: int = 0
    cumulative_utility: float = 0.50     # Running estimate of strategy return in [0.05, 1.0]
    consecutive_failures: int = 0
    last_used_tick: int = 0

    @property
    def success_rate(self) -> float:
        if self.attempts_count == 0:
            return 0.50
        return self.success_count / self.attempts_count

    @property
    def xp_per_tick(self) -> float:
        if self.total_ticks_invested == 0:
            return 1.0
        return self.total_xp_gained / max(1, self.total_ticks_invested)

    def record_outcome(self, xp_gained: float, duration_ticks: int, was_successful: bool, current_tick: int) -> None:
        self.attempts_count += 1
        self.total_xp_gained += xp_gained
        self.total_ticks_invested += duration_ticks
        self.last_used_tick = current_tick

        if was_successful:
            self.success_count += 1
            self.consecutive_failures = 0
            # Upward Bayesian-like update of perceived utility
            gain_rate = xp_gained / max(1, duration_ticks)
            norm_gain = min(1.0, gain_rate / 8.0)
            self.cumulative_utility = 0.85 * self.cumulative_utility + 0.15 * norm_gain
        else:
            self.consecutive_failures += 1
            # Downward revision of perceived utility
            self.cumulative_utility = max(0.05, self.cumulative_utility * 0.80)


@dataclasses.dataclass
class MetaLearningEngine:
    """Second-order adaptation engine managing learning strategies and error heuristics."""

    human_uid: str
    strategy_records: dict[LearningStrategy, StrategyRecord] = dataclasses.field(default_factory=dict)
    current_preferred_strategy: LearningStrategy = LearningStrategy.DELIBERATE_PRACTICE
    domain_error_counts: dict[str, int] = dataclasses.field(default_factory=dict)
    recent_errors: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    plateau_threshold_attempts: int = 4
    strategy_switch_count: int = 0
    mentorship_requests_count: int = 0

    def __post_init__(self) -> None:
        if not self.strategy_records:
            for strat in LearningStrategy:
                self.strategy_records[strat] = StrategyRecord(strategy=strat)

    def select_best_strategy(
        self,
        task_domain: str,
        cognitive_profile: CognitiveProfile,
        mentor_available: bool = False,
        peers_available: bool = False,
        has_analogy_source: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> LearningStrategy:
        """Select an optimal learning strategy based on past utility, current cognitive profile, and social context."""
        scores: dict[LearningStrategy, float] = {}
        generator = rng or np.random.default_rng()

        for strat, rec in self.strategy_records.items():
            base_score = rec.cumulative_utility

            # Capability compatibility bonuses
            if strat == LearningStrategy.OBSERVATION:
                soc_fid = cognitive_profile.get_level(CognitiveCapability.SOCIAL_LEARNING_FIDELITY)
                pat_rec = cognitive_profile.get_level(CognitiveCapability.PATTERN_RECOGNITION)
                base_score *= (0.6 + 0.4 * soc_fid + 0.2 * pat_rec)
                if not mentor_available and not peers_available:
                    base_score *= 0.10  # Cannot observe if no one is around

            elif strat == LearningStrategy.DELIBERATE_PRACTICE:
                proc_lrn = cognitive_profile.get_level(CognitiveCapability.PROCEDURAL_LEARNING)
                plan_dep = cognitive_profile.get_level(CognitiveCapability.PLANNING_DEPTH)
                base_score *= (0.5 + 0.5 * proc_lrn + 0.2 * plan_dep)

            elif strat == LearningStrategy.FORMAL_INSTRUCTION:
                comm_eff = cognitive_profile.get_level(CognitiveCapability.COMMUNICATION_EFFICACY)
                soc_fid = cognitive_profile.get_level(CognitiveCapability.SOCIAL_LEARNING_FIDELITY)
                base_score *= (0.5 + 0.4 * comm_eff + 0.3 * soc_fid)
                if not mentor_available:
                    base_score *= 0.05  # Requires mentor

            elif strat == LearningStrategy.TRIAL_AND_ERROR:
                comb_creat = cognitive_profile.get_level(CognitiveCapability.COMBINATORIAL_CREATIVITY)
                env_adapt = cognitive_profile.get_level(CognitiveCapability.ENVIRONMENTAL_ADAPTABILITY)
                base_score *= (0.5 + 0.4 * comb_creat + 0.3 * env_adapt)

            elif strat == LearningStrategy.PEER_COLLABORATION:
                comm_eff = cognitive_profile.get_level(CognitiveCapability.COMMUNICATION_EFFICACY)
                base_score *= (0.6 + 0.4 * comm_eff)
                if not peers_available:
                    base_score *= 0.10

            elif strat == LearningStrategy.ANALOGICAL_INFERENCE:
                abs_thk = cognitive_profile.get_level(CognitiveCapability.ABSTRACT_THINKING)
                caus_und = cognitive_profile.get_level(CognitiveCapability.CAUSAL_UNDERSTANDING)
                base_score *= (0.5 + 0.4 * abs_thk + 0.4 * caus_und)
                if not has_analogy_source:
                    base_score *= 0.20

            # Exploration noise (Softmax / epsilon-greedy)
            noise = float(generator.normal(0.0, 0.03))
            scores[strat] = max(0.01, base_score + noise)

        chosen = max(scores.items(), key=lambda x: x[1])[0]
        if chosen != self.current_preferred_strategy:
            self.strategy_switch_count += 1
            self.current_preferred_strategy = chosen

        return chosen

    def register_learning_outcome(
        self,
        strategy: LearningStrategy,
        task_domain: str,
        xp_gained: float,
        duration_ticks: int,
        was_successful: bool,
        current_tick: int,
    ) -> None:
        """Record the empirical outcome of using a strategy."""
        rec = self.strategy_records.get(strategy)
        if rec:
            rec.record_outcome(
                xp_gained=xp_gained,
                duration_ticks=duration_ticks,
                was_successful=was_successful,
                current_tick=current_tick,
            )

        if not was_successful:
            self.domain_error_counts[task_domain] = self.domain_error_counts.get(task_domain, 0) + 1
            self.recent_errors.append({
                "tick": current_tick,
                "strategy": strategy.value,
                "domain": task_domain,
            })
            if len(self.recent_errors) > 20:
                self.recent_errors.pop(0)

    def should_seek_help(self, task_domain: str) -> bool:
        """Recognize when learning has stalled and seeking mentorship or collaboration is needed."""
        err_count = self.domain_error_counts.get(task_domain, 0)
        curr_rec = self.strategy_records.get(self.current_preferred_strategy)
        consec_fail = curr_rec.consecutive_failures if curr_rec else 0

        # Help needed if 3+ consecutive failures with current strategy or 5+ domain errors
        if consec_fail >= 3 or err_count >= self.plateau_threshold_attempts:
            self.mentorship_requests_count += 1
            return True
        return False

    def is_strategy_obsolete(self, strategy: LearningStrategy) -> bool:
        """Detect when a strategy has experienced severe diminishing returns or failure."""
        rec = self.strategy_records.get(strategy)
        if not rec or rec.attempts_count < 3:
            return False
        # Obsolete if cumulative utility fell below 0.20 or failure rate exceeds 75%
        return rec.cumulative_utility < 0.20 or (rec.consecutive_failures >= 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "human_uid": self.human_uid,
            "preferred_strategy": self.current_preferred_strategy.value,
            "switches": self.strategy_switch_count,
            "help_requests": self.mentorship_requests_count,
            "strategies": {
                s.value: {
                    "attempts": r.attempts_count,
                    "success_rate": round(r.success_rate, 3),
                    "xp_per_tick": round(r.xp_per_tick, 3),
                    "utility": round(r.cumulative_utility, 3),
                    "consecutive_failures": r.consecutive_failures,
                }
                for s, r in self.strategy_records.items()
            },
        }
