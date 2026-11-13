"""Mathematically explicit aggregation mechanisms for large-scale population simulation.

Preserves demographic moments, occupational distributions, economic balances,
and explicitly retains exceptional individuals (outliers, leaders, acute distress).
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from saltbor.population.multilevel.models import (
    CohortGroup,
    CommunityAggregate,
    PersistentIndividualRecord,
    RegionalAggregate,
)


class PopulationAggregator:
    """Computes exact statistical moments and updates aggregated simulation layers."""

    @staticmethod
    def calculate_gini(values: Sequence[float]) -> float:
        """Compute the Gini coefficient of inequality for an array of values."""
        if not values or len(values) < 2:
            return 0.0
        arr = np.sort(np.asarray(values, dtype=np.float64))
        arr = arr[arr >= 0]
        n = len(arr)
        if n == 0 or np.sum(arr) == 0:
            return 0.0
        index = np.arange(1, n + 1)
        return float((2.0 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)))

    @staticmethod
    def aggregate_to_community(
        community_id: str,
        name: str,
        district_id: str,
        center_lat: float,
        center_lon: float,
        records: list[PersistentIndividualRecord],
    ) -> CommunityAggregate:
        """Aggregate a collection of persistent individual records into a CommunityAggregate."""
        agg = CommunityAggregate(
            community_id=community_id,
            district_id=district_id,
            name=name,
            center_lat=center_lat,
            center_lon=center_lon,
            total_population=len(records),
        )

        if not records:
            return agg

        # 1. Age Cohort Distribution (18 bins of 5 years: 0-4, 5-9 ... 85+)
        cohorts = [0] * 18
        wealth_list: list[float] = []
        occupations: dict[str, int] = {}
        exceptional_uids: list[str] = []

        total_wealth = 0.0
        for r in records:
            cohort_idx = min(17, max(0, int(r.age_years // 5)))
            cohorts[cohort_idx] += 1

            occupations[r.occupation] = occupations.get(r.occupation, 0) + 1
            wealth_list.append(r.wealth)
            total_wealth += r.wealth

            # Check exceptional criteria:
            # - Leaders / VIPs
            # - Extreme wealth (> $500 or < $5)
            # - Critical need (health < 0.25 or hunger > 0.80)
            if r.is_exceptional or r.health < 0.25 or r.hunger > 0.80 or r.wealth > 500.0 or r.wealth < 5.0:
                exceptional_uids.append(r.uid)

        agg.age_cohorts = cohorts
        agg.occupations = occupations
        agg.total_wealth = round(total_wealth, 2)
        agg.mean_wealth = round(total_wealth / len(records), 2)
        agg.gini_coefficient = round(PopulationAggregator.calculate_gini(wealth_list), 4)
        agg.exceptional_uids = exceptional_uids

        return agg

    @staticmethod
    def step_community_dynamics(
        agg: CommunityAggregate,
        dt_ticks: int = 32,
        ambient_temp_c: float = 24.0,
    ) -> None:
        """Execute aggregate ODE / difference equations for LOD 3 community state over dt_ticks.

        Updates resource balances (food, water) and demographic rates.
        """
        n = agg.total_population
        if n == 0:
            return

        dt_hours = dt_ticks * 0.25  # 1 tick = 15 mins = 0.25 hours

        # 1. Aggregate Food & Water Consumption
        # Base consumption: 0.25 kg food/day/person, 2.5 L water/day/person (scaled by temperature)
        temp_factor = 1.0 + max(0.0, (ambient_temp_c - 20.0) * 0.04)
        daily_food_per_person = 0.25
        daily_water_per_person = 2.5 * temp_factor

        hours_fraction = dt_hours / 24.0
        food_consumed = n * daily_food_per_person * hours_fraction
        water_consumed = n * daily_water_per_person * hours_fraction

        agg.food_reserves_kg = max(0.0, agg.food_reserves_kg - food_consumed)
        agg.water_reserves_liters = max(0.0, agg.water_reserves_liters - water_consumed)

        # 2. Aggregate Production (Cobb-Douglas Y = A * K^alpha * L^beta)
        # Working population: cohorts 3 to 12 (ages 15 to 64)
        working_pop = sum(agg.age_cohorts[3:13])
        A = 1.2 # Total factor productivity
        K = 100.0 # Community infrastructure / land
        L = max(1.0, float(working_pop))
        alpha = 0.3
        beta = 0.7

        # Resource stress dampener
        food_adequacy = min(1.0, agg.food_reserves_kg / max(1.0, (n * 2.0)))
        production_rate = A * (K ** alpha) * (L ** beta) * food_adequacy
        produced_units = production_rate * hours_fraction

        # Reinvest portion into food reserves
        agg.daily_production_units = round(production_rate, 2)
        agg.food_reserves_kg += produced_units * 0.4 # Agricultural yield conversion

    @staticmethod
    def aggregate_to_region(
        region_id: str,
        name: str,
        polygon_id: str,
        area_sqkm: float,
        communities: list[CommunityAggregate],
    ) -> RegionalAggregate:
        """Aggregate multiple communities into an LOD 4 RegionalAggregate."""
        total_pop = sum(c.total_population for c in communities)
        density = total_pop / max(0.1, area_sqkm)

        return RegionalAggregate(
            region_id=region_id,
            name=name,
            polygon_id=polygon_id,
            population_density_sqkm=round(density, 2),
            total_population=total_pop,
            active_communities_count=len(communities),
            environmental_stress=0.25,
            gdp_index=1.05,
        )
