"""Multi-turn conversational exchange management with topic continuity and memory formation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID, Tick
from saltbor.social.language.intent import DialogueIntent, Utterance
from saltbor.social.language.nlg import LocalDialogueGenerator

logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """A coherent multi-turn dialogue exchange between two synthetic humans."""

    conversation_id: str
    participant_a: HumanID
    participant_b: HumanID
    topic: str
    start_tick: Tick
    turns: list[Utterance] = field(default_factory=list)
    is_active: bool = True
    mutual_satisfaction: float = 0.5

    def add_turn(self, utterance: Utterance) -> None:
        self.turns.append(utterance)

    def terminate(self) -> None:
        self.is_active = False


class ConversationManager:
    """Orchestrates turn-taking, topic progression, and dialogue consequences."""

    def __init__(self, nlg: Optional[LocalDialogueGenerator] = None) -> None:
        self.nlg = nlg or LocalDialogueGenerator()

    def conduct_conversation(
        self,
        human_a: any,
        human_b: any,
        topic: str,
        current_tick: Tick,
        trust_ab: float,
        affinity_ab: float,
        intent_a: DialogueIntent = DialogueIntent.GREETING,
        content_a: Optional[dict] = None,
    ) -> ConversationSession:
        """Execute a structured 3-to-4 turn exchange between two co-located individuals."""
        session = ConversationSession(
            conversation_id=f"conv_{human_a.uid}_{human_b.uid}_{current_tick}",
            participant_a=human_a.uid,
            participant_b=human_b.uid,
            topic=topic,
            start_tick=current_tick,
        )

        # Turn 1: Speaker A opening utterance
        utt1 = Utterance(
            speaker_uid=human_a.uid,
            listener_uid=human_b.uid,
            intent=intent_a,
            topic=topic,
            content_data=content_a or {},
            tick=current_tick,
        )
        utt1.text = self.nlg.generate_surface_text(utt1, trust=trust_ab, affinity=affinity_ab)
        session.add_turn(utt1)

        # Turn 2: Speaker B response
        # High trust/affinity -> AGREEMENT or OFFER; low -> DISAGREEMENT
        if intent_a == DialogueIntent.GOSSIP:
            resp_intent = DialogueIntent.QUESTION if trust_ab < 0.6 else DialogueIntent.AGREEMENT
        elif intent_a == DialogueIntent.REQUEST:
            resp_intent = DialogueIntent.AGREEMENT if trust_ab > 0.55 else DialogueIntent.DISAGREEMENT
        elif intent_a == DialogueIntent.BEREAVEMENT_CONDOLENCE:
            resp_intent = DialogueIntent.EMOTIONAL_EXPRESSION
        else:
            resp_intent = DialogueIntent.AGREEMENT if affinity_ab > 0.4 else DialogueIntent.DISAGREEMENT

        utt2 = Utterance(
            speaker_uid=human_b.uid,
            listener_uid=human_a.uid,
            intent=resp_intent,
            topic=topic,
            content_data={"response_to": intent_a.value},
            tick=current_tick,
        )
        utt2.text = self.nlg.generate_surface_text(utt2, trust=trust_ab, affinity=affinity_ab)
        session.add_turn(utt2)

        # Turn 3: Closing confirmation from Speaker A
        close_intent = DialogueIntent.AGREEMENT if resp_intent == DialogueIntent.AGREEMENT else DialogueIntent.EXPLANATION
        utt3 = Utterance(
            speaker_uid=human_a.uid,
            listener_uid=human_b.uid,
            intent=close_intent,
            topic=topic,
            content_data={"closing": True},
            tick=current_tick,
        )
        utt3.text = self.nlg.generate_surface_text(utt3, trust=trust_ab, affinity=affinity_ab)
        session.add_turn(utt3)

        session.terminate()

        # Encode episodic memory in both participants
        summary_ab = f"Conversó con {human_b.name} sobre {topic} ({intent_a.value})."
        human_a.memory.working.add_fact(summary_ab, current_tick) if hasattr(human_a.memory.working, "add_fact") else None
        return session
