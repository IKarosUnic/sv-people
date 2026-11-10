"""Curiosity and Autonomous Exploration Engine for Saltbor Phase 0.7 (Section 7).

Drives exploratory behaviors across physical, social, and intellectual dimensions:
- Physical exploration: Unvisited loci, boundary regions, terrain features.
- Social exploration: Seeking out strangers, specialists, and peers with alien skills.
- Intellectual exploration: Unexplained phenomena, unmastered crafts, experimental ideas.

Exploration intensity is dynamically modulated by personality (Openness, Extraversion),
affective state (Curiosity vs. Fear/Anxiety), biological safety margins (energy, satiety),
and perceived physical/economic risk. Enforces realistic population heterogeneity.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


class ExplorationModality(str, Enum):
    """Categorical modes of autonomous exploration."""

    PHYSICAL = "physical"
    SOCIAL = "social"
    INTELLECTUAL = "intellectual"


@dataclasses.dataclass
class ExplorationTarget:
    """A candidate object, location, person, or puzzle stimulating curiosity."""

    target_id: str
    modality: ExplorationModality
    name: str
    description: str
    novelty_score: float                # [0.0, 1.0]
    estimated_risk: float               # [0.0, 1.0]
    required_energy: float = 0.20
    potential_benefit: str = "Epistemic discovery and personal growth"

    def curiosity_attractiveness(
        self,
        curiosity_drive: float,
        risk_tolerance: float,
    ) -> float:
        """Net attractiveness balancing epistemic novelty against perceived risk."""
        appeal = (self.novelty_score * curiosity_drive * 0.7) + (risk_tolerance * (1.0 - self.estimated_risk) * 0.3)
        return max(0.0, appeal)


class CuriosityEngine:
    """Manages individual exploratory drives and selects targeted discovery actions."""

    @staticmethod
    def calculate_curiosity_drive(
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        energy: float = 1.0,
        hunger: float = 0.0,
    ) -> float:
        """Compute the instantaneous exploration drive of an individual.

        Heavily depressed by biological deprivation (starvation/fatigue) or fear.
        """
        openness = personality.get_trait("openness")
        neuroticism = personality.get_trait("neuroticism")

        curiosity_emotion = emotions.get_emotion("curiosity")
        fear_emotion = emotions.get_emotion("fear")
        anxiety_emotion = emotions.get_emotion("anxiety")

        # Biological safety gate: starving or exhausted agents cannot indulge curiosity
        biological_gate = max(0.0, 1.0 - (hunger * 0.8) - ((1.0 - energy) * 0.6))
        if biological_gate < 0.25:
            return 0.05

        base_drive = (openness * 0.45) + (curiosity_emotion * 0.40) - (neuroticism * 0.15)
        risk_inhibition = (fear_emotion * 0.35) + (anxiety_emotion * 0.25)

        net_drive = max(0.02, min(0.98, (base_drive - risk_inhibition) * biological_gate))
        return net_drive

    def find_exploration_targets(
        self,
        graph: IndividualKnowledgeGraph,
        unvisited_locations: list[str],
        known_unmet_peers: list[dict[str, Any]], # list of {uid, name, profession}
        unexplained_anomalies: list[str],
    ) -> list[ExplorationTarget]:
        """Compile candidate targets across all 3 modalities."""
        targets: list[ExplorationTarget] = []

        # 1. Physical targets
        for loc in unvisited_locations:
            targets.append(
                ExplorationTarget(
                    target_id=loc,
                    modality=ExplorationModality.PHYSICAL,
                    name=f"Unvisited Location: {loc}",
                    description=f"Physical exploration of {loc} to map terrain and resource deposits",
                    novelty_score=0.80,
                    estimated_risk=0.35,
                    required_energy=0.25,
                )
            )

        # 2. Social targets
        for peer in known_unmet_peers:
            targets.append(
                ExplorationTarget(
                    target_id=str(peer["uid"]),
                    modality=ExplorationModality.SOCIAL,
                    name=f"Social Encounter: {peer.get('name', 'Stranger')}",
                    description=f"Engage in dialogue with {peer.get('name')} to discover their trade ({peer.get('profession', 'unknown')})",
                    novelty_score=0.70,
                    estimated_risk=0.15,
                    required_energy=0.10,
                )
            )

        # 3. Intellectual targets
        for anomaly in unexplained_anomalies:
            targets.append(
                ExplorationTarget(
                    target_id=anomaly,
                    modality=ExplorationModality.INTELLECTUAL,
                    name=f"Epistemic Puzzle: {anomaly}",
                    description=f"Investigate causal mechanisms underlying {anomaly}",
                    novelty_score=0.85,
                    estimated_risk=0.20,
                    required_energy=0.15,
                )
            )

        return targets

    def select_exploration_target(
        self,
        targets: list[ExplorationTarget],
        curiosity_drive: float,
        risk_tolerance: float = 0.5,
    ) -> Optional[ExplorationTarget]:
        """Select highest attractiveness exploration target given drive and risk posture."""
        if not targets or curiosity_drive < 0.25:
            return None

        ranked = sorted(
            targets,
            key=lambda t: t.curiosity_attractiveness(curiosity_drive, risk_tolerance),
            reverse=True,
        )
        best = ranked[0]
        if best.curiosity_attractiveness(curiosity_drive, risk_tolerance) > 0.20:
            return best
        return None
