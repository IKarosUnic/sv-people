"""Contextual dialogue and multi-outcome negotiation without external LLM dependencies."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.population.human import SyntheticHuman
from saltbor.social.dimensions.relationship import MultiDimensionalRelationship

logger = logging.getLogger(__name__)


class NegotiationOutcome(enum.Enum):
    """Possible outcomes of an interpersonal bargaining or persuasion dialogue."""

    AGREEMENT = "agreement"                    # Full consensus reached
    REFUSAL = "refusal"                        # Outright rejection
    CONDITIONAL_AGREEMENT = "conditional"      # Agreement contingent on reciprocal concession
    MISUNDERSTANDING = "misunderstanding"      # Communication breakdown or false assumption
    PERSUASION = "persuasion"                  # One party shifted stance due to compelling argument
    RECONSIDERATION = "reconsideration"        # Deferred decision awaiting further information
    CONFLICT_ESCALATION = "conflict_escalation" # Heated dispute, anger spike
    APOLOGY = "apology"                        # Sincere admission of fault
    RECONCILIATION = "reconciliation"          # Mutual healing of historical rupture


@dataclass
class DialogueTurn:
    """A single communicative move in a contextual conversation."""

    speaker_uid: HumanID
    text: str
    intent: str
    emotional_charge: str
    tick: Tick


@dataclass
class ContextualDialogueSession:
    """A complete structured conversation session between two co-located humans."""

    session_id: str
    participant_a: HumanID
    participant_b: HumanID
    topic: str
    outcome: NegotiationOutcome
    turns: list[DialogueTurn] = field(default_factory=list)
    resulting_trust_delta: float = 0.0
    resulting_affection_delta: float = 0.0
    summary: str = ""


class AdvancedOfflineDialogueEngine:
    """Orchestrates nuanced, context-grounded conversational exchanges and negotiations."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.recent_dialogues: list[ContextualDialogueSession] = []

    def get_recent_dialogues(self, limit: int = 50) -> list[ContextualDialogueSession]:
        """Return the most recent contextual dialogue sessions."""
        return self.recent_dialogues[-limit:]

    def conduct_negotiation(
        self,
        human_a: SyntheticHuman,
        human_b: SyntheticHuman,
        topic: str,
        relationship: MultiDimensionalRelationship,
        proposal_favor: str,
        current_tick: Tick,
        is_apology: bool = False,
    ) -> ContextualDialogueSession:
        """Execute a context-aware negotiation exchange.

        Evaluates emotional state, relationship dimensions (trust, resentment, reciprocity),
        and personality to determine dialogue progression and resolution.
        """
        session_id = f"dial_{human_a.uid}_{human_b.uid}_{current_tick}"
        turns: list[DialogueTurn] = []

        # Speaker A emotional and personality stance
        a_agree = human_a.personality.traits.get_trait_value("agreeableness") if human_a.personality else 0.5
        a_extra = human_a.personality.traits.get_trait_value("extraversion") if human_a.personality else 0.5
        a_mood = human_a.emotions.get_mood() if human_a.emotions else 0.0

        # Speaker B stance
        b_agree = human_b.personality.traits.get_trait_value("agreeableness") if human_b.personality else 0.5
        b_resent = relationship.resentment
        b_trust = relationship.trust

        if is_apology:
            # Apology arc
            turns.append(
                DialogueTurn(
                    speaker_uid=human_a.uid,
                    text=f"Quiero disculparme sinceramente por lo ocurrido respecto a {topic}. Reconozco mi falta.",
                    intent="apologize",
                    emotional_charge="guilt",
                    tick=current_tick,
                )
            )

            # Respondent evaluation: high resentment makes acceptance harder
            receptive_score = b_agree * 0.5 + (1.0 - b_resent) * 0.5
            if receptive_score >= 0.45:
                outcome = NegotiationOutcome.RECONCILIATION
                turns.append(
                    DialogueTurn(
                        speaker_uid=human_b.uid,
                        text=f"Agradezco tus palabras. Ha sido difícil, pero acepto tu disculpa. Sigamos adelante.",
                        intent="reconcile",
                        emotional_charge="relief",
                        tick=current_tick,
                    )
                )
                trust_delta = +0.15
                aff_delta = +0.20
                summary = f"{human_a.name} apologized to {human_b.name} and achieved reconciliation."
            else:
                outcome = NegotiationOutcome.REFUSAL
                turns.append(
                    DialogueTurn(
                        speaker_uid=human_b.uid,
                        text=f"Tus disculpas no compensan el daño causado en {topic}. Necesito tiempo y distancia.",
                        intent="refuse",
                        emotional_charge="resentment",
                        tick=current_tick,
                    )
                )
                trust_delta = 0.0
                aff_delta = -0.05
                summary = f"{human_b.name} rejected {human_a.name}'s apology due to deep resentment."

        else:
            # Standard proposal / negotiation
            turns.append(
                DialogueTurn(
                    speaker_uid=human_a.uid,
                    text=f"Me gustaría proponerte un acuerdo respecto a {topic}: {proposal_favor}.",
                    intent="propose",
                    emotional_charge="curiosity",
                    tick=current_tick,
                )
            )

            # Check for conflict escalation if mutual resentment/conflict is high
            if relationship.conflict > 0.60 or b_resent > 0.65:
                outcome = NegotiationOutcome.CONFLICT_ESCALATION
                turns.append(
                    DialogueTurn(
                        speaker_uid=human_b.uid,
                        text=f"¿Cómo te atreves a pedirme eso después de lo que hiciste? No quiero saber nada de tus tratos.",
                        intent="escalate",
                        emotional_charge="anger",
                        tick=current_tick,
                    )
                )
                trust_delta = -0.10
                aff_delta = -0.15
                summary = f"Negotiation on {topic} broke down into open conflict escalation."
            elif b_trust >= 0.60 and b_agree >= 0.50:
                outcome = NegotiationOutcome.AGREEMENT
                turns.append(
                    DialogueTurn(
                        speaker_uid=human_b.uid,
                        text=f"Me parece justo y conveniente. Cuentas con mi apoyo para {topic}.",
                        intent="agree",
                        emotional_charge="satisfaction",
                        tick=current_tick,
                    )
                )
                trust_delta = +0.05
                aff_delta = +0.05
                summary = f"Bilateral agreement reached on {topic}."
            elif b_trust >= 0.40:
                outcome = NegotiationOutcome.CONDITIONAL_AGREEMENT
                turns.append(
                    DialogueTurn(
                        speaker_uid=human_b.uid,
                        text=f"Podría aceptarlo, pero a cambio necesito que me ayudes con la faena del sábado.",
                        intent="counter_offer",
                        emotional_charge="cautious",
                        tick=current_tick,
                    )
                )
                trust_delta = +0.03
                aff_delta = +0.02
                summary = f"Conditional agreement reached on {topic} with reciprocal terms."
            else:
                outcome = NegotiationOutcome.REFUSAL
                turns.append(
                    DialogueTurn(
                        speaker_uid=human_b.uid,
                        text=f"No estoy en posición de comprometerme con eso ahora. Mejor no.",
                        intent="decline",
                        emotional_charge="indifference",
                        tick=current_tick,
                    )
                )
                trust_delta = 0.0
                aff_delta = 0.0
                summary = f"{human_b.name} declined proposal on {topic}."

        # Apply relationship consequences
        relationship.record_interaction(
            tick=current_tick,
            interaction_type=outcome.value,
            description=summary,
            affection_delta=aff_delta,
            trust_delta=trust_delta,
        )

        session = ContextualDialogueSession(
            session_id=session_id,
            participant_a=human_a.uid,
            participant_b=human_b.uid,
            topic=topic,
            outcome=outcome,
            turns=turns,
            resulting_trust_delta=trust_delta,
            resulting_affection_delta=aff_delta,
            summary=summary,
        )
        self.recent_dialogues.append(session)
        if len(self.recent_dialogues) > 200:
            self.recent_dialogues.pop(0)
        return session
