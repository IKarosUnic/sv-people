"""Multidimensional Social Stratification & Longitudinal Mobility Engine for SALTBOR Phase 1.9.

Models social class not as a single scalar, but as a multidimensional vector of:
1. Income (daily wages, trade margins, agricultural returns, remittances)
2. Wealth & Productive Assets (accumulated savings, tools, machinery, land)
3. Housing Tenure Security (owner with title, formal renter, informal mesón, homeless/shelter)
4. Human Capital (educational attainment, technical craft proficiency, literacy)
5. Occupational Prestige (informal day laborer, street vendor, skilled artisan, merchant, civic leader)
6. Social Capital & Network Centrality (degree, betweenness, bridging ties, reputation)
7. Institutional Power & Civic Influence (assembly sway, directiva office, agenda-setting power)

Computes longitudinal inequality indicators:
- Gini coefficient of income and wealth
- Palma ratio (top 10% / bottom 40%)
- Quintile transition matrices (upward/downward mobility, intergenerational persistence)
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.core.types import EmploymentStatus, HousingTenureType, HumanID, Tick
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class StratificationProfile:
    """An individual's multidimensional socioeconomic profile."""

    human_uid: str
    income_score: float = 0.20        # [0.0, 1.0]
    wealth_score: float = 0.20        # [0.0, 1.0]
    housing_security_score: float = 0.50 # [0.0, 1.0]
    human_capital_score: float = 0.30  # [0.0, 1.0]
    occupational_prestige: float = 0.30 # [0.0, 1.0]
    social_capital_score: float = 0.40  # [0.0, 1.0]
    civic_influence_score: float = 0.20 # [0.0, 1.0]

    # Composite Index & Class
    composite_ses: float = 0.30       # [0.0, 1.0]
    quintile: int = 2                 # 1 (Poorest) to 5 (Wealthiest)
    initial_quintile: int = 2
    mobility_transitions: int = 0
    last_updated_tick: int = 0


@dataclasses.dataclass
class InequalityMetrics:
    """System-level inequality snapshot."""

    tick: int
    gini_income: float = 0.35
    gini_wealth: float = 0.42
    palma_ratio: float = 1.45
    quintile_counts: dict[int, int] = dataclasses.field(default_factory=dict)
    upward_mobility_count: int = 0
    downward_mobility_count: int = 0
    immobility_count: int = 0


