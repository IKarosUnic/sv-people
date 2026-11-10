"""Metacognitive Self-Audit for Saltbor Phase 0.7 (Section 5).

Evaluates an individual's self-model of their cognitive state:
- What is known (K: verified facts with high confidence).
- What is unknown (U: identified epistemic gaps or known-unknowns).
- What is believed known (B: subjective beliefs pending verification).
- Reliability of current knowledge (R: mean confidence and validation ratio).
- Possessed skills (S: current proficiency levels).
- Needed skills (S_need: requirements for active goals).
- Self-efficacy: estimated capability to solve a specific challenge.
- Help-seeking threshold: when to request external collaboration.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class MetacognitiveProfile:
    """An agent's introspective self-assessment snapshot."""

    known_concepts_count: int
    known_unknowns: list[str]
    subjective_beliefs_count: int
    mean_epistemic_reliability: float   # [0.0, 1.0]
    possessed_skills: dict[str, float]
    needed_skills: list[str]
    self_efficacy_score: float          # [0.0, 1.0]
    help_seeking_threshold: float       # If required difficulty > self_efficacy + threshold, seek help
    recognized_limitations: list[str]
    tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "known_count": self.known_concepts_count,
            "known_unknowns": self.known_unknowns,
            "beliefs_count": self.subjective_beliefs_count,
            "mean_reliability": round(self.mean_epistemic_reliability, 3),
            "possessed_skills": {k: round(v, 2) for k, v in self.possessed_skills.items()},
            "needed_skills": self.needed_skills,
            "self_efficacy": round(self.self_efficacy_score, 3),
            "help_seeking_threshold": round(self.help_seeking_threshold, 3),
            "limitations": self.recognized_limitations,
        }


class MetacognitiveAuditor:
    """Performs introspective audits of an individual's cognitive assets and deficits."""

    @staticmethod
    def audit(
        graph: IndividualKnowledgeGraph,
        epistemic: Optional[EpistemicInterface] = None,
        skills: Optional[dict[str, float]] = None,
        active_goal_requirements: Optional[list[str]] = None,
        neuroticism: float = 0.5,
        conscientiousness: float = 0.5,
        tick: int = 0,
    ) -> MetacognitiveProfile:
        """Perform a structured metacognitive self-audit."""
        skills = skills or {}
        reqs = active_goal_requirements or []

        # 1. Evaluate known concepts (K)
        known_ids = graph.all_known_node_ids()
        claims = [graph.get_claim(nid) for nid in known_ids]
        valid_claims = [c for c in claims if c is not None and not c.is_forgotten]

        mean_rel = (
            sum(c.confidence for c in valid_claims) / max(1, len(valid_claims))
            if valid_claims
            else 0.5
        )

        # 2. Known-unknowns (U)
        known_unknowns: list[str] = []
        if epistemic:
            known_unknowns = epistemic.identify_missing_information(reqs)

        # 3. Needed skills vs possessed skills
        needed_skills: list[str] = []
        limitations: list[str] = []
        for r in reqs:
            lvl = skills.get(r, 0.0)
            if lvl < 0.35:
                needed_skills.append(r)
                limitations.append(f"Low proficiency in {r} ({lvl:.2f} < 0.35)")

        # 4. Self-efficacy calculation
        # High skills + high knowledge reliability = high self-efficacy
        avg_skill = sum(skills.values()) / max(1, len(skills)) if skills else 0.4
        efficacy_base = (mean_rel * 0.4) + (avg_skill * 0.6)
        # Modulated by personality: neuroticism lowers efficacy, conscientiousness raises it
        efficacy = max(0.1, min(0.95, efficacy_base - (neuroticism * 0.15) + (conscientiousness * 0.10)))

        # 5. Help-seeking threshold: individuals with lower self-efficacy seek help earlier
        # Higher neuroticism -> seeks help sooner (lower threshold); high independence/pride -> delays seeking help
        help_threshold = max(0.2, min(0.8, 0.55 - (neuroticism * 0.2) + (conscientiousness * 0.1)))

        beliefs_count = len(epistemic._beliefs) if epistemic else len(valid_claims)

        return MetacognitiveProfile(
            known_concepts_count=len(known_ids),
            known_unknowns=known_unknowns,
            subjective_beliefs_count=beliefs_count,
            mean_epistemic_reliability=mean_rel,
            possessed_skills=dict(skills),
            needed_skills=needed_skills,
            self_efficacy_score=efficacy,
            help_seeking_threshold=help_threshold,
            recognized_limitations=limitations,
            tick=tick,
        )
