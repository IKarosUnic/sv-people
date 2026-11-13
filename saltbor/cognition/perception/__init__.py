"""Structured human perception for SALTBOR.

Public surface::

    from saltbor.cognition.perception import PerceptionEngine, PerceptionSnapshot

The engine is the only supported way for a simulated individual to acquire
knowledge of the world.  Other systems should consult
``PerceptionEngine.has_perceived`` / ``get_snapshot`` instead of assuming an
individual knows about an entity that exists in the world state.
"""

from saltbor.cognition.perception.engine import PerceptionEngine
from saltbor.cognition.perception.models import (
    AcuityProfile,
    Interpretation,
    Observation,
    PerceptionChannel,
    PerceptionSnapshot,
    TargetKind,
)

__all__ = [
    "AcuityProfile",
    "Interpretation",
    "Observation",
    "PerceptionChannel",
    "PerceptionEngine",
    "PerceptionSnapshot",
    "TargetKind",
]
