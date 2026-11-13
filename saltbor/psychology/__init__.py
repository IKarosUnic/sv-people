"""Integrated psychological realism layer (Phase 1.7).

Public surface:

* :class:`PsychologicalState` — persistent per-individual state and history.
* :class:`PsychologicalEngine` — runtime orchestration used by SimulationRunner.
* :class:`AppraisalEngine` — OCC-inspired event appraisal.
* :class:`AdaptiveCopingEngine` — coping selection, execution and learning.
* :class:`RegulationEngine` — self-regulation, crisis and recovery.
* :class:`AssociativeRetrieval` — indexed recall and imperfect reconstruction.
* :class:`SupportEngine` — social support assessment and transactions.
"""

from saltbor.psychology.appraisal import AppraisalEngine, apply_appraisal
from saltbor.psychology.coping import AdaptiveCopingEngine, CopingContext, CopingSpec
from saltbor.psychology.engine import PsychologicalEngine
from saltbor.psychology.models import (
    AppraisalRecord,
    CopingCategory,
    CopingEpisode,
    CopingStrategy,
    CrisisEpisode,
    CrisisKind,
    LifeEventRecord,
    PsychLOD,
    PsychologicalState,
)
from saltbor.psychology.regulation import BodySignals, RegulationEngine
from saltbor.psychology.retrieval import AssociativeRetrieval, RetrievalQuery
from saltbor.psychology.support import SupportAssessment, SupportEngine

__all__ = [
    "AppraisalEngine",
    "AppraisalRecord",
    "AssociativeRetrieval",
    "AdaptiveCopingEngine",
    "BodySignals",
    "CopingCategory",
    "CopingContext",
    "CopingEpisode",
    "CopingSpec",
    "CopingStrategy",
    "CrisisEpisode",
    "CrisisKind",
    "LifeEventRecord",
    "PsychLOD",
    "PsychologicalEngine",
    "PsychologicalState",
    "RegulationEngine",
    "RetrievalQuery",
    "SupportAssessment",
    "SupportEngine",
    "apply_appraisal",
]
