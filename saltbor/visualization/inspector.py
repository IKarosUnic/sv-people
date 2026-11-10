"""Deep individual inspection utility for synthetic humans.

Allows researchers and developers to inspect psychological states, memory contents,
personality drifts, emotional balances, and social relationships of any individual.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman
    from saltbor.social.engine import SocialEngine


class IndividualInspector:
    """Detailed inspection reports for individual synthetic humans."""

    @staticmethod
    def inspect(human: SyntheticHuman, social_engine: Optional[SocialEngine] = None) -> str:
        """Generate a comprehensive multi-panel diagnostic profile."""
        lines: list[str] = []
        ident = human.identity
        demo = human.demographics
        phys = human.physical_state
        pers = human.personality
        emot = human.emotions
        mem = human.memory

        lines.append("╔" + "═" * 78 + "╗")
        lines.append(f"║  INDIVIDUAL PROFILE: {ident.full_name} (#{ident.serial})".ljust(79) + "║")
        lines.append(f"║  UID: {ident.uid} | Source: {ident.data_source.value}".ljust(79) + "║")
        lines.append("╠" + "═" * 78 + "╣")

        # Demographics & Physical
        lines.append(f"║  [DEMOGRAPHICS] Age: {demo.age} | Gender: {demo.gender.value} | Occupation: {demo.occupation}".ljust(79) + "║")
        lines.append(f"║  Education: {demo.education_level} | Income: ${phys.money:.2f}".ljust(79) + "║")
        lines.append(f"║  [PHYSICAL] Energy: {phys.energy:.2f} | Hunger: {phys.hunger:.2f} | Health: {phys.health:.2f}".ljust(79) + "║")
        lines.append(f"║  Current Location: {phys.current_location_id} | Home: {phys.home_location_id}".ljust(79) + "║")
        lines.append(f"║  Current Activity: {phys.current_activity.value if phys.current_activity else 'idle'} ({phys.activity_ticks_remaining} ticks remaining)".ljust(79) + "║")
        lines.append("╟" + "─" * 78 + "╢")

        # Personality Traits & Temperament
        lines.append(f"║  [PERSONALITY & TEMPERAMENT: {pers.temperament_value.upper()}]".ljust(79) + "║")
        traits = pers.traits
        for t_name in [
            "openness", "conscientiousness", "extraversion", "agreeableness",
            "neuroticism", "risk_tolerance", "patience", "persistence"
        ]:
            tv = traits.get_trait(t_name)
            drift_str = f"{tv.current_value - tv.base_value:+.3f}"
            lines.append(f"║    • {t_name:<18}: Base {tv.base_value:.2f} | Current {tv.current_value:.2f} (drift: {drift_str})".ljust(79) + "║")
        lines.append("╟" + "─" * 78 + "╢")

        # Emotions
        reg_cap = getattr(emot, "regulation_capacity", 0.5)
        expr = getattr(emot.profile, "expressiveness", 0.5)
        lines.append(f"║  [EMOTIONAL PROFILE] Mood: {emot.get_mood():+.2f} | RegCap: {reg_cap:.2f} | Expr: {expr:.2f}".ljust(79) + "║")
        emot_states = getattr(emot.profile, "active_emotions", {})
        active_emots = [f"{e.value if hasattr(e, 'value') else str(e)}:{st.intensity:.2f}" for e, st in emot_states.items() if st.intensity > 0.05]
        active_str = ", ".join(active_emots) if active_emots else "None (quiescent)"
        lines.append(f"║    Active: {active_str}".ljust(79) + "║")
        lines.append("╟" + "─" * 78 + "╢")

        # Memory Systems
        stats = mem.get_memory_stats()
        lines.append(f"║  [MEMORY ENGINE] Footprint: {stats['approx_bytes']} bytes ({stats['usage_pct']}% of 1MB quota)".ljust(79) + "║")
        lines.append(f"║    Working items: {stats['working_items']} | Episodic: {stats['episodic_records']} (Stored: {mem.episodic.total_stored_count}) | Skills: {stats['skills']}".ljust(79) + "║")
        lines.append("║    Top Episodic Memories:".ljust(79) + "║")
        recent = mem.episodic.get_recent(3)
        if not recent:
            lines.append("║      (No episodic memories yet)".ljust(79) + "║")
        else:
            for r in recent:
                lines.append(f"║      • [T{r.tick}] {r.summary[:50]} (imp: {r.importance:.2f}, val: {r.emotional_valence:+.2f})".ljust(79) + "║")
        lines.append("╟" + "─" * 78 + "╢")

        # Goals Lifecycle
        lines.append("║  [AUTONOMOUS GOALS LIFECYCLE]".ljust(79) + "║")
        goals = human.autonomy.get_active_goals()
        if not goals:
            lines.append("║    (No active goals)".ljust(79) + "║")
        else:
            for g in goals[:3]:
                step_info = f" | Step: {g.plan_steps[g.current_step_index]}" if g.plan_steps and g.current_step_index < len(g.plan_steps) else ""
                lines.append(f"║    • [{g.category.upper()}] {g.description} ({int(g.progress*100)}%{step_info})".ljust(79) + "║")
        lines.append("╟" + "─" * 78 + "╢")

        # Social Network
        if social_engine:
            lines.append("║  [SOCIAL RELATIONSHIPS & ATTITUDES]".ljust(79) + "║")
            rels = social_engine.get_relationships_for(human.uid)
            if not rels:
                lines.append("║    (No recorded relationships)".ljust(79) + "║")
            else:
                for rel in rels[:4]:
                    other_uid = rel.other_id(human.uid)
                    try:
                        att = rel.get_attitude(human.uid)
                        att_str = f"DirTrust: {att.trust:.2f}"
                    except Exception:
                        att_str = ""
                    lines.append(f"║    • With {str(other_uid)[:8]}...: {rel.relationship_type.value} | Trust: {rel.trust:.2f} ({att_str})".ljust(79) + "║")

        lines.append("╚" + "═" * 78 + "╝")
        return "\n".join(lines)
