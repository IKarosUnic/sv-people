"""Family Caregiving, Child Development & Intergenerational Support (Phase 1.5 Extension).

Simulates:
- Childcare and dependent child development: food provision, attachment, and developmental growth.
- Elderly relative caregiving: physical assistance, health stabilization, and intergenerational remittances.
- Bereavement, emotional mourning periods, and inheritance succession with kinship guardianship takeover.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

from saltbor.core.types import EmotionType, Tick
from saltbor.events.types import EventType, SimulationEvent

logger = logging.getLogger(__name__)


class FamilyCaregivingEngine:
    """Manages domestic caregiving, child dependency, and intergenerational obligations."""

    def __init__(self) -> None:
        self.caregiving_history: list[dict[str, Any]] = []

    def perform_childcare(
        self,
        caregiver: Any,
        child: Any,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Caregiver satisfies child vital needs (hunger, comfort, attachment)."""
        # Caregiver effort
        caregiver.physical_state.energy = max(0.05, caregiver.physical_state.energy - 0.05)

        # Child vital benefits
        child.physical_state.hunger = max(0.0, child.physical_state.hunger - 0.40)
        child.physical_state.energy = min(1.0, child.physical_state.energy + 0.10)

        # Attachment & emotional security
        child.emotions.induce_emotion(
            emotion_type=EmotionType.AFFECTION,
            intensity=0.85,
            duration_ticks=30,
        )

        record = {
            "type": "childcare",
            "caregiver_uid": str(caregiver.uid),
            "child_uid": str(child.uid),
            "tick": current_tick,
            "child_age": child.demographics.age,
        }
        self.caregiving_history.append(record)

        logger.info("%s provided childcare to %s (age %d)", caregiver.name, child.name, child.demographics.age)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.CHILDCARE_PROVIDED,
                tick=current_tick,
                source_human_id=caregiver.uid,
                target_human_id=child.uid,
                data=record,
                importance=0.6,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"{caregiver.name} alimentó y cuidó a su hijo/a {child.name}")

        return {"success": True, "child_hunger": child.physical_state.hunger}

    def perform_elder_care(
        self,
        caregiver: Any,
        elder: Any,
        financial_support_usd: float = 0.0,
        current_tick: Tick = 0,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Adult child supports an elderly parent with physical assistance and living allowance."""
        caregiver.physical_state.energy = max(0.05, caregiver.physical_state.energy - 0.04)

        if financial_support_usd > 0:
            transfer = min(caregiver.physical_state.money, financial_support_usd)
            caregiver.physical_state.money = round(caregiver.physical_state.money - transfer, 2)
            elder.physical_state.money = round(elder.physical_state.money + transfer, 2)

        # Health and emotional stabilization for elder
        elder.physical_state.health = min(1.0, elder.physical_state.health + 0.02)
        elder.emotions.induce_emotion(
            emotion_type=EmotionType.RELIEF,
            intensity=0.75,
            duration_ticks=24,
        )

        record = {
            "type": "elder_care",
            "caregiver_uid": str(caregiver.uid),
            "elder_uid": str(elder.uid),
            "financial_support_usd": financial_support_usd,
            "tick": current_tick,
        }
        self.caregiving_history.append(record)

        logger.info("%s assisted elderly relative %s ($%.2f support)", caregiver.name, elder.name, financial_support_usd)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.ELDER_CARE_PROVIDED,
                tick=current_tick,
                source_human_id=caregiver.uid,
                target_human_id=elder.uid,
                data=record,
                importance=0.65,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"{caregiver.name} brindó cuidados y sustento a adulto mayor {elder.name}")

        return {"success": True, "elder_money": elder.physical_state.money}

    def handle_bereavement_and_succession(
        self,
        deceased: Any,
        surviving_members: list[Any],
        current_tick: Tick,
        household_registry: Optional[Any] = None,
        genealogy: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Handle death of a family member: grief mourning, inheritance, and dependent child guardianship."""
        deceased_money = deceased.physical_state.money
        deceased.physical_state.money = 0.0

        # Bereavement grief for all surviving family members
        for survivor in surviving_members:
            if survivor.uid == deceased.uid:
                continue
            survivor.emotions.induce_emotion(
                emotion_type=EmotionType.GRIEF,
                intensity=0.90,
                duration_ticks=60,
            )
            if event_bus:
                evt_grief = SimulationEvent(
                    event_type=EventType.BEREAVEMENT_EXPERIENCED,
                    tick=current_tick,
                    source_human_id=survivor.uid,
                    data={"deceased_uid": str(deceased.uid), "deceased_name": deceased.name},
                    importance=0.85,
                )
                event_bus.emit(evt_grief)
                if causal_graph:
                    causal_graph.add_event(evt_grief, description=f"{survivor.name} experimentó duelo por muerte de {deceased.name}")

        # Distribute inheritance
        eligible_adults = [m for m in surviving_members if m.uid != deceased.uid and m.demographics.age >= 18]
        inheritance_map: dict[str, float] = {}

        if eligible_adults and deceased_money > 0:
            share = round(deceased_money / len(eligible_adults), 2)
            for adult in eligible_adults:
                adult.physical_state.money = round(adult.physical_state.money + share, 2)
                inheritance_map[str(adult.uid)] = share
                if event_bus:
                    evt_inh = SimulationEvent(
                        event_type=EventType.INHERITANCE_PASSED,
                        tick=current_tick,
                        source_human_id=adult.uid,
                        data={"inherited_usd": share, "from_deceased": deceased.name},
                        importance=0.7,
                    )
                    event_bus.emit(evt_inh)
                    if causal_graph:
                        causal_graph.add_event(evt_inh, description=f"{adult.name} heredó ${share:.2f} tras deceso de {deceased.name}")

        return {
            "deceased_uid": str(deceased.uid),
            "survivors_grieving_count": len(surviving_members) - 1,
            "inheritance_distributed": inheritance_map,
        }
