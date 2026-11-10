"""Economic inequality metrics, household wealth tracking, and social mobility."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.economy.credit.engine import CreditEngine
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


@dataclass
class WealthProfile:
    """An individual or household's net balance of assets and liabilities."""

    human_uid: HumanID
    liquid_cash: float
    inventory_asset_value: float
    gross_assets: float
    total_debt: float
    net_worth: float
    vulnerability_score: float  # 0.0 (resilient) to 1.0 (critically fragile)


@dataclass
class InequalitySnapshot:
    """Distributional metrics across the entire settlement at a point in time."""

    tick: Tick
    total_population: int
    mean_wealth: float
    median_wealth: float
    gini_coefficient: float
    palma_ratio: float  # Share of top 10% / Share of bottom 40%
    quintile_shares: list[float]  # Share of total wealth held by Q1 (poorest) to Q5 (richest)
    vulnerable_population_fraction: float


class EconomicMobilityEngine:
    """Computes empirical inequality metrics and traces intergenerational asset transmission."""

    def __init__(self) -> None:
        self.snapshots: list[InequalitySnapshot] = []

    @staticmethod
    def calculate_gini(values: list[float]) -> float:
        """Compute the Gini coefficient for a non-negative distribution.

        Returns float in [0.0, 1.0], where 0.0 is perfect equality.
        """
        if not values or len(values) < 2:
            return 0.0

        # Shift negative values (net debt) to 0.0 for standard Gini evaluation
        non_neg = np.array([max(0.0, v) for v in values], dtype=np.float64)
        if np.sum(non_neg) == 0.0:
            return 0.0

        non_neg = np.sort(non_neg)
        n = len(non_neg)
        index = np.arange(1, n + 1)
        gini = (2.0 * np.sum(index * non_neg) - (n + 1) * np.sum(non_neg)) / (n * np.sum(non_neg))
        return float(np.clip(gini, 0.0, 1.0))

    def evaluate_settlement_wealth(
        self,
        humans: list[SyntheticHuman],
        credit_engine: Optional[CreditEngine] = None,
        current_tick: Tick = 0,
    ) -> tuple[list[WealthProfile], InequalitySnapshot]:
        """Audit individual net worth across population and calculate macroeconomic metrics."""
        profiles: list[WealthProfile] = []
        net_worths: list[float] = []

        for h in humans:
            cash = max(0.0, h.physical_state.money)
            debt = credit_engine.get_active_debt(h.uid) if credit_engine else 0.0

            # Approximate inventory value if agent carries items
            inv_val = 0.0
            if hasattr(h, "inventory") and h.inventory:
                inv_val = getattr(h.inventory, "total_quantity", 0.0) * 3.0

            gross = cash + inv_val
            net = gross - debt
            net_worths.append(net)

            # Economic vulnerability: high if liquid funds are near zero or debt exceeds assets
            if cash < 15.0 or debt > cash * 1.5:
                vuln = min(1.0, 0.5 + (debt / max(1.0, cash + 1.0)) * 0.3)
            else:
                vuln = max(0.0, 0.3 - (cash / 200.0))

            profiles.append(
                WealthProfile(
                    human_uid=h.uid,
                    liquid_cash=round(cash, 2),
                    inventory_asset_value=round(inv_val, 2),
                    gross_assets=round(gross, 2),
                    total_debt=round(debt, 2),
                    net_worth=round(net, 2),
                    vulnerability_score=round(vuln, 3),
                )
            )

        # Distributional indicators
        sorted_nw = sorted(net_worths)
        n = len(sorted_nw)
        mean_w = float(np.mean(sorted_nw)) if n > 0 else 0.0
        median_w = float(np.median(sorted_nw)) if n > 0 else 0.0
        gini = self.calculate_gini(sorted_nw)

        # Quintile calculations
        total_positive_w = sum(max(0.0, w) for w in sorted_nw)
        quintiles = [0.0] * 5
        if total_positive_w > 0 and n >= 5:
            q_size = n // 5
            for q_idx in range(5):
                start = q_idx * q_size
                end = (q_idx + 1) * q_size if q_idx < 4 else n
                q_sum = sum(max(0.0, w) for w in sorted_nw[start:end])
                quintiles[q_idx] = round(q_sum / total_positive_w, 3)

        # Palma ratio: top 10% / bottom 40%
        top_10_sum = sum(max(0.0, w) for w in sorted_nw[int(n * 0.90) :])
        bottom_40_sum = sum(max(0.0, w) for w in sorted_nw[: int(n * 0.40)])
        palma = round(top_10_sum / bottom_40_sum, 2) if bottom_40_sum > 0.0 else 0.0

        vulnerable_count = sum(1 for p in profiles if p.vulnerability_score > 0.6)
        vuln_fraction = round(vulnerable_count / n, 3) if n > 0 else 0.0

        snapshot = InequalitySnapshot(
            tick=current_tick,
            total_population=n,
            mean_wealth=round(mean_w, 2),
            median_wealth=round(median_w, 2),
            gini_coefficient=round(gini, 3),
            palma_ratio=palma,
            quintile_shares=quintiles,
            vulnerable_population_fraction=vuln_fraction,
        )
        self.snapshots.append(snapshot)
        return profiles, snapshot

    @staticmethod
    def calculate_intergenerational_elasticity(
        parent_child_wealth_pairs: list[tuple[float, float]],
    ) -> float:
        """Measure intergenerational persistence of economic status (IGE).

        A value close to 0.0 indicates high social mobility (child wealth independent of parent).
        A value close to 1.0 indicates severe rigidity (parent wealth determines child wealth).
        """
        if len(parent_child_wealth_pairs) < 3:
            return 0.0

        parents = np.log([max(1.0, p) for p, _ in parent_child_wealth_pairs])
        children = np.log([max(1.0, c) for _, c in parent_child_wealth_pairs])

        # Slope of log-linear regression: log(y_child) = alpha + beta * log(y_parent)
        cov = np.cov(parents, children)
        if cov[0, 0] == 0:
            return 0.0
        beta = cov[0, 1] / cov[0, 0]
        return float(np.clip(beta, 0.0, 1.0))
