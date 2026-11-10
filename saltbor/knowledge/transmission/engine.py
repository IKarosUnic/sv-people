"""Knowledge Transmission and Teaching Engine for Saltbor Phase 0.6.

Models inter-agent pedagogy, demonstration, mentorship, apprenticeships,
and intergenerational transmission with full provenance auditing and distortion
tracking.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Optional
from uuid import uuid4

from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProceduralKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TransmissionRecord:
    """Historical trace of a specific knowledge transfer event."""

    record_id: str
    item_id: str                      # concept or procedure or relationship ID
    item_type: str                    # 'concept', 'relationship', 'procedure'
    original_discoverer_uid: Optional[str]
    immediate_transmitter_uid: str
    recipient_uid: str
    transmission_method: str          # 'instruction', 'demonstration', 'apprenticeship', 'dialogue', 'family_tradition'
    timestamp_tick: int
    context: str
    transmitter_confidence: float
    recipient_confidence_before: float
    recipient_confidence_after: float
    distortion_introduced: bool = False
    distortion_notes: str = ""


class KnowledgeTransmissionEngine:
    """Coordinates teaching, mentorship, and transmission between agents."""

    def __init__(self) -> None:
        self.history: list[TransmissionRecord] = []

    def teach_concept(
        self,
        transmitter_graph: IndividualKnowledgeGraph,
        recipient_graph: IndividualKnowledgeGraph,
        concept_id: str,
        transmission_method: str = "instruction",
        teacher_pedagogy_skill: float = 0.7,
        learner_receptivity: float = 0.8,
        tick: int = 0,
        original_discoverer_uid: Optional[str] = None,
    ) -> tuple[bool, Optional[TransmissionRecord], str]:
        """Transmit concept knowledge from teacher to student.

        Enforces non-negotiable rule: Teacher cannot teach what they don't know!
        """
        # 1. Competence check
        if not transmitter_graph.knows_concept(concept_id, min_confidence=0.3):
            return False, None, f"Transmitter does not know concept '{concept_id}'"

        transmitter_claim = transmitter_graph.get_claim(concept_id)
        assert transmitter_claim is not None
        trans_conf = transmitter_claim.confidence

        # 2. Check if student already knows
        student_claim = recipient_graph.get_claim(concept_id)
        conf_before = student_claim.confidence if student_claim and not student_claim.is_forgotten else 0.0

        # 3. Transmission fidelity calculation
        # Effective confidence transferred depends on teacher's confidence, pedagogy skill, and learner receptivity
        transfer_fidelity = trans_conf * (0.5 + teacher_pedagogy_skill * 0.3) * (0.6 + learner_receptivity * 0.4)

        # Potential distortion (if teacher's confidence is low or pedagogy skill < 0.3)
        distortion = False
        distortion_notes = ""
        is_misconception = transmitter_claim.is_misconception
        if teacher_pedagogy_skill < 0.35 and not is_misconception:
            distortion = True
            distortion_notes = "Incomplete explanation led to slight semantic distortion"
            transfer_fidelity *= 0.75

        # 4. Student acquires concept
        recipient_graph.learn_concept(
            node_id=concept_id,
            confidence=transfer_fidelity,
            source_pathway="teaching" if transmission_method == "instruction" else transmission_method,
            source_agent_id=transmitter_graph.human_uid,
            tick=tick,
            is_misconception=is_misconception or distortion,
            evidence=f"Taught by agent {transmitter_graph.human_uid} via {transmission_method}",
        )

        conf_after = recipient_graph.get_claim(concept_id).confidence

        # 5. Record historical transmission
        rec = TransmissionRecord(
            record_id=f"tx_{uuid4().hex[:8]}",
            item_id=concept_id,
            item_type="concept",
            original_discoverer_uid=original_discoverer_uid or transmitter_claim.source_agent_id,
            immediate_transmitter_uid=transmitter_graph.human_uid,
            recipient_uid=recipient_graph.human_uid,
            transmission_method=transmission_method,
            timestamp_tick=tick,
            context=f"Session at tick {tick}",
            transmitter_confidence=trans_conf,
            recipient_confidence_before=conf_before,
            recipient_confidence_after=conf_after,
            distortion_introduced=distortion,
            distortion_notes=distortion_notes,
        )
        self.history.append(rec)
        return True, rec, "Transmission successful"

    def teach_relationship(
        self,
        transmitter_graph: IndividualKnowledgeGraph,
        recipient_graph: IndividualKnowledgeGraph,
        relationship: KnowledgeRelationship,
        tick: int = 0,
        original_discoverer_uid: Optional[str] = None,
    ) -> tuple[bool, Optional[TransmissionRecord], str]:
        """Transmit relationship knowledge from teacher to learner."""
        rel_claim = transmitter_graph.get_claim(relationship.rel_id)
        if not rel_claim or rel_claim.is_forgotten or rel_claim.confidence < 0.25:
            return False, None, "Transmitter does not know or believe this relationship"

        conf_before = 0.0
        r_student = recipient_graph.get_claim(relationship.rel_id)
        if r_student and not r_student.is_forgotten:
            conf_before = r_student.confidence

        trans_conf = rel_claim.confidence
        effective_conf = max(0.2, min(0.95, trans_conf * 0.85))

        recipient_graph.learn_relationship(
            rel=relationship,
            confidence=effective_conf,
            source_pathway="teaching",
            source_agent_id=transmitter_graph.human_uid,
            tick=tick,
            is_misconception=rel_claim.is_misconception,
            evidence=f"Learned relationship from agent {transmitter_graph.human_uid}",
        )

        conf_after = recipient_graph.get_claim(relationship.rel_id).confidence

        rec = TransmissionRecord(
            record_id=f"tx_{uuid4().hex[:8]}",
            item_id=relationship.rel_id,
            item_type="relationship",
            original_discoverer_uid=original_discoverer_uid or rel_claim.source_agent_id,
            immediate_transmitter_uid=transmitter_graph.human_uid,
            recipient_uid=recipient_graph.human_uid,
            transmission_method="teaching",
            timestamp_tick=tick,
            context=f"Relationship instruction at tick {tick}",
            transmitter_confidence=trans_conf,
            recipient_confidence_before=conf_before,
            recipient_confidence_after=conf_after,
        )
        self.history.append(rec)
        return True, rec, "Relationship transmission successful"

    def get_transmission_lineage(self, item_id: str) -> list[TransmissionRecord]:
        """Trace how a specific knowledge item propagated through the population."""
        return [r for r in self.history if r.item_id == item_id]
