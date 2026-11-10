"""Environmental dynamics: seasonal cycles (verano/invierno), temperature, rainfall, and agricultural yield."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from saltbor.core.types import Tick

logger = logging.getLogger(__name__)


class Season(enum.Enum):
    """The tropical seasons of El Salvador."""

    DRY_SEASON = "epoca_seca"        # November to April (Verano): Warm, dry, low rainfall
    RAINY_SEASON = "epoca_lluviosa"  # May to October (Invierno): Humid, frequent afternoon downpours
    VERANO = "epoca_seca"
    INVIERNO = "epoca_lluviosa"


class WeatherCondition(enum.Enum):
    """Current atmospheric state."""

    SUNNY_CLEAR = "sunny_clear"
    OVERCAST = "overcast"
    MODERATE_RAIN = "moderate_rain"
    TORRENTIAL_DOWNPOUR = "torrential_downpour"
    DROUGHT_HEATWAVE = "drought_heatwave"
    DROUGHT = "drought_heatwave"
    RAINY = "moderate_rain"
    STORM = "torrential_downpour"
    SUNNY = "sunny_clear"


@dataclass
class EnvironmentState:
    """The physical meteorological state of the settlement at current tick."""

    tick: Tick
    season: Season
    condition: WeatherCondition
    temperature_celsius: float
    rainfall_mm_per_hour: float
    soil_moisture: float               # 0.0 (bone dry) to 1.0 (waterlogged)
    crop_growth_multiplier: float      # Multiplier on agricultural harvest yield
    travel_speed_penalty: float        # Multiplier on outdoor travel speed (e.g. mud during downpour)
    hazard_warning: Optional[str] = None

    @property
    def weather_condition(self) -> WeatherCondition:
        return self.condition


class EnvironmentEngine:
    """Simulates dynamic weather, annual season cycles, and environmental shocks."""

    def __init__(
        self,
        ticks_per_year: float = 35040.0,
        rng: Optional[np.random.Generator] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.ticks_per_year = ticks_per_year
        if rng is not None:
            self.rng = rng
        elif seed is not None:
            self.rng = np.random.default_rng(seed)
        else:
            self.rng = np.random.default_rng()
        self.soil_moisture: float = 0.5
        self._active_hazard: Optional[str] = None
        self.state: Optional[EnvironmentState] = None

    def trigger_hazard(self, hazard_type: str) -> None:
        """Trigger an environmental shock: 'drought' or 'flood'."""
        self._active_hazard = hazard_type
        logger.warning("Environmental shock triggered: %s", hazard_type)

    def force_weather_condition(self, condition: WeatherCondition, duration_ticks: int = 10) -> None:
        """Manually force an atmospheric condition."""
        if condition in (WeatherCondition.DROUGHT, WeatherCondition.DROUGHT_HEATWAVE):
            self.trigger_hazard("drought")
            if self.state:
                self.state.crop_growth_multiplier = 0.30
        elif condition in (WeatherCondition.TORRENTIAL_DOWNPOUR, WeatherCondition.STORM):
            self.trigger_hazard("flood")
            if self.state:
                self.state.crop_growth_multiplier = 0.40
        else:
            self.clear_hazard()
        if self.state:
            self.state.condition = condition

    def get_crop_yield_multiplier(self) -> float:
        """Return the current agricultural multiplier."""
        return self.state.crop_growth_multiplier if self.state else 1.0

    def clear_hazard(self) -> None:
        self._active_hazard = None

    def step(self, current_tick: Tick) -> EnvironmentState:
        """Update environmental conditions for current simulation tick."""
        # Annual fraction [0.0, 1.0)
        year_frac = (current_tick % self.ticks_per_year) / self.ticks_per_year

        # Dry season (ticks 0 to 50% of year), Rainy season (50% to 100%)
        is_dry = year_frac < 0.50
        season = Season.DRY_SEASON if is_dry else Season.RAINY_SEASON

        # Baseline diurnal temperature cycle
        hour = (current_tick % 96) * 0.25  # 0 to 24 hours
        diurnal_temp = 24.0 + 8.0 * np.sin((hour - 9.0) * np.pi / 12.0)

        if self._active_hazard == "drought":
            season = Season.DRY_SEASON
            condition = WeatherCondition.DROUGHT_HEATWAVE
            temp = float(diurnal_temp + 6.0)
            rain = 0.0
            self.soil_moisture = max(0.05, self.soil_moisture - 0.005)
            crop_mult = 0.30  # Severe agricultural failure
            speed_penalty = 1.0
            warning = "Alerta de Sequía Prolongada: escasez de agua y marchitamiento de cultivos."

        elif self._active_hazard == "flood":
            condition = WeatherCondition.TORRENTIAL_DOWNPOUR
            temp = float(diurnal_temp - 4.0)
            rain = float(self.rng.uniform(35.0, 65.0))
            self.soil_moisture = 1.0
            crop_mult = 0.40  # Soil erosion and crop drowning
            speed_penalty = 0.55  # Severe mud and swollen rivers
            warning = "Alerta de Desbordamiento e Inundación: caminos anegados y vados intransitables."

        else:
            # Normal weather stochasticity
            if season == Season.DRY_SEASON:
                condition = WeatherCondition.SUNNY_CLEAR if self.rng.random() < 0.85 else WeatherCondition.OVERCAST
                temp = float(diurnal_temp + self.rng.uniform(0.0, 2.0))
                rain = 0.0
                self.soil_moisture = max(0.20, self.soil_moisture - 0.001)
                crop_mult = 0.85
                speed_penalty = 1.0
                warning = None
            else:
                p_rain = 0.60
                if self.rng.random() < p_rain:
                    is_heavy = self.rng.random() < 0.25
                    condition = WeatherCondition.TORRENTIAL_DOWNPOUR if is_heavy else WeatherCondition.MODERATE_RAIN
                    rain = float(self.rng.uniform(15.0, 40.0) if is_heavy else self.rng.uniform(3.0, 12.0))
                    speed_penalty = 0.75 if is_heavy else 0.90
                    self.soil_moisture = min(0.95, self.soil_moisture + 0.005)
                else:
                    condition = WeatherCondition.OVERCAST
                    rain = 0.0
                    speed_penalty = 1.0

                temp = float(diurnal_temp - self.rng.uniform(1.0, 3.0))
                # Fertile rain boosts normal crop yields
                crop_mult = 1.35 if self.soil_moisture < 0.85 else 0.90
                warning = None

        self.state = EnvironmentState(
            tick=current_tick,
            season=season,
            condition=condition,
            temperature_celsius=round(temp, 1),
            rainfall_mm_per_hour=round(rain, 1),
            soil_moisture=round(self.soil_moisture, 3),
            crop_growth_multiplier=round(crop_mult, 2),
            travel_speed_penalty=round(speed_penalty, 2),
            hazard_warning=warning,
        )
        return self.state
