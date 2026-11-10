"""Developmental cognitive model: memory, language, play, and caregiving needs."""

from __future__ import annotations

import dataclasses
from typing import Optional

import numpy as np

from saltbor.lifecycle.demographics.stages import (
    DEFAULT_STAGE_CONFIGS,
    DevelopmentalStage,
    StageConfig,
)


@dataclasses.dataclass
class DevelopmentalCapabilities:
    """Cognitive and behavioral capacities modulated by developmental stage."""

    stage: DevelopmentalStage
    language_proficiency: float
    motor_coordination: float
    autonomy_capacity: float
    episodic_retention: float
    attachment_bonding: float
    play_drive: float
    school_readiness: bool
    requires_caregiver: bool

    @classmethod
    def from_stage(
        cls,
        stage: DevelopmentalStage,
        stage_configs: Optional[dict[DevelopmentalStage, StageConfig]] = None,
    ) -> DevelopmentalCapabilities:
        configs = stage_configs or DEFAULT_STAGE_CONFIGS
        cfg = configs[stage]

        if stage == DevelopmentalStage.INFANCY:
            return cls(
                stage=stage,
                language_proficiency=cfg.language_proficiency,
                motor_coordination=cfg.motor_coordination,
                autonomy_capacity=cfg.autonomy_capacity,
                episodic_retention=cfg.autobiographical_memory,
                attachment_bonding=0.95,
                play_drive=0.40,
                school_readiness=False,
                requires_caregiver=True,
            )
        elif stage == DevelopmentalStage.EARLY_CHILDHOOD:
            return cls(
                stage=stage,
                language_proficiency=cfg.language_proficiency,
                motor_coordination=cfg.motor_coordination,
                autonomy_capacity=cfg.autonomy_capacity,
                episodic_retention=cfg.autobiographical_memory,
                attachment_bonding=0.85,
                play_drive=0.90,
                school_readiness=False,
                requires_caregiver=True,
            )
        elif stage == DevelopmentalStage.CHILDHOOD:
            return cls(
                stage=stage,
                language_proficiency=cfg.language_proficiency,
                motor_coordination=cfg.motor_coordination,
                autonomy_capacity=cfg.autonomy_capacity,
                episodic_retention=cfg.autobiographical_memory,
                attachment_bonding=0.70,
                play_drive=0.75,
                school_readiness=True,
                requires_caregiver=False,
            )
        elif stage == DevelopmentalStage.ADOLESCENCE:
            return cls(
                stage=stage,
                language_proficiency=cfg.language_proficiency,
                motor_coordination=cfg.motor_coordination,
                autonomy_capacity=cfg.autonomy_capacity,
                episodic_retention=cfg.autobiographical_memory,
                attachment_bonding=0.55,
                play_drive=0.40,
                school_readiness=True,
                requires_caregiver=False,
            )
        else:
            return cls(
                stage=stage,
                language_proficiency=cfg.language_proficiency,
                motor_coordination=cfg.motor_coordination,
                autonomy_capacity=cfg.autonomy_capacity,
                episodic_retention=cfg.autobiographical_memory,
                attachment_bonding=0.50,
                play_drive=0.20,
                school_readiness=False,
                requires_caregiver=False,
            )


class ChildDevelopmentEngine:
    """Manages developmental progressions and childhood learning heuristics."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()

    def get_capabilities(self, stage: DevelopmentalStage) -> DevelopmentalCapabilities:
        return DevelopmentalCapabilities.from_stage(stage)

    def filter_memory_encoding(
        self,
        stage: DevelopmentalStage,
        raw_importance: float,
    ) -> float:
        """Modulate memory retention to account for infantile amnesia.

        Events experienced in infancy (< 3 years) are retained with very low probability
        as autobiographical episodic memories, but affect emotional attachment.
        """
        caps = self.get_capabilities(stage)
        effective_importance = raw_importance * caps.episodic_retention
        return float(np.clip(effective_importance, 0.0, 1.0))

    def evaluate_caregiver_need(
        self,
        stage: DevelopmentalStage,
        hunger: float,
        energy: float,
    ) -> float:
        """Calculate urgency of caregiver assistance for infants and toddlers."""
        if stage == DevelopmentalStage.INFANCY:
            return float(np.clip(0.5 + hunger * 0.4 + (1.0 - energy) * 0.3, 0.0, 1.0))
        elif stage == DevelopmentalStage.EARLY_CHILDHOOD:
            return float(np.clip(0.3 + hunger * 0.3, 0.0, 1.0))
        return 0.0
