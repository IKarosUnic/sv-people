"""Knowledge transmission, rumor propagation, provenance tracking, and belief dynamics."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


@dataclass
class TransmissionRecord:
    """Historical record of an information transfer step."""

    from_human_id: HumanID
    to_human_id: HumanID
    tick: Tick
    generation: int
    transmitted_statement: str
    receiver_believed: bool


@dataclass
class InformationItem:
    """A claim, news item, or rumor circulating in the society."""

    info_id: str
    topic: str
    original_statement: str
    current_statement: str
    is_true: bool
    origin_human_id: HumanID
    created_tick: Tick
    generation: int = 0
    confidence: float = 1.0
    is_verified: bool = False
    transmission_chain: list[TransmissionRecord] = field(default_factory=list)

    def copy(self) -> InformationItem:
        return InformationItem(
            info_id=self.info_id,
            topic=self.topic,
            original_statement=self.original_statement,
            current_statement=self.current_statement,
            is_true=self.is_true,
            origin_human_id=self.origin_human_id,
            created_tick=self.created_tick,
            generation=self.generation,
            confidence=self.confidence,
            is_verified=self.is_verified,
            transmission_chain=list(self.transmission_chain),
        )


class RumorEngine:
    """Manages information sharing, trust-modulated belief adoption, and rumor distortion."""

    def __init__(
        self,
        distortion_rate: float = 0.15,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.distortion_rate = distortion_rate
        self.rng = rng or np.random.default_rng()
        self._known_information: dict[HumanID, dict[str, InformationItem]] = {} # human -> {info_id: item}

    def register_origin_knowledge(
        self,
        human_id: HumanID,
        info_id: str,
        topic: str,
        statement: str,
        is_true: bool,
        current_tick: Tick,
    ) -> InformationItem:
        """Introduce a new piece of knowledge known by an initial witness."""
        item = InformationItem(
            info_id=info_id,
            topic=topic,
            original_statement=statement,
            current_statement=statement,
            is_true=is_true,
            origin_human_id=human_id,
            created_tick=current_tick,
            generation=0,
            confidence=1.0,
            is_verified=True,
        )
        if human_id not in self._known_information:
            self._known_information[human_id] = {}
        self._known_information[human_id][info_id] = item
        return item

    def get_known_items(self, human_id: HumanID) -> list[InformationItem]:
        return list(self._known_information.get(human_id, {}).values())

    def has_knowledge(self, human_id: HumanID, info_id: str) -> bool:
        return info_id in self._known_information.get(human_id, {})

    def transmit(
        self,
        sender_id: HumanID,
        receiver_id: HumanID,
        info_id: str,
        trust_in_sender: float,
        current_tick: Tick,
    ) -> tuple[bool, str, Optional[InformationItem]]:
        """Transmit information from sender to receiver.

        Receiver evaluates belief based on trust in sender:
        - If trust >= 0.60: Receiver believes and stores the item.
        - If 0.35 <= trust < 0.60: Receiver doubts (stores with low confidence).
        - If trust < 0.35: Receiver disbelieves/ignores (item rejected).

        Returns (accepted: bool, reaction: str, received_item: Optional[InformationItem]).
        """
        sender_items = self._known_information.get(sender_id, {})
        item = sender_items.get(info_id)
        if not item:
            return False, "Sender does not possess this information", None

        # Determine receiver belief
        if trust_in_sender < 0.35:
            reaction = "disbelieve"
            believed = False
        elif trust_in_sender < 0.60:
            reaction = "doubt"
            believed = False
        else:
            reaction = "believe"
            believed = True

        # Copy item for receiver and advance generation
        rec_item = item.copy()
        rec_item.generation += 1

        # Possible rumor distortion / exaggeration over multiple hops
        if not rec_item.is_verified and self.rng.random() < self.distortion_rate:
            rec_item.current_statement = f"[Rumor exagerado] {rec_item.current_statement}"

        if believed:
            rec_item.confidence = min(1.0, trust_in_sender * rec_item.confidence)
        else:
            rec_item.confidence = 0.25

        tx_record = TransmissionRecord(
            from_human_id=sender_id,
            to_human_id=receiver_id,
            tick=current_tick,
            generation=rec_item.generation,
            transmitted_statement=rec_item.current_statement,
            receiver_believed=believed,
        )
        rec_item.transmission_chain.append(tx_record)

        if receiver_id not in self._known_information:
            self._known_information[receiver_id] = {}

        if believed or reaction == "doubt":
            self._known_information[receiver_id][info_id] = rec_item
            return True, reaction, rec_item

        return False, reaction, None

    def verify_information(self, human_id: HumanID, info_id: str, actual_truth: bool) -> bool:
        """Individual verifies the rumor by direct inspection, resolving doubts."""
        items = self._known_information.get(human_id, {})
        if info_id in items:
            item = items[info_id]
            item.is_verified = True
            item.is_true = actual_truth
            item.confidence = 1.0
            return True
        return False
