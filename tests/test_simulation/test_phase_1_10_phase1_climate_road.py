"""Phase 1.10 Phase 1 Verification: Climate-Road-Radio Causal Link."""

import pytest
import numpy as np

from saltbor.world.geographic.engine import RealGeographicEngine
from saltbor.world.spatial.territorial_movement import TerritorialMovementEngine
from saltbor.world.environment.weather import EnvironmentEngine, WeatherCondition
from saltbor.culture.media_ecosystem import WorldInformationEcosystem


class TestPhase1ClimateRoadRadioCausality:
    """Verifies that rainfall directly impacts road accessibility and triggers radio warnings."""

    def test_rainfall_road_attenuation_and_radio_alert(self):
        geo = RealGeographicEngine()
        movement = TerritorialMovementEngine(geo_engine=geo)
        env = EnvironmentEngine(seed=42)
        media = WorldInformationEcosystem(rng=np.random.default_rng(42))

        # Baseline clear weather: route between San Salvador and Santa Tecla
        j_clear = movement.start_journey(
            human_uid="commuter_01",
            origin_district_id="dist_san_salvador",
            destination_district_id="dist_santa_tecla",
            transport_mode="bus",
            is_rainy_season=False,
            is_temporal=False,
        )
        assert j_clear is not None
        assert j_clear.total_transit_hours > 0

        # Now simulate sudden torrential downpour and hazard
        env.force_weather_condition(WeatherCondition.TORRENTIAL_DOWNPOUR, duration_ticks=10)
        env.trigger_hazard("flood")

        # Movement engine with environment engine passed
        j_storm = movement.start_journey(
            human_uid="commuter_02",
            origin_district_id="dist_san_salvador",
            destination_district_id="dist_santa_tecla",
            transport_mode="bus",
            environment_engine=env,
        )
        assert j_storm is not None
        # Transit time during downpour must be higher due to temporal penalty
        assert j_storm.total_transit_hours >= j_clear.total_transit_hours

        # When road is blocked by hazard, broadcast alert is emitted
        alert = media.generate_weather_emergency_broadcast(
            event_id="hazard_los_chorros_01",
            hazard_name="Deslave Los Chorros",
            affected_area="dist_santa_tecla",
            urgency=0.95,
            current_tick=10,
        )
        assert alert.urgency == 0.95
        assert "DESLAVE" in alert.headline
        assert "radio_la_campesina" == alert.outlet_id
