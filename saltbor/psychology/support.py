"""Social support: available, perceived, requested and refused.

Support is not a global buffer.  It is a set of asymmetric relationships that
cost the provider time, energy and money, can be refused, and can accumulate
stigma for the requester.  The engine therefore distinguishes:

* **available support** — what the network could plausibly provide,
* **perceived support** — what the individual expects, filtered by personality
  and history,
* **realised support** — what was actually given after a request.

Kinship and intimacy are read from the existing genealogy and social engines;
nothing is duplicated here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from saltbor.core.types import RelationshipType, Tick
from saltbor.psychology.models import PsychologicalState, _clamp


@dataclass
class SupportAssessment:
    network_size: int = 0
    intimate_ties: int = 0
    family_ties: int = 0
    friend_ties: int = 0
    partner_tie: float = 0.0
    objective_support: float = 0.0
    perceived_support: float = 0.0
    reciprocity_balance: float = 0.0
    isolation: float = 1.0
    burden: float = 0.0
    closest: list[tuple[str, float]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "network_size": self.network_size,
            "intimate_ties": self.intimate_ties,
            "family_ties": self.family_ties,
            "friend_ties": self.friend_ties,
            "partner_tie": round(self.partner_tie, 3),
            "objective_support": round(self.objective_support, 3),
            "perceived_support": round(self.perceived_support, 3),
            "reciprocity_balance": round(self.reciprocity_balance, 3),
            "isolation": round(self.isolation, 3),
            "burden": round(self.burden, 3),
            "closest": [(uid, round(score, 3)) for uid, score in self.closest[:6]],
        }


@dataclass
class SupportOutcome:
    granted: bool
    provider_uid: Optional[str] = None
    amount_usd: float = 0.0
    energy_relief: float = 0.0
    emotional_relief: float = 0.0
    reason: str = ""
    stigma_increase: float = 0.0
    provider_cost: float = 0.0


@dataclass
class _SupportRequestRecord:
    requester: str
    provider: str
    tick: int
    granted: bool


class SupportEngine:
    """Assesses and executes social support transactions."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._request_log: list[_SupportRequestRecord] = []
        self._stigma: dict[tuple[str, str], float] = {}

    # ------------------------------------------------------------------
    # Assessment
    # ------------------------------------------------------------------

    def assess(
        self,
        human: Any,
        social: Any,
        genealogy: Any = None,
        population: Any = None,
    ) -> SupportAssessment:
        uid = human.uid
        psych = getattr(human, "psychology", None)
        assessment = SupportAssessment()

        family_ids: set[str] = set()
        if genealogy is not None:
            for getter in ("get_parents", "get_children", "get_siblings"):
                try:
                    family_ids.update(str(x) for x in getattr(genealogy, getter)(uid))
                except Exception:
                    continue
        partner = getattr(human, "romantic_partner_id", None)
        if partner:
            family_ids.add(str(partner))

        relationships = []
        if social is not None:
            try:
                relationships = social.get_relationships_for(uid)
            except Exception:
                relationships = []

        family_ties = 0
        friend_ties = 0
        intimate = 0
        closeness_sum = 0.0
        partner_tie = 0.0
        closest: list[tuple[str, float]] = []
        reciprocity_total = 0.0
        weighed = 0.0
        burden = 0.0

        for rel in relationships:
            try:
                other = str(rel.other_id(uid))
            except Exception:
                continue
            trust = float(getattr(rel, "trust", 0.0))
            affinity = float(getattr(rel, "affinity", 0.0))
            familiarity = float(getattr(rel, "familiarity", 0.0))
            closeness = _clamp(0.65 * trust + 0.35 * affinity)
            closeness_sum += closeness
            weighed += 1.0
            closest.append((other, closeness))

            is_family = other in family_ids
            if is_family:
                family_ties += 1
            if rel.relationship_type in (RelationshipType.FRIEND, RelationshipType.CLOSE_FRIEND):
                friend_ties += 1
            if partner and other == str(partner):
                partner_tie = closeness
            if closeness >= 0.62 and familiarity >= 0.25:
                intimate += 1
            reciprocity_total += float(getattr(rel, "respect", 0.5)) - 0.5
            burden += max(0.0, familiarity - closeness) * 0.25

        network_size = len(relationships)
        mean_closeness = (closeness_sum / weighed) if weighed else 0.0
        objective = _clamp(
            0.22 * min(1.0, network_size / 12.0)
            + 0.28 * min(1.0, intimate / 3.0)
            + 0.18 * min(1.0, family_ties / 4.0)
            + 0.22 * mean_closeness
            + 0.10 * partner_tie
        )

        # Perceived support is not objective support: neuroticism and prior
        # refusals lower it; agreeableness and secure ties raise it.
        if psych is not None:
            perceived = _clamp(
                objective
                * (0.55 + 0.45 * psych.trust)
                * (1.0 + 0.30 * psych.social_sensitivity - 0.22 * psych.loneliness)
                - 0.05 * psych.support_refusals
            )
        else:
            perceived = objective

        assessment.network_size = network_size
        assessment.intimate_ties = intimate
        assessment.family_ties = family_ties
        assessment.friend_ties = friend_ties
        assessment.partner_tie = partner_tie
        assessment.objective_support = round(objective, 4)
        assessment.perceived_support = round(perceived, 4)
        assessment.reciprocity_balance = round(
            (reciprocity_total / weighed) if weighed else 0.0, 4
        )
        assessment.isolation = round(_clamp(1.0 - objective), 4)
        assessment.burden = round(_clamp(burden / max(1.0, weighed)), 4)
        assessment.closest = sorted(closest, key=lambda pair: pair[1], reverse=True)
        return assessment

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def request_support(
        self,
        requester: Any,
        psych: PsychologicalState,
        *,
        need: str,
        amount_usd: float = 0.0,
        tick: Tick = 0,
        social: Any = None,
        population: Any = None,
        genealogy: Any = None,
        assessment: Optional[SupportAssessment] = None,
    ) -> SupportOutcome:
        """Ask the closest plausible tie for help.

        The provider may refuse.  Refusal is informative: it lowers trust,
        raises loneliness and makes a repeated request less likely to succeed.
        """
        if social is None:
            # Asking with no one to ask is itself a costly social experience.
            psych.support_refusals += 1
            psych.support_requests += 1
            psych.loneliness = _clamp(psych.loneliness + 0.05)
            return SupportOutcome(False, reason="sin red social registrada")

        assessment = assessment or self.assess(requester, social, genealogy, population)
        if not assessment.closest:
            psych.support_refusals += 1
            psych.loneliness = _clamp(psych.loneliness + 0.05)
            return SupportOutcome(False, reason="sin vínculos íntimos disponibles")

        requester_uid = str(getattr(requester, "uid", ""))
        provider_uid, closeness = assessment.closest[0]
        provider = None
        if population is not None:
            try:
                provider = population.get_optional(_as_uuid(provider_uid))
            except Exception:
                provider = None

        if provider is None:
            return SupportOutcome(False, reason="vínculo no disponible en la población activa")

        rel = social.get_relationship(requester.uid, provider.uid)
        stigma = self._stigma.get((requester_uid, provider_uid), 0.0)
        provider_psych = getattr(provider, "psychology", None)
        provider_load = provider_psych.chronic_stress if provider_psych is not None else 0.4
        provider_money = float(getattr(provider.physical_state, "money", 0.0))
        provider_agree = provider.personality.effective_value("agreeableness")
        requester_persistence = requester.personality.effective_value("persistence")

        probability = _clamp(
            0.18
            + 0.42 * closeness
            + 0.16 * provider_agree
            + 0.10 * requester_persistence
            + 0.12 * float(getattr(rel, "respect", 0.5))
            - 0.28 * provider_load
            - 0.45 * stigma
            - (0.10 if need == "financial" else 0.0)
        )

        # Financial support has a hard feasibility check; emotional support
        # only costs time and attention.
        if need == "financial":
            feasible = provider_money >= max(3.0, amount_usd * 0.6)
            probability *= 1.0 if feasible else 0.15
            amount = min(amount_usd, max(0.0, provider_money * 0.25))
        else:
            amount = 0.0
            feasible = True

        granted = bool(self._rng.random() < probability)
        self._request_log.append(
            _SupportRequestRecord(requester_uid, provider_uid, int(tick), granted)
        )
        if len(self._request_log) > 500:
            self._request_log = self._request_log[-500:]

        if granted:
            self._stigma[(requester_uid, provider_uid)] = max(0.0, stigma - 0.10)
            return self._execute_grant(
                requester,
                provider,
                psych,
                rel,
                need,
                amount,
                closeness,
                tick,
                social,
            )

        # Refusal
        psych.support_refusals += 1
        psych.support_requests += 1
        psych.loneliness = _clamp(psych.loneliness + 0.055)
        psych.trust = _clamp(psych.trust - 0.04)
        psych.hope = _clamp(psych.hope - 0.025)
        psych.anger = _clamp(psych.anger + 0.02 * (1.0 - requester.personality.effective_value("agreeableness")))
        self._stigma[(requester_uid, provider_uid)] = min(1.0, stigma + 0.18)
        try:
            social.record_interaction(
                requester.uid,
                provider.uid,
                tick,
                positive=False,
                intensity=0.15,
                interaction_type="support_refused",
            )
        except Exception:
            pass
        return SupportOutcome(
            False,
            provider_uid,
            reason=f"{provider.name} no pudo o no quiso ayudar ({need})",
            stigma_increase=0.18,
        )

    def _execute_grant(
        self,
        requester: Any,
        provider: Any,
        psych: PsychologicalState,
        rel: Any,
        need: str,
        amount: float,
        closeness: float,
        tick: Tick,
        social: Any,
    ) -> SupportOutcome:
        provider_money = float(getattr(provider.physical_state, "money", 0.0))
        provider_energy = float(getattr(provider.physical_state, "energy", 1.0))
        provider_psych = getattr(provider, "psychology", None)

        if need == "financial":
            amount = round(min(amount, provider_money * 0.25), 2)
            provider.physical_state.money = max(0.0, provider_money - amount)
            requester.physical_state.money = float(getattr(requester.physical_state, "money", 0.0)) + amount
            psych.material_buffer = _clamp(psych.material_buffer + amount / 240.0)
            relief = 0.24 + min(0.18, amount / 60.0)
            energy_relief = 0.0
        else:
            mental = max(0.0, 0.06 + 0.10 * closeness)
            provider_psych = provider_psych
            if provider_psych is not None:
                provider_psych.chronic_stress = _clamp(provider_psych.chronic_stress + mental * 0.35)
                provider_psych.mental_fatigue = _clamp(provider_psych.mental_fatigue + mental * 0.30)
                provider_psych.self_control = _clamp(provider_psych.self_control - mental * 0.15)
                provider_psych.support_given += 1
            relief = 0.22 + 0.20 * closeness
            energy_relief = 0.05 * closeness
            amount = 0.0

        provider.physical_state.energy = max(0.0, provider_energy - (0.02 + 0.03 * closeness))

        psych.support_requests += 1
        psych.perceived_support = _clamp(psych.perceived_support + 0.06)
        psych.trust = _clamp(psych.trust + 0.035)
        psych.loneliness = _clamp(psych.loneliness - 0.08)
        psych.hope = _clamp(psych.hope + 0.035)
        psych.relieve(relief * 0.55)
        psych.support_received += 1

        try:
            social.record_interaction(
                requester.uid,
                provider.uid,
                tick,
                positive=True,
                intensity=0.30,
                interaction_type="support_given",
            )
        except Exception:
            pass

        return SupportOutcome(
            True,
            str(provider.uid),
            amount_usd=amount,
            energy_relief=energy_relief,
            emotional_relief=relief,
            reason=f"{provider.name} brindó apoyo {need}",
            provider_cost=amount + 0.05,
        )

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def recent_requests(self, limit: int = 20) -> list[dict[str, Any]]:
        return [
            {
                "requester": r.requester,
                "provider": r.provider,
                "tick": r.tick,
                "granted": r.granted,
            }
            for r in self._request_log[-limit:]
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests": [
                {
                    "requester": r.requester,
                    "provider": r.provider,
                    "tick": r.tick,
                    "granted": r.granted,
                }
                for r in self._request_log[-200:]
            ],
            "stigma": {f"{a}|{b}": round(v, 3) for (a, b), v in list(self._stigma.items())[-500:]},
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self._request_log = [
            _SupportRequestRecord(
                str(r.get("requester", "")),
                str(r.get("provider", "")),
                int(r.get("tick", 0)),
                bool(r.get("granted", False)),
            )
            for r in data.get("requests", [])
        ]
        self._stigma = {}
        for key, value in dict(data.get("stigma", {})).items():
            parts = key.split("|", 1)
            if len(parts) == 2:
                self._stigma[(parts[0], parts[1])] = float(value)


def _as_uuid(value: str):
    import uuid

    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return value
