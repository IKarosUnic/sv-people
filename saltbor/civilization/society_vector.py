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
        """Calculates normalized Euclidean distance between two societal identity vectors."""
        v1 = self.to_normalized_vector()
        v2 = other.to_normalized_vector()
        return float(np.linalg.norm(v1 - v2))

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
