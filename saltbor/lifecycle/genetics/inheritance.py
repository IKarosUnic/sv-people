"""Synthetic genetics and inheritance model.

Implements non-deterministic, bounded transmission of biological predispositions
(temperament anchors, vitality baselines, sensory sensitivity) without genetic determinism.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

import numpy as np


@dataclasses.dataclass
class Genome:
    """Heritable biological predispositions.

    All values are bounded in [0.0, 1.0].
    These represent biological temperamental baselines and physiological tendencies,
    NOT deterministic traits, moral character, or intelligence.
    """

    temperament_openness: float = 0.5
    temperament_conscientiousness: float = 0.5
    temperament_extraversion: float = 0.5
    temperament_agreeableness: float = 0.5
    temperament_neuroticism: float = 0.5
    temperament_risk_tolerance: float = 0.5
    temperament_patience: float = 0.5
    temperament_persistence: float = 0.5
    metabolic_vitality: float = 0.5  # Baseline resilience and stamina recovery
    sensory_sensitivity: float = 0.5 # Baseline reactivity to sensory/emotional stimuli

    def to_dict(self) -> dict[str, float]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> Genome:
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: float(v) for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class GeneticsEngine:
    """Simulates parental recombination and bounded variation for offspring."""

    def __init__(self, mutation_rate: float = 0.05, rng: Optional[np.random.Generator] = None) -> None:
        self.mutation_rate = mutation_rate
        self.rng = rng or np.random.default_rng()

    def generate_random_genome(self) -> Genome:
        """Create a diverse baseline genome with random bounded values."""
        return Genome(
            temperament_openness=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_conscientiousness=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_extraversion=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_agreeableness=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_neuroticism=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_risk_tolerance=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_patience=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            temperament_persistence=float(np.clip(self.rng.normal(0.5, 0.15), 0.1, 0.9)),
            metabolic_vitality=float(np.clip(self.rng.normal(0.5, 0.12), 0.2, 0.8)),
            sensory_sensitivity=float(np.clip(self.rng.normal(0.5, 0.12), 0.2, 0.8)),
        )

    def recombine(
        self,
        parent_a: Genome,
        parent_b: Optional[Genome] = None,
    ) -> Genome:
        """Recombine parental genomes with bounded stochastic variation.

        If only one parent genome is available (e.g. unknown parent or single founder),
        the offspring receives that genome plus bounded environmental variation.
        """
        child_dict: dict[str, float] = {}
        fields = dataclasses.fields(Genome)

        for f in fields:
            val_a = getattr(parent_a, f.name)
            if parent_b is not None:
                val_b = getattr(parent_b, f.name)
                # Random parental crossover weight between 0.3 and 0.7
                alpha = self.rng.uniform(0.3, 0.7)
                blended = alpha * val_a + (1.0 - alpha) * val_b
            else:
                blended = val_a

            # Apply bounded mutation/variation (normal noise with sigma = mutation_rate)
            noise = self.rng.normal(0.0, self.mutation_rate)
            final_val = float(np.clip(blended + noise, 0.05, 0.95))
            child_dict[f.name] = round(final_val, 4)

        return Genome(**child_dict)
