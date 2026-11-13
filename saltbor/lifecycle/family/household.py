"""Household structures, cohabitation, caregiving responsibilities, and succession."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from saltbor.core.types import HumanID, LocationID
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph


@dataclass
class Household:
    """A cohabiting family or living unit sharing domestic space and resources."""

    household_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Household"
    residence_location_id: LocationID = "casa_residencial_1"
    members: set[HumanID] = field(default_factory=set)
    head_of_household: Optional[HumanID] = None
    dependents: set[HumanID] = field(default_factory=set)  # Children / infants requiring care
    caregiver_assignments: dict[HumanID, HumanID] = field(default_factory=dict) # dependent -> caregiver
    shared_funds: float = 0.0

    def add_member(
        self,
        uid: HumanID,
        is_head: bool = False,
        is_dependent: bool = False,
    ) -> None:
        """Add an individual to this household."""
        self.members.add(uid)
        if is_head or self.head_of_household is None:
            self.head_of_household = uid
        if is_dependent:
            self.dependents.add(uid)
            # Assign head or any non-dependent adult as default caregiver
            potential_caregivers = [m for m in self.members if m not in self.dependents]
            if potential_caregivers:
                self.caregiver_assignments[uid] = potential_caregivers[0]

    def remove_member(self, uid: HumanID) -> None:
        """Remove a member (due to departure, marriage, or death)."""
        self.members.discard(uid)
        self.dependents.discard(uid)
        self.caregiver_assignments.pop(uid, None)

        # Remove as caregiver for others and reassign
        orphaned = [dep for dep, cg in self.caregiver_assignments.items() if cg == uid]
        remaining_adults = [m for m in self.members if m not in self.dependents]
        for dep in orphaned:
            if remaining_adults:
                self.caregiver_assignments[dep] = remaining_adults[0]
            else:
                self.caregiver_assignments.pop(dep, None)

        if self.head_of_household == uid:
            self.head_of_household = remaining_adults[0] if remaining_adults else (next(iter(self.members)) if self.members else None)

    def assign_caregiver(self, dependent_uid: HumanID, caregiver_uid: HumanID) -> None:
        """Explicitly assign a primary caregiver for an infant or young child."""
        if dependent_uid in self.members and caregiver_uid in self.members:
            self.dependents.add(dependent_uid)
            self.caregiver_assignments[dependent_uid] = caregiver_uid

    def get_caregiver_for(self, dependent_uid: HumanID) -> Optional[HumanID]:
        return self.caregiver_assignments.get(dependent_uid)

    def process_succession_and_inheritance(
        self,
        deceased_uid: HumanID,
        personal_funds: float,
        genealogy: GenealogicalGraph,
    ) -> dict[HumanID, float]:
        """Distribute deceased member's assets and elect new head if necessary.

        Inheritance rule:
        1. Surviving spouse/partner in household receives 50% of personal funds.
        2. Surviving children receive remaining 50% split equally.
        3. If no partner/children in household, split equally among surviving household members.
        4. If household empty, funds default to community estate.
        """
        self.remove_member(deceased_uid)
        distribution: dict[HumanID, float] = {}
        if personal_funds <= 0.0 or not self.members:
            return distribution

        # Check partner
        rec = genealogy.get_record(deceased_uid)
        partner = rec.partner if rec else None
        partner_in_house = partner if (partner and partner in self.members) else None

        children = genealogy.get_children(deceased_uid) if rec else []
        children_in_house = [c for c in children if c in self.members]

        if partner_in_house and children_in_house:
            partner_share = personal_funds * 0.5
            child_pool = personal_funds * 0.5
            distribution[partner_in_house] = round(partner_share, 2)
            per_child = child_pool / len(children_in_house)
            for c in children_in_house:
                distribution[c] = round(per_child, 2)
        elif partner_in_house:
            distribution[partner_in_house] = round(personal_funds, 2)
        elif children_in_house:
            per_child = personal_funds / len(children_in_house)
            for c in children_in_house:
                distribution[c] = round(per_child, 2)
        else:
            # Fallback to remaining household members
            per_member = personal_funds / len(self.members)
            for m in self.members:
                distribution[m] = round(per_member, 2)

        return distribution


class HouseholdRegistry:
    """Manages all households across the settlement."""

    def __init__(self) -> None:
        self._households: dict[str, Household] = {}
        self._human_to_household: dict[HumanID, str] = {}

    def register_household(self, household: Household) -> None:
        self._households[household.household_id] = household
        for m in household.members:
            self._human_to_household[m] = household.household_id

    def create_household(
        self,
        name: str,
        residence_location_id: LocationID,
        members: Optional[list[HumanID]] = None,
        head: Optional[HumanID] = None,
    ) -> Household:
        h = Household(
            name=name,
            residence_location_id=residence_location_id,
        )
        if members:
            for idx, m in enumerate(members):
                is_head = (m == head) if head else (idx == 0)
                h.add_member(m, is_head=is_head)
        self.register_household(h)
        return h

    def get(self, household_id: str) -> Optional[Household]:
        return self._households.get(household_id)

    def get_for_human(self, uid: HumanID) -> Optional[Household]:
        hid = self._human_to_household.get(uid)
        return self._households.get(hid) if hid else None

    def add_human_to_household(self, household_id: str, uid: HumanID, is_dependent: bool = False) -> None:
        h = self._households.get(household_id)
        if h:
            h.add_member(uid, is_dependent=is_dependent)
            self._human_to_household[uid] = household_id

    def remove_human(self, uid: HumanID) -> None:
        hid = self._human_to_household.pop(uid, None)
        if hid and hid in self._households:
            self._households[hid].remove_member(uid)
            if not self._households[hid].members:
                # Remove empty household
                self._households.pop(hid, None)

    def move_human(self, uid: HumanID, household_id: str) -> None:
        """Move an individual between households (cohabitation, displacement)."""
        target = self._households.get(household_id)
        if target is None:
            return
        old_id = self._human_to_household.get(uid)
        if old_id and old_id in self._households and old_id != household_id:
            self._households[old_id].remove_member(uid)
            if not self._households[old_id].members:
                self._households.pop(old_id, None)
        target.add_member(uid)
        self._human_to_household[uid] = household_id

    def all_households(self) -> list[Household]:
        return list(self._households.values())
