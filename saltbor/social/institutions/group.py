"""Enhanced social groups, collective structures, and organizational roles."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID


class GroupType(enum.Enum):
    FAMILY = "family"
    FRIEND_GROUP = "friend_group"
    WORK_TEAM = "work_team"
    GUILD = "guild"
    COOPERATIVE = "cooperative"
    COMMUNITY_ASSEMBLY = "community_assembly"


@dataclass
class EnhancedSocialGroup:
    """A persistent collective group with defined roles, objectives, and reputation."""

    group_id: str
    name: str
    group_type: GroupType
    purpose: str = "mutual support"
    members: set[HumanID] = field(default_factory=set)
    roles: dict[HumanID, str] = field(default_factory=dict) # member_uid -> role ('leader', 'member', 'elder', 'apprentice')
    shared_objectives: list[str] = field(default_factory=list)
    reputation: float = 0.5
    history: list[str] = field(default_factory=list)

    def add_member(self, uid: HumanID, role: str = "member") -> None:
        self.members.add(uid)
        self.roles[uid] = role
        self.history.append(f"Added member {uid} with role {role}")

    def remove_member(self, uid: HumanID) -> None:
        self.members.discard(uid)
        self.roles.pop(uid, None)
        self.history.append(f"Removed member {uid}")

    def get_role(self, uid: HumanID) -> Optional[str]:
        return self.roles.get(uid)

    def set_role(self, uid: HumanID, role: str) -> None:
        if uid in self.members:
            self.roles[uid] = role

    def get_leader(self) -> Optional[HumanID]:
        for uid, r in self.roles.items():
            if r in ("leader", "president", "head"):
                return uid
        return next(iter(self.members)) if self.members else None
