"""Learning pathways and profile models for autonomous knowledge acquisition."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class LearningPathway(str, enum.Enum):
    """The 12 distinct learning channels defined for Saltbor Phase 0.6."""

    DIRECT_EXPERIENCE = "direct_experience"
    OBSERVATION = "observation"
    TEACHING = "teaching"
    APPRENTICESHIP = "apprenticeship"
    DIALOGUE = "dialogue"
    READING_RECORDS = "reading_records"
    EXPERIMENTATION = "experimentation"
    TRIAL_AND_ERROR = "trial_and_error"
    PROBLEM_SOLVING = "problem_solving"
    SOCIAL_IMITATION = "social_imitation"
    ENVIRONMENTAL_EXPLORATION = "environmental_exploration"
    REFLECTION = "reflection"


# Baseline confidence multipliers and retention biases per pathway
PATHWAY_CONFIDENCE_WEIGHTS: dict[LearningPathway, float] = {
    LearningPathway.DIRECT_EXPERIENCE: 0.95,
    LearningPathway.EXPERIMENTATION: 0.90,
    LearningPathway.APPRENTICESHIP: 0.85,
    LearningPathway.TEACHING: 0.80,
    LearningPathway.PROBLEM_SOLVING: 0.75,
    LearningPathway.READING_RECORDS: 0.70,
    LearningPathway.OBSERVATION: 0.65,
    LearningPathway.REFLECTION: 0.60,
    LearningPathway.TRIAL_AND_ERROR: 0.55,
    LearningPathway.SOCIAL_IMITATION: 0.50,
    LearningPathway.DIALOGUE: 0.45,
    LearningPathway.ENVIRONMENTAL_EXPLORATION: 0.70,
}


@dataclass
class LearningProfile:
    """Individual cognitive traits governing learning behavior and speed."""

    learning_speed: float = 1.0         # Rate multiplier for acquiring knowledge
    memory_retention: float = 0.90      # Resistance to forgetting
    observational_ability: float = 0.70 # Fidelity of learning through watching
    curiosity: float = 0.70             # Drive to explore unfamiliar concepts
    persistence: float = 0.65           # Willingness to repeat failed attempts
    analytical_reasoning: float = 0.60  # Logic and causal inference competence
    practical_aptitude: float = 0.65    # Motor and procedural mastery rate
    communication_ability: float = 0.60 # Expressive and receptive dialogue skill
    adaptability: float = 0.65          # Speed of belief revision upon contradictory evidence
