"""Multidimensional Societal Identity Vector for SALTBOR Phase 1.2.1.

Captures the complete structural state of a society across 6 fundamental dimensions:
1. Demography (population, births, deaths, net migration)
2. Economy (production, liquidity, Gini inequality, debt, trade)
3. Culture (active traditions, diversity index, retained knowledge, extinctions)
4. Collective Cognition (skill proficiency, validated innovations, failures, learning rate)
5. Social Organization (trust, antagonism, institutions, cohesion)
6. Territory (infrastructure, habitability, housing, settlement status)

Allows detecting deep societal divergence even among societies with identical population sizes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class SocietalIdentityVector:
    """Multidimensional vector capturing a society's complete structural state."""

    society_id: str
    society_name: str

    # 1. Demografía
    population: int = 15
    birth_count: int = 0
    death_count: int = 0
    net_migration: int = 0

    # 2. Economía
    total_production_units: float = 100.0
    circulating_liquidity: float = 500.0
    wealth_gini: float = 0.25
    total_debt_volume: float = 0.0
    trade_volume: float = 50.0

    # 3. Cultura
    active_traditions_count: int = 3
    cultural_diversity_index: float = 0.50
    retained_knowledge_count: int = 5
    extinct_traditions_count: int = 0

    # 4. Cognición Colectiva
    mean_skill_proficiency: float = 0.45
    validated_innovations_count: int = 2
    failed_innovations_count: int = 0
    mean_learning_rate: float = 0.35

    # 5. Organización Social
    mean_trust: float = 0.65
    antagonism_index: float = 0.10
    active_institutions_count: int = 2
    community_cohesion: float = 0.70

    # 6. Territorio
    infrastructure_level: float = 0.40
    ecological_habitability: float = 0.75
    housing_capacity: int = 30
    settlement_status: str = "thriving"

    def to_normalized_vector(self) -> np.ndarray:
        """Converts the multidimensional state into an 18-element normalized numerical vector in [0.0, 1.0]."""
        return np.array([
            # Demography (4)
            min(1.0, self.population / 100.0),
            min(1.0, self.birth_count / 20.0),
            min(1.0, self.death_count / 20.0),
            max(0.0, min(1.0, (self.net_migration + 30.0) / 60.0)),
            # Economy (5)
            min(1.0, self.total_production_units / 1000.0),
            min(1.0, self.circulating_liquidity / 2000.0),
            max(0.0, min(1.0, self.wealth_gini)),
            min(1.0, self.total_debt_volume / 1000.0),
            min(1.0, self.trade_volume / 500.0),
            # Culture (3)
            min(1.0, self.active_traditions_count / 10.0),
            max(0.0, min(1.0, self.cultural_diversity_index)),
            min(1.0, self.extinct_traditions_count / 5.0),
            # Cognition (3)
            max(0.0, min(1.0, self.mean_skill_proficiency)),
            min(1.0, self.validated_innovations_count / 8.0),
            min(1.0, self.failed_innovations_count / 8.0),
            # Social Organization (3)
            max(0.0, min(1.0, self.mean_trust)),
            max(0.0, min(1.0, self.antagonism_index)),
            max(0.0, min(1.0, self.community_cohesion)),
        ], dtype=float)

    def distance(self, other: SocietalIdentityVector) -> float:
        """Calculates normalized Euclidean (L2) distance between two societal identity vectors."""
        v1 = self.to_normalized_vector()
        v2 = other.to_normalized_vector()
        return float(np.linalg.norm(v1 - v2))

    def distance_manhattan(self, other: SocietalIdentityVector) -> float:
        """Calculates Manhattan (L1) distance between two societal identity vectors."""
        v1 = self.to_normalized_vector()
        v2 = other.to_normalized_vector()
        return float(np.sum(np.abs(v1 - v2)))

    def distance_mahalanobis(
        self, other: SocietalIdentityVector, cov_inv: Optional[np.ndarray] = None
    ) -> float:
        """Calculates Mahalanobis distance using provided inverse covariance matrix or regularized identity."""
        v1 = self.to_normalized_vector()
        v2 = other.to_normalized_vector()
        diff = v1 - v2
        if cov_inv is None:
            # Fallback to normalized identity with mild regularization
            cov_inv = np.eye(len(diff))
        d_sq = float(diff.T @ cov_inv @ diff)
        return float(math.sqrt(max(0.0, d_sq)))

    def to_weighted_vector(self, weights: Optional[Dict[str, float]] = None) -> np.ndarray:
        """Converts state into a weighted normalized vector based on dimension importance."""
        v = self.to_normalized_vector()
        if not weights:
            return v
        w = np.ones(len(v), dtype=float)
        # Apply dimensional weight multipliers
        w[0:4] *= weights.get("demography", 1.0)
        w[4:9] *= weights.get("economy", 1.0)
        w[9:12] *= weights.get("culture", 1.0)
        w[12:15] *= weights.get("cognition", 1.0)
        w[15:18] *= weights.get("social", 1.0)
        return v * w

    @staticmethod
    def compute_correlation_matrix(vectors: List[SocietalIdentityVector]) -> np.ndarray:
        """Computes pairwise Pearson correlation matrix across the 18 normalized features for an ensemble."""
        if len(vectors) < 2:
            return np.eye(18)
        matrix = np.array([v.to_normalized_vector() for v in vectors])
        std = np.std(matrix, axis=0)
        std[std == 0] = 1.0  # Prevent divide-by-zero on invariant features
        norm_matrix = (matrix - np.mean(matrix, axis=0)) / std
        corr = (norm_matrix.T @ norm_matrix) / max(1, len(vectors) - 1)
        return np.clip(corr, -1.0, 1.0)

    @staticmethod
    def compute_trajectory_divergence(trajectories: List[List[SocietalIdentityVector]]) -> float:
        """Computes mean pairwise distance between societies over time trajectories."""
        if len(trajectories) < 2:
            return 0.0
        n_steps = min(len(t) for t in trajectories)
        if n_steps == 0:
            return 0.0
        total_dist = 0.0
        comparisons = 0
        for step in range(n_steps):
            for i in range(len(trajectories)):
                for j in range(i + 1, len(trajectories)):
                    total_dist += trajectories[i][step].distance(trajectories[j][step])
                    comparisons += 1
        return float(total_dist / max(1, comparisons))

    def classify_archetype(self) -> str:
        """Classifies the society into an emergent developmental archetype."""
        if self.population == 0 or self.settlement_status == "abandoned":
            return "SOCIEDAD_COLAPSADA_ABANDONADA"

        if self.settlement_status == "decaying" or self.ecological_habitability < 0.25:
            return "ASENTAMIENTO_FRAGIL_EN_DECADENCIA"

        if self.antagonism_index > 0.45 or self.mean_trust < 0.35:
            return "ENCLAVE_FACIONAL_EN_CONFLICTO"

        if self.trade_volume > 150.0 and self.circulating_liquidity > 600.0 and self.infrastructure_level > 0.60:
            return "NUCLEO_COMERCIAL_PROSPERO"

        if self.wealth_gini < 0.25 and self.community_cohesion > 0.75 and self.active_institutions_count >= 2:
            return "COMUNA_AGRARIA_COHESIVA"

        if self.validated_innovations_count >= 3 and self.mean_skill_proficiency > 0.60:
            return "POLO_INNOVADOR_ESPECIALIZADO"

        return "CASERIO_TRADICIONAL_ESTABLE"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes vector to dictionary."""
        return {
            "society_id": self.society_id,
            "society_name": self.society_name,
            "archetype": self.classify_archetype(),
            "demography": {
                "population": self.population,
                "birth_count": self.birth_count,
                "death_count": self.death_count,
                "net_migration": self.net_migration,
            },
            "economy": {
                "total_production_units": round(self.total_production_units, 2),
                "circulating_liquidity": round(self.circulating_liquidity, 2),
                "wealth_gini": round(self.wealth_gini, 3),
                "total_debt_volume": round(self.total_debt_volume, 2),
                "trade_volume": round(self.trade_volume, 2),
            },
            "culture": {
                "active_traditions_count": self.active_traditions_count,
                "cultural_diversity_index": round(self.cultural_diversity_index, 3),
                "retained_knowledge_count": self.retained_knowledge_count,
                "extinct_traditions_count": self.extinct_traditions_count,
            },
            "collective_cognition": {
                "mean_skill_proficiency": round(self.mean_skill_proficiency, 3),
                "validated_innovations_count": self.validated_innovations_count,
                "failed_innovations_count": self.failed_innovations_count,
                "mean_learning_rate": round(self.mean_learning_rate, 3),
            },
            "social_organization": {
                "mean_trust": round(self.mean_trust, 3),
                "antagonism_index": round(self.antagonism_index, 3),
                "active_institutions_count": self.active_institutions_count,
                "community_cohesion": round(self.community_cohesion, 3),
            },
            "territory": {
                "infrastructure_level": round(self.infrastructure_level, 3),
                "ecological_habitability": round(self.ecological_habitability, 3),
                "housing_capacity": self.housing_capacity,
                "settlement_status": self.settlement_status,
            },
        }
