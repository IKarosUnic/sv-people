"""Associative, contextual memory retrieval and imperfect reconstruction.

This extends the existing :class:`EpisodicMemory` instead of replacing it.  The
original record stays immutable in provenance terms; what changes is:

* **which** records are recalled (selective, cue-indexed, not a full scan),
* **how** they are reconstructed at recall time (fidelity, mood congruence,
  detail loss, reinterpretation),
* how the recall affects accessibility (rehearsal strengthens, neglect fades).

Scoring follows the spirit of the Stanford Generative Agents formula
(recency × importance × relevance) but adds emotional intensity, relationship,
place, repetition, confidence and association, and the weights are explicit so
an experiment can change them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.psychology.models import PsychologicalState, _clamp


@dataclass(frozen=True)
class RetrievalWeights:
    recency: float = 0.24
    importance: float = 0.24
    relevance: float = 0.26
    emotional_intensity: float = 0.12
    accessibility: float = 0.08
    association: float = 0.06


@dataclass
class RetrievalQuery:
    text: Optional[str] = None
    associated_human: Optional[str] = None
    location_id: Optional[str] = None
    tags: tuple[str, ...] = ()
    emotion: Optional[str] = None
    limit: int = 5
    min_score: float = 0.0


@dataclass
class MemoryReconstruction:
    memory_id: str
    original_summary: str
    reconstructed_summary: str
    fidelity: float
    confidence: float
    age_days: float
    distortions: list[str] = field(default_factory=list)
    source_event_id: Optional[str] = None
    accessibility: float = 0.0
    contradictory_with: list[str] = field(default_factory=list)


@dataclass
class _MemoryIndex:
    by_human: dict[str, set[str]] = field(default_factory=dict)
    by_location: dict[str, set[str]] = field(default_factory=dict)
    by_tag: dict[str, set[str]] = field(default_factory=dict)
    recent: list[str] = field(default_factory=list)
    salient: list[str] = field(default_factory=list)
    built_count: int = 0


class AssociativeRetrieval:
    """Cue-indexed recall with bounded scans per individual."""

    def __init__(self, weights: Optional[RetrievalWeights] = None) -> None:
        self.weights = weights or RetrievalWeights()
        self._indexes: dict[str, _MemoryIndex] = {}
        self.stats = {"queries": 0, "candidates_examined": 0, "reconstructions": 0}

    # ------------------------------------------------------------------
    # Index
    # ------------------------------------------------------------------

    def _index_for(self, uid: str, records: list[EpisodicRecord]) -> _MemoryIndex:
        idx = self._indexes.get(uid)
        if idx is not None and idx.built_count == len(records):
            return idx
        idx = _MemoryIndex(built_count=len(records))
        for rec in records:
            rid = str(rec.memory_id)
            for human in rec.associated_humans:
                idx.by_human.setdefault(str(human), set()).add(rid)
            if rec.location_id:
                idx.by_location.setdefault(str(rec.location_id), set()).add(rid)
            for tag in rec.context_tags:
                idx.by_tag.setdefault(str(tag).lower(), set()).add(rid)
        ordered = sorted(records, key=lambda r: r.tick, reverse=True)
        idx.recent = [str(r.memory_id) for r in ordered[:32]]
        idx.salient = [
            str(r.memory_id)
            for r in sorted(records, key=lambda r: r.importance, reverse=True)[:24]
        ]
        self._indexes[uid] = idx
        return idx

    def invalidate(self, uid: Optional[str] = None) -> None:
        if uid is None:
            self._indexes.clear()
        else:
            self._indexes.pop(uid, None)

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------

    def retrieve(
        self,
        *,
        uid: str,
        records: list[EpisodicRecord],
        tick: int,
        query: RetrievalQuery,
        psych: Optional[PsychologicalState] = None,
        text_terms: Optional[set[str]] = None,
    ) -> list[EpisodicRecord]:
        """Select a bounded candidate set, score it and return the top records.

        The index narrows the scan to records associated with the cue; when no
        cue exists only recent and salient records are considered.  This is the
        requirement "do not consult the whole memory every tick".
        """
        if not records:
            return []
        idx = self._index_for(uid, records)
        candidates: set[str] = set()

        if query.associated_human:
            candidates |= idx.by_human.get(str(query.associated_human), set())
        if query.location_id:
            candidates |= idx.by_location.get(str(query.location_id), set())
        for tag in query.tags:
            candidates |= idx.by_tag.get(str(tag).lower(), set())
        if query.emotion:
            candidates |= idx.by_tag.get(f"emotion:{query.emotion}".lower(), set())

        if not candidates:
            candidates = set(idx.recent) | set(idx.salient)

        self.stats["queries"] += 1
        self.stats["candidates_examined"] += len(candidates)

        by_id = {str(r.memory_id): r for r in records}
        scored: list[tuple[float, EpisodicRecord]] = []
        terms = text_terms or self._terms(query.text)
        for rid in candidates:
            rec = by_id.get(rid)
            if rec is None:
                continue
            score = self._score(rec, tick, query, terms, psych)
            if score >= query.min_score:
                scored.append((score, rec))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = [pair[1] for pair in scored[: max(1, query.limit)]]
        for rec in top:
            rec.touch(tick, reinforcement=0.12)
            rec.last_accessed = tick
        return top

    def _score(
        self,
        rec: EpisodicRecord,
        tick: int,
        query: RetrievalQuery,
        terms: set[str],
        psych: Optional[PsychologicalState],
    ) -> float:
        age_days = max(0.0, (tick - rec.tick) / 96.0)
        importance = _clamp(rec.importance)
        intensity = _clamp(abs(rec.emotional_valence) * 0.7 + max(rec.emotional_associations.values(), default=0.0) * 0.5)

        # Important and emotionally charged memories decay more slowly.
        half_life = 2.5 + 9.0 * importance + 6.0 * intensity
        recency = math.exp(-age_days / max(0.5, half_life))

        relevance = 0.0
        if query.associated_human:
            relevance += 0.45 if str(query.associated_human) in {str(h) for h in rec.associated_humans} else 0.0
        if query.location_id and str(query.location_id) == str(rec.location_id):
            relevance += 0.25
        if terms:
            words = set(rec.summary.lower().split()) | {str(t).lower() for t in rec.context_tags}
            overlap = len(terms & words)
            relevance += min(0.30, overlap * 0.09)
        if query.tags:
            tag_set = {str(t).lower() for t in rec.context_tags}
            relevance += min(0.20, 0.08 * len(tag_set & {t.lower() for t in query.tags}))
        if query.emotion:
            relevance += 0.20 if str(rec.emotional_associations.get(query.emotion, 0.0)) not in ("0.0", "0") else 0.0
        relevance = _clamp(relevance)

        # Mood-congruent recall: current affect raises the accessibility of
        # memories with the same sign.  This is small and bounded.
        mood = 0.0
        if psych is not None:
            mood = 0.30 * psych.sadness - 0.20 * psych.hope + 0.18 * psych.anger
        congruence = 0.0
        if mood != 0.0:
            congruence = _clamp(0.12 * (1.0 if (mood > 0) == (rec.emotional_valence > 0) else -1.0))

        association = _clamp(math.log1p(rec.access_count) / 4.0)
        w = self.weights
        return (
            w.recency * recency
            + w.importance * importance
            + w.relevance * (relevance + congruence)
            + w.emotional_intensity * intensity
            + w.accessibility * _clamp(rec.accessibility)
            + w.association * association
        )

    @staticmethod
    def _terms(text: Optional[str]) -> set[str]:
        if not text:
            return set()
        return {t for t in text.lower().replace(",", " ").replace(".", " ").split() if len(t) > 2}

    # ------------------------------------------------------------------
    # Reconstruction
    # ------------------------------------------------------------------

    def reconstruct(
        self,
        rec: EpisodicRecord,
        *,
        tick: int,
        psych: Optional[PsychologicalState] = None,
        contradiction_ids: Optional[list[str]] = None,
    ) -> MemoryReconstruction:
        """Return an imperfect, current-state-dependent reconstruction.

        The original event is not modified.  This is the individual's memory of
        it, and the provenance fields keep the two separable.
        """
        age_days = max(0.0, (tick - rec.tick) / 96.0)
        importance = _clamp(rec.importance)
        accessibility = _clamp(rec.accessibility)
        fidelity = _clamp(
            math.exp(-age_days / max(3.0, 20.0 + 70.0 * importance))
            * (0.55 + 0.45 * accessibility)
            * (0.85 + 0.15 * importance)
        )
        distortions: list[str] = []

        if fidelity < 0.35:
            distortions.append("detalles perdidos")
        if fidelity < 0.20:
            distortions.append("recuerdo esquemático")
        if rec.access_count == 0 and age_days > 7:
            distortions.append("nunca evocado desde entonces")

        mood_shift = 0.0
        if psych is not None:
            mood_shift = 0.20 * psych.sadness - 0.14 * psych.hope
            if psych.chronic_stress > 0.55 and rec.emotional_valence < 0:
                distortions.append("sesgo de amenaza por estrés crónico")
                mood_shift -= 0.06
            if psych.hope > 0.70 and rec.emotional_valence > 0:
                distortions.append("recuerdo idealizado")
                mood_shift += 0.05

        reinterpreted_valence = _clamp(
            rec.emotional_valence + mood_shift * (1.0 - fidelity), -1.0, 1.0
        )
        if abs(reinterpreted_valence - rec.emotional_valence) > 0.10:
            distortions.append("reinterpretación afectiva")

        confidence = _clamp(fidelity * (0.55 + 0.45 * accessibility) * (0.9 if importance > 0.6 else 0.75))
        summary = rec.summary
        if fidelity < 0.55:
            summary = self._soften(summary)
        if fidelity < 0.30:
            summary = f"Recuerdo difuso: {summary[:90]}"
        if abs(mood_shift) > 0.05 and psych is not None:
            if mood_shift > 0:
                summary += " [recordado con más calidez que en su momento]"
            else:
                summary += " [recordado con más dureza que en su momento]"

        self.stats["reconstructions"] += 1
        return MemoryReconstruction(
            memory_id=str(rec.memory_id),
            original_summary=rec.summary,
            reconstructed_summary=summary,
            fidelity=round(fidelity, 4),
            confidence=round(confidence, 4),
            age_days=round(age_days, 2),
            distortions=distortions,
            source_event_id=None,
            accessibility=round(accessibility, 4),
            contradictory_with=list(contradiction_ids or []),
        )

    @staticmethod
    def _soften(summary: str) -> str:
        """Drop specific details without inventing new ones.

        The simulation does not fabricate a false fact; it loses precision and
        marks that loss, which keeps provenance honest.
        """
        parts = [p.strip() for p in summary.replace(";", ",").split(",") if p.strip()]
        if len(parts) <= 1:
            return summary
        kept = parts[: max(1, len(parts) // 2)]
        return ", ".join(kept) + " (detalles imprecisos)"

    # ------------------------------------------------------------------
    # Contradiction and forgetting
    # ------------------------------------------------------------------

    @staticmethod
    def find_contradictions(records: list[EpisodicRecord], limit: int = 400) -> list[tuple[str, str]]:
        """Return pairs of memories about the same people with opposite valence.

        Human memory is allowed to be inconsistent; the simulation should be
        able to represent that without asserting which version is true.
        """
        pairs: list[tuple[str, str]] = []
        seen: dict[tuple[str, ...], EpisodicRecord] = {}
        for rec in records[:limit]:
            key = tuple(sorted(str(h) for h in rec.associated_humans))
            if not key:
                continue
            previous = seen.get(key)
            if previous is not None and previous.emotional_valence * rec.emotional_valence < -0.10:
                pairs.append((str(previous.memory_id), str(rec.memory_id)))
            else:
                seen[key] = rec
        return pairs

    def forgetting_pass(
        self,
        records: list[EpisodicRecord],
        tick: int,
        *,
        archive_callback: Any = None,
        dormancy_threshold: float = 0.055,
    ) -> list[str]:
        """Fade unrehearsed memories; archive rather than delete.

        ``archive_callback`` is the existing ``EpisodicMemory.remove`` path, so
        the historical record survives in the archive (the prior phases already
        guarantee no silent data destruction).
        """
        forgotten: list[str] = []
        for rec in records:
            age_days = max(0.0, (tick - rec.tick) / 96.0)
            if rec.access_count == 0 and age_days > 2.0:
                rec.accessibility = _clamp(
                    rec.accessibility * math.exp(-0.030 * age_days * (1.35 - rec.importance))
                )
            elif rec.access_count > 0:
                rec.accessibility = _clamp(rec.accessibility + 0.002)
            if rec.accessibility < dormancy_threshold and not rec.is_dormant:
                rec.is_dormant = True
                forgotten.append(str(rec.memory_id))
                if archive_callback is not None:
                    try:
                        archive_callback(rec.memory_id)
                    except Exception:
                        pass
        return forgotten
