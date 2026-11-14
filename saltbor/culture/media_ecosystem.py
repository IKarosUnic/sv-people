"""Media & Cultural Intelligence: Information and Entertainment Ecosystem.

Implements the multi-modal media landscape of the simulation:
- Radio stations (frecuencia, alcance, formato)
- Synthetic media generation (bulletins, press, storm warnings, cultural commentary)
- Music & entertainment ecosystem (genres, generational taste profiles, procedural songs)
- Sports ecosystem (football league, derbies, match outcomes, fan emotions)
- Probabilistic cognitive ingestion & interpersonal diffusion integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class MediumCategory(str, Enum):
    """Channels of public and community communication."""

    RADIO = "radio"
    NEWSPAPER = "newspaper"
    TELEVISION = "television"
    COMMUNITY_MEGAPHONE = "community_megaphone"
    DIGITAL_PRESS = "digital_press"
    WORD_OF_MOUTH = "word_of_mouth"


class MusicGenre(str, Enum):
    """Dominant cultural and generational music styles."""

    CUMBIA_SALVADORENA = "cumbia_salvadorena"
    SALSA_Y_MERENGUE = "salsa_y_merengue"
    ROCK_EN_ESPANOL = "rock_en_espanol"
    URBANO_REGGAETON = "urbano_reggaeton"
    BALADA_DEL_RECUERDO = "balada_del_recuerdo"
    MARIACHI_RANCHERA = "mariachi_ranchera"


@dataclass
class FictionalMediaOutlet:
    """A broadcasting entity, newspaper publisher, or megaphone hub."""

    outlet_id: str
    name: str
    category: MediumCategory
    coverage_radius_km: float
    center_location: tuple[float, float]  # (latitude, longitude)
    editorial_stance: str  # e.g., "institutional", "alarmist", "populist", "community"
    credibility_rating: float  # 0.0 to 1.0
    audience_reach_factor: float = 0.5


@dataclass
class MediaBroadcast:
    """A generated news item, bulletin, or public warning."""

    broadcast_id: str
    outlet_id: str
    category: MediumCategory
    headline: str
    body: str
    urgency: float  # 0.0 (leisure) to 1.0 (emergency evacuation)
    topic: str  # e.g., "weather", "traffic", "sports", "economy", "festivity"
    tick_issued: Tick
    is_fictional: bool = True
    ground_truth_event_id: Optional[str] = None
    affected_locations: list[str] = field(default_factory=list)


@dataclass
class ProceduralSong:
    """A procedural musical piece circulating in the culture."""

    song_id: str
    title: str
    artist_name: str
    genre: MusicGenre
    release_tick: Tick
    catchiness: float  # 0.0 to 1.0
    popularity: float = 0.5


@dataclass
class SportsTeam:
    """A simulated sports club or canton football squad."""

    team_id: str
    name: str
    city: str
    department: str
    prestige: float  # 0.0 to 1.0
    fan_base_size: int = 1000
    rival_team_id: Optional[str] = None


@dataclass
class MatchResult:
    """The outcome of a simulated sporting competition."""

    match_id: str
    tick: Tick
    home_team_id: str
    away_team_id: str
    home_score: int
    away_score: int
    excitement_level: float


@dataclass
class HumanCultureProfile:
    """Cultural, entertainment, and media consumption traits of an individual."""

    human_id: HumanID
    primary_medium: MediumCategory
    media_trust: float  # 0.0 to 1.0
    preferred_genre: MusicGenre
    favorite_team_id: Optional[str]
    sports_passion: float  # 0.0 (indifferent) to 1.0 (diehard fan)
    receptivity_to_rumors: float = 0.3


class WorldInformationEcosystem:
    """Central engine orchestrating broadcasts, entertainment, sports, and cultural trends."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng(42)
        self.outlets: dict[str, FictionalMediaOutlet] = {}
        self.broadcast_archive: list[MediaBroadcast] = []
        self.songs_catalog: dict[str, ProceduralSong] = {}
        self.sports_teams: dict[str, SportsTeam] = {}
        self.match_history: list[MatchResult] = []
        self.agent_profiles: dict[HumanID, HumanCultureProfile] = {}
        self._initialize_salvadoran_media_and_sports_baseline()

    def _initialize_salvadoran_media_and_sports_baseline(self) -> None:
        """Seed representative Salvadoran media outlets, football clubs, and cultural music."""
        # 1. Media Outlets
        self.register_outlet(
            FictionalMediaOutlet(
                outlet_id="radio_la_campesina",
                name="Radio La Campesina 98.1 FM",
                category=MediumCategory.RADIO,
                coverage_radius_km=45.0,
                center_location=(13.6929, -89.2182),
                editorial_stance="community",
                credibility_rating=0.85,
                audience_reach_factor=0.75,
            )
        )
        self.register_outlet(
            FictionalMediaOutlet(
                outlet_id="diario_el_cuscatleco",
                name="Diario El Cuscatleco",
                category=MediumCategory.NEWSPAPER,
                coverage_radius_km=80.0,
                center_location=(13.6980, -89.1914),
                editorial_stance="institutional",
                credibility_rating=0.90,
                audience_reach_factor=0.60,
            )
        )
        self.register_outlet(
            FictionalMediaOutlet(
                outlet_id="megafono_cantonal",
                name="Megáfono Comunitario El Espino",
                category=MediumCategory.COMMUNITY_MEGAPHONE,
                coverage_radius_km=3.0,
                center_location=(13.6800, -89.2600),
                editorial_stance="community",
                credibility_rating=0.70,
                audience_reach_factor=0.90,
            )
        )

        # 2. Sports Teams (Fictionalized homage to classic Salvadoran football)
        self.sports_teams["tigres_santa_ana"] = SportsTeam(
            team_id="tigres_santa_ana",
            name="Club Deportivo Los Tigres",
            city="Santa Ana",
            department="Santa Ana",
            prestige=0.88,
            rival_team_id="albos_capitalinos",
        )
        self.sports_teams["albos_capitalinos"] = SportsTeam(
            team_id="albos_capitalinos",
            name="Albos de San Salvador",
            city="San Salvador",
            department="San Salvador",
            prestige=0.92,
            rival_team_id="tigres_santa_ana",
        )
        self.sports_teams["aguilas_orientales"] = SportsTeam(
            team_id="aguilas_orientales",
            name="Águilas de San Miguel",
            city="San Miguel",
            department="San Miguel",
            prestige=0.87,
            rival_team_id="albos_capitalinos",
        )

        # 3. Procedural Songs
        self.songs_catalog["cumbia_san_salvador"] = ProceduralSong(
            song_id="cumbia_san_salvador",
            title="El Torito de San Salvador",
            artist_name="Los Hermanos del Valle",
            genre=MusicGenre.CUMBIA_SALVADORENA,
            release_tick=0,
            catchiness=0.85,
            popularity=0.80,
        )
        self.songs_catalog["balada_recuerdo_01"] = ProceduralSong(
            song_id="balada_recuerdo_01",
            title="Bajo el Ciprés de Santa Tecla",
            artist_name="Trio Sonsonate",
            genre=MusicGenre.BALADA_DEL_RECUERDO,
            release_tick=0,
            catchiness=0.65,
            popularity=0.55,
        )

    def register_outlet(self, outlet: FictionalMediaOutlet) -> None:
        self.outlets[outlet.outlet_id] = outlet

    def get_or_create_human_profile(
        self,
        human_id: HumanID,
        age: int = 35,
        openness: float = 0.5,
        neuroticism: float = 0.5,
    ) -> HumanCultureProfile:
        """Create or return a human culture profile calibrated by demographics."""
        if human_id in self.agent_profiles:
            return self.agent_profiles[human_id]

        # Generational genre distribution
        if age > 50:
            genre_weights = [0.35, 0.25, 0.05, 0.0, 0.25, 0.10]
        elif age > 30:
            genre_weights = [0.30, 0.25, 0.25, 0.10, 0.05, 0.05]
        else:
            genre_weights = [0.15, 0.15, 0.20, 0.45, 0.0, 0.05]

        genres = list(MusicGenre)
        chosen_idx = int(self.rng.choice(len(genres), p=genre_weights))
        chosen_genre = genres[chosen_idx]

        # Medium preference
        if age > 45:
            medium = MediumCategory.RADIO
        elif age > 25:
            medium = MediumCategory.NEWSPAPER if openness > 0.6 else MediumCategory.RADIO
        else:
            medium = MediumCategory.DIGITAL_PRESS

        # Team fandom
        teams = list(self.sports_teams.keys())
        fav_team = self.rng.choice(teams) if self.rng.random() > 0.25 else None
        passion = float(self.rng.beta(2, 3)) if fav_team else 0.0

        profile = HumanCultureProfile(
            human_id=human_id,
            primary_medium=medium,
            media_trust=float(np.clip(0.5 + 0.3 * (openness - neuroticism), 0.1, 0.95)),
            preferred_genre=chosen_genre,
            favorite_team_id=fav_team,
            sports_passion=passion,
            receptivity_to_rumors=float(np.clip(0.2 + 0.4 * neuroticism, 0.05, 0.9)),
        )
        self.agent_profiles[human_id] = profile
        return profile

    def generate_weather_emergency_broadcast(
        self,
        event_id: str,
        hazard_name: str,
        affected_area: str,
        urgency: float,
        current_tick: Tick,
    ) -> MediaBroadcast:
        """Generate a synthetic emergency news bulletin prompted by an environmental hazard."""
        outlet_id = "radio_la_campesina"
        headline = f"¡ALERTA CLIMÁTICA!: {hazard_name.upper()} en sector {affected_area}"
        body = (
            f"Se reportan fuertes precipitaciones e inestabilidad en la ruta {affected_area}. "
            f"Protección Civil y autoridades de tránsito recomiendan postergar viajes no esenciales "
            f"y mantenerse atentos a las emisiones de esta emisora."
        )
        broadcast = MediaBroadcast(
            broadcast_id=f"alert_{current_tick}_{event_id}",
            outlet_id=outlet_id,
            category=MediumCategory.RADIO,
            headline=headline,
            body=body,
            urgency=urgency,
            topic="weather",
            tick_issued=current_tick,
            is_fictional=True,
            ground_truth_event_id=event_id,
            affected_locations=[affected_area],
        )
        self.broadcast_archive.append(broadcast)
        logger.info("MediaBroadcast generated: %s [Urgency: %.2f]", headline, urgency)
        return broadcast

    def simulate_sports_match(
        self,
        home_team_id: str,
        away_team_id: str,
        current_tick: Tick,
    ) -> tuple[MatchResult, MediaBroadcast]:
        """Simulate a football fixture and generate post-match sports news."""
        home = self.sports_teams[home_team_id]
        away = self.sports_teams[away_team_id]

        # Poisson distribution for realistic football scores
        home_lambda = 1.2 * home.prestige
        away_lambda = 1.0 * away.prestige
        home_goals = int(self.rng.poisson(home_lambda))
        away_goals = int(self.rng.poisson(away_lambda))

        excitement = float(min(1.0, (home_goals + away_goals) * 0.2 + (0.3 if home_goals == away_goals else 0.1)))
        match = MatchResult(
            match_id=f"match_{current_tick}_{home_team_id}_{away_team_id}",
            tick=current_tick,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_goals,
            away_score=away_goals,
            excitement_level=excitement,
        )
        self.match_history.append(match)

        # Sports broadcast
        if home_goals > away_goals:
            headline = f"¡Gran Victoria!: {home.name} se impone {home_goals}-{away_goals} a {away.name}"
        elif away_goals > home_goals:
            headline = f"¡Campanazo de Visita!: {away.name} vence {away_goals}-{home_goals} a {home.name}"
        else:
            headline = f"Clásico Empatado: {home.name} y {away.name} igualan {home_goals}-{away_goals}"

        body = (
            f"Emocionante encuentro disputado en {home.city}. El resultado genera euforia en la hinchada local "
            f"y debate táctico en las tertulias deportivas de todo el departamento."
        )
        broadcast = MediaBroadcast(
            broadcast_id=f"sports_{match.match_id}",
            outlet_id="diario_el_cuscatleco",
            category=MediumCategory.NEWSPAPER,
            headline=headline,
            body=body,
            urgency=0.2,
            topic="sports",
            tick_issued=current_tick,
            is_fictional=True,
            ground_truth_event_id=match.match_id,
            affected_locations=[home.city, away.city],
        )
        self.broadcast_archive.append(broadcast)
        return match, broadcast

    def evaluate_human_broadcast_exposure(
        self,
        human_id: HumanID,
        broadcast: MediaBroadcast,
        force_exposure: bool = False,
    ) -> dict[str, Any]:
        """Model the cognitive intake and behavioral reaction of an individual human to news."""
        profile = self.get_or_create_human_profile(human_id)
        outlet = self.outlets.get(broadcast.outlet_id)
        credibility = outlet.credibility_rating if outlet else 0.5

        # Exposure probability: does the person tune in or see it?
        channel_match = 1.0 if profile.primary_medium == broadcast.category else 0.4
        exposure_prob = 1.0 if force_exposure else channel_match * (outlet.audience_reach_factor if outlet else 0.5)
        is_exposed = bool(self.rng.random() < exposure_prob)

        if not is_exposed:
            return {
                "human_id": human_id,
                "exposed": False,
                "believed": False,
                "behavioral_shift": "none",
                "appraisal_emotion": "neutral",
            }

        # Trust-weighted belief adoption
        adoption_score = profile.media_trust * credibility * (1.0 + broadcast.urgency * 0.5)
        believed = bool(adoption_score > 0.4)

        behavioral_shift = "none"
        appraisal_emotion = "neutral"

        if believed and broadcast.topic == "weather" and broadcast.urgency > 0.6:
            behavioral_shift = "cancel_travel_and_shelter"
            appraisal_emotion = "fear_and_vigilance"
        elif believed and broadcast.topic == "sports":
            if profile.favorite_team_id and broadcast.ground_truth_event_id:
                # Find matching match
                match = next((m for m in self.match_history if m.match_id == broadcast.ground_truth_event_id), None)
                if match:
                    if match.home_team_id == profile.favorite_team_id:
                        appraisal_emotion = "joy" if match.home_score > match.away_score else "disappointment"
                    elif match.away_team_id == profile.favorite_team_id:
                        appraisal_emotion = "joy" if match.away_score > match.home_score else "disappointment"
            behavioral_shift = "discuss_with_peers"
        elif not believed:
            appraisal_emotion = "skepticism"
            behavioral_shift = "ignore_or_mock"

        return {
            "human_id": human_id,
            "exposed": True,
            "believed": believed,
            "behavioral_shift": behavioral_shift,
            "appraisal_emotion": appraisal_emotion,
            "receptivity_to_rumors": profile.receptivity_to_rumors,
        }
