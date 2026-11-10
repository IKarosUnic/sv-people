"""Historical Memory Engine for SALTBOR Phase 1.0.

Distinguishes between:
1. Ground Truth Historical Events (simulation reality).
2. Institutional Knowledge of events (archives, legal records).
3. Individual Memories (recalled with subjective bias/fidelity).
4. Transmitted Narratives (oral/written lore subject to mutation).
5. Cultural Interpretations (symbolic framing, heroization, stigma).
6. Incomplete / Incorrect Information (rumor, historical drift, uncertainty).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from saltbor.core.types import Tick


class HistoricalCategory(str, Enum):
    FOUNDATION = "foundation"
    MIGRATION = "migration"
    INSTITUTIONAL = "institutional"
    INNOVATION = "innovation"
    DISCOVERY = "discovery"
    CONFLICT = "conflict"
    AGREEMENT = "agreement"
    ECONOMIC_CRISIS = "economic_crisis"
    NATURAL_DISASTER = "natural_disaster"
    EPIDEMIC = "epidemic"
    CULTURAL_SHIFT = "cultural_shift"
    DEMOGRAPHIC_CHANGE = "demographic_change"
    INFRASTRUCTURE = "infrastructure"
    ORGANIZATION_CHANGE = "organization_change"


@dataclass
class HistoricalEvent:
    """Objective event that actually occurred in simulation ground truth."""

    event_id: str
    tick: Tick
    year: float
    category: HistoricalCategory
    location: str
    actors: List[str]
    title: str
    description: str
    causes: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.0  # 0.0 (certain) to 1.0 (unverifiable)
    significance: float = 0.5  # 0.0 to 1.0 historical importance
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstitutionalRecord:
    """Formal institutional registry of an event (e.g. municipal archive, legal statute)."""

    record_id: str
    institution_id: str
    event_id: str
    recorded_tick: Tick
    recorded_version: str
    formal_status: str = "archived"  # archived, ratified, contested, suppressed
    completeness: float = 0.9  # 0.0 to 1.0
    fidelity: float = 0.95  # accuracy to ground truth


@dataclass
class CulturalNarrative:
    """Interpreted, oral or symbolic lore passed between generations."""

    narrative_id: str
    event_id: str
    society_id: str
    framing: str  # e.g., heroic, tragic, cautionary, sacred, contested
    transmission_count: int = 0
    drift_factor: float = 0.0  # increases with generations / oral retellings
    key_themes: List[str] = field(default_factory=list)
    current_relevance: float = 0.7


class HistoricalMemoryEngine:
    """Manages ground-truth history, institutional archives, narratives, and collective memory."""

    def __init__(self) -> None:
        self.ground_truth: Dict[str, HistoricalEvent] = {}
        self.institutional_archives: Dict[str, List[InstitutionalRecord]] = {}  # institution_id -> records
        self.narratives: Dict[str, List[CulturalNarrative]] = {}  # society_id -> narratives
        self.event_by_location: Dict[str, List[str]] = {}
        self.event_by_actor: Dict[str, List[str]] = {}

    def record_ground_truth(
        self,
        category: HistoricalCategory,
        tick: Tick,
        year: float,
        location: str,
        actors: List[str],
        title: str,
        description: str,
        causes: Optional[List[str]] = None,
        consequences: Optional[List[str]] = None,
        significance: float = 0.5,
        uncertainty: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HistoricalEvent:
        event_id = f"hist_{uuid4().hex[:10]}"
        event = HistoricalEvent(
            event_id=event_id,
            tick=tick,
            year=year,
            category=category,
            location=location,
            actors=actors,
            title=title,
            description=description,
            causes=causes or [],
            consequences=consequences or [],
            uncertainty=max(0.0, min(1.0, uncertainty)),
            significance=max(0.0, min(1.0, significance)),
            metadata=metadata or {},
        )
        self.ground_truth[event_id] = event

        self.event_by_location.setdefault(location, []).append(event_id)
        for actor in actors:
            self.event_by_actor.setdefault(actor, []).append(event_id)

        return event

    def archive_institutionally(
        self,
        institution_id: str,
        event_id: str,
        tick: Tick,
        recorded_version: str,
        completeness: float = 0.85,
        fidelity: float = 0.95,
    ) -> InstitutionalRecord:
        record = InstitutionalRecord(
            record_id=f"rec_{uuid4().hex[:8]}",
            institution_id=institution_id,
            event_id=event_id,
            recorded_tick=tick,
            recorded_version=recorded_version,
            completeness=completeness,
            fidelity=fidelity,
        )
        self.institutional_archives.setdefault(institution_id, []).append(record)
        return record

    def form_cultural_narrative(
        self,
        society_id: str,
        event_id: str,
        framing: str = "heroic",
        themes: Optional[List[str]] = None,
    ) -> CulturalNarrative:
        narrative = CulturalNarrative(
            narrative_id=f"narr_{uuid4().hex[:8]}",
            event_id=event_id,
            society_id=society_id,
            framing=framing,
            transmission_count=1,
            drift_factor=0.05,
            key_themes=themes or ["resilience", "ancestral_heritage"],
        )
        self.narratives.setdefault(society_id, []).append(narrative)
        return narrative

    def transmit_narrative(
        self,
        narrative_id: str,
        fidelity_loss: Optional[float] = None,
        source_trust: Optional[float] = None,
        age_gap_years: Optional[float] = None,
        speaker_conscientiousness: Optional[float] = None,
    ) -> Optional[CulturalNarrative]:
        """Simulate generational retelling: increases transmission count and semantic drift.

        If contextual parameters are supplied, computes dynamic fidelity loss based
        on interpersonal trust, generation gap, and speaker conscientiousness.
        """
        if fidelity_loss is None:
            base_loss = 0.08
            trust = source_trust if source_trust is not None else 0.5
            consc = speaker_conscientiousness if speaker_conscientiousness is not None else 0.5
            gap = age_gap_years if age_gap_years is not None else 20.0
            dyn_loss = base_loss * (1.5 - trust) * (1.4 - 0.8 * consc) * (1.0 + min(1.0, gap / 50.0))
            fidelity_loss = max(0.01, min(0.35, dyn_loss))

        for narr_list in self.narratives.values():
            for narr in narr_list:
                if narr.narrative_id == narrative_id:
                    narr.transmission_count += 1
                    narr.drift_factor = min(1.0, narr.drift_factor + fidelity_loss)
                    narr.current_relevance = max(0.05, narr.current_relevance * 0.98)
                    return narr
        return None

    def query_collective_recollection(
        self,
        society_id: str,
        min_significance: float = 0.3,
        max_age_years: float = 100.0,
        current_year: float = 2026.0,
    ) -> List[Dict[str, Any]]:
        """Retrieve remembered history for a society: partial, filtered by significance and narrative survival."""
        recollections = []
        narrative_event_ids = {n.event_id for n in self.narratives.get(society_id, [])}

        for ev in self.ground_truth.values():
            age = max(0.0, current_year - ev.year)
            if age > max_age_years and ev.event_id not in narrative_event_ids:
                # Forgotten because of old age and lack of cultural narrative
                continue

            # Event is retained if significance is high, or maintained in narrative or archive
            has_narrative = ev.event_id in narrative_event_ids
            if ev.significance >= min_significance or has_narrative:
                drift = 0.0
                framing = "neutral"
                if has_narrative:
                    narr = next(n for n in self.narratives[society_id] if n.event_id == ev.event_id)
                    drift = narr.drift_factor
                    framing = narr.framing

                recollections.append({
                    "event_id": ev.event_id,
                    "title": ev.title,
                    "category": ev.category.value,
                    "perceived_year": ev.year if drift < 0.3 else round(ev.year + (drift * 5 - 2.5), 1),
                    "significance": ev.significance,
                    "framing": framing,
                    "drift_level": round(drift, 2),
                    "remembered_actors": ev.actors if drift < 0.5 else ev.actors[:1],
                })
        return recollections
