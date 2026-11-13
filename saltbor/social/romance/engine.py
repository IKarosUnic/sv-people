"""Romantic Relationship, Dynamics, Infidelity & Heartbreak Engine (Phase 1.5 Extension).

Simulates:
- Initial attraction and mutual courtship dates.
- Stage progression: Interest -> Dating -> Cohabitation -> Marriage.
- Jealousy emergence and causal infidelity based on low commitment and opportunity.
- Discovery mechanisms, catastrophic trust collapse, and non-deterministic confrontation outcomes:
  forgiveness/reconciliation vs irrevocable separation/divorce.
- Unrequited love, heartbreak grief, and gradual emotional recovery over time.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np

from saltbor.core.types import EmotionType, RomanceStage, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.social.romance.models import (
    HeartbreakRecord,
    InfidelityRecord,
    RomanticDimensions,
    RomanticRelationship,
)

logger = logging.getLogger(__name__)


class RomanceEngine:
    """Central engine orchestrating romantic dynamics, courtship, infidelity, and heartbreak."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self._relationships: dict[str, RomanticRelationship] = {}
        self.heartbreak_records: list[HeartbreakRecord] = []
        self.infidelity_records: list[InfidelityRecord] = []
        self._pending_widow_heartbreaks: dict[str, HeartbreakRecord] = {}
        self._rng = np.random.default_rng(seed)

    def get_relationship(self, rel_id: str) -> Optional[RomanticRelationship]:
        return self._relationships.get(rel_id)

    def get_all_relationships(self) -> list[RomanticRelationship]:
        return list(self._relationships.values())

    def get_agent_relationship(self, agent_uid: str) -> Optional[RomanticRelationship]:
        """Find active romantic relationship for an agent."""
        for r in self._relationships.values():
            if r.is_active and agent_uid in (r.partner_a_id, r.partner_b_id):
                return r
        return None

    # -------------------------------------------------------------------------
    # Attraction & Initiation
    # -------------------------------------------------------------------------

    def calculate_initial_attraction(self, human_a: Any, human_b: Any) -> float:
        """Calculate pairwise attraction based on age difference, personality compatibility, and traits."""
        age_diff = abs(human_a.demographics.age - human_b.demographics.age)
        age_score = max(0.20, 1.0 - (age_diff / 30.0))

        # Big Five trait harmony (Agreeableness, Extraversion, Openness)
        traits_a = getattr(human_a.personality, "traits", None)
        traits_b = getattr(human_b.personality, "traits", None)

        compat = 0.50
        if traits_a and traits_b:
            t_a = traits_a.get_trait("agreeableness") if hasattr(traits_a, "get_trait") else None
            t_b = traits_b.get_trait("agreeableness") if hasattr(traits_b, "get_trait") else None
            agr_a = getattr(t_a, "current_value", 0.5) if t_a else 0.5
            agr_b = getattr(t_b, "current_value", 0.5) if t_b else 0.5
            compat = (agr_a + agr_b) / 2.0

        random_spark = float(self._rng.uniform(0.10, 0.35))
        attraction = round(min(1.0, (age_score * 0.40) + (compat * 0.30) + random_spark), 2)
        return attraction

    def initiate_romantic_interest(
        self,
        human_a: Any,
        human_b: Any,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> Optional[RomanticRelationship]:
        """Initiate romantic interest and register new relationship if both are available."""
        # Check if already partnered
        if self.get_agent_relationship(str(human_a.uid)) or self.get_agent_relationship(str(human_b.uid)):
            return None

        attr_a = self.calculate_initial_attraction(human_a, human_b)
        attr_b = self.calculate_initial_attraction(human_b, human_a)

        # Require minimum mutual attraction
        if attr_a < 0.40 or attr_b < 0.40:
            return None

        rel_id = f"rom_{uuid.uuid4().hex[:8]}"
        rel = RomanticRelationship(
            relationship_id=rel_id,
            partner_a_id=str(human_a.uid),
            partner_b_id=str(human_b.uid),
            stage=RomanceStage.INTEREST,
            dims_a=RomanticDimensions(attraction=attr_a, affection=0.45, trust=0.50, commitment=0.20),
            dims_b=RomanticDimensions(attraction=attr_b, affection=0.45, trust=0.50, commitment=0.20),
            start_tick=current_tick,
            is_active=True,
        )
        self._relationships[rel_id] = rel

        human_a.romantic_partner_id = str(human_b.uid)
        human_b.romantic_partner_id = str(human_a.uid)

        logger.info("Romantic interest formed between %s and %s", human_a.name, human_b.name)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.ROMANTIC_ATTRACTION_FORMED,
                tick=current_tick,
                source_human_id=human_a.uid,
                target_human_id=human_b.uid,
                data={"relationship_id": rel_id, "attraction_a": attr_a, "attraction_b": attr_b},
                importance=0.7,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Atracción romántica mutua entre {human_a.name} y {human_b.name}")

        return rel

    # -------------------------------------------------------------------------
    # Courtship Dates & Stage Progression
    # -------------------------------------------------------------------------

    def conduct_courtship_date(
        self,
        relationship_id: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> dict[str, Any]:
        """A courtship outing deepening mutual affection, trust, and commitment."""
        rel = self._relationships.get(relationship_id)
        if not rel or not rel.is_active:
            return {"success": False, "reason": "Relationship inactive or not found"}

        rel.dates_count += 1
        rel.shared_memories_count += 1

        # Deepen bond vectors
        for d in (rel.dims_a, rel.dims_b):
            d.affection = min(1.0, round(d.affection + 0.08, 2))
            d.trust = min(1.0, round(d.trust + 0.05, 2))
            d.commitment = min(1.0, round(d.commitment + 0.06, 2))
            d.conflict_level = max(0.0, round(d.conflict_level - 0.05, 2))

        avg_comm = (rel.dims_a.commitment + rel.dims_b.commitment) / 2.0
        prior_stage = rel.stage

        # Stage progression rules
        if rel.stage == RomanceStage.INTEREST and rel.dates_count >= 2 and avg_comm >= 0.30:
            rel.stage = RomanceStage.DATING
            if event_bus:
                evt = SimulationEvent(
                    event_type=EventType.DATING_STARTED,
                    tick=current_tick,
                    data={"relationship_id": relationship_id, "dates_count": rel.dates_count},
                    importance=0.75,
                )
                event_bus.emit(evt)
                if causal_graph:
                    causal_graph.add_event(evt, description=f"Formalización de noviazgo en relación {relationship_id}")

        elif rel.stage == RomanceStage.DATING and rel.dates_count >= 5 and avg_comm >= 0.55:
            rel.stage = RomanceStage.COHABITING
            if event_bus:
                evt = SimulationEvent(
                    event_type=EventType.PARTNERSHIP_FORMED,
                    tick=current_tick,
                    data={"relationship_id": relationship_id},
                    importance=0.8,
                )
                event_bus.emit(evt)
                if causal_graph:
                    causal_graph.add_event(evt, description=f"Convivencia y unión de hecho en relación {relationship_id}")

        elif rel.stage == RomanceStage.COHABITING and rel.dates_count >= 8 and avg_comm >= 0.75:
            rel.stage = RomanceStage.MARRIED
            rel.marriage_tick = current_tick
            if event_bus:
                evt = SimulationEvent(
                    event_type=EventType.MARRIAGE_CELEBRATED,
                    tick=current_tick,
                    data={"relationship_id": relationship_id},
                    importance=0.9,
                )
                event_bus.emit(evt)
                if causal_graph:
                    causal_graph.add_event(evt, description=f"Celebración de matrimonio en relación {relationship_id}")

        return {
            "success": True,
            "dates_count": rel.dates_count,
            "stage": rel.stage.value,
            "promoted": rel.stage != prior_stage,
        }

    # -------------------------------------------------------------------------
    # Infidelity & Jealousy Dynamics
    # -------------------------------------------------------------------------

    def evaluate_jealousy_and_infidelity(
        self,
        human: Any,
        third_party: Any,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> Optional[InfidelityRecord]:
        """Evaluate infidelity emergence based on low commitment, friction, and third-party attraction."""
        rel = self.get_agent_relationship(str(human.uid))
        if not rel or rel.stage == RomanceStage.INTEREST:
            return None

        dims = rel.get_partner_dims(str(human.uid))
        partner_uid = rel.get_other_uid(str(human.uid))

        # Check attraction to third party
        attraction_to_third = self.calculate_initial_attraction(human, third_party)

        # Plausibility conditions:
        # Commitment < 0.50 OR Conflict > 0.40, combined with high attraction to third party
        vulnerability_score = (1.0 - dims.commitment) * 0.6 + (dims.conflict_level * 0.4)
        infidelity_prob = min(0.70, max(0.0, vulnerability_score * (attraction_to_third - 0.25)))

        if infidelity_prob <= 0.0 or self._rng.random() >= infidelity_prob:
            return None

        # Infidelity occurs
        rec_id = f"inf_{uuid.uuid4().hex[:8]}"
        record = InfidelityRecord(
            record_id=rec_id,
            wayward_partner_uid=str(human.uid),
            betrayed_partner_uid=partner_uid,
            third_party_uid=str(third_party.uid),
            tick_occurred=current_tick,
            is_discovered=False,
            outcome="undiscovered",
        )
        self.infidelity_records.append(record)
        rel.infidelity_history.append(record)

        # Erodes internal commitment further
        dims.commitment = max(0.05, dims.commitment - 0.15)
        dims.jealousy = min(1.0, dims.jealousy + 0.10)

        logger.warning("Infidelity occurred: %s betrayed %s with %s", human.name, partner_uid, third_party.name)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.INFIDELITY_COMMITTED,
                tick=current_tick,
                source_human_id=human.uid,
                target_human_id=third_party.uid,
                data={"infidelity_id": rec_id, "primary_relationship_id": rel.relationship_id},
                importance=0.85,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Infidelidad de {human.name} con {third_party.name}")

        return record

    def evaluate_infidelity_discovery(
        self,
        relationship_id: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> Optional[dict[str, Any]]:
        """Evaluate discovery of undiscovered infidelity incidents."""
        rel = self._relationships.get(relationship_id)
        if not rel or not rel.is_active:
            return None

        undiscovered = [inf for inf in rel.infidelity_history if not inf.is_discovered]
        if not undiscovered:
            return None

        target_inf = undiscovered[0]
        betrayed_dims = rel.get_partner_dims(target_inf.betrayed_partner_uid)

        # Discovery probability proportional to betrayed partner's jealousy & suspicion
        discovery_prob = 0.20 + (betrayed_dims.jealousy * 0.40)

        if self._rng.random() >= discovery_prob:
            return None

        # Discovery occurs!
        target_inf.is_discovered = True
        target_inf.discovery_tick = current_tick

        # Catastrophic trust collapse
        betrayed_dims.trust = max(0.02, round(betrayed_dims.trust * 0.15, 2))
        betrayed_dims.affection = max(0.05, round(betrayed_dims.affection * 0.30, 2))
        betrayed_dims.conflict_level = 0.95

        # Emit discovery event
        if event_bus:
            evt_disc = SimulationEvent(
                event_type=EventType.INFIDELITY_DISCOVERED,
                tick=current_tick,
                data={
                    "infidelity_id": target_inf.record_id,
                    "relationship_id": relationship_id,
                    "betrayed_uid": target_inf.betrayed_partner_uid,
                },
                importance=0.95,
            )
            event_bus.emit(evt_disc)
            if causal_graph:
                causal_graph.add_event(evt_disc, description=f"Descubrimiento de infidelidad en relación {relationship_id}")

        # Non-deterministic outcome: Forgiveness vs Separation
        # Forgiveness chance: high compatibility + communication + luck
        forgiveness_prob = (betrayed_dims.compatibility * 0.3) + (betrayed_dims.communication_quality * 0.3)
        if self._rng.random() < forgiveness_prob and rel.stage != RomanceStage.INTEREST:
            # Reconcile with scarred trust
            target_inf.outcome = "forgiven_reconciliation"
            betrayed_dims.trust = 0.25
            logger.info("Relationship %s reconciled after infidelity confrontation", relationship_id)
            if event_bus:
                evt_rec = SimulationEvent(
                    event_type=EventType.ROMANCE_RECONCILED,
                    tick=current_tick,
                    data={"relationship_id": relationship_id},
                    importance=0.8,
                )
                event_bus.emit(evt_rec)
                if causal_graph:
                    causal_graph.add_event(evt_rec, description=f"Perdón y reconciliación conyugal en relación {relationship_id}")
            return {"outcome": "forgiven_reconciliation", "relationship_id": relationship_id}
        else:
            # Separation / Divorce
            target_inf.outcome = "divorce" if rel.stage == RomanceStage.MARRIED else "separation"
            rel.is_active = False
            rel.separation_tick = current_tick
            rel.stage = RomanceStage.DIVORCED if rel.stage == RomanceStage.MARRIED else RomanceStage.SEPARATED

            # Record heartbreak for betrayed partner
            hb_id = f"hb_{uuid.uuid4().hex[:8]}"
            hb = HeartbreakRecord(
                record_id=hb_id,
                individual_uid=target_inf.betrayed_partner_uid,
                former_partner_uid=target_inf.wayward_partner_uid,
                tick_started=current_tick,
                pain_intensity=0.85,
                reason="Traición por infidelidad y ruptura de matrimonio/unión",
            )
            self.heartbreak_records.append(hb)

            logger.warning("Relationship %s terminated by %s following infidelity", relationship_id, target_inf.outcome)
            if event_bus:
                evt_end = SimulationEvent(
                    event_type=EventType.DIVORCE_FINALIZED if rel.stage == RomanceStage.DIVORCED else EventType.RELATIONSHIP_SEPARATED,
                    tick=current_tick,
                    data={"relationship_id": relationship_id, "outcome": target_inf.outcome},
                    importance=0.9,
                )
                event_bus.emit(evt_end)
                if causal_graph:
                    causal_graph.add_event(evt_end, description=f"Ruptura definitiva de relación {relationship_id}: {target_inf.outcome}")

            return {"outcome": target_inf.outcome, "relationship_id": relationship_id}

    # -------------------------------------------------------------------------
    # Pre-existing Unions and Everyday Relationship Dynamics
    # -------------------------------------------------------------------------

    def register_existing_relationship(
        self,
        human_a: Any,
        human_b: Any,
        stage: RomanceStage,
        start_tick: Tick = 0,
        trust: float = 0.50,
        affinity: float = 0.50,
        dates_count: int = 0,
        marriage_tick: Optional[Tick] = None,
    ) -> RomanticRelationship:
        """Register a pre-existing union without fabricating a new courtship event.

        This restores an initial condition (for example a married couple that
        already existed before the simulation started).  It is deliberately
        separate from :meth:`initiate_romantic_interest`, which represents an
        observable state transition during the run.
        """
        existing = self.get_agent_relationship(str(human_a.uid))
        if existing is not None:
            return existing

        rel_id = f"rom_{uuid.uuid4().hex[:8]}"
        compatibility = round(min(1.0, 0.45 + (trust + affinity) * 0.25), 2)
        rel = RomanticRelationship(
            relationship_id=rel_id,
            partner_a_id=str(human_a.uid),
            partner_b_id=str(human_b.uid),
            stage=stage,
            dims_a=RomanticDimensions(
                attraction=round(affinity, 2),
                affection=round(affinity, 2),
                trust=round(trust, 2),
                commitment=0.85 if stage in (RomanceStage.COHABITING, RomanceStage.MARRIED) else 0.40,
                compatibility=compatibility,
                communication_quality=round(min(1.0, (trust + affinity) / 2.0), 2),
                jealousy=0.10,
                conflict_level=0.05,
            ),
            dims_b=RomanticDimensions(
                attraction=round(affinity, 2),
                affection=round(affinity, 2),
                trust=round(trust, 2),
                commitment=0.85 if stage in (RomanceStage.COHABITING, RomanceStage.MARRIED) else 0.40,
                compatibility=compatibility,
                communication_quality=round(min(1.0, (trust + affinity) / 2.0), 2),
                jealousy=0.10,
                conflict_level=0.05,
            ),
            shared_memories_count=dates_count,
            dates_count=dates_count,
            start_tick=start_tick,
            marriage_tick=marriage_tick,
            is_active=True,
        )
        self._relationships[rel_id] = rel
        human_a.romantic_partner_id = str(human_b.uid)
        human_b.romantic_partner_id = str(human_a.uid)
        return rel

    def step_relationship_dynamics(
        self,
        relationship_id: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Apply one day of ordinary romantic drift, friction and repair.

        Trust, affection and communication are not static scores: they drift
        toward compatibility, are eroded by unresolved conflict, and can be
        repaired.  A union may end through ordinary irreconcilable friction,
        not only through infidelity.
        """
        rel = self._relationships.get(relationship_id)
        if not rel or not rel.is_active:
            return {"success": False, "reason": "Relationship inactive or not found"}

        for dims in (rel.dims_a, rel.dims_b):
            dims.affection = round(
                max(0.0, min(1.0, dims.affection + (dims.compatibility - dims.affection) * 0.010
                                  + float(self._rng.normal(0.0, 0.002)))),
                3,
            )
            dims.trust = round(
                max(0.0, min(1.0, dims.trust + float(self._rng.normal(0.0, 0.0015))
                                  - dims.conflict_level * 0.004)),
                3,
            )
            dims.communication_quality = round(
                max(0.0, min(1.0, dims.communication_quality + 0.002
                                  - dims.conflict_level * 0.003)),
                3,
            )
            dims.commitment = round(
                max(0.05, min(1.0, dims.commitment + (0.001 if dims.trust > 0.45 else -0.002))),
                3,
            )
            dims.jealousy = round(
                max(0.0, min(1.0, dims.jealousy + (0.004 if dims.trust < 0.35 else -0.003))),
                3,
            )
            # Friction decays when communication is healthy.
            dims.conflict_level = round(
                max(0.0, dims.conflict_level - 0.02 * max(0.20, dims.communication_quality)),
                3,
            )

        avg_conflict = (rel.dims_a.conflict_level + rel.dims_b.conflict_level) / 2.0
        avg_comm = (rel.dims_a.communication_quality + rel.dims_b.communication_quality) / 2.0
        avg_affection = (rel.dims_a.affection + rel.dims_b.affection) / 2.0

        conflict_prob = max(0.0, 0.012 + avg_conflict * 0.05 - avg_comm * 0.012)
        if rel.stage != RomanceStage.INTEREST and self._rng.random() < conflict_prob:
            increase = round(float(self._rng.uniform(0.04, 0.12)), 2)
            for dims in (rel.dims_a, rel.dims_b):
                dims.conflict_level = min(1.0, round(dims.conflict_level + increase, 2))
                dims.affection = max(0.0, round(dims.affection - increase * 0.20, 2))
            if event_bus:
                evt = SimulationEvent(
                    event_type=EventType.ROMANTIC_CONFLICT,
                    tick=current_tick,
                    data={
                        "relationship_id": relationship_id,
                        "conflict_increase": increase,
                        "conflict_level": round(avg_conflict + increase, 2),
                        "reason": "fricción cotidiana y comunicación insuficiente",
                    },
                    importance=0.55,
                )
                event_bus.emit(evt)
                if causal_graph:
                    causal_graph.add_event(evt, description=f"Conflicto cotidiano en relación {relationship_id}")

        # Irreconcilable ordinary separation: low affection + chronic conflict.
        if avg_affection < 0.24 and avg_conflict > 0.72 and self._rng.random() < 0.06:
            self._terminate_relationship(
                rel,
                current_tick=current_tick,
                reason="Separación por conflicto crónico e incompatibilidad",
                event_bus=event_bus,
                causal_graph=causal_graph,
                heartbroken_uids=[rel.partner_a_id, rel.partner_b_id],
            )
            return {"success": True, "stage": rel.stage.value, "separated": True}

        return {"success": True, "stage": rel.stage.value, "separated": False}

    def evaluate_reconciliation(
        self,
        relationship_id: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> bool:
        """Evaluate whether a separated couple attempts reconciliation."""
        rel = self._relationships.get(relationship_id)
        if not rel or rel.is_active or rel.stage != RomanceStage.SEPARATED:
            return False

        avg_affection = (rel.dims_a.affection + rel.dims_b.affection) / 2.0
        avg_comm = (rel.dims_a.communication_quality + rel.dims_b.communication_quality) / 2.0
        prob = max(0.0, (avg_affection * 0.20) + (avg_comm * 0.10) - 0.02)
        if self._rng.random() >= prob:
            return False

        rel.is_active = True
        rel.stage = RomanceStage.DATING
        rel.separation_tick = None
        for dims in (rel.dims_a, rel.dims_b):
            dims.trust = max(dims.trust, 0.35)
            dims.conflict_level = min(dims.conflict_level, 0.35)
            dims.commitment = max(dims.commitment, 0.45)
        for uid in (rel.partner_a_id, rel.partner_b_id):
            hb = self.find_active_heartbreak(uid, rel.relationship_id)
            if hb:
                hb.recovery_progress = max(hb.recovery_progress, 0.5)

        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.ROMANCE_RECONCILED,
                tick=current_tick,
                data={"relationship_id": relationship_id, "reason": "reconciliación tras separación"},
                importance=0.80,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Reconciliación de la relación {relationship_id}")
        return True

    # -------------------------------------------------------------------------
    # Unrequited Love, Widowhood and Relationship Termination
    # -------------------------------------------------------------------------

    def evaluate_unrequited_love(
        self,
        seeker: Any,
        target: Any,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> Optional[HeartbreakRecord]:
        """Model one-sided attraction that is not reciprocated.

        The target's lack of attraction is a state, not an arbitrary rejection
        label.  A heartbreak record is only created when the asymmetry is real.
        """
        if self.get_agent_relationship(str(seeker.uid)) or self.get_agent_relationship(str(target.uid)):
            return None
        if getattr(target, "romantic_partner_id", None):
            return None

        seeker_attr = self.calculate_initial_attraction(seeker, target)
        target_attr = self.calculate_initial_attraction(target, seeker)
        if seeker_attr < 0.55 or target_attr >= 0.35:
            return None

        # Not every one-sided crush becomes a lingering heartbreak.
        if self._rng.random() >= 0.20:
            return None

        hb = HeartbreakRecord(
            record_id=f"hb_{uuid.uuid4().hex[:8]}",
            individual_uid=str(seeker.uid),
            former_partner_uid=str(target.uid),
            tick_started=current_tick,
            pain_intensity=round(min(0.85, 0.45 + seeker_attr * 0.35), 2),
            is_unrequited=True,
            reason="Amor no correspondido: atracción unilateral sin reciprocidad",
        )
        self.heartbreak_records.append(hb)
        seeker.heartbreak_state = hb

        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.UNREQUITED_LOVE,
                tick=current_tick,
                source_human_id=seeker.uid,
                target_human_id=target.uid,
                location_id=getattr(seeker.physical_state, "current_location_id", None),
                data={
                    "heartbreak_id": hb.record_id,
                    "seeker_attraction": seeker_attr,
                    "target_attraction": target_attr,
                    "is_unrequited": True,
                },
                importance=0.65,
            )
            event_bus.emit(evt)
            hb_evt = SimulationEvent(
                event_type=EventType.HEARTBREAK_EXPERIENCED,
                tick=current_tick,
                source_human_id=seeker.uid,
                data={"heartbreak_id": hb.record_id, "reason": hb.reason, "pain_intensity": hb.pain_intensity},
                importance=0.70,
                cause_event_id=evt.event_id,
            )
            event_bus.emit(hb_evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"{seeker.name} desarrolló amor no correspondido por {target.name}")
                causal_graph.add_event(hb_evt, cause_event_id=str(evt.event_id), description=f"{seeker.name} sufrió desamor")
        return hb

    def handle_partner_death(
        self,
        relationship_id: str,
        deceased_uid: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> Optional[HeartbreakRecord]:
        """Close a union because one partner died, without inventing a breakup."""
        rel = self._relationships.get(relationship_id)
        if not rel or not rel.is_active:
            return None
        if deceased_uid not in (rel.partner_a_id, rel.partner_b_id):
            return None

        survivor_uid = rel.get_other_uid(deceased_uid)
        rel.is_active = False
        rel.stage = RomanceStage.WIDOWED
        rel.separation_tick = current_tick

        hb = HeartbreakRecord(
            record_id=f"hb_{uuid.uuid4().hex[:8]}",
            individual_uid=survivor_uid,
            former_partner_uid=deceased_uid,
            tick_started=current_tick,
            pain_intensity=0.95,
            reason="Viudez: fallecimiento de la pareja",
        )
        self.heartbreak_records.append(hb)
        self._pending_widow_heartbreaks[survivor_uid] = hb

        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.HEARTBREAK_EXPERIENCED,
                tick=current_tick,
                data={
                    "heartbreak_id": hb.record_id,
                    "survivor_uid": survivor_uid,
                    "deceased_uid": deceased_uid,
                    "reason": hb.reason,
                },
                importance=0.95,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Viudez y duelo de pareja en relación {relationship_id}")
        return hb

    def _terminate_relationship(
        self,
        rel: RomanticRelationship,
        current_tick: Tick,
        reason: str,
        event_bus: Optional[Any],
        causal_graph: Optional[Any],
        heartbroken_uids: list[str],
    ) -> None:
        rel.is_active = False
        rel.separation_tick = current_tick
        rel.stage = RomanceStage.DIVORCED if rel.stage == RomanceStage.MARRIED else RomanceStage.SEPARATED

        for uid in heartbroken_uids:
            hb = HeartbreakRecord(
                record_id=f"hb_{uuid.uuid4().hex[:8]}",
                individual_uid=uid,
                former_partner_uid=rel.get_other_uid(uid),
                tick_started=current_tick,
                pain_intensity=0.80,
                reason=reason,
            )
            self.heartbreak_records.append(hb)
            self._pending_widow_heartbreaks[uid] = hb

        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.DIVORCE_FINALIZED if rel.stage == RomanceStage.DIVORCED else EventType.RELATIONSHIP_SEPARATED,
                tick=current_tick,
                data={"relationship_id": rel.relationship_id, "reason": reason},
                importance=0.82,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Ruptura de relación {rel.relationship_id}: {reason}")

    def find_active_heartbreak(self, uid: str, relationship_id: Optional[str] = None) -> Optional[HeartbreakRecord]:
        """Return an unrecovered heartbreak record for an individual."""
        for hb in reversed(self.heartbreak_records):
            if hb.individual_uid == uid and not hb.is_healed:
                return hb
        return None

    def attach_pending_heartbreak(self, human: Any) -> Optional[HeartbreakRecord]:
        """Attach a newly created widowhood/breakup record to its live human."""
        hb = self._pending_widow_heartbreaks.pop(str(human.uid), None)
        if hb is None:
            hb = self.find_active_heartbreak(str(human.uid))
        if hb is not None:
            human.heartbreak_state = hb
        return hb

    def to_dict(self) -> dict[str, Any]:
        """Serialize romantic state for SQLite checkpoint restoration."""
        relationships = []
        for rel in self._relationships.values():
            relationships.append({
                "relationship_id": rel.relationship_id,
                "partner_a_id": rel.partner_a_id,
                "partner_b_id": rel.partner_b_id,
                "stage": rel.stage.value,
                "dims_a": rel.dims_a.to_dict(),
                "dims_b": rel.dims_b.to_dict(),
                "shared_memories_count": rel.shared_memories_count,
                "dates_count": rel.dates_count,
                "start_tick": rel.start_tick,
                "marriage_tick": rel.marriage_tick,
                "separation_tick": rel.separation_tick,
                "is_active": rel.is_active,
                "infidelity_history": [
                    {
                        "record_id": r.record_id,
                        "wayward_partner_uid": r.wayward_partner_uid,
                        "betrayed_partner_uid": r.betrayed_partner_uid,
                        "third_party_uid": r.third_party_uid,
                        "tick_occurred": r.tick_occurred,
                        "is_discovered": r.is_discovered,
                        "discovery_tick": r.discovery_tick,
                        "outcome": r.outcome,
                    }
                    for r in rel.infidelity_history
                ],
            })
        heartbreaks = [
            {
                "record_id": h.record_id,
                "individual_uid": h.individual_uid,
                "former_partner_uid": h.former_partner_uid,
                "tick_started": h.tick_started,
                "pain_intensity": h.pain_intensity,
                "is_unrequited": h.is_unrequited,
                "reason": h.reason,
                "recovery_progress": h.recovery_progress,
            }
            for h in self.heartbreak_records
        ]
        infidelities = [
            {
                "record_id": r.record_id,
                "wayward_partner_uid": r.wayward_partner_uid,
                "betrayed_partner_uid": r.betrayed_partner_uid,
                "third_party_uid": r.third_party_uid,
                "tick_occurred": r.tick_occurred,
                "is_discovered": r.is_discovered,
                "discovery_tick": r.discovery_tick,
                "outcome": r.outcome,
            }
            for r in self.infidelity_records
        ]
        return {"relationships": relationships, "heartbreaks": heartbreaks, "infidelities": infidelities}

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore romantic state captured by :meth:`to_dict`."""
        self._relationships.clear()
        self.heartbreak_records.clear()
        self.infidelity_records.clear()

        for r in data.get("relationships", []):
            rel = RomanticRelationship(
                relationship_id=r["relationship_id"],
                partner_a_id=r["partner_a_id"],
                partner_b_id=r["partner_b_id"],
                stage=RomanceStage(r.get("stage", "interest")),
                dims_a=RomanticDimensions(**r.get("dims_a", {})),
                dims_b=RomanticDimensions(**r.get("dims_b", {})),
                shared_memories_count=int(r.get("shared_memories_count", 0)),
                dates_count=int(r.get("dates_count", 0)),
                start_tick=int(r.get("start_tick", 0)),
                marriage_tick=r.get("marriage_tick"),
                separation_tick=r.get("separation_tick"),
                is_active=bool(r.get("is_active", True)),
            )
            for inf in r.get("infidelity_history", []):
                record = InfidelityRecord(
                    record_id=inf["record_id"],
                    wayward_partner_uid=inf["wayward_partner_uid"],
                    betrayed_partner_uid=inf["betrayed_partner_uid"],
                    third_party_uid=inf["third_party_uid"],
                    tick_occurred=int(inf.get("tick_occurred", 0)),
                    is_discovered=bool(inf.get("is_discovered", False)),
                    discovery_tick=inf.get("discovery_tick"),
                    outcome=inf.get("outcome", "undiscovered"),
                )
                rel.infidelity_history.append(record)
            self._relationships[rel.relationship_id] = rel

        for h in data.get("heartbreaks", []):
            self.heartbreak_records.append(HeartbreakRecord(
                record_id=h["record_id"],
                individual_uid=h["individual_uid"],
                former_partner_uid=h["former_partner_uid"],
                tick_started=int(h.get("tick_started", 0)),
                pain_intensity=float(h.get("pain_intensity", 0.7)),
                is_unrequited=bool(h.get("is_unrequited", False)),
                reason=h.get("reason", "Ruptura sentimental"),
                recovery_progress=float(h.get("recovery_progress", 0.0)),
            ))

        for r in data.get("infidelities", []):
            self.infidelity_records.append(InfidelityRecord(
                record_id=r["record_id"],
                wayward_partner_uid=r["wayward_partner_uid"],
                betrayed_partner_uid=r["betrayed_partner_uid"],
                third_party_uid=r["third_party_uid"],
                tick_occurred=int(r.get("tick_occurred", 0)),
                is_discovered=bool(r.get("is_discovered", False)),
                discovery_tick=r.get("discovery_tick"),
                outcome=r.get("outcome", "undiscovered"),
            ))

    # -------------------------------------------------------------------------
    # Heartbreak Recovery
    # -------------------------------------------------------------------------

    def step_heartbreak_recovery(
        self,
        human: Any,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> None:
        """Advance emotional healing for heartbroken individuals."""
        hb = getattr(human, "heartbreak_state", None)
        if not hb:
            return

        # Emotional healing per day (proportional to conscientiousness and social support)
        daily_healing = 0.05
        hb.recovery_progress = min(1.0, hb.recovery_progress + (daily_healing / 24.0))

        if hb.is_healed:
            human.heartbreak_state = None
            logger.info("Human %s emotionally recovered from heartbreak", human.name)
            if event_bus:
                evt = SimulationEvent(
                    event_type=EventType.HEARTBREAK_HEALED,
                    tick=current_tick,
                    source_human_id=human.uid,
                    location_id=getattr(human.physical_state, "current_location_id", None),
                    data={"heartbreak_id": hb.record_id, "reason": hb.reason},
                    importance=0.55,
                )
                event_bus.emit(evt)
                if causal_graph:
                    causal_graph.add_event(evt, description=f"{human.name} sanó emocionalmente tras desamor")
