"""Romance, Relationships, Infidelity and Heartbreak module."""

from saltbor.social.romance.engine import RomanceEngine
from saltbor.social.romance.models import (
    HeartbreakRecord,
    InfidelityRecord,
    RomanticDimensions,
    RomanticRelationship,
)

__all__ = [
    "RomanceEngine",
    "RomanticRelationship",
    "RomanticDimensions",
    "InfidelityRecord",
    "HeartbreakRecord",
]
