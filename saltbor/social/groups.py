"""Social groups — lightweight group management for Milestone 1."""

from __future__ import annotations

import logging
from typing import Iterator

from pydantic import BaseModel, Field

from saltbor.core.types import HumanID

logger = logging.getLogger(__name__)


class SocialGroup(BaseModel):
    """A named group of synthetic humans with a shared purpose."""

    group_id: str = Field(description="Unique identifier for the group.")
    name: str = Field(description="Human-readable group name.")
    members: set[HumanID] = Field(default_factory=set)
    purpose: str = Field(
        default="general",
        description="Short description of why this group exists.",
    )


class GroupRegistry:
    """Manages the collection of :class:`SocialGroup` instances."""

    def __init__(self) -> None:
        self._groups: dict[str, SocialGroup] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_group(
        self,
        group_id: str,
        name: str,
        purpose: str = "general",
    ) -> SocialGroup:
        """Create and register a new group."""
        if group_id in self._groups:
            raise ValueError(f"Group '{group_id}' already exists.")
        group = SocialGroup(group_id=group_id, name=name, purpose=purpose)
        self._groups[group_id] = group
        logger.info("Created group '%s' (%s)", name, group_id)
        return group

    def get(self, group_id: str) -> SocialGroup | None:
        """Return the group or ``None``."""
        return self._groups.get(group_id)

    def add_member(self, group_id: str, human_id: HumanID) -> None:
        """Add a human to a group (no-op if already a member)."""
        group = self._groups.get(group_id)
        if group is None:
            raise KeyError(f"Group '{group_id}' not found.")
        group.members.add(human_id)

    def remove_member(self, group_id: str, human_id: HumanID) -> None:
        """Remove a human from a group (no-op if not a member)."""
        group = self._groups.get(group_id)
        if group is None:
            raise KeyError(f"Group '{group_id}' not found.")
        group.members.discard(human_id)

    def groups_for(self, human_id: HumanID) -> list[SocialGroup]:
        """Return all groups that *human_id* belongs to."""
        return [g for g in self._groups.values() if human_id in g.members]

    def delete_group(self, group_id: str) -> None:
        """Remove a group entirely."""
        self._groups.pop(group_id, None)

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def get_all(self) -> list[SocialGroup]:
        return list(self._groups.values())

    @property
    def count(self) -> int:
        return len(self._groups)

    def __iter__(self) -> Iterator[SocialGroup]:
        return iter(self._groups.values())

    def __len__(self) -> int:
        return len(self._groups)
