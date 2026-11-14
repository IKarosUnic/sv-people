"""Phase 1.10 Phase 4 Verification: Entertainment, Sports, and Cultural Identity."""

import pytest
import numpy as np

from saltbor.culture.media_ecosystem import WorldInformationEcosystem, MediumCategory, MusicGenre


class TestPhase4EntertainmentAndSportsEcosystem:
    """Verifies sports fixture outcomes, football derbies, radio musical broadcasting, and fan appraisal."""

    def test_football_derby_and_fan_emotional_appraisal(self):
        rng = np.random.default_rng(777)
        media = WorldInformationEcosystem(rng=rng)

        # 1. Establish fan profiles
        fan_tigres = media.get_or_create_human_profile("fan_tigres_01", age=28, openness=0.7)
        fan_tigres.favorite_team_id = "tigres_santa_ana"
        fan_tigres.primary_medium = MediumCategory.NEWSPAPER

        fan_albos = media.get_or_create_human_profile("fan_albos_01", age=26, openness=0.6)
        fan_albos.favorite_team_id = "albos_capitalinos"
        fan_albos.primary_medium = MediumCategory.NEWSPAPER

        # 2. Simulate match fixture
        match, broadcast = media.simulate_sports_match(
            home_team_id="tigres_santa_ana",
            away_team_id="albos_capitalinos",
            current_tick=300,
        )
        assert match.home_score >= 0 and match.away_score >= 0
        assert broadcast.topic == "sports"
        assert "sports_" in broadcast.broadcast_id

        # 3. Evaluate emotional appraisal of fans exposed to the chronicle
        appraisal_tigres = media.evaluate_human_broadcast_exposure("fan_tigres_01", broadcast, force_exposure=True)
        appraisal_albos = media.evaluate_human_broadcast_exposure("fan_albos_01", broadcast, force_exposure=True)

        assert appraisal_tigres["exposed"] is True
        assert appraisal_albos["exposed"] is True

        # Opposing reactions based on scores
        if match.home_score > match.away_score:
            assert appraisal_tigres["appraisal_emotion"] == "joy"
            assert appraisal_albos["appraisal_emotion"] == "disappointment"
        elif match.away_score > match.home_score:
            assert appraisal_albos["appraisal_emotion"] == "joy"
            assert appraisal_tigres["appraisal_emotion"] == "disappointment"
        else:
            # Draw
            assert appraisal_tigres["behavioral_shift"] == "discuss_with_peers"

    def test_music_radio_programming_and_generations(self):
        rng = np.random.default_rng(888)
        media = WorldInformationEcosystem(rng=rng)

        # Elder listener prefers Cumbia or Balada
        p_elder = media.get_or_create_human_profile("elderly_listener", age=70)
        assert p_elder.preferred_genre in [
            MusicGenre.CUMBIA_SALVADORENA,
            MusicGenre.BALADA_DEL_RECUERDO,
            MusicGenre.SALSA_Y_MERENGUE,
            MusicGenre.MARIACHI_RANCHERA,
        ]
        # Young adult prefers modern urban/reggaeton or rock
        p_youth = media.get_or_create_human_profile("young_listener", age=20)
        assert p_youth.preferred_genre in [
            MusicGenre.URBANO_REGGAETON,
            MusicGenre.ROCK_EN_ESPANOL,
            MusicGenre.CUMBIA_SALVADORENA,
            MusicGenre.SALSA_Y_MERENGUE,
        ]
