"""Semantic dialogue intents and utterance representations for offline communication."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.types import HumanID, Tick


class DialogueIntent(enum.Enum):
    """Categorization of pragmatic communicative intentions."""

    GREETING = "greeting"
    REQUEST = "request"
    OFFER = "offer"
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    QUESTION = "question"
    EXPLANATION = "explanation"
    WARNING = "warning"
    GOSSIP = "gossip"
    APOLOGY = "apology"
    EMOTIONAL_EXPRESSION = "emotional_expression"
    NEGOTIATION = "negotiation"
    BEREAVEMENT_CONDOLENCE = "bereavement_condolence"


@dataclass
class Utterance:
    """A single communicative act transmitted between individuals."""

    speaker_uid: HumanID
    listener_uid: Optional[HumanID]
    intent: DialogueIntent
    topic: str
    content_data: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    emotional_tone: str = "neutral"   # 'warm', 'tense', 'sorrowful', 'excited', 'formal', 'playful'
    tick: Tick = 0
    is_public: bool = False
