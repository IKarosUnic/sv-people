"""Social and Collective Knowledge Integration Bridge for Saltbor Phase 0.9.

Bridges IndividualKnowledgeGraph, CollectiveKnowledgeGraph, and Social Networks:
- Preserves provenance (creator, transmitter, hops, tick, context, evidence, confidence).
- Distinguishes individual knowledge from community knowledge.
- Models organic peer-to-peer transmission, communal debate, consensus building,
  and institutionalization without omniscient global leakage.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


class EpistemicProvenanceType(str, enum.Enum):
    """Source provenance of a knowledge assertion."""

    DIRECT_DISCOVERY = "direct_discovery"
    PEER_TRANSMISSION = "peer_transmission"
    COMMUNITY_TRADITION = "community_tradition"
    INSTITUTIONAL_RECORD = "institutional_record"
    RUMOR_OR_HEARSAY = "rumor_or_hearsay"


@dataclasses.dataclass
class KnowledgeTransmissionReceipt:
    """Audit record of a verified or attempted knowledge transmission."""

    receipt_id: str
    node_id: str
    sender_uid: str
    recipient_uid: str
    provenance_type: EpistemicProvenanceType
    evidence_score: float
    confidence_transferred: float
    tick: int
    was_accepted: bool
    rejection_reason: Optional[str] = None


class SocialKnowledgeBridge:
    """Manages the lifecycle of knowledge as it moves from individuals to collectives."""

    def __init__(self, collective_kg: Optional[CollectiveKnowledgeGraph] = None) -> None:
        self.collective_kg = collective_kg or CollectiveKnowledgeGraph()
        self.transmission_log: list[KnowledgeTransmissionReceipt] = []

    def transmit_to_individual(
        self,
        node: KnowledgeNode,
        sender_uid: str,
        recipient_uid: str,
        recipient_kg: IndividualKnowledgeGraph,
        rel_trust: float = 0.7,
        evidence_level: float = 0.6,
        tick: int = 0,
    ) -> KnowledgeTransmissionReceipt:
        """Transmit an individual knowledge node to a peer along a social link."""
        receipt_id = f"tx_{uuid.uuid4().hex[:6]}"

        # Recipient evaluates plausibility
        acceptance_threshold = 0.35
        evaluation_score = rel_trust * 0.6 + evidence_level * 0.4
        accepted = evaluation_score >= acceptance_threshold

        if accepted:
            # Clone node for recipient with updated provenance
            cloned_node = KnowledgeNode(
                node_id=node.node_id,
                node_type=node.node_type,
                label=node.label,
                description=node.description,
                properties=dict(node.properties),
                created_tick=tick,
                origin_type="peer_transmission",
                origin_id=sender_uid,
                validation_status=ValidationStatus.TESTING if evidence_level < 0.7 else ValidationStatus.SUPPORTED,
            )
            cloned_node.properties["transmitted_by"] = sender_uid
            cloned_node.properties["transmission_tick"] = tick
            recipient_kg.add_node(cloned_node)

        receipt = KnowledgeTransmissionReceipt(
            receipt_id=receipt_id,
            node_id=node.node_id,
            sender_uid=sender_uid,
            recipient_uid=recipient_uid,
            provenance_type=EpistemicProvenanceType.PEER_TRANSMISSION,
            evidence_score=evidence_level,
            confidence_transferred=round(evaluation_score, 3),
            tick=tick,
            was_accepted=accepted,
            rejection_reason=None if accepted else "Insufficient trust or evidence",
        )
        self.transmission_log.append(receipt)
        return receipt

    def elevate_to_communal_knowledge(
        self,
        node: KnowledgeNode,
        community_id: str,
        proposer_uid: str,
        community_members_count: int,
        supporting_uids: list[str],
        tick: int = 0,
    ) -> Optional[KnowledgeNode]:
        """Elevate verified individual knowledge into shared community knowledge if consensus reached."""
        consensus_ratio = len(supporting_uids) / max(1, community_members_count)
        if consensus_ratio < 0.50:
            return None

        comm_node = KnowledgeNode(
            node_id=f"comm_{node.node_id[:12]}_{uuid.uuid4().hex[:4]}",
            node_type=node.node_type,
            label=f"[Comunal] {node.label}",
            description=node.description,
            properties={
                **node.properties,
                "consensus_ratio": round(consensus_ratio, 3),
                "community_id": community_id,
                "proposer_uid": proposer_uid,
            },
            created_tick=tick,
            origin_type="community_tradition",
            origin_id=community_id,
            validation_status=ValidationStatus.CANONICAL,
        )
        self.collective_kg.institutionalize_knowledge(
            group_id=community_id,
            group_type="community",
            node=comm_node,
            documentation_type="oral_tradition",
            custodian_uid=proposer_uid,
            tick=tick,
        )
        return comm_node
