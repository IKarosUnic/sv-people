"""Persistent genealogical graph tracking ancestry, descent, and kinship."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from saltbor.core.types import HumanID, Tick


@dataclass
class GenealogyRecord:
    """Genealogical pedigree node for an individual."""

    uid: HumanID
    parents: list[HumanID] = field(default_factory=list)
    children: list[HumanID] = field(default_factory=list)
    partner: Optional[HumanID] = None
    generation: int = 0
    birth_tick: Tick = 0
    death_tick: Optional[Tick] = None
    is_alive: bool = True

    def to_dict(self) -> dict:
        return {
            "uid": str(self.uid),
            "parents": [str(p) for p in self.parents],
            "children": [str(c) for c in self.children],
            "partner": str(self.partner) if self.partner else None,
            "generation": self.generation,
            "birth_tick": self.birth_tick,
            "death_tick": self.death_tick,
            "is_alive": self.is_alive,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GenealogyRecord:
        return cls(
            uid=UUID(data["uid"]),
            parents=[UUID(p) for p in data.get("parents", [])],
            children=[UUID(c) for c in data.get("children", [])],
            partner=UUID(data["partner"]) if data.get("partner") else None,
            generation=int(data.get("generation", 0)),
            birth_tick=int(data.get("birth_tick", 0)),
            death_tick=int(data["death_tick"]) if data.get("death_tick") is not None else None,
            is_alive=bool(data.get("is_alive", True)),
        )


class GenealogicalGraph:
    """Bi-directional graph maintaining full pedigree relationships across generations."""

    def __init__(self) -> None:
        self._records: dict[HumanID, GenealogyRecord] = {}

    def register_individual(
        self,
        uid: HumanID,
        parents: Optional[list[HumanID]] = None,
        birth_tick: Tick = 0,
        generation: Optional[int] = None,
    ) -> GenealogyRecord:
        """Register a new person in the genealogy graph."""
        if uid in self._records:
            rec = self._records[uid]
            if parents:
                parent_list = [p for p in parents if p in self._records and p not in rec.parents]
                rec.parents.extend(parent_list)
                for p in parent_list:
                    if uid not in self._records[p].children:
                        self._records[p].children.append(uid)
            return rec

        parent_list = [p for p in (parents or []) if p in self._records]
        if generation is None:
            if parent_list:
                gen = max(self._records[p].generation for p in parent_list) + 1
            else:
                gen = 0
        else:
            gen = generation

        rec = GenealogyRecord(
            uid=uid,
            parents=parent_list,
            generation=gen,
            birth_tick=birth_tick,
        )
        self._records[uid] = rec

        # Add child reference to parents
        for p in parent_list:
            if uid not in self._records[p].children:
                self._records[p].children.append(uid)

        return rec

    def record_birth(
        self,
        child_uid: HumanID,
        parent_a_uid: HumanID,
        parent_b_uid: Optional[HumanID] = None,
        tick: Tick = 0,
    ) -> GenealogyRecord:
        """Record the birth of a child and connect with parent records."""
        parents = [parent_a_uid]
        if parent_b_uid:
            parents.append(parent_b_uid)

        return self.register_individual(
            uid=child_uid,
            parents=parents,
            birth_tick=tick,
        )

    def record_partnership(self, a_uid: HumanID, b_uid: HumanID) -> None:
        """Record union or long-term partnership between two individuals."""
        if a_uid in self._records:
            self._records[a_uid].partner = b_uid
        if b_uid in self._records:
            self._records[b_uid].partner = a_uid

    def record_death(self, uid: HumanID, tick: Tick) -> None:
        """Record mortality event without deleting genealogical provenance."""
        if uid in self._records:
            self._records[uid].is_alive = False
            self._records[uid].death_tick = tick

    def get_record(self, uid: HumanID) -> Optional[GenealogyRecord]:
        return self._records.get(uid)

    def get_parents(self, uid: HumanID) -> list[HumanID]:
        rec = self._records.get(uid)
        return list(rec.parents) if rec else []

    def get_children(self, uid: HumanID) -> list[HumanID]:
        rec = self._records.get(uid)
        return list(rec.children) if rec else []

    def get_siblings(self, uid: HumanID) -> list[HumanID]:
        rec = self._records.get(uid)
        if not rec or not rec.parents:
            return []
        siblings: set[HumanID] = set()
        for p in rec.parents:
            parent_rec = self._records.get(p)
            if parent_rec:
                for c in parent_rec.children:
                    if c != uid:
                        siblings.add(c)
        return list(siblings)

    def get_grandparents(self, uid: HumanID) -> list[HumanID]:
        parents = self.get_parents(uid)
        grandparents: set[HumanID] = set()
        for p in parents:
            for gp in self.get_parents(p):
                grandparents.add(gp)
        return list(grandparents)

    def get_ancestors_with_depth(self, uid: HumanID, max_depth: int = 10) -> dict[HumanID, int]:
        """Collect all known ancestors with their minimal generational distance."""
        distances: dict[HumanID, int] = {uid: 0}
        queue = [(p, 1) for p in self.get_parents(uid)]
        while queue:
            curr, depth = queue.pop(0)
            if curr not in distances or depth < distances[curr]:
                distances[curr] = depth
                if depth < max_depth:
                    for p in self.get_parents(curr):
                        queue.append((p, depth + 1))
        return distances

    def get_ancestors(self, uid: HumanID, max_depth: int = 10) -> set[HumanID]:
        """Collect all known ancestors transitively up to max_depth."""
        ancestors: set[HumanID] = set()
        queue = [(p, 1) for p in self.get_parents(uid)]
        while queue:
            curr, depth = queue.pop(0)
            if curr not in ancestors and depth <= max_depth:
                ancestors.add(curr)
                for p in self.get_parents(curr):
                    queue.append((p, depth + 1))
        return ancestors

    def get_descendants(self, uid: HumanID, max_depth: int = 10) -> set[HumanID]:
        """Collect all descendants transitively up to max_depth."""
        descendants: set[HumanID] = set()
        queue = [(c, 1) for c in self.get_children(uid)]
        while queue:
            curr, depth = queue.pop(0)
            if curr not in descendants and depth <= max_depth:
                descendants.add(curr)
                for c in self.get_children(curr):
                    queue.append((c, depth + 1))
        return descendants

    def get_kinship_degree(self, a_uid: HumanID, b_uid: HumanID) -> Optional[int]:
        """Calculate degree of consanguinity. 1=Parent/Child, 2=Sibling/Grandparent, 3=Aunt/Uncle, 4=Cousins, etc."""
        if a_uid == b_uid:
            return 0
        dist_a = self.get_ancestors_with_depth(a_uid, max_depth=5)
        dist_b = self.get_ancestors_with_depth(b_uid, max_depth=5)
        common = set(dist_a.keys()).intersection(dist_b.keys())
        if not common:
            return None
        min_degree = min(dist_a[anc] + dist_b[anc] for anc in common)
        return min_degree if min_degree > 0 else None

    def is_related(self, a_uid: HumanID, b_uid: HumanID) -> bool:
        return self.get_kinship_degree(a_uid, b_uid) is not None

    def all_records(self) -> list[GenealogyRecord]:
        return list(self._records.values())
