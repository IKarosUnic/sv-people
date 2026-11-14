"""Phase 1.10 Phase 3 Verification: Interpersonal Information and Rumor Diffusion."""

import pytest
import numpy as np

from saltbor.social.information.rumor import RumorEngine
from saltbor.culture.media_ecosystem import WorldInformationEcosystem


class TestPhase3InterpersonalRumorDiffusion:
    """Verifies that an agent listening to the radio propagates the news to peers via RumorEngine."""

    def test_radio_to_peer_transmission_chain(self):
        rng = np.random.default_rng(42)
        media = WorldInformationEcosystem(rng=rng)
        rumor_engine = RumorEngine(distortion_rate=0.20, rng=rng)

        # 1. Radio broadcast generated
        alert = media.generate_weather_emergency_broadcast(
            event_id="lempa_storm_03",
            hazard_name="Alerta Roja Río Lempa",
            affected_area="dist_usulutan",
            urgency=0.9,
            current_tick=100,
        )

        # 2. Agent 1 (Listener) tunes in and ingests broadcast into RumorEngine
        item = rumor_engine.ingest_broadcast_as_origin(
            listener_id="agent_1_listener",
            broadcast=alert,
            current_tick=100,
        )
        assert rumor_engine.has_knowledge("agent_1_listener", alert.broadcast_id)
        assert item.generation == 0

        # 3. Agent 1 transmits to Agent 2 (high trust: 0.85)
        accepted, reaction, item_gen1 = rumor_engine.transmit(
            sender_id="agent_1_listener",
            receiver_id="agent_2_neighbor",
            info_id=alert.broadcast_id,
            trust_in_sender=0.85,
            current_tick=102,
        )
        assert accepted is True
        assert reaction == "believe"
        assert item_gen1 is not None
        assert item_gen1.generation == 1
        assert len(item_gen1.transmission_chain) == 1

        # 4. Agent 2 transmits to Agent 3 (low trust: 0.20 -> rejected/disbelieved)
        acc_low, react_low, item_low = rumor_engine.transmit(
            sender_id="agent_2_neighbor",
            receiver_id="agent_3_skeptic",
            info_id=alert.broadcast_id,
            trust_in_sender=0.20,
            current_tick=104,
        )
        assert acc_low is False
        assert react_low == "disbelieve"
        assert not rumor_engine.has_knowledge("agent_3_skeptic", alert.broadcast_id)
