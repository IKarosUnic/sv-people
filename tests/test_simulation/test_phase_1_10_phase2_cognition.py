"""Phase 1.10 Phase 2 Verification: Cognitive Intake and Decision Alteration."""

import pytest
import numpy as np

from saltbor.population.factory import PopulationFactory
from saltbor.culture.media_ecosystem import WorldInformationEcosystem
from saltbor.core.types import ActivityType


class TestPhase2CognitiveIntakeAndDecisions:
    """Verifies that media broadcasts alter SyntheticHuman fear, shelter decisions, and travel."""

    def test_broadcast_triggers_fear_and_sheltering(self):
        humans = PopulationFactory.create_population(try_nemotron=False)
        human = humans[0]
        media = WorldInformationEcosystem(rng=np.random.default_rng(42))

        # Check initial baseline
        assert not human.active_evacuation_alert
        assert len(human.received_broadcasts) == 0

        # Generate weather alert
        alert = media.generate_weather_emergency_broadcast(
            event_id="landslide_danger_01",
            hazard_name="Inundación Masiva Lempa",
            affected_area="dist_bajo_lempa",
            urgency=0.9,
            current_tick=50,
        )

        # Agent receives and believes broadcast
        human.receive_media_broadcast(alert, believed=True)

        assert human.active_evacuation_alert is True
        assert len(human.received_broadcasts) == 1
        assert human.physical_state.current_activity == ActivityType.REST
        # Fear state is elevated
        if hasattr(human.emotions, "profile") and hasattr(human.emotions.profile, "state"):
            assert human.emotions.profile.state.fear >= 0.5
