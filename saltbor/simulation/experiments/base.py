"""Base classes and contracts for the Behavioral Experiment System."""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.config import SimulationConfig
from saltbor.simulation.runner import SimulationRunner


@dataclass
class ExperimentConfig:
    """Configuration specification for an experiment run."""

    experiment_id: str
    name: str
    description: str
    duration_ticks: int = 96
    random_seed: int = 42
    population_size: int = 20
    custom_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Comprehensive execution outcome of an experiment."""

    experiment_id: str
    name: str
    success: bool
    summary: str
    hypotheses: list[dict[str, Any]]
    metrics: dict[str, Any]
    observed_anomalies: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    report_markdown: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)


class BaseExperiment(abc.ABC):
    """Abstract base class for behavioral validation experiments."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        self.config = config or self.default_config()

    @abc.abstractmethod
    def default_config(self) -> ExperimentConfig:
        """Provide default experiment configuration."""
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        """Execute the experiment and record empirical observations."""
        raise NotImplementedError
