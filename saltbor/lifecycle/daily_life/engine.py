"""DailyLifeSimulationEngine — Emergent Daily Life & Diurnal Routines (Phase 1.8).

Orchestrates authentic, non-uniform everyday routines for synthetic humans
in El Salvador: waking, hygiene, meals, work shifts, market shopping, pupusería
dining, family caregiving, leisure, worship, community assemblies, and sleep.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from saltbor.core.types import (
    ActivityType,
    EmploymentStatus,
    HousingTenureType,
    LocationID,
    Tick,
)
from saltbor.lifecycle.daily_life.models import (
    DailyLifeProfile,
    DailyRoutineSlot,
    DiurnalPhase,
)

logger = logging.getLogger(__name__)


def get_diurnal_phase(hour: int) -> DiurnalPhase:
    """Classify 24-hour time into cultural-diurnal phases of El Salvador."""
    if 4 <= hour < 6:
        return DiurnalPhase.EARLY_DAWN
    elif 6 <= hour < 12:
        return DiurnalPhase.MORNING
    elif 12 <= hour < 14:
        return DiurnalPhase.MIDDAY
    elif 14 <= hour < 18:
        return DiurnalPhase.AFTERNOON
    elif 18 <= hour < 21:
        return DiurnalPhase.EVENING
    else:
        return DiurnalPhase.NIGHT


class DailyLifeSimulationEngine:
    """Manages individual daily routines, temporal rhythms, and life organization."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self.profiles: Dict[str, DailyLifeProfile] = {}
        self.seed = seed

    def ensure_profile(self, human: Any) -> DailyLifeProfile:
        """Ensure an individual has a daily life profile."""
        uid_str = str(human.uid)
        if uid_str in self.profiles:
            return self.profiles[uid_str]

        # Derive waking and sleeping habits from personality & occupation
        conscientiousness = 0.5
        neuroticism = 0.5
        if hasattr(human, "personality") and hasattr(human.personality, "traits"):
            c_val = getattr(human.personality.traits, "conscientiousness", 0.5)
            conscientiousness = float(getattr(c_val, "current_value", c_val))
            n_val = getattr(human.personality.traits, "neuroticism", 0.5)
            neuroticism = float(getattr(n_val, "current_value", n_val))

        # In El Salvador, informal vendors and agricultural workers wake very early (4:00 - 5:00 AM)
        occ = getattr(getattr(human, "demographics", None), "occupation", "").lower()
        if any(w in occ for w in ["agricultor", "jornalero", "pupusera", "comerciante"]):
            wake_h = 4 if conscientiousness > 0.4 else 5
        elif any(w in occ for w in ["maestro", "enfermero", "oficinista"]):
            wake_h = 5 if conscientiousness > 0.5 else 6
        else:
            wake_h = 6 if conscientiousness > 0.3 else 7

        sleep_h = 21 if wake_h <= 5 else 22

        profile = DailyLifeProfile(
            human_uid=uid_str,
            wake_hour=wake_h,
            sleep_hour=sleep_h,
            punctuality=round(0.4 + 0.5 * conscientiousness, 2),
            procrastination_tendency=round(0.6 - 0.5 * conscientiousness + 0.2 * neuroticism, 2),
            primary_occupation_type=occ or "informal",
        )
        self.profiles[uid_str] = profile
        return profile

    def get_or_create_profile(self, uid_str: str, human: Optional[Any] = None) -> DailyLifeProfile:
        """Get existing profile or create a new one."""
        if uid_str in self.profiles:
            return self.profiles[uid_str]
        if human is not None:
            return self.ensure_profile(human)
        prof = DailyLifeProfile(human_uid=uid_str)
        self.profiles[uid_str] = prof
        return prof

    def suggest_next_activity(
        self,
        human: Any,
        current_tick: Tick,
        current_hour: int,
        weather_rain: float = 0.0,
    ) -> Tuple[ActivityType, Optional[LocationID], str]:
        """
        Evaluate individual biorhythm, needs, and context to recommend the next natural activity.
        Respects individual autonomy while providing realistic daily rhythm.
        """
        profile = self.ensure_profile(human)
        phase = get_diurnal_phase(current_hour)
        profile.diurnal_phase = phase

        pstate = getattr(human, "physical_state", None)
        energy = getattr(pstate, "energy", 0.8)
        hunger = getattr(pstate, "hunger", 0.2)
        health = getattr(pstate, "health", 1.0)
        money = getattr(pstate, "money", 50.0)
        home_loc = getattr(pstate, "home_location_id", "casa_norte_1")
        work_loc = getattr(pstate, "work_location_id", "mercado_central")

        # 1. CRITICAL BIOLOGICAL OVERRIDES
        # Severe exhaustion
        if energy < 0.15:
            return ActivityType.SLEEP, home_loc, "Agotamiento físico extremo; necesidad de dormir"

        # Severe acute illness -> Seek medical care or convalesce
        active_conditions = getattr(human, "active_health_conditions", [])
        if active_conditions and health < 0.45:
            if money >= 3.0:
                return ActivityType.SEEK_MEDICAL_CARE, "clinica_salud", "Enfermedad aguda; acude a clínica de salud"
            else:
                return ActivityType.REST_RECOVER, home_loc, "Enfermedad sin fondos médicos; reposo en casa"

        # Severe hunger
        if hunger > 0.70:
            if money >= 2.0 and phase in (DiurnalPhase.MIDDAY, DiurnalPhase.EVENING):
                return ActivityType.DINE_OUT, "comedor_dona_maria", "Hambre intensa; almuerzo/cena en pupusería"
            return ActivityType.COOK, home_loc, "Hambre intensa; cocinar alimentos en el hogar"

        # 2. DIURNAL PHASE SCHEDULING

        # NIGHT: Sleep at home
        if phase == DiurnalPhase.NIGHT:
            if current_hour >= profile.sleep_hour or current_hour < profile.wake_hour:
                return ActivityType.SLEEP, home_loc, "Horario nocturno de descanso y sueño en casa"
            return ActivityType.RELAX, home_loc, "Esparcimiento nocturno tranquilo en el hogar"

        # EARLY DAWN (04:00 - 06:00): Awakening, hygiene, breakfast prep
        if phase == DiurnalPhase.EARLY_DAWN:
            if current_hour < profile.wake_hour:
                return ActivityType.SLEEP, home_loc, "Descanso matutino previo al despertar"
            if hunger > 0.35:
                return ActivityType.COOK, home_loc, "Preparación de café, atol y desayuno matutino"
            return ActivityType.HYGIENE, home_loc, "Aseo personal y preparación para la jornada"

        # MORNING (06:00 - 12:00): Productive labor, school, or job search
        if phase == DiurnalPhase.MORNING:
            emp_status = getattr(human, "employment_status", None)

            # Unemployed -> Search for work
            if emp_status == EmploymentStatus.UNEMPLOYED:
                return ActivityType.SEARCH_EMPLOYMENT, "mercado_central", "Búsqueda activa de empleo y jornales"

            # Rainstorm override: delay outdoor work if weather is dangerous
            if weather_rain > 8.0:
                return ActivityType.IDLE_INACTIVE, home_loc, "Lluvia torrencial; resguardo en casa esperando amaine"

            # Caregiving responsibilities
            if getattr(human, "has_dependent_child", False):
                return ActivityType.CARE_FOR_CHILD, home_loc, "Cuidado y alimentación de hijos menores"

            # Employed -> Work shift
            return ActivityType.WORK, work_loc or "mercado_central", "Jornada laboral matutina"

        # MIDDAY (12:00 - 14:00): Lunch & midday break
        if phase == DiurnalPhase.MIDDAY:
            if hunger > 0.30:
                if money >= 2.50:
                    return ActivityType.DINE_OUT, "comedor_dona_maria", "Almuerzo de mediodía en pupusería/comedor"
                return ActivityType.EAT, home_loc, "Almuerzo en casa con alimentos familiares"
            return ActivityType.REST, home_loc, "Pausa de sobremesa y descanso de mediodía"

        # AFTERNOON (14:00 - 18:00): Second work block, market shopping, errands
        if phase == DiurnalPhase.AFTERNOON:
            emp_status = getattr(human, "employment_status", None)
            if emp_status == EmploymentStatus.UNEMPLOYED:
                # Afternoon trade or study
                return ActivityType.STUDY, "binaes_estudio", "Lectura y estudio en biblioteca comunitaria"

            # Shopping for household groceries before stores close
            if current_hour >= 16 and money >= 5.0:
                return ActivityType.PURCHASE_GOODS, "mercado_central", "Compra de provisiones y verduras para la cena"

            return ActivityType.WORK, work_loc or "taller_artesanal", "Turno laboral de la tarde"

        # EVENING (18:00 - 21:00): Family time, pupusas, community, leisure
        if phase == DiurnalPhase.EVENING:
            if hunger > 0.35:
                if money >= 2.0:
                    return ActivityType.DINE_OUT, "comedor_dona_maria", "Cena de pupusas revueltas con familia o amigos"
                return ActivityType.COOK, home_loc, "Preparación de cena en casa"

            # Community assembly or leisure
            if getattr(human, "has_active_adesco_meeting", False):
                return ActivityType.COMMUNITY_MEETING, "plaza_central", "Asistencia a asamblea comunitaria ADESCO"

            if getattr(human, "has_social_invitation", False):
                return ActivityType.SOCIALIZE, "plaza_central", "Encuentro social con amistades en la plaza"

            return ActivityType.SPEND_TIME_WITH_PARTNER, home_loc, "Convivencia familiar y descanso nocturno"

        # Fallback default
        return ActivityType.REST, home_loc, "Descanso cotidiano"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profiles": {uid: p.to_dict() for uid, p in self.profiles.items()},
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        if not data:
            return
        for uid, p_dict in data.get("profiles", {}).items():
            self.profiles[uid] = DailyLifeProfile(
                human_uid=uid,
                wake_hour=p_dict.get("wake_hour", 5),
                sleep_hour=p_dict.get("sleep_hour", 22),
                diurnal_phase=DiurnalPhase(p_dict.get("diurnal_phase", "morning")),
                primary_occupation_type=p_dict.get("primary_occupation_type", "informal"),
                punctuality=float(p_dict.get("punctuality", 0.8)),
                unmet_commitments_count=int(p_dict.get("unmet_commitments_count", 0)),
                delayed_trips_count=int(p_dict.get("delayed_trips_count", 0)),
            )
