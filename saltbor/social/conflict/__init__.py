"""Conflict, negotiation, and dispute resolution package."""

from saltbor.social.conflict.dispute import (
    CollectiveConflictManager,
    Dispute,
    DisputeCause,
    DisputeStage,
)
from saltbor.social.conflict.engine import (
    ConflictCooperationEngine,
    ConflictDomain,
    ConflictStage,
    NegotiationOffer,
    SocialDispute,
)
from saltbor.social.conflict.intergroup_engine import (
    ConflictTensionStage,
    IntergroupConflictEngine,
    IntergroupConflictType,
    IntergroupDispute,
)

__all__ = [
    "CollectiveConflictManager",
    "Dispute",
    "DisputeCause",
    "DisputeStage",
    "ConflictCooperationEngine",
    "ConflictDomain",
    "ConflictStage",
    "NegotiationOffer",
    "SocialDispute",
    "ConflictTensionStage",
    "IntergroupConflictEngine",
    "IntergroupConflictType",
    "IntergroupDispute",
]
