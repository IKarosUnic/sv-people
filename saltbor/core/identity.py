"""Identity management for synthetic humans."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import DataSource, HumanID


@dataclass(frozen=True)
class HumanIdentity:
    """Immutable identity for a synthetic human.

    Once created, the identity never changes.  Everything else about the
    individual — personality, emotions, memories — is mutable, but identity
    is the anchor of continuity.
    """

    uid: HumanID = field(default_factory=uuid.uuid4)
    serial: int = 0  # sequential number for display/debugging
    given_name: str = ""
    family_name: str = ""
    nickname: Optional[str] = None
    data_source: DataSource = DataSource.MOCK_GENERATED

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}".strip()

    @property
    def display_name(self) -> str:
        return self.nickname or self.given_name or f"Human-{self.serial}"

    def __str__(self) -> str:
        return f"{self.display_name} (#{self.serial})"


class IdentityFactory:
    """Generates unique identities with sequential serial numbers."""

    def __init__(self, start_serial: int = 1) -> None:
        self._next_serial = start_serial

    def create(
        self,
        given_name: str = "",
        family_name: str = "",
        nickname: Optional[str] = None,
        data_source: DataSource = DataSource.MOCK_GENERATED,
        uid: Optional[HumanID] = None,
    ) -> HumanIdentity:
        identity = HumanIdentity(
            uid=uid or uuid.uuid4(),
            serial=self._next_serial,
            given_name=given_name,
            family_name=family_name,
            nickname=nickname,
            data_source=data_source,
        )
        self._next_serial += 1
        return identity

    @property
    def next_serial(self) -> int:
        return self._next_serial
