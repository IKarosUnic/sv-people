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
    MOTIVATION = "motivation"


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
