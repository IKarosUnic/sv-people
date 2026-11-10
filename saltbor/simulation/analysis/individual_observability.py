"""Individual observability and structured decision trace generator."""

from __future__ import annotations

from typing import Any, Optional

from saltbor.population.human import SyntheticHuman
from saltbor.social.engine import SocialEngine


class IndividualObservability:
    """Provides complete state inspection and formatted decision traces for any individual."""

    @staticmethod
    def get_structured_dossier(human: SyntheticHuman, social_engine: Optional[SocialEngine] = None) -> dict[str, Any]:
        """Return a structured, serialization-friendly dossier of an individual's state."""
        ident = human.identity
        demo = human.demographics
        phys = human.physical_state
        pers = human.personality
        emot = human.emotions
        mem = human.memory
        aut = human.autonomy
        dec = human.decision

        # Skills
        skills = {
            s.name: {"level": round(s.proficiency, 3), "practice_count": s.practice_count}
            for s in mem.procedural.get_all_skills()
        }

        # Relationships
        rels: list[dict[str, Any]] = []
        if social_engine:
            for r in social_engine.get_relationships_for(human.uid):
                target_uid = r.human_b_id if r.human_a_id == human.uid else r.human_a_id
                rels.append({
                    "target_uid": str(target_uid),
                    "relation_type": r.relationship_type.value,
                    "trust": round(r.trust, 3),
                    "affinity": round(r.affinity, 3),
                    "familiarity": round(r.familiarity, 3),
                })

        # Recent memories
        recent_mems = [
            {
                "tick": m.tick,
                "summary": m.summary,
                "importance": round(m.importance, 2),
                "valence": round(m.emotional_valence, 2),
            }
            for m in mem.episodic.get_recent(5)
        ]

        # Active goals
        active_goals = [
            {
                "id": str(g.goal_id),
                "category": g.category,
                "description": g.description,
                "priority": round(g.priority, 2),
                "progress": round(g.progress, 2),
                "status": g.status,
            }
            for g in aut.get_active_goals()
        ]

        # Recent decision trace
        last_trace = dec.get_last_trace()
        trace_dict: Optional[dict[str, Any]] = None
        if last_trace:
            trace_dict = {
                "chosen_action": last_trace.chosen_action.value if hasattr(last_trace.chosen_action, "value") else str(last_trace.chosen_action),
                "target_location": last_trace.target_location_id,
                "expected_utility": round(last_trace.expected_utility, 3),
                "reasoning": last_trace.reasoning,
                "dominant_factors": last_trace.dominant_factors,
                "alternatives": last_trace.alternatives,
            }

        return {
            "identity": {
                "uid": str(ident.uid),
                "serial": ident.serial,
                "full_name": ident.full_name,
                "age": demo.age,
                "occupation": demo.occupation,
                "education": demo.education_level,
            },
            "physical": {
                "energy": round(phys.energy, 3),
                "hunger": round(phys.hunger, 3),
                "money": round(phys.money, 2),
                "location": phys.current_location_id,
                "current_activity": phys.current_activity.value if phys.current_activity else "idle",
            },
            "personality": {
                "temperament": pers.temperament_value,
                "traits": {
                    t: round(pers.get_trait(t), 3)
                    for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                },
            },
            "emotions": {
                "mood": round(emot.get_mood(), 3),
                "dominant": (
                    emot.profile.get_dominant_emotion().value
                    if hasattr(emot, "profile") and emot.profile.get_dominant_emotion() is not None
                    else "quiescent"
                ),
            },
            "active_goals": active_goals,
            "skills": skills,
            "relationships": rels,
            "recent_memories": recent_mems,
            "last_decision_trace": trace_dict,
        }

    @staticmethod
    def format_decision_trace_text(human: SyntheticHuman) -> str:
        """Produce an interpretable text explanation trace as specified in Section 7."""
        trace = human.decision.get_last_trace()
        ident = human.identity
        phys = human.physical_state
        emot = human.emotions

        if not trace:
            return f"Individual: {ident.full_name} (#{ident.serial})\nNo decision trace recorded yet."

        action_name = trace.chosen_action.value if hasattr(trace.chosen_action, "value") else str(trace.chosen_action)
        lines: list[str] = [
            f"Individual: {ident.full_name} (#{ident.serial})",
            "",
            "Decision:",
            f"Action: {action_name.upper()} at {trace.target_location_id or phys.current_location_id}",
            "",
            "Relevant factors:",
            f"- Energy: {round(phys.energy, 2)}",
            f"- Hunger: {round(phys.hunger, 2)}",
            f"- Available money: ${round(phys.money, 2)}",
            f"- Emotional mood: {round(emot.get_mood(), 2):+}",
        ]
        for f in trace.dominant_factors:
            lines.append(f"- {f}")

        lines.extend([
            "",
            "Selected action:",
            f"{action_name} (Utility: {round(trace.expected_utility, 3)})",
            "",
            "Reason for selection:",
            f"{trace.reasoning}",
            "",
            "Alternatives considered:",
        ])

        for alt in trace.alternatives[:3]:
            lines.append(f"- {alt.get('action')}: utility {alt.get('utility')} at {alt.get('location')}")

        return "\n".join(lines)