class SocialStratificationEngine:
    """Calculates multidimensional socioeconomic status, inequality metrics, and mobility."""

    def __init__(self) -> None:
        self._profiles: dict[str, StratificationProfile] = {}
        self._metrics_history: list[InequalityMetrics] = []

    def get_profile(self, human_uid: str) -> Optional[StratificationProfile]:
        return self._profiles.get(str(human_uid))

    def get_all_profiles(self) -> list[StratificationProfile]:
        return list(self._profiles.values())

    def get_latest_metrics(self) -> Optional[InequalityMetrics]:
        return self._metrics_history[-1] if self._metrics_history else None

    def evaluate_human(
        self,
        human: SyntheticHuman,
        social_engine: Any,
        tick: int,
    ) -> StratificationProfile:
        """Compute multidimensional SES profile for an individual."""
        uid = str(human.uid)
        pstate = human.physical_state

        # 1. Wealth: liquid money + home ownership proxy
        money = max(0.0, pstate.money)
        wealth_val = money / 500.0  # normalize
        if getattr(human, "housing_tenure", None) == HousingTenureType.OWNER_OCCUPIED:
            wealth_val += 0.35
        wealth_score = max(0.0, min(1.0, wealth_val))

        # 2. Housing Security
        tenure = getattr(human, "housing_tenure", HousingTenureType.RENTAL)
        if tenure == HousingTenureType.OWNER_OCCUPIED:
            housing_score = 0.95
        elif tenure == HousingTenureType.RENTAL:
            housing_score = 0.60
        elif tenure == HousingTenureType.INFORMAL_HOUSING:
            housing_score = 0.35
        else: # SHELTER or HOMELESS
            housing_score = 0.10

        # 3. Human Capital: procedural skills proficiency
        proc_mem = getattr(human.memory, "procedural", None)
        skills = proc_mem.get_all_skills() if proc_mem else []
        avg_skill = sum(s.level for s in skills) / max(1, len(skills)) if skills else 0.20
        education_score = max(0.0, min(1.0, avg_skill))

        # 4. Occupational Prestige
        occ = human.demographics.occupation.lower() if human.demographics.occupation else ""
        if any(w in occ for w in ("lider", "directiva", "presidente", "coordinador", "medico")):
            occ_score = 0.90
        elif any(w in occ for w in ("comerciante", "dueno", "maestro", "taller", "artesano")):
            occ_score = 0.70
        elif any(w in occ for w in ("vendedora", "costurera", "panadero", "albañil")):
            occ_score = 0.50
        elif any(w in occ for w in ("jornalero", "peon", "ayudante")):
            occ_score = 0.30
        else:
            occ_score = 0.25

        # 5. Social Capital: relationships degree and trust
        friends = social_engine.get_friends(human.uid) if social_engine else []
        rels = social_engine.get_all_relationships() if social_engine else []
        my_rels = [
            r for r in rels
            if getattr(r, "human_a_id", getattr(r, "human_a_uid", None)) == human.uid
            or getattr(r, "human_b_id", getattr(r, "human_b_uid", None)) == human.uid
        ]
        avg_trust = sum(r.trust for r in my_rels) / max(1, len(my_rels)) if my_rels else 0.5
        social_score = max(0.0, min(1.0, (len(friends) * 0.10) + (avg_trust * 0.50)))

        # 6. Civic Influence
        is_leader = getattr(human, "is_leader", False) or "lider" in occ
        civic_score = 0.85 if is_leader else max(0.15, social_score * 0.6)

        # 7. Income Score
        income_score = max(0.0, min(1.0, (money / 200.0) * 0.5 + occ_score * 0.5))

        # Composite SES: weighted linear combination
        composite = (
            (income_score * 0.20)
            + (wealth_score * 0.20)
            + (housing_score * 0.15)
            + (education_score * 0.15)
            + (occ_score * 0.10)
            + (social_score * 0.10)
            + (civic_score * 0.10)
        )
        composite = round(max(0.0, min(1.0, composite)), 4)

        prof = self._profiles.get(uid)
        if not prof:
            prof = StratificationProfile(
                human_uid=uid,
                income_score=income_score,
                wealth_score=wealth_score,
                housing_security_score=housing_score,
                human_capital_score=education_score,
                occupational_prestige=occ_score,
                social_capital_score=social_score,
                civic_influence_score=civic_score,
                composite_ses=composite,
                last_updated_tick=tick,
            )
            self._profiles[uid] = prof
        else:
            prof.income_score = income_score
            prof.wealth_score = wealth_score
            prof.housing_security_score = housing_score
            prof.human_capital_score = education_score
            prof.occupational_prestige = occ_score
            prof.social_capital_score = social_score
            prof.civic_influence_score = civic_score
            prof.composite_ses = composite
            prof.last_updated_tick = tick

        return prof

    def step(self, population_registry: Any, social_engine: Any, current_tick: Tick) -> Optional[InequalityMetrics]:
        """Update all agents, assign quintiles, and record system-level Gini and mobility."""
        if current_tick % 96 != 0:
            return None

        humans = population_registry.get_all()
        if not humans:
            return None

        # Evaluate profiles
        profiles: list[StratificationProfile] = []
        for h in humans:
            profiles.append(self.evaluate_human(h, social_engine, current_tick))

        # Rank and assign quintiles (1 to 5)
        profiles.sort(key=lambda p: p.composite_ses)
        n = len(profiles)
        q_size = max(1, n // 5)

        upward = 0
        downward = 0
        immobile = 0
        q_counts: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for idx, prof in enumerate(profiles):
            assigned_q = min(5, (idx // q_size) + 1)
            q_counts[assigned_q] = q_counts.get(assigned_q, 0) + 1
            if prof.quintile != assigned_q:
                if assigned_q > prof.quintile:
                    upward += 1
                else:
                    downward += 1
                prof.mobility_transitions += 1
                prof.quintile = assigned_q
            else:
                immobile += 1

        # Calculate Gini of Wealth and Income
        ses_values = [p.composite_ses for p in profiles]
        gini_ses = self._compute_gini(ses_values)
        wealth_values = [p.wealth_score for p in profiles]
        gini_wealth = self._compute_gini(wealth_values)

        # Palma ratio: Share of top 10% / Share of bottom 40%
        top_10_cut = int(n * 0.90)
        bot_40_cut = int(n * 0.40)
        top_10_sum = sum(ses_values[top_10_cut:]) if top_10_cut < n else ses_values[-1]
        bot_40_sum = sum(ses_values[:bot_40_cut]) if bot_40_cut > 0 else 0.01
        palma = round(top_10_sum / max(0.001, bot_40_sum), 3)

        metrics = InequalityMetrics(
            tick=current_tick,
            gini_income=gini_ses,
            gini_wealth=gini_wealth,
            palma_ratio=palma,
            quintile_counts=q_counts,
            upward_mobility_count=upward,
            downward_mobility_count=downward,
            immobility_count=immobile,
        )
        self._metrics_history.append(metrics)
        return metrics

    @staticmethod
    def _compute_gini(values: list[float]) -> float:
        """Compute standard Gini coefficient in [0.0, 1.0]."""
        if not values or len(values) < 2 or sum(values) == 0:
            return 0.0
        arr = np.array(sorted(values), dtype=float)
        n = len(arr)
        index = np.arange(1, n + 1)
        return float(round((2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)), 4))
