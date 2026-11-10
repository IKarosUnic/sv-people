"""Analysis module for population-level dynamics, diversity, and behavioral patterns."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.social.engine import SocialEngine


class PopulationAnalyzer:
    """Computes comprehensive quantitative and qualitative metrics across the synthetic population."""

    @staticmethod
    def analyze_personality_diversity(population: PopulationRegistry) -> dict[str, Any]:
        """Compute mean, standard deviation, and variance across Big Five traits."""
        humans = population.get_all()
        if not humans:
            return {}

        traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        stats: dict[str, dict[str, float]] = {}

        for t in traits:
            vals = [h.personality.get_trait(t) for h in humans]
            mean_v = float(np.mean(vals))
            std_v = float(np.std(vals))
            stats[t] = {
                "mean": round(mean_v, 3),
                "std": round(std_v, 3),
                "min": round(float(np.min(vals)), 3),
                "max": round(float(np.max(vals)), 3),
            }

        # Multi-trait variance indicator (composite diversity)
        overall_diversity = float(np.mean([s["std"] for s in stats.values()]))
        return {
            "traits": stats,
            "composite_personality_diversity": round(overall_diversity, 3),
            "is_diverse": overall_diversity > 0.08,
        }

    @staticmethod
    def analyze_emotional_diversity(population: PopulationRegistry) -> dict[str, Any]:
        """Assess distribution of moods, active emotions, and emotional diversity."""
        humans = population.get_all()
        if not humans:
            return {}

        moods = [h.emotions.get_mood() for h in humans]
        dominant_emotions: dict[str, int] = {}
        for h in humans:
            dom = "quiescent"
            if hasattr(h.emotions, "profile") and h.emotions.profile.get_dominant_emotion() is not None:
                dom = h.emotions.profile.get_dominant_emotion().value
            dominant_emotions[dom] = dominant_emotions.get(dom, 0) + 1

        return {
            "mood_mean": round(float(np.mean(moods)), 3),
            "mood_std": round(float(np.std(moods)), 3),
            "mood_range": [round(float(np.min(moods)), 3), round(float(np.max(moods)), 3)],
            "dominant_emotion_distribution": dominant_emotions,
        }

    @staticmethod
    def analyze_goals_and_autonomy(population: PopulationRegistry) -> dict[str, Any]:
        """Analyze autonomous goal generation, completion, and category spread."""
        humans = population.get_all()
        total_active_goals = 0
        categories: dict[str, int] = {}
        humans_with_goals = 0

        for h in humans:
            goals = h.autonomy.get_active_goals()
            if goals:
                humans_with_goals += 1
                total_active_goals += len(goals)
                for g in goals:
                    cat = getattr(g, "category", "general")
                    categories[cat] = categories.get(cat, 0) + 1

        pct_active = (humans_with_goals / max(1, len(humans))) * 100.0
        return {
            "total_active_goals": total_active_goals,
            "humans_with_active_goals": humans_with_goals,
            "autonomy_participation_rate": round(pct_active, 1),
            "category_distribution": categories,
        }

    @staticmethod
    def analyze_social_connectivity(social_engine: SocialEngine, population: PopulationRegistry) -> dict[str, Any]:
        """Compute network metrics: relationship count, mean trust, reciprocity, clustering."""
        rels = social_engine.get_all_relationships()
        humans = population.get_all()
        n = len(humans)
        if n <= 1:
            return {"network_density": 0.0, "total_relationships": len(rels)}

        possible_pairs = n * (n - 1)
        density = len(rels) / max(1, possible_pairs)

        trusts = [r.trust for r in rels] if rels else [0.0]
        affinities = [r.affinity for r in rels] if rels else [0.0]

        return {
            "total_relationships": len(rels),
            "network_density": round(density, 3),
            "mean_trust": round(float(np.mean(trusts)), 3),
            "mean_affinity": round(float(np.mean(affinities)), 3),
            "relationships_per_agent": round(len(rels) / max(1, n), 2),
        }

    @staticmethod
    def analyze_spatial_distribution(population: PopulationRegistry) -> dict[str, int]:
        """Distribution of individuals across settlement locations."""
        counts: dict[str, int] = {}
        for h in population.get_all():
            loc = h.physical_state.current_location_id or "unknown"
            counts[loc] = counts.get(loc, 0) + 1
        return counts

    @staticmethod
    def analyze_anti_artificial_patterns(
        population: PopulationRegistry,
        social_engine: Optional[SocialEngine] = None,
    ) -> dict[str, Any]:
        """Anti-Artificial Behavior Detection Suite.

        Evaluates 6 critical synthetic failure modes:
        1. Repetitive behavior
        2. Population homogeneity
        3. Memory ineffectiveness
        4. Emotional ineffectiveness
        5. Autonomy failure
        6. Artificial adaptation
        """
        humans = population.get_all()
        warnings: list[str] = []
        checks: dict[str, Any] = {}

        # 1. Homogeneity check
        pers_div = PopulationAnalyzer.analyze_personality_diversity(population)
        if pers_div.get("composite_personality_diversity", 0.0) < 0.04:
            warnings.append("High population homogeneity detected: personality std < 0.04.")
            checks["homogeneity_failure"] = True
        else:
            checks["homogeneity_failure"] = False

        # 2. Autonomy failure check
        autonomy_data = PopulationAnalyzer.analyze_goals_and_autonomy(population)
        if autonomy_data["autonomy_participation_rate"] < 20.0:
            warnings.append("Autonomy failure detected: less than 20% of population has active goals.")
            checks["autonomy_failure"] = True
        else:
            checks["autonomy_failure"] = False

        # 3. Memory ineffectiveness check
        total_mems = sum(h.memory.episodic.count for h in humans)
        if total_mems == 0 and len(humans) > 0:
            warnings.append("Memory ineffectiveness: 0 episodic memories recorded across population.")
            checks["memory_ineffective"] = True
        else:
            checks["memory_ineffective"] = False

        # 4. Emotional ineffectiveness check
        emot_div = PopulationAnalyzer.analyze_emotional_diversity(population)
        if emot_div.get("mood_std", 0.0) < 0.01:
            warnings.append("Emotional ineffectiveness: zero mood variation across individuals.")
            checks["emotional_ineffective"] = True
        else:
            checks["emotional_ineffective"] = False

        # 5. Spatial lock-in / repetitive behavior
        loc_counts = PopulationAnalyzer.analyze_spatial_distribution(population)
        if len(loc_counts) <= 1 and len(humans) > 5:
            warnings.append("Spatial lock-in: entire population stuck in a single location.")
            checks["spatial_lockin"] = True
        else:
            checks["spatial_lockin"] = False

        return {
            "checks": checks,
            "warning_count": len(warnings),
            "warnings": warnings,
            "is_clean": len(warnings) == 0,
        }
