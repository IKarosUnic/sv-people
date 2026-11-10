"""Demographic and developmental stages model."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional


class DevelopmentalStage(enum.Enum):
    """The biological and cognitive developmental stages of an individual."""

    INFANCY = "infancy"                  # 0–2: Dependence, sensory and early motor development
    EARLY_CHILDHOOD = "early_childhood"  # 3–5: Language, attachment, imitation, exploration
    CHILDHOOD = "childhood"              # 6–11: Education, social learning, basic skills
    ADOLESCENCE = "adolescence"          # 12–17: Identity development, autonomy, advanced learning
    EARLY_ADULTHOOD = "early_adulthood"  # 18–25: Increasing independence, vocational development
    ADULTHOOD = "adulthood"              # 26–64: Work, family, relationships, long-term goals
    OLDER_ADULTHOOD = "older_adulthood"  # 65+: Aging, changing capabilities, accumulated experience


@dataclass(frozen=True)
class StageConfig:
    """Configurable boundaries and behavioral constraints for developmental stages."""

    min_age: float
    max_age: float
    requires_caregiver: bool = False
    can_work: bool = False
    can_reproduce: bool = False
    can_attend_school: bool = False
    autonomy_capacity: float = 1.0        # 0.0 to 1.0 multiplier on goal complexity
    language_proficiency: float = 1.0     # 0.0 to 1.0 expressive vocabulary & grammar
    motor_coordination: float = 1.0       # 0.0 to 1.0 walking speed & tool agility
    autobiographical_memory: float = 1.0  # 0.0 to 1.0 fidelity of long-term episodic memory


# Default standard configurations
DEFAULT_STAGE_CONFIGS: dict[DevelopmentalStage, StageConfig] = {
    DevelopmentalStage.INFANCY: StageConfig(
        min_age=0.0,
        max_age=2.999,
        requires_caregiver=True,
        can_work=False,
        can_reproduce=False,
        can_attend_school=False,
        autonomy_capacity=0.05,
        language_proficiency=0.1,
        motor_coordination=0.2,
        autobiographical_memory=0.05,  # Infantile amnesia
    ),
    DevelopmentalStage.EARLY_CHILDHOOD: StageConfig(
        min_age=3.0,
        max_age=5.999,
        requires_caregiver=True,
        can_work=False,
        can_reproduce=False,
        can_attend_school=False,
        autonomy_capacity=0.25,
        language_proficiency=0.45,
        motor_coordination=0.55,
        autobiographical_memory=0.30,
    ),
    DevelopmentalStage.CHILDHOOD: StageConfig(
        min_age=6.0,
        max_age=11.999,
        requires_caregiver=False,
        can_work=False,
        can_reproduce=False,
        can_attend_school=True,
        autonomy_capacity=0.55,
        language_proficiency=0.75,
        motor_coordination=0.80,
        autobiographical_memory=0.70,
    ),
    DevelopmentalStage.ADOLESCENCE: StageConfig(
        min_age=12.0,
        max_age=17.999,
        requires_caregiver=False,
        can_work=True,  # Part-time / apprentice
        can_reproduce=False,
        can_attend_school=True,
        autonomy_capacity=0.85,
        language_proficiency=0.90,
        motor_coordination=0.95,
        autobiographical_memory=0.95,
    ),
    DevelopmentalStage.EARLY_ADULTHOOD: StageConfig(
        min_age=18.0,
        max_age=25.999,
        requires_caregiver=False,
        can_work=True,
        can_reproduce=True,
        can_attend_school=True,
        autonomy_capacity=1.0,
        language_proficiency=1.0,
        motor_coordination=1.0,
        autobiographical_memory=1.0,
    ),
    DevelopmentalStage.ADULTHOOD: StageConfig(
        min_age=26.0,
        max_age=64.999,
        requires_caregiver=False,
        can_work=True,
        can_reproduce=True,
        can_attend_school=False,
        autonomy_capacity=1.0,
        language_proficiency=1.0,
        motor_coordination=1.0,
        autobiographical_memory=1.0,
    ),
    DevelopmentalStage.OLDER_ADULTHOOD: StageConfig(
        min_age=65.0,
        max_age=125.0,
        requires_caregiver=False,
        can_work=True,
        can_reproduce=False,
        can_attend_school=False,
        autonomy_capacity=0.90,
        language_proficiency=1.0,
        motor_coordination=0.75,  # Gradual physical slowdown
        autobiographical_memory=0.85,
    ),
}


def get_stage_for_age(
    age_years: float,
    configs: Optional[dict[DevelopmentalStage, StageConfig]] = None,
) -> DevelopmentalStage:
    """Determine the developmental stage corresponding to an age in years."""
    table = configs or DEFAULT_STAGE_CONFIGS
    sorted_stages = sorted(table.items(), key=lambda kv: kv[1].min_age)
    for i, (stage, cfg) in enumerate(sorted_stages):
        next_min = sorted_stages[i + 1][1].min_age if i + 1 < len(sorted_stages) else float("inf")
        if cfg.min_age <= age_years < next_min:
            return stage
    return DevelopmentalStage.OLDER_ADULTHOOD if age_years >= 65.0 else DevelopmentalStage.INFANCY
