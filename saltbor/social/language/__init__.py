"""Language and offline dialogue package for Saltbor."""

from saltbor.social.language.contextual_dialogue import (
    AdvancedOfflineDialogueEngine,
    ContextualDialogueSession,
    DialogueTurn,
    NegotiationOutcome,
)
from saltbor.social.language.conversation import (
    ConversationManager,
    ConversationSession,
)
from saltbor.social.language.intent import DialogueIntent, Utterance
from saltbor.social.language.nlg import LocalDialogueGenerator
from saltbor.social.language.salvadoran_spanish import (
    SalvadoranSpanishEngine,
    SalvadoranUtterance,
)

__all__ = [
    "AdvancedOfflineDialogueEngine",
    "ContextualDialogueSession",
    "ConversationManager",
    "ConversationSession",
    "DialogueIntent",
    "DialogueTurn",
    "LocalDialogueGenerator",
    "NegotiationOutcome",
    "Utterance",
    "SalvadoranSpanishEngine",
    "SalvadoranUtterance",
]
