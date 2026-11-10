"""Metacognition and self-assessment architecture for Saltbor Phase 0.7."""

from saltbor.cognition.metacognition.confidence import CalibratedConfidenceEstimator, ConfidenceAudit
from saltbor.cognition.metacognition.engine import MetacognitionEngine
from saltbor.cognition.metacognition.error_detection import CognitiveErrorDetector, DetectedCognitiveError
from saltbor.cognition.metacognition.reflection import CognitiveReflector, ReflectionRecord
from saltbor.cognition.metacognition.self_audit import MetacognitiveAuditor, MetacognitiveProfile

__all__ = [
    "CalibratedConfidenceEstimator",
    "CognitiveErrorDetector",
    "CognitiveReflector",
    "ConfidenceAudit",
    "DetectedCognitiveError",
    "MetacognitionEngine",
    "MetacognitiveAuditor",
    "MetacognitiveProfile",
    "ReflectionRecord",
]
