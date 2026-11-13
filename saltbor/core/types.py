"""Shared enums, type aliases, and constants for the Saltbor simulation."""

from __future__ import annotations

import enum
from typing import TypeAlias
from uuid import UUID

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
HumanID: TypeAlias = UUID
LocationID: TypeAlias = str
EventID: TypeAlias = UUID
MemoryID: TypeAlias = UUID
RelationshipID: TypeAlias = UUID
SkillID: TypeAlias = str
GoalID: TypeAlias = UUID
Tick: TypeAlias = int
Coordinate: TypeAlias = tuple[float, float]  # (x, y) in metres


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"


class LocationType(enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    EDUCATIONAL = "educational"
    RECREATIONAL = "recreational"
    WORKPLACE = "workplace"
    PUBLIC_SPACE = "public_space"
    NATURAL = "natural"
    ROAD = "road"
    PATH = "path"
    HEALTH_FACILITY = "health_facility"
    HAZARD_ZONE = "hazard_zone"
    WATER_SOURCE = "water_source"


class ActivityType(enum.Enum):
    SLEEP = "sleep"
    EAT = "eat"
    WORK = "work"
    STUDY = "study"
    SHOP = "shop"
    COOK = "cook"
    SOCIALIZE = "socialize"
    EXERCISE = "exercise"
    RELAX = "relax"
    TRAVEL = "travel"
    REST = "rest"

    # Phase 1.4 Civilization Integration Activities
    COMMUNITY_MEETING = "community_meeting"
    COMMUNITY_PROPOSAL = "community_proposal"
    LITIGATE = "litigate"
    SEEK_MEDIATION = "seek_mediation"
    COMMERCE_SELL = "commerce_sell"
    COMMERCE_BUY = "commerce_buy"
    BUSINESS_CREATE = "business_create"
    SEEK_CREDIT = "seek_credit"
    REPAY_DEBT = "repay_debt"
    RECEIVE_REMITTANCE = "receive_remittance"
    TEACH_APPRENTICE = "teach_apprentice"
    LEARN_TRADE = "learn_trade"
    CONDUCT_EXPERIMENT = "conduct_experiment"
    SHARE_DISCOVERY = "share_discovery"
    ATTEND_CELEBRATION = "attend_celebration"
    ORGANIZE_EVENT = "organize_event"
    SEEK_EMPLOYMENT = "seek_employment"
    NEGOTIATE = "negotiate"
    COOPERATE = "cooperate"
    MIGRATE = "migrate"

    # Phase 1.5 Human Daily Life, Labor Market, Housing & Socioeconomic Dynamics
    WINDOW_SHOPPING = "window_shopping"
    BROWSE_STORE = "browse_store"
    COMPARE_PRICES = "compare_prices"
    PURCHASE_GOODS = "purchase_goods"
    DINE_OUT = "dine_out"
    SEEK_ENTERTAINMENT = "seek_entertainment"
    VISIT_PARK = "visit_park"
    VISIT_FRIEND = "visit_friend"
    VISIT_RELATIVE = "visit_relative"
    ATTEND_EVENT = "attend_event"
    SEARCH_EMPLOYMENT = "search_employment"
    APPLY_FOR_JOB = "apply_for_job"
    ATTEND_INTERVIEW = "attend_interview"
    NEGOTIATE_SALARY = "negotiate_salary"
    ACCEPT_JOB = "accept_job"
    REJECT_JOB = "reject_job"
    RESIGN = "resign"
    START_BUSINESS = "start_business"
    CLOSE_BUSINESS = "close_business"
    SEEK_HOUSING = "seek_housing"
    RENT_HOUSING = "rent_housing"
    SEEK_SHELTER = "seek_shelter"
    REQUEST_ASSISTANCE = "request_assistance"
    OFFER_ASSISTANCE = "offer_assistance"
    PARTICIPATE_IN_HOBBY = "participate_in_hobby"
    PLAY_SPORT = "play_sport"
    EXPLORE_LOCATION = "explore_location"

    # Phase 1.5 Extension: Health, Caregiving, Romance & Environment
    SEEK_MEDICAL_CARE = "seek_medical_care"
    REST_RECOVER = "rest_recover"
    COURTSHIP_DATE = "courtship_date"
    SPEND_TIME_WITH_PARTNER = "spend_time_with_partner"
    CARE_FOR_CHILD = "care_for_child"
    CARE_FOR_ELDER = "care_for_elder"
    COMMUNITY_CLEANUP = "community_cleanup"
    REPAIR_DAMAGE = "repair_damage"


class HousingTenureType(enum.Enum):
    """Housing accommodation status and tenancy condition."""
    OWNER_OCCUPIED = "owner_occupied"
    RENTAL = "rental"
    SHARED_FAMILY = "shared_family"
    INFORMAL_HOUSING = "informal_housing"
    TEMPORARY_ACCOMMODATION = "temporary_accommodation"
    SHELTER = "shelter"
    HOMELESS = "homeless"


class EmploymentStatus(enum.Enum):
    """Labor market status and contractual arrangement."""
    UNEMPLOYED = "unemployed"
    EMPLOYED_FORMAL = "employed_formal"
    EMPLOYED_INFORMAL = "employed_informal"
    SELF_EMPLOYED = "self_employed"
    EMPLOYER = "employer"
    RETIRED = "retired"
    STUDENT = "student"


class ContractType(enum.Enum):
    """Employment contract classification."""
    FORMAL_PERMANENT = "formal_permanent"
    FORMAL_TEMPORARY = "formal_temporary"
    INFORMAL_WAGE = "informal_wage"
    DAY_LABOR = "day_labor"


class EmotionType(enum.Enum):
    JOY = "joy"
    SADNESS = "sadness"
    FEAR = "fear"
    ANGER = "anger"
    AFFECTION = "affection"
    SHAME = "shame"
    GUILT = "guilt"
    CURIOSITY = "curiosity"
    FRUSTRATION = "frustration"
    ANXIETY = "anxiety"
    SATISFACTION = "satisfaction"
    DISAPPOINTMENT = "disappointment"
    LONELINESS = "loneliness"
    EXCITEMENT = "excitement"
    MOTIVATION = "motivation"
    STRESS = "stress"
    GRIEF = "grief"
    HOPE = "hope"
    PRIDE = "pride"
    REGRET = "regret"
    RELIEF = "relief"
    RESENTMENT = "resentment"
    JEALOUSY = "jealousy"


class NeedType(enum.Enum):
    HUNGER = "hunger"
    REST = "rest"
    SOCIAL = "social"
    SAFETY = "safety"
    ACHIEVEMENT = "achievement"
    AUTONOMY = "autonomy"
    COMFORT = "comfort"
    STIMULATION = "stimulation"


class RelationshipType(enum.Enum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    FAMILY = "family"
    PARTNER = "partner"
    COLLEAGUE = "colleague"
    RIVAL = "rival"
    ENEMY = "enemy"


class EventCategory(enum.Enum):
    SOCIAL = "social"
    ECONOMIC = "economic"
    PERSONAL = "personal"
    ENVIRONMENTAL = "environmental"
    COGNITIVE = "cognitive"
    ACHIEVEMENT = "achievement"


class MemoryCategory(enum.Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class SkillCategory(enum.Enum):
    PHYSICAL = "physical"
    MENTAL = "mental"
    SOCIAL = "social"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    ACADEMIC = "academic"


class DataSource(enum.Enum):
    """Tracks where a piece of data originated."""
    NEMOTRON_DATASET = "nemotron_dataset"
    MOCK_GENERATED = "mock_generated"
    SIMULATION_GENERATED = "simulation_generated"
    USER_DEFINED = "user_defined"


class SimulationPhase(enum.Enum):
    """High-level phases of the simulation loop."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    CHECKPOINTING = "checkpointing"


# ---------------------------------------------------------------------------
# Phase 1.5 Extension Core Domain Enums
# ---------------------------------------------------------------------------

class GeographicObjectType(enum.Enum):
    """Distinction of geographic objects per Section 2."""
    REAL_WORLD_GEOGRAPHIC = "real_world_geographic"
    VERIFIED_REAL_ESTABLISHMENT = "verified_real_establishment"
    SIMULATED_ESTABLISHMENT = "simulated_establishment"
    SYNTHETIC_BUILDING = "synthetic_building"
    TEMPORARY_ENVIRONMENTAL_OBJECT = "temporary_environmental_object"


class ConditionCategory(enum.Enum):
    """Broad biological classification of medical & health conditions."""
    INFECTIOUS = "infectious"
    GASTROINTESTINAL = "gastrointestinal"
    RESPIRATORY = "respiratory"
    CHRONIC = "chronic"
    INJURY = "injury"
    MENTAL_DISTRESS = "mental_distress"


class AccidentType(enum.Enum):
    """Classification of everyday human accidents and misfortunes."""
    TRAFFIC_ACCIDENT = "traffic_accident"
    WORKPLACE_INJURY = "workplace_injury"
    DOMESTIC_FALL = "domestic_fall"
    THEFT_ROBBERY = "theft_robbery"


class DisasterType(enum.Enum):
    """Classification of contextual environmental disasters."""
    FLOODING = "flooding"
    LANDSLIDE = "landslide"
    DROUGHT_SHOCK = "drought_shock"
    INFRASTRUCTURE_COLLAPSE = "infrastructure_collapse"


class RomanceStage(enum.Enum):
    """Stages of interpersonal romantic relationship evolution."""
    UNACQUAINTED = "unacquainted"
    INTEREST = "interest"
    DATING = "dating"
    COHABITING = "cohabiting"
    MARRIED = "married"
    SEPARATED = "separated"
    DIVORCED = "divorced"
    WIDOWED = "widowed"

