"""
Salvadoran Environmental and Climate Simulation (Section 19.2).

Models authentic Salvadoran tropical meteorological and agricultural dynamics:
- Dry season (Época Seca / Verano: Nov - Apr) and Rainy season (Época Lluviosa / Invierno: May - Oct)
- Mid-summer intra-estival drought (Canícula en Julio/Agosto)
- Tropical weather shocks (Temporales continuos, Sequías prolongadas, Inundaciones, Deslaves)
- Formal Salvadoran agricultural calendar:
  - Siembra y Cosecha de Primera (Maíz y Frijol)
  - Siembra y Cosecha de Postrera (Frijol y Maicillo)
  - Siembra de Apante
  - Corta de Café (Noviembre a Febrero)
- Causal cascading impacts on agriculture, fishing, transport, household water, and public health
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Optional
import numpy as np


class SalvadoranSeason(str, Enum):
    """The tropical seasons of El Salvador."""
    EPOCA_SECA_VERANO = "epoca_seca_verano"         # November to April
    EPOCA_LLUVIOSA_INVIERNO = "epoca_lluviosa_invierno" # May to October
    CANICULA_INTRAESTIVAL = "canicula_intraestival" # Dry spell inside rainy season (July/August)


class SalvadoranWeatherPhenomenon(str, Enum):
    """Atmospheric and meteorological conditions in El Salvador."""
    DESPEJADO_SOLEADO = "despejado_soleado"         # Typical bright sunny tropical day
    VIENTOS_DE_OCTUBRE_NOVIEMBRE = "vientos_alisios" # Strong dry season trade winds (frescos)
    CHAPARRON_VESPERTINO = "chaparron_vespertino"   # Typical afternoon downpour with thunder
    TEMPORAL_TROPICAL = "temporal_tropical"         # Multi-day continuous heavy rain from low pressure / tropical wave
    CANICULA_SECA = "canicula_seca"                 # Rain stops for 1-3 weeks in middle of winter
    SEQUIA_METEOROLOGICA = "sequia_meteorologica"   # Extended drought linked to El Niño (ENSO)
    CALOR_CANICULAR = "calor_canicular"             # High heat index in lowlands and eastern plains


@dataclasses.dataclass
class SalvadoranEnvironmentSnapshot:
    """Instantaneous state of the Salvadoran environment."""
    month: int                                      # 1 to 12
    season: SalvadoranSeason
    phenomenon: SalvadoranWeatherPhenomenon
    temperature_celsius: float                      # Average temperature
    relative_humidity: float                        # [0.0, 1.0]
    daily_rainfall_mm: float                        # Precipitation in mm
    soil_moisture_level: float                      # [0.0, 1.0] (0.2 = parched, 0.6 = ideal, 0.95 = saturated)
    is_canicular_active: bool
    is_temporal_active: bool
    river_flooding_risk: float                      # [0.0, 1.0] Bajo Lempa & San Miguel alert
    mountain_landslide_risk: float                  # [0.0, 1.0] Los Chorros & volcanic slopes alert
    artisan_fishing_safe: bool                      # False if high seas or vientos de norte
    dirt_road_passability: float                    # [0.0, 1.0] 1.0 = dry firm dirt; 0.2 = deep mud
    active_agricultural_phase: str                  # Current agricultural calendar milestone


class SalvadoranClimateEngine:
    """Simulates the physical climate and causal environmental feedback in El Salvador."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self.rng = np.random.default_rng(seed)

    def evaluate_environment(
        self,
        month: int,
        day_of_month: int = 15,
        elevation_m: float = 600.0,
        is_coastal_or_eastern: bool = False,
        consecutive_rainy_days: int = 0,
        forced_phenomenon: Optional[SalvadoranWeatherPhenomenon] = None,
    ) -> SalvadoranEnvironmentSnapshot:
        """Calculate environmental state and causal risks for a given time of year and location."""
        # 1. Season determination
        if 5 <= month <= 10:
            if month in (7, 8) and (15 <= day_of_month <= 30):
                season = SalvadoranSeason.CANICULA_INTRAESTIVAL
                is_canicular = True
            else:
                season = SalvadoranSeason.EPOCA_LLUVIOSA_INVIERNO
                is_canicular = False
        else:
            season = SalvadoranSeason.EPOCA_SECA_VERANO
            is_canicular = False

        # 2. Temperature based on elevation and region (lapse rate ~6.5°C per 1000m)
        sea_level_base_temp = 32.0 if is_coastal_or_eastern else 29.5
        if month in (3, 4): # Hottest months before rains
            sea_level_base_temp += 2.5
        elif month in (11, 12, 1): # Cooler months (vientos)
            sea_level_base_temp -= 2.0

        temp_c = sea_level_base_temp - (elevation_m * 0.0065)

        # 3. Weather phenomenon & Precipitation
        if forced_phenomenon:
            phenomenon = forced_phenomenon
        elif is_canicular:
            phenomenon = SalvadoranWeatherPhenomenon.CANICULA_SECA
        elif season == SalvadoranSeason.EPOCA_LLUVIOSA_INVIERNO:
            if consecutive_rainy_days >= 3:
                phenomenon = SalvadoranWeatherPhenomenon.TEMPORAL_TROPICAL
            else:
                phenomenon = SalvadoranWeatherPhenomenon.CHAPARRON_VESPERTINO
        else: # Dry season
            if month in (10, 11, 12):
                phenomenon = SalvadoranWeatherPhenomenon.VIENTOS_DE_OCTUBRE_NOVIEMBRE
            elif month in (3, 4) and is_coastal_or_eastern:
                phenomenon = SalvadoranWeatherPhenomenon.CALOR_CANICULAR
            else:
                phenomenon = SalvadoranWeatherPhenomenon.DESPEJADO_SOLEADO

        # Rainfall and humidity values
        if phenomenon == SalvadoranWeatherPhenomenon.TEMPORAL_TROPICAL:
            rainfall_mm = 85.0 + float(self.rng.uniform(10.0, 45.0))
            humidity = 0.92
            soil_moisture = min(0.98, 0.65 + (consecutive_rainy_days * 0.08))
        elif phenomenon == SalvadoranWeatherPhenomenon.CHAPARRON_VESPERTINO:
            rainfall_mm = 25.0 + float(self.rng.uniform(5.0, 20.0))
            humidity = 0.78
            soil_moisture = 0.65
        elif phenomenon == SalvadoranWeatherPhenomenon.CANICULA_SECA:
            rainfall_mm = 1.0
            humidity = 0.60
            soil_moisture = 0.38 # Depletion during mid-winter dry spell
        elif phenomenon == SalvadoranWeatherPhenomenon.SEQUIA_METEOROLOGICA:
            rainfall_mm = 0.0
            humidity = 0.45
            soil_moisture = 0.18 # Severe parching
        else: # Dry season
            rainfall_mm = 0.0
            humidity = 0.52
            soil_moisture = 0.25

        # 4. Causal risks
        is_temporal = (phenomenon == SalvadoranWeatherPhenomenon.TEMPORAL_TROPICAL)
        flood_risk = min(1.0, (consecutive_rainy_days * 0.22) if is_temporal else 0.05)
        landslide_risk = min(1.0, (soil_moisture * 0.9) if (is_temporal and elevation_m > 500) else 0.05)

        # Fishing safety: High winds or temporales close small artisanal boats
        fishing_safe = True
        if phenomenon in (
            SalvadoranWeatherPhenomenon.TEMPORAL_TROPICAL,
            SalvadoranWeatherPhenomenon.VIENTOS_DE_OCTUBRE_NOVIEMBRE,
        ):
            fishing_safe = False

        # Dirt road passability: degrades as soil moisture exceeds 0.70
        if soil_moisture > 0.75:
            road_passability = max(0.15, 1.0 - ((soil_moisture - 0.70) * 3.0))
        else:
            road_passability = 1.0

        # 5. Agricultural Phase
        if month in (5, 6):
            agri_phase = "siembra_de_primera_maiz_frijol"
        elif month in (7, 8):
            if is_canicular:
                agri_phase = "desarrollo_primera_vulnerable_a_canicula"
            else:
                agri_phase = "cosecha_de_elote_tierno_y_primera"
        elif month in (8, 9):
            agri_phase = "siembra_de_postrera_frijol_maicillo"
        elif month in (10,):
            agri_phase = "desarrollo_de_postrera_y_granos_secos"
        elif month in (11, 12, 1):
            agri_phase = "corta_de_cafe_y_cosecha_de_postrera"
        elif month in (2, 3, 4):
            agri_phase = "tregua_seca_limpieza_de_rastrojo_y_quema_controlada"
        else:
            agri_phase = "mantenimiento_general"

        return SalvadoranEnvironmentSnapshot(
            month=month,
            season=season,
            phenomenon=phenomenon,
            temperature_celsius=round(temp_c, 1),
            relative_humidity=round(humidity, 2),
            daily_rainfall_mm=round(rainfall_mm, 1),
            soil_moisture_level=round(soil_moisture, 2),
            is_canicular_active=is_canicular,
            is_temporal_active=is_temporal,
            river_flooding_risk=round(flood_risk, 2),
            mountain_landslide_risk=round(landslide_risk, 2),
            artisan_fishing_safe=fishing_safe,
            dirt_road_passability=round(road_passability, 2),
            active_agricultural_phase=agri_phase,
        )

    # -------------------------------------------------------------------------
    # Causal Impact Calculators
    # -------------------------------------------------------------------------

    def calculate_crop_impact(
        self,
        snapshot: SalvadoranEnvironmentSnapshot,
        crop_type: str = "maiz", # "maiz", "frijol", "cafe"
    ) -> dict[str, Any]:
        """Causal consequence of environmental snapshot on crops."""
        if crop_type == "maiz":
            if snapshot.is_canicular_active and snapshot.soil_moisture_level <= 0.45:
                yield_mult = 0.55 # Canícula damages flowering maize
                status = "Estrés hídrico severo: espigas de maíz secas por canícula prolongada"
            elif snapshot.is_temporal_active:
                yield_mult = 0.70 # Wind lodging and waterlogging
                status = "Milpa acamada por vientos y raíces asfixiadas por encharcamiento"
            elif snapshot.soil_moisture_level >= 0.55:
                yield_mult = 1.15 # Optimal rains
                status = "Excelente vigor vegetativo: mazorcas llenando grano adecuadamente"
            else:
                yield_mult = 0.90
                status = "Desarrollo normal bajo condiciones de secano"

        elif crop_type == "frijol":
            if snapshot.is_temporal_active or snapshot.soil_moisture_level > 0.85:
                yield_mult = 0.40 # Fungal rust and rot in beans
                status = "Pérdida severa por antracnosis y pudrición de vainas por exceso de agua"
            elif snapshot.soil_moisture_level < 0.30:
                yield_mult = 0.60
                status = "Vainas marchitas y aborto de flores por sequía"
            else:
                yield_mult = 1.05
                status = "Floración y formación de vainas óptima"

        elif crop_type == "cafe":
            if snapshot.month in (11, 12, 1): # Corta season
                if snapshot.is_temporal_active:
                    yield_mult = 0.65
                    status = "Caída prematura de grano maduro al suelo por lluvias atípicas"
                else:
                    yield_mult = 1.0
                    status = "Corta activa en fincas de altura: grano madurando de forma uniforme"
            else:
                yield_mult = 0.95
                status = "Desarrollo vegetativo bajo sombra de ingas y copales"
        else:
            yield_mult = 1.0
            status = "Condiciones agrícolas generales estables"

        return {
            "crop": crop_type,
            "yield_multiplier": round(yield_mult, 2),
            "status_description": status,
            "phase": snapshot.active_agricultural_phase,
        }
