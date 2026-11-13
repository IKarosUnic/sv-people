"""SimulationController — Thread-safe, asynchronous orchestrator for visual observability.

Decouples the simulation engine execution from HTTP serving and frontend rendering.
Provides real-time event streaming, speed scaling (1x..1000x), checkpoint management,
scenario switching, and time-series aggregation for scientific observability.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from saltbor.core.config import SimulationConfig
from saltbor.core.types import SimulationPhase, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.simulation.laboratory.lab import SimulationLaboratory
from saltbor.simulation.runner import SimulationRunner
from saltbor.world.geographic.engine import RealGeographicEngine

logger = logging.getLogger(__name__)


@dataclass
class CivilizationMetricSnapshot:
    """Time-series metric point for historical charts."""

    tick: int
    day: int
    hour: int
    minute: int
    season: str
    population: int
    births: int
    deaths: int
    avg_energy: float
    avg_hunger: float
    avg_money: float
    avg_mood: float
    gini_coefficient: float
    active_businesses: int
    total_loans: int
    active_traditions: int
    active_communities: int
    temperature_c: float
    rainfall_mm: float
    events_count: int
    tick_latency_ms: float


class SimulationController:
    """Master controller managing simulation lifecycle and telemetry distribution."""

    def __init__(
        self,
        config: Optional[SimulationConfig] = None,
        seed: Optional[int] = 42,
        db_path: str = "saltbor.db",
    ) -> None:
        self.config = config or SimulationConfig(
            random_seed=seed,
            database_path=Path(db_path),
        )
        self.seed = seed
        self.scenario_name = "baseline"

        # Lock for mutating simulation state
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start paused by default for user control

        # Target ticks per second:
        # 1x = 1 tick/sec, 10x = 10 ticks/sec, 100x = 100 ticks/sec, 1000x = max speed
        self._speed_multiplier: int = 1
        self._worker_thread: Optional[threading.Thread] = None

        # Telemetry & Performance
        self.real_fps: float = 0.0
        self.last_tick_duration_ms: float = 0.0
        self._last_fps_calc_time = time.perf_counter()
        self._ticks_in_window = 0

        # Ring buffers for observability
        self._history_max_len = 2000
        self.history_metrics: list[CivilizationMetricSnapshot] = []
        self._events_max_len = 1000
        self.recent_events: list[dict[str, Any]] = []

        # SSE subscriber queues (non-blocking)
        self._subscribers: list[queue.Queue[dict[str, Any]]] = []
        self._subscribers_lock = threading.Lock()

        # Engine instances
        self.runner: Optional[SimulationRunner] = None
        self.geo_engine = RealGeographicEngine(seed=seed)
        self.laboratory = SimulationLaboratory(config=self.config)

        # Initialize engine
        self._initialize_runner()

    def _initialize_runner(self, load_existing: bool = False) -> None:
        """Create and initialize a fresh or restored SimulationRunner."""
        with self._lock:
            if self.runner is not None:
                try:
                    if load_existing:
                        # Avoid saving new tick over the checkpoint we want to restore
                        self.runner.db.close()
                    else:
                        self.runner.close()
                except Exception as ex:
                    logger.warning("Error closing previous runner: %s", ex)

            self.runner = SimulationRunner(config=self.config)
            self.runner.initialize(load_existing=load_existing)

            # Wire event listener for live telemetry
            self.runner.event_bus.subscribe(None, self._on_simulation_event)

            # Take initial snapshot
            self._record_telemetry_snapshot(self.runner.clock.current_tick, 0.0, 0)

    def _on_simulation_event(self, evt: SimulationEvent) -> None:
        """Process and buffer simulation events."""
        payload = {
            "event_type": evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type),
            "tick": evt.tick,
            "importance": round(evt.importance, 2),
            "source_human_id": str(evt.source_human_id) if evt.source_human_id else None,
            "target_human_id": str(evt.target_human_id) if evt.target_human_id else None,
            "location_id": evt.location_id,
            "data": evt.data,
            "timestamp": time.time(),
        }

        with self._lock:
            self.recent_events.append(payload)
            if len(self.recent_events) > self._events_max_len:
                self.recent_events.pop(0)

        # Push to SSE queues
        self._broadcast_to_subscribers({"type": "event", "data": payload})

    def _broadcast_to_subscribers(self, message: dict[str, Any]) -> None:
        """Send message to all SSE clients without blocking."""
        with self._subscribers_lock:
            dead_queues = []
            for q in self._subscribers:
                try:
                    q.put_nowait(message)
                except queue.Full:
                    # Drop oldest or mark as dead
                    try:
                        q.get_nowait()
                        q.put_nowait(message)
                    except Exception:
                        dead_queues.append(q)
                except Exception:
                    dead_queues.append(q)
            for dead in dead_queues:
                if dead in self._subscribers:
                    self._subscribers.remove(dead)

    def subscribe_events(self) -> queue.Queue[dict[str, Any]]:
        """Register a new SSE client queue."""
        q: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=150)
        with self._subscribers_lock:
            self._subscribers.append(q)
        return q

    def unsubscribe_events(self, q: queue.Queue[dict[str, Any]]) -> None:
        """Unregister an SSE client queue."""
        with self._subscribers_lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    # -------------------------------------------------------------------------
    # Worker Thread Lifecycle
    # -------------------------------------------------------------------------

    def start_worker(self) -> None:
        """Start the background execution worker thread."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._run_loop, name="SaltborWorkerThread", daemon=True)
        self._worker_thread.start()
        logger.info("Simulation background worker thread started.")

    def stop_worker(self) -> None:
        """Signal and stop the background execution thread."""
        self._stop_event.set()
        self._pause_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None
        logger.info("Simulation background worker thread stopped.")

    def _run_loop(self) -> None:
        """Autonomous simulation execution loop."""
        while not self._stop_event.is_set():
            # Wait if paused
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            t0 = time.perf_counter()
            tick = self.step_sync()
            elapsed = time.perf_counter() - t0

            # Calculate FPS / rate
            self._ticks_in_window += 1
            now = time.perf_counter()
            if now - self._last_fps_calc_time >= 0.5:
                self.real_fps = self._ticks_in_window / (now - self._last_fps_calc_time)
                self._last_fps_calc_time = now
                self._ticks_in_window = 0

            # Throttle according to speed multiplier
            # 1x -> target 1 tick/sec (sleep 1.0s)
            # 10x -> target 10 tick/sec (sleep 0.1s)
            # 100x -> target 100 tick/sec (sleep 0.01s)
            # 1000x -> unthrottled (sleep 0)
            if self._speed_multiplier < 1000:
                target_period = 1.0 / max(1, self._speed_multiplier)
                sleep_time = target_period - elapsed
                if sleep_time > 0.001:
                    time.sleep(sleep_time)

    # -------------------------------------------------------------------------
    # Execution Commands
    # -------------------------------------------------------------------------

    def play(self) -> None:
        """Resume continuous simulation execution."""
        with self._lock:
            if self.runner:
                self.runner.phase = SimulationPhase.RUNNING
            self._pause_event.set()
        self._broadcast_to_subscribers({"type": "state_change", "is_running": True})

    def pause(self) -> None:
        """Pause simulation execution."""
        with self._lock:
            if self.runner:
                self.runner.phase = SimulationPhase.PAUSED
            self._pause_event.clear()
        self._broadcast_to_subscribers({"type": "state_change", "is_running": False})

    def is_running(self) -> bool:
        """Check if simulation is currently actively advancing."""
        return self._pause_event.is_set() and not self._stop_event.is_set()

    def set_speed(self, multiplier: int) -> int:
        """Set execution speed preset: 1, 10, 100, 1000."""
        valid_speeds = [1, 10, 100, 1000]
        if multiplier not in valid_speeds:
            multiplier = min(valid_speeds, key=lambda s: abs(s - multiplier))
        with self._lock:
            self._speed_multiplier = multiplier
        self._broadcast_to_subscribers({"type": "speed_change", "speed": self._speed_multiplier})
        return self._speed_multiplier

    def get_speed(self) -> int:
        return self._speed_multiplier

    def step_sync(self, count: int = 1) -> int:
        """Advance simulation synchronously by exact number of ticks."""
        with self._lock:
            if self.runner is None:
                return 0
            current_tick = 0
            for _ in range(count):
                t0 = time.perf_counter()
                initial_events = len(self.recent_events)
                current_tick = self.runner.step()
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                self.last_tick_duration_ms = elapsed_ms
                new_events_count = len(self.recent_events) - initial_events

                # Record time-series metric snapshot
                self._record_telemetry_snapshot(current_tick, elapsed_ms, new_events_count)

            # Broadcast tick telemetry
            status_payload = self.get_status_summary()
            self._broadcast_to_subscribers({"type": "tick", "data": status_payload})
            return current_tick

    def _record_telemetry_snapshot(self, tick: int, latency_ms: float, events_emitted: int) -> None:
        """Compute and store aggregate metrics for charts."""
        if self.runner is None:
            return

        humans = self.runner.population.get_all()
        pop_count = len(humans)
        if pop_count == 0:
            return

        energies = [h.physical_state.energy for h in humans]
        hungers = [h.physical_state.hunger for h in humans]
        moneys = [h.physical_state.money for h in humans]
        moods = [h.emotions.get_mood() for h in humans]

        # Calculate empirical Gini coefficient on money
        sorted_moneys = np.sort(moneys)
        n = len(sorted_moneys)
        total_m = np.sum(sorted_moneys)
        gini = 0.0
        if total_m > 0 and n > 1:
            index = np.arange(1, n + 1)
            gini = float((2 * np.sum(index * sorted_moneys)) / (n * total_m) - (n + 1) / n)
            gini = max(0.0, min(1.0, gini))

        # Count institutions and traditions
        active_traditions = len(self.runner.culture.get_all_elements())
        active_comms = len(self.runner.community_engine.get_all_communities(active_only=True))
        active_biz = len(self.runner.businesses.get_all())
        total_loans = len(self.runner.credit.loans)

        # Environmental
        env = self.runner.environment
        env_state = getattr(env, "state", None)
        if env_state is not None:
            temp_c = getattr(env_state, "temperature_celsius", 24.5)
            rain_mm = getattr(env_state, "rainfall_mm_per_hour", 0.0)
            season_val = getattr(env_state.season, "value", str(env_state.season)) if hasattr(env_state, "season") else "epoca_seca"
        else:
            temp_c = 24.5
            rain_mm = 0.0
            season_val = "epoca_seca"

        clock = self.runner.clock
        hour_int = clock.current_hour_int
        min_int = int((clock.current_hour - hour_int) * 60)

        snap = CivilizationMetricSnapshot(
            tick=tick,
            day=clock.current_day + 1,
            hour=hour_int,
            minute=min_int,
            season=season_val,
            population=pop_count,
            births=0,
            deaths=0,
            avg_energy=round(float(np.mean(energies)), 3),
            avg_hunger=round(float(np.mean(hungers)), 3),
            avg_money=round(float(np.mean(moneys)), 2),
            avg_mood=round(float(np.mean(moods)), 3),
            gini_coefficient=round(gini, 3),
            active_businesses=active_biz,
            total_loans=total_loans,
            active_traditions=active_traditions,
            active_communities=active_comms,
            temperature_c=round(float(temp_c), 1),
            rainfall_mm=round(float(rain_mm), 2),
            events_count=events_emitted,
            tick_latency_ms=round(latency_ms, 2),
        )

        self.history_metrics.append(snap)
        if len(self.history_metrics) > self._history_max_len:
            self.history_metrics.pop(0)

    # -------------------------------------------------------------------------
    # Scenarios, Seed & Reset
    # -------------------------------------------------------------------------

    def apply_scenario(self, scenario_name: str) -> bool:
        """Apply a predefined environmental and economic scenario."""
        with self._lock:
            if self.runner is None:
                return False
            self.scenario_name = scenario_name
            current_tick = self.runner.clock.current_tick

            if scenario_name == "drought_crisis":
                from saltbor.world.environment.weather import WeatherCondition
                self.runner.environment.force_weather_condition(WeatherCondition.DROUGHT_HEATWAVE)
                self.runner.environment.soil_moisture = 0.12
                self.runner.environment.trigger_hazard("Alerta de Sequía en Corredor Seco: estrés hídrico severo.")
                self.runner.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.SHORTAGE_DETECTED,
                        tick=current_tick,
                        data={"scenario": "drought_crisis", "severity": 0.85},
                        importance=0.9,
                    )
                )
            elif scenario_name == "regional_trade_boom":
                for biz in self.runner.businesses.get_all():
                    biz.cash_reserve += 300.0
                self.runner.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.TRADE_COMPLETED,
                        tick=current_tick,
                        data={"scenario": "regional_trade_boom", "liquidity_injection": 300.0},
                        importance=0.75,
                    )
                )
            elif scenario_name == "cultural_renaissance":
                self.runner.cultural_evolution.innovation_rate = 0.40
                self.runner.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.ACHIEVEMENT,
                        tick=current_tick,
                        data={"scenario": "cultural_renaissance", "innovation_boost": 0.40},
                        importance=0.8,
                    )
                )
            elif scenario_name == "coffee_economic_boom":
                for h in self.runner.population.get_all():
                    if "agri" in h.demographics.occupation.lower() or "jornal" in h.demographics.occupation.lower():
                        h.physical_state.money += 75.0
                self.runner.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.TRADE_COMPLETED,
                        tick=current_tick,
                        data={"scenario": "coffee_economic_boom", "wage_bonus": 75.0},
                        importance=0.7,
                    )
                )
            else:
                self.scenario_name = "baseline"

            return True

    def reset_simulation(
        self,
        seed: Optional[int] = None,
        initial_pop: int = 20,
        scenario: str = "baseline",
    ) -> None:
        """Reset simulation state with fresh or specified seed and population."""
        was_running = self.is_running()
        self.pause()
        with self._lock:
            if seed is not None:
                self.seed = seed
                self.config.random_seed = seed
            self.config.initial_population_size = max(5, initial_pop)
            self.history_metrics.clear()
            self.recent_events.clear()
            self._initialize_runner(load_existing=False)
            self.apply_scenario(scenario)

        if was_running:
            self.play()

    def scale_active_population(self, target_count: int, reset: bool = False) -> int:
        """Dynamically scale active synthetic population to target_count without losing tick progress, or reset."""
        target_count = max(5, min(10000, target_count))
        if reset:
            self.reset_simulation(initial_pop=target_count, scenario=self.scenario_name)
            return target_count

        with self._lock:
            if self.runner is None:
                self.reset_simulation(initial_pop=target_count, scenario=self.scenario_name)
                return target_count

            current_humans = self.runner.population.get_all()
            current_count = len(current_humans)
            self.config.initial_population_size = target_count

            if target_count == current_count:
                return current_count

            if target_count < current_count:
                # Remove excess humans from registry
                excess = current_humans[target_count:]
                for h in excess:
                    self.runner.population.unregister(h.uid)
                self.runner.population.build_location_index()
            else:
                from saltbor.datasets.mock_data import MockDataGenerator
                from saltbor.population.factory import PopulationFactory

                all_profiles = MockDataGenerator.get_personas(target_count)
                new_profiles = all_profiles[current_count:target_count]

                # Distribute homes & workplaces across real anchor locations
                available_locations = [
                    "casa_norte_1", "casa_norte_2", "casa_sur_1", "casa_sur_2",
                    "casa_este_1", "casa_oeste_1", "plaza_central", "mercado_central",
                    "taller_artesanal", "casa_comunal", "clinica", "parque_cuscatlan"
                ]
                for idx, p in enumerate(new_profiles):
                    if not p.get("home_id") or p.get("home_id") not in available_locations:
                        p["home_id"] = available_locations[(current_count + idx) % len(available_locations)]
                    if not p.get("work_id") or p.get("work_id") not in available_locations:
                        p["work_id"] = available_locations[(current_count + idx * 3) % len(available_locations)]

                new_humans = PopulationFactory.create_from_profiles(
                    profiles=new_profiles,
                    config=self.config,
                    identity_factory=self.runner.identity_factory,
                    rng=self.runner.master_rng,
                )
                for h in new_humans:
                    self.runner.population.register(h)

                self.runner.population.build_location_index()
                if self.runner.human_repo:
                    try:
                        self.runner.human_repo.save_all(new_humans)
                    except Exception as ex:
                        logger.debug("Error persisting scaled humans: %s", ex)

            # Update multilevel LOD manager if active
            try:
                from saltbor.population.multilevel import get_multilevel_manager, LODLevel
                mgr = get_multilevel_manager()
                for i in range(min(target_count, 1000)):
                    mgr.promote_to_active(f"agent_{i:07d}", LODLevel.LOD_0_INDIVIDUAL)
            except Exception:
                pass

            new_pop = self.runner.population.count
            self._broadcast_to_subscribers({
                "type": "population_change",
                "population": new_pop,
                "target": target_count,
            })
            return new_pop

    def save_checkpoint(self) -> dict[str, Any]:
        """Trigger an immediate SQLite persistence checkpoint."""
        with self._lock:
            if self.runner is None:
                return {"status": "error", "message": "Runner not initialized"}
            self.runner.checkpoint()
            return {
                "status": "success",
                "tick": self.runner.clock.current_tick,
                "population": self.runner.population.count,
                "database": str(self.config.database_path),
            }

    def load_checkpoint(self) -> dict[str, Any]:
        """Restore simulation state from the SQLite database."""
        was_running = self.is_running()
        self.pause()
        with self._lock:
            self._initialize_runner(load_existing=True)
            res = {
                "status": "restored",
                "tick": self.runner.clock.current_tick if self.runner else 0,
                "population": self.runner.population.count if self.runner else 0,
            }
        if was_running:
            self.play()
        return res

    # -------------------------------------------------------------------------
    # Status & Summary Queries
    # -------------------------------------------------------------------------

    def get_status_summary(self) -> dict[str, Any]:
        """Return high-level real-time telemetry."""
        with self._lock:
            if self.runner is None:
                return {"status": "uninitialized"}
            clock = self.runner.clock
            hour_int = clock.current_hour_int
            min_int = int((clock.current_hour - hour_int) * 60)
            env_state = getattr(self.runner.environment, "state", None)
            season_str = getattr(env_state.season, "value", str(env_state.season)) if env_state and hasattr(env_state, "season") else "epoca_seca"
            return {
                "tick": clock.current_tick,
                "day": clock.current_day + 1,
                "hour": hour_int,
                "minute": min_int,
                "time_string": f"Day {clock.current_day + 1}, {hour_int:02d}:{min_int:02d}",
                "is_daytime": clock.is_daytime,
                "season": season_str,
                "is_running": self.is_running(),
                "speed_multiplier": self._speed_multiplier,
                "real_fps": round(self.real_fps, 1),
                "tick_latency_ms": round(self.last_tick_duration_ms, 2),
                "active_population": self.runner.population.count,
                "scenario": self.scenario_name,
                "random_seed": self.seed,
                "events_logged": len(self.recent_events),
                "phase": self.runner.phase.value if hasattr(self.runner.phase, "value") else str(self.runner.phase),
            }
