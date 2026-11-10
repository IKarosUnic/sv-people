"""Public civic offices: elected or appointed magistrates, sheriffs, and town treasurers."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import HumanID, Tick


class PublicOfficeType(enum.Enum):
    """Elected or appointed civic magistrates and public officers."""

    MAGISTRATE_JUDGE = "magistrate_judge"       # Presides over trials, delivers binding verdicts
    SHERIFF_ALGUACIL = "sheriff_alguacil"       # Enforces court orders, serves notices, maintains order
    TOWN_TREASURER = "town_treasurer"           # Audits municipal funds, collects court fines & dues
    MARKET_INSPECTOR = "market_inspector"       # Verifies weights, measures, and fair trade practices


@dataclass
class PublicOfficer:
    """An official post within the settlement's institutional apparatus."""

    office_id: str
    office_type: PublicOfficeType
    title: str
    current_holder_uid: Optional[HumanID] = None
    appointed_tick: Tick = 0
    term_length_ticks: int = 1440               # e.g. 15 simulated days per term (1440 ticks)
    daily_stipend: float = 6.0                  # Municipal stipend paid from community treasury
    cases_adjudicated: int = 0
    performance_rating: float = 0.8             # Citizen trust in officeholder's fairness [0.0, 1.0]

    def is_term_expired(self, current_tick: Tick) -> bool:
        return (current_tick - self.appointed_tick) >= self.term_length_ticks
