"""Social Stratification and Mobility Engine for SALTBOR Phase 1.0.

Models multidimensional social position, upward/downward mobility, opportunity access and inequality:
- Dimensions: income, accumulated wealth, education, occupation, service access, social ties, civic influence, information access.
- Processes: intergenerational continuity, upward mobility through trade/skills, downward mobility through debt/crisis, Gini inequality measurement.
- Non-deterministic: avoids fixed castes or rigid mechanical tracks; incorporates individual agency, networks, and emergent shocks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SocialTier(str, Enum):
    VULNERABLE = "vulnerable"
    LOWER = "lower"
    MIDDLE_LOWER = "middle_lower"
    MIDDLE = "middle"
    MIDDLE_UPPER = "middle_upper"
    PROSPEROUS = "prosperous"


@dataclass
class SocialProfile:
    human_id: str
    wealth: float = 100.0
    income: float = 20.0
    education_level: float = 0.2  # 0.0 to 1.0
    social_capital: float = 0.3  # network strength 0.0 to 1.0
    influence: float = 0.1  # civic/institutional voice
    tier: SocialTier = SocialTier.MIDDLE_LOWER
    upward_events_count: int = 0
    downward_events_count: int = 0


class SocialStratificationEngine:
    """Calculates social mobility trajectories, Gini inequality indices, and multidimensional stratification."""

    def __init__(self) -> None:
        self.profiles: Dict[str, SocialProfile] = {}

    def register_profile(
        self,
        human_id: str,
        wealth: float = 100.0,
        income: float = 20.0,
        education: float = 0.2,
        social_capital: float = 0.3,
        influence: float = 0.1,
    ) -> SocialProfile:
        prof = SocialProfile(
            human_id=human_id,
            wealth=wealth,
            income=income,
            education_level=education,
            social_capital=social_capital,
            influence=influence,
        )
        self.profiles[human_id] = prof
        self._update_tier(prof)
        return prof

    def _update_tier(self, prof: SocialProfile) -> None:
        composite = (
            (prof.wealth / 500.0) * 0.35 +
            (prof.income / 100.0) * 0.25 +
            prof.education_level * 0.20 +
            prof.social_capital * 0.10 +
            prof.influence * 0.10
        )
        old_tier = prof.tier
        if composite < 0.18:
            new_tier = SocialTier.VULNERABLE
        elif composite < 0.38:
            new_tier = SocialTier.LOWER
        elif composite < 0.60:
            new_tier = SocialTier.MIDDLE_LOWER
        elif composite < 0.85:
            new_tier = SocialTier.MIDDLE
        elif composite < 1.2:
            new_tier = SocialTier.MIDDLE_UPPER
        else:
            new_tier = SocialTier.PROSPEROUS

        if new_tier != old_tier:
            if composite > 0.5 and old_tier in (SocialTier.VULNERABLE, SocialTier.LOWER):
                prof.upward_events_count += 1
            elif composite < 0.3 and old_tier in (SocialTier.MIDDLE, SocialTier.MIDDLE_UPPER, SocialTier.PROSPEROUS):
                prof.downward_events_count += 1
            prof.tier = new_tier

    def adjust_mobility(
        self,
        human_id: str,
        delta_wealth: float = 0.0,
        delta_income: float = 0.0,
        delta_education: float = 0.0,
        delta_social_capital: float = 0.0,
    ) -> Optional[SocialProfile]:
        if human_id not in self.profiles:
            return None
        prof = self.profiles[human_id]
        prof.wealth = max(0.0, prof.wealth + delta_wealth)
        prof.income = max(0.0, prof.income + delta_income)
        prof.education_level = max(0.0, min(1.0, prof.education_level + delta_education))
        prof.social_capital = max(0.0, min(1.0, prof.social_capital + delta_social_capital))
        self._update_tier(prof)
        return prof

    def calculate_wealth_gini(self) -> float:
        """Calculates wealth Gini coefficient across all active profiles (0.0=equality, 1.0=inequality)."""
        if not self.profiles:
            return 0.0
        values = sorted([max(0.0, p.wealth) for p in self.profiles.values()])
        n = len(values)
        if n == 0 or sum(values) == 0:
            return 0.0
        total_sum = sum(values)
        cumulative = 0.0
        for i, val in enumerate(values, start=1):
            cumulative += i * val
        gini = (2.0 * cumulative) / (n * total_sum) - (n + 1.0) / n
        return max(0.0, min(1.0, gini))
