"""Inter-Civilization and Multi-Society Interaction Engine for SALTBOR Phase 1.0.

Provides regional, multi-society diplomacy, trade networks, migration, cultural diffusion, and alliance systems.
- Scalable territorial hierarchy: Region -> Country / Society -> Municipality / District -> Settlement -> Household -> Individual.
- Relational modalities: bilateral commerce, cultural assimilation/influence, formal diplomacy, alliances, friction/conflict, asymmetric dependency.
- Extensible beyond El Salvador to neighboring Mesoamerican / global societies without core engine alteration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from saltbor.core.types import Tick


class RelationType(str, Enum):
    ALLIANCE = "alliance"
    TRADE_PARTNER = "trade_partner"
    NEUTRAL = "neutral"
    ECONOMIC_DEPENDENCY = "economic_dependency"
    TENSION = "tension"
    ACTIVE_CONFLICT = "active_conflict"


@dataclass
class SocietyRelation:
    relation_id: str
    society_a: str
    society_b: str
    relation_type: RelationType = RelationType.NEUTRAL
    trust_level: float = 0.5  # 0.0 to 1.0
    trade_volume: float = 0.0
    cultural_diffusion_rate: float = 0.1
    established_tick: Tick = 0


class MultiSocietyInteractionEngine:
    """Orchestrates relationships, trade treaties, and diplomatic dynamics across independent societies."""

    def __init__(self) -> None:
        self.relations: Dict[str, SocietyRelation] = {}
        self.registered_societies: Set[str] = set()

    def register_society(self, society_id: str) -> None:
        self.registered_societies.add(society_id)

    def establish_relation(
        self,
        society_a: str,
        society_b: str,
        relation_type: RelationType = RelationType.NEUTRAL,
        trust: float = 0.5,
        tick: Tick = 0,
    ) -> SocietyRelation:
        rel_key = f"{min(society_a, society_b)}__{max(society_a, society_b)}"
        if rel_key in self.relations:
            rel = self.relations[rel_key]
            rel.relation_type = relation_type
            rel.trust_level = trust
            return rel

        rel = SocietyRelation(
            relation_id=f"srel_{uuid4().hex[:8]}",
            society_a=min(society_a, society_b),
            society_b=max(society_a, society_b),
            relation_type=relation_type,
            trust_level=trust,
            established_tick=tick,
        )
        self.relations[rel_key] = rel
        self.registered_societies.add(society_a)
        self.registered_societies.add(society_b)
        return rel

    def conduct_trade(self, society_a: str, society_b: str, value: float) -> Optional[SocietyRelation]:
        rel_key = f"{min(society_a, society_b)}__{max(society_a, society_b)}"
        if rel_key not in self.relations:
            self.establish_relation(society_a, society_b, RelationType.TRADE_PARTNER, trust=0.6)
        rel = self.relations[rel_key]
        rel.trade_volume += value
        rel.trust_level = min(1.0, rel.trust_level + 0.02)
        if rel.relation_type == RelationType.NEUTRAL and rel.trade_volume > 100.0:
            rel.relation_type = RelationType.TRADE_PARTNER
        return rel

    def trigger_conflict(self, society_a: str, society_b: str) -> Optional[SocietyRelation]:
        rel_key = f"{min(society_a, society_b)}__{max(society_a, society_b)}"
        if rel_key not in self.relations:
            self.establish_relation(society_a, society_b, RelationType.TENSION, trust=0.2)
        rel = self.relations[rel_key]
        rel.relation_type = RelationType.ACTIVE_CONFLICT
        rel.trust_level = max(0.0, rel.trust_level - 0.4)
        return rel
