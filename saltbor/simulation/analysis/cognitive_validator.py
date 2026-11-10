"""Cognitive engine integration tests and validation suite."""

from __future__ import annotations

from typing import Any

from saltbor.cognition.autonomy.engine import AutonomyEngine
from saltbor.cognition.cognitive.engine import CognitiveEngine, Perception
from saltbor.cognition.decision.engine import DecisionContext, DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.learning.engine import LearningEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.types import ActivityType, EmotionType
from saltbor.events.types import EventType, SimulationEvent


class CognitiveSystemValidator:
    """Validates the causal feedback loop between the brain-inspired cognitive modules:

    Frontal (autonomy/planning)
    Limbic (emotions/motivation)
    Hippocampal (episodic memory/consolidation)
    Temporal (semantic/language knowledge)
    Parietal (spatial integration)
    Occipital (perceptual filtering)
    Cerebellar (procedural skill learning)
    """

    @staticmethod
    def validate_causal_feedback_loop() -> dict[str, Any]:
        """Subject an agent to an adverse event and verify cross-module ripple effects."""
        # 1. Setup individual
        traits = PersonalityTraits(
            neuroticism=TraitValue(base_value=0.5, current_value=0.5),
            extraversion=TraitValue(base_value=0.6, current_value=0.6),
            agreeableness=TraitValue(base_value=0.7, current_value=0.7),
        )
        personality = PersonalityEngine(traits)
        emotions = EmotionalEngine(profile=EmotionalProfile())
        memory = MemoryEngine()
        autonomy = AutonomyEngine()
        learning = LearningEngine()
        cognition = CognitiveEngine()
        decision = DecisionEngine()

        initial_neuroticism = personality.get_trait("neuroticism")
        initial_mood = emotions.get_mood()

        # Step 1 & 2: Adverse event happens at market (scam/loss of funds)
        event = SimulationEvent(
            event_type=EventType.FINANCIAL_LOSS,
            tick=10,
            location_id="mercado_municipal",
            data={"amount": -50.0, "reason": "swindled in bad trade"},
            importance=0.85,
        )

        # Limbic system processes event
        emot_states = emotions.process_event(event, personality.traits)
        post_event_mood = emotions.get_mood()

        # Hippocampal encodes with negative valence
        memory.record_event(
            event,
            importance=0.85,
            emotional_valence=post_event_mood,
            emotional_charges={s.emotion_type.value: s.intensity for s in emot_states},
        )

        # Personality adapts under high significance
        personality.apply_experience(event, emotional_impact=post_event_mood)
        post_adapt_neuroticism = personality.get_trait("neuroticism")

        # Temporal extracts semantic knowledge
        learning.extract_knowledge_from_event(event, memory)

        # Parietal / Occipital spatial memory check
        loc_assoc = memory.get_location_association("mercado_municipal")

        # Frontal / Decision system evaluates choices
        context = DecisionContext(
            current_location_id="plaza_central",
            available_activities=[ActivityType.SHOP, ActivityType.REST],
            current_needs={},
            current_energy=0.8,
            current_hunger=0.2,
            current_money=100.0,
            is_daytime=True,
            hour_int=10,
        )
        options = decision.evaluate_options(context, personality, emotions, memory)
        shop_option = next((o for o in options if o.action_type == ActivityType.SHOP), None)

        trace = decision.decide(context, personality, emotions, memory)

        results = {
            "limbic_response": post_event_mood < initial_mood,
            "hippocampal_encoding": memory.episodic.count > 0,
            "personality_adaptation": post_adapt_neuroticism >= initial_neuroticism,
            "spatial_aversion_formed": loc_assoc.get("valence", 0.0) < 0.0,
            "decision_affected": "Avoidance" in (shop_option.reasoning if shop_option else ""),
            "all_systems_coupled": True,
        }
        results["all_systems_coupled"] = all([
            results["limbic_response"],
            results["hippocampal_encoding"],
            results["personality_adaptation"],
            results["spatial_aversion_formed"],
            results["decision_affected"],
        ])
        return results
