"""Data models for Autonomous Daily Life in SALTBOR (Phase 1.8).

Defines diurnal phases, daily schedule slots, routine preferences, and
disruption events for synthetic humans living in El Salvador.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

from saltbor.core.types import ActivityType, LocationID


class DiurnalPhase(str, Enum):
    """Phases of the 24-hour cycle in El Salvador."""
    EARLY_DAWN = "early_dawn"       # 04:00 - 06:00 (Despertar temprano, atol, café, preparativos)
    MORNING = "morning"             # 06:00 - 12:00 (Trabajo, escuela, mercado, labores matutinas)
    MIDDAY = "midday"               # 12:00 - 14:00 (Almuerzo, pausa, convivencia, compras del mediodía)
    AFTERNOON = "afternoon"         # 14:00 - 18:00 (Continuación laboral, oficios, estudio, regreso)
    EVENING = "evening"             # 18:00 - 21:00 (Cena de pupusas, vida familiar, ADESCO, pláticas)
    NIGHT = "night"                 # 21:00 - 04:00 (Descanso nocturno, sueño reparador)


@dataclass
class DailyRoutineSlot:
    """A scheduled slot in an individual's emergent daily trajectory."""
    start_hour: int
    end_hour: int
    preferred_activity: ActivityType
    target_location_id: Optional[LocationID] = None
    priority: float = 0.5
    flexibility: float = 0.5  # 0.0 = rigid contract, 1.0 = highly improvisational
    completed: bool = False
    disrupted: bool = False
    disruption_reason: Optional[str] = None


@dataclass
class DailyLifeProfile:
    """Individual daily life state, biorhythms, and routine records."""
    human_uid: str
    wake_hour: int = 5
    sleep_hour: int = 22
    diurnal_phase: DiurnalPhase = DiurnalPhase.MORNING
    primary_occupation_type: str = "informal"
    routine_slots: List[DailyRoutineSlot] = field(default_factory=list)
    punctuality: float = 0.80  # Conscientiousness-driven
    procrastination_tendency: float = 0.20
    improvisation_rate: float = 0.30
    unmet_commitments_count: int = 0
    delayed_trips_count: int = 0
    current_intended_activity: Optional[ActivityType] = None
    is_at_home: bool = True
    is_at_work: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "human_uid": self.human_uid,
            "wake_hour": self.wake_hour,
            "sleep_hour": self.sleep_hour,
            "diurnal_phase": self.diurnal_phase.value,
            "primary_occupation_type": self.primary_occupation_type,
            "punctuality": round(self.punctuality, 2),
            "unmet_commitments_count": self.unmet_commitments_count,
            "delayed_trips_count": self.delayed_trips_count,
            "is_at_home": self.is_at_home,
            "is_at_work": self.is_at_work,
        }
