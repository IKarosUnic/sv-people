"""Personality trait model based on the Big Five plus custom traits."""

from __future__ import annotations

import random as _random
from typing import Any, Iterator

from pydantic import BaseModel, Field


class TraitValue(BaseModel):
    """A single personality trait with base, current, and temperament values.

    The *temperament_value* is the immutable biological starting baseline.
    The *base_value* represents the evolving long-term trait level.
    The *current_value* fluctuates dynamically due to immediate experiences and
    drifts back toward base_value at *drift_rate* per tick.
    """

    base_value: float = Field(ge=0.0, le=1.0, description="Stable evolving long-term baseline.")
    current_value: float = Field(ge=0.0, le=1.0, description="Current effective value.")
    temperament_value: float = Field(default=0.5, ge=0.0, le=1.0, description="Initial biological temperament.")
    drift_rate: float = Field(
        default=0.005,
        ge=0.0,
        le=1.0,
        description="Rate at which current_value drifts toward base_value per tick.",
    )

    def model_post_init(self, __context: Any) -> None:
        # If temperament_value was not explicitly set different from default, anchor to base_value
        if self.temperament_value == 0.5 and self.base_value != 0.5:
            self.temperament_value = self.base_value

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def apply_drift(self, ticks: int = 1) -> None:
        """Move *current_value* toward *base_value* over *ticks* ticks."""
        if ticks <= 0:
            return
        diff = self.base_value - self.current_value
        # Exponential decay toward base: each tick closes the gap by drift_rate
        remaining = (1.0 - self.drift_rate) ** ticks
        self.current_value = self.base_value - diff * remaining
        # Clamp to valid range
        self.current_value = max(0.0, min(1.0, self.current_value))

    def shift_base(self, delta: float) -> None:
        """Permanently shift the base trait value (very small amounts)."""
        self.base_value = max(0.0, min(1.0, self.base_value + delta))

    def shift_current(self, delta: float) -> None:
        """Temporarily shift the current trait value."""
        self.current_value = max(0.0, min(1.0, self.current_value + delta))


# The canonical list of trait names in iteration order.
TRAIT_NAMES: tuple[str, ...] = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
    "risk_tolerance",
    "patience",
    "persistence",
)


class PersonalityTraits(BaseModel):
    """Eight-dimension personality model.

    Five dimensions come from the Big Five / OCEAN model; three additional
    custom dimensions capture risk-taking, patience, and persistence.
    """

    openness: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    conscientiousness: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    extraversion: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    agreeableness: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    neuroticism: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    risk_tolerance: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    patience: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))
    persistence: TraitValue = Field(default_factory=lambda: TraitValue(base_value=0.5, current_value=0.5))

    # Temperament classification
    temperament_name: str = Field(
        default="balanced",
        description="Qualitative temperament archetype.",
    )

    # Personal values and priorities (Schwartz-inspired)
    personal_values: dict[str, float] = Field(
        default_factory=lambda: {
            "security": 0.5,
            "achievement": 0.5,
            "benevolence": 0.5,
            "autonomy": 0.5,
            "tradition": 0.5,
        }
    )

    # Learned behavioral patterns and coping heuristics
    behavioral_patterns: dict[str, float] = Field(
        default_factory=lambda: {
            "cooperativeness": 0.5,
            "assertiveness": 0.5,
            "risk_tendency": 0.5,
            "patience_tendency": 0.5,
            "sociability": 0.5,
        }
    )

    # ------------------------------------------------------------------
    # Access helpers
    # ------------------------------------------------------------------

    def get_trait(self, name: str) -> TraitValue:
        """Return the :class:`TraitValue` for *name*."""
        if name not in TRAIT_NAMES:
            raise ValueError(f"Unknown trait: {name!r}")
        return getattr(self, name)

    def effective_value(self, trait_name: str) -> float:
        """Return the effective (current) value for the named trait."""
        return self.get_trait(trait_name).current_value

    def get_trait_value(self, name: str) -> float:
        """Alias returning the effective current value of a trait."""
        return self.effective_value(name)

    def iter_traits(self) -> Iterator[tuple[str, TraitValue]]:
        """Yield ``(name, TraitValue)`` for every trait."""
        for name in TRAIT_NAMES:
            yield name, getattr(self, name)

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def apply_drift(self, ticks: int = 1) -> None:
        """Drift all traits toward their base values."""
        for _, tv in self.iter_traits():
            tv.apply_drift(ticks)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def random(cls, rng: _random.Random | None = None) -> PersonalityTraits:
        """Generate a random personality using a Beta(2,2) distribution.

        Beta(2, 2) produces values centred around 0.5 with moderate variance,
        giving a natural-looking spread of trait values.
        """
        r = rng if rng is not None else _random.Random()

        def _rand_trait() -> TraitValue:
            if hasattr(r, "betavariate"):
                val = float(r.betavariate(2.0, 2.0))
            elif hasattr(r, "beta"):
                val = float(r.beta(2.0, 2.0))
            else:
                val = 0.5
            return TraitValue(base_value=val, current_value=val)

        return cls(
            openness=_rand_trait(),
            conscientiousness=_rand_trait(),
            extraversion=_rand_trait(),
            agreeableness=_rand_trait(),
            neuroticism=_rand_trait(),
            risk_tolerance=_rand_trait(),
            patience=_rand_trait(),
            persistence=_rand_trait(),
        )

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def summary(self) -> dict[str, float]:
        """Return a compact ``{trait_name: effective_value}`` dict."""
        return {name: tv.current_value for name, tv in self.iter_traits()}

    def __repr__(self) -> str:  # pragma: no cover
        parts = ", ".join(f"{n}={tv.current_value:.2f}" for n, tv in self.iter_traits())
        return f"PersonalityTraits({parts})"
