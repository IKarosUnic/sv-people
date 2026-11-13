"""Unit and integration tests for SimulationController."""

from __future__ import annotations

import time
import pytest

from saltbor.visualization.controller import SimulationController


@pytest.fixture
def controller(tmp_path):
    db_file = tmp_path / "test_controller.db"
    ctrl = SimulationController(seed=123, db_path=str(db_file))
    yield ctrl
    ctrl.stop_worker()


def test_controller_initial_state(controller: SimulationController) -> None:
    status = controller.get_status_summary()
    assert status["tick"] == 0
    assert status["day"] == 1
    assert status["hour"] == 6
    assert status["active_population"] == 20
    assert status["scenario"] == "baseline"


def test_controller_step_sync(controller: SimulationController) -> None:
    t1 = controller.step_sync(count=1)
    assert t1 == 1
    assert controller.runner.clock.current_tick == 1

    t4 = controller.step_sync(count=3)
    assert t4 == 4
    assert controller.runner.clock.current_tick == 4
    assert len(controller.history_metrics) >= 4


def test_controller_speed_settings(controller: SimulationController) -> None:
    spd = controller.set_speed(10)
    assert spd == 10
    assert controller.get_speed() == 10

    spd100 = controller.set_speed(100)
    assert spd100 == 100

    spd1000 = controller.set_speed(1000)
    assert spd1000 == 1000


def test_controller_scenarios(controller: SimulationController) -> None:
    ok = controller.apply_scenario("drought_crisis")
    assert ok is True
    assert controller.scenario_name == "drought_crisis"

    ok = controller.apply_scenario("regional_trade_boom")
    assert ok is True
    assert controller.scenario_name == "regional_trade_boom"

    ok = controller.apply_scenario("cultural_renaissance")
    assert ok is True
    assert controller.scenario_name == "cultural_renaissance"

    ok = controller.apply_scenario("coffee_economic_boom")
    assert ok is True
    assert controller.scenario_name == "coffee_economic_boom"


def test_controller_checkpoints(controller: SimulationController) -> None:
    controller.step_sync(count=2)
    save_res = controller.save_checkpoint()
    assert save_res["status"] == "success"
    assert save_res["tick"] == 2

    # Advance further
    controller.step_sync(count=3)
    assert controller.runner.clock.current_tick == 5

    # Restore
    load_res = controller.load_checkpoint()
    assert load_res["status"] == "restored"
    assert load_res["tick"] == 2


def test_controller_event_subscription(controller: SimulationController) -> None:
    q = controller.subscribe_events()
    assert q is not None

    controller.step_sync(count=1)
    # Check queue got messages
    messages = []
    while not q.empty():
        messages.append(q.get_nowait())

    assert len(messages) > 0
    controller.unsubscribe_events(q)
