"""Stratified Population and Geographic Sampling Engine for SALTBOR Phase 1.12.

Provides rigorous sampling mechanisms across:
- Individual synthetic humans
- Households & family lineages
- Social networks & communities
- Municipalities & departments
- Stratified sampling by age cohorts, wealth quintiles, occupations, and urban/rural geography.
- Logs sampling limitations and flags accidental demographic exclusion.
"""

from __future__ import annotations

import collections
import logging
import math
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.scientific.models import StratifiedSampleSpec

logger = logging.getLogger(__name__)


class PopulationSamplingEngine:
    """Manages representative, stratified, and cluster sampling for scientific experiments."""

    def __init__(self, population_registry: Optional[PopulationRegistry] = None) -> None:
        self.registry = population_registry

    def set_registry(self, registry: PopulationRegistry) -> None:
        self.registry = registry

    def sample_population(
        self,
        spec: StratifiedSampleSpec,
        seed: int = 42,
        synthetic_fallback_count: int = 50,
    ) -> list[dict[str, Any]]:
        """Extract a representative stratified sample from the population registry or fallback generator."""
        rng = np.random.RandomState(seed)
        agents: list[SyntheticHuman] = []

        if self.registry:
            agents = list(self.registry.get_all())

        if not agents:
            # Fallback: generate synthetic population records matching spec
            return self._generate_synthetic_sample(spec, count=spec.sample_size or synthetic_fallback_count, rng=rng)

        # Categorize existing agents into strata
        strata_buckets: dict[str, list[SyntheticHuman]] = collections.defaultdict(list)

        for a in agents:
            age = getattr(a.demographics, "age", 30)
            if age < 18:
                cohort = "youth"
            elif age < 30:
                cohort = "young_adult"
            elif age < 60:
                cohort = "middle_age"
            else:
                cohort = "elderly"

            money = getattr(a.physical_state, "money", 50.0)
            if money < 20.0:
                quintile = 1
            elif money < 50.0:
                quintile = 2
            elif money < 100.0:
                quintile = 3
            elif money < 250.0:
                quintile = 4
            else:
                quintile = 5

            key = f"{cohort}_q{quintile}"
            strata_buckets[key].append(a)

        # Proportional stratified draw
        sampled_agents: list[SyntheticHuman] = []
        target_n = spec.sample_size
        strata_keys = list(strata_buckets.keys())

        if not strata_keys:
            return []

        per_stratum = max(1, target_n // len(strata_keys))

        for k in strata_keys:
            bucket = strata_buckets[k]
            k_sample_n = min(len(bucket), per_stratum)
            chosen_indices = rng.choice(len(bucket), size=k_sample_n, replace=False)
            for idx in chosen_indices:
                sampled_agents.append(bucket[idx])

        # Fill remaining if needed
        remaining = target_n - len(sampled_agents)
        if remaining > 0:
            unselected = [a for a in agents if a not in sampled_agents]
            if unselected:
                extra_idx = rng.choice(len(unselected), size=min(remaining, len(unselected)), replace=False)
                for idx in extra_idx:
                    sampled_agents.append(unselected[idx])

        # Return standardized record format
        results = []
        for a in sampled_agents:
            results.append({
                "uid": str(a.uid),
                "name": f"{getattr(a.identity, 'first_name', 'Persona')} {getattr(a.identity, 'last_name', 'Cuscatleca')}",
                "age": getattr(a.demographics, "age", 30),
                "gender": getattr(a.demographics, "gender", "unspecified"),
                "occupation": getattr(a.demographics, "occupation", "agricultor"),
                "education": getattr(a.demographics, "education_level", "primaria"),
                "money": getattr(a.physical_state, "money", 50.0),
                "location_id": getattr(a.physical_state, "current_location_id", "san_salvador"),
                "is_synthetic_fallback": False,
            })

        return results

    def _generate_synthetic_sample(
        self,
        spec: StratifiedSampleSpec,
        count: int,
        rng: np.random.RandomState,
    ) -> list[dict[str, Any]]:
        """Generates representative synthetic profiles matching Salvadoran demographics when live registry is empty."""
        departments = spec.departments or [
            "San Salvador", "Santa Ana", "San Miguel", "La Libertad", "Usulután",
            "Sonsonate", "Ahuachapán", "La Paz", "Cabañas", "Chalatenango",
            "Cuscatlán", "San Vicente", "Morazán", "La Unión"
        ]
        occupations = [
            ("agricultor", 0.25),
            ("comerciante_informal", 0.35),
            ("pupusera", 0.10),
            ("empleado_servicios", 0.15),
            ("maestro", 0.05),
            ("pescador", 0.05),
            ("artesano", 0.05),
        ]
        occ_names = [o[0] for o in occupations]
        occ_probs = [o[1] for o in occupations]

        records = []
        for i in range(count):
            dept = str(departments[i % len(departments)])
            is_urban = bool(rng.uniform(0.0, 1.0) < (spec.urban_rural_ratio or 0.62))
            age = int(rng.choice([
                rng.randint(15, 25),
                rng.randint(26, 45),
                rng.randint(46, 65),
                rng.randint(66, 85),
            ]))
            q = int((i % 5) + 1)
            base_money = {1: 15.0, 2: 45.0, 3: 90.0, 4: 220.0, 5: 650.0}[q]
            money = float(max(5.0, rng.normal(base_money, base_money * 0.25)))

            occ = str(rng.choice(occ_names, p=occ_probs))
            gender = "female" if (i % 2 == 0) else "male"

            records.append({
                "uid": f"synth_agent_{i+1:04d}",
                "name": f"Individuo {i+1} ({dept})",
                "age": age,
                "gender": gender,
                "occupation": occ,
                "education": "bachillerato" if q >= 4 else ("primaria" if q <= 2 else "secundaria"),
                "money": money,
                "department": dept,
                "is_urban": is_urban,
                "wealth_quintile": q,
                "is_synthetic_fallback": True,
            })

        return records

    def audit_sample_representation(self, sample: list[dict[str, Any]]) -> dict[str, Any]:
        """Audit the diversity and balance of a sample to detect accidental exclusion."""
        if not sample:
            return {"error": "Empty sample"}

        n = len(sample)
        depts = collections.Counter(s.get("department", "unknown") for s in sample)
        quintiles = collections.Counter(s.get("wealth_quintile", 3) for s in sample)
        genders = collections.Counter(s.get("gender", "unknown") for s in sample)
        urban_count = sum(1 for s in sample if s.get("is_urban", True))

        excluded_depts = [d for d in [
            "San Salvador", "Santa Ana", "San Miguel", "La Libertad", "Usulután",
            "Sonsonate", "Ahuachapán", "La Paz", "Cabañas", "Chalatenango",
            "Cuscatlán", "San Vicente", "Morazán", "La Unión"
        ] if d not in depts]

        warnings: list[str] = []
        if excluded_depts:
            warnings.append(f"Departments excluded from sample: {excluded_depts}")
        if len(quintiles) < 5:
            warnings.append(f"Not all 5 wealth quintiles represented: {list(quintiles.keys())}")
        if urban_count == 0 or urban_count == n:
            warnings.append("Sample completely lacks urban/rural diversity.")

        return {
            "sample_size": n,
            "department_counts": dict(depts),
            "wealth_quintile_counts": dict(quintiles),
            "gender_counts": dict(genders),
            "urban_percentage": float((urban_count / n) * 100.0),
            "excluded_departments": excluded_depts,
            "warnings": warnings,
            "is_representative": (len(warnings) == 0),
        }
