"""Environmental Hazards, Pollution and Climate State (Phase 1.5 Extension).

Tracks bidirectional territorial indicators:
- Water pollution index and water source cleanliness.
- Waste accumulation and ecological degradation.
- Flood and landslide vulnerability.
- Offline cacheable meteorological conditions.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict


@dataclasses.dataclass
class EnvironmentalHazardProfile:
    """Territorial environmental quality and hazard state."""
    # Water & Sanitation
    water_pollution_index: float = 0.20   # [0.0 = pristine, 1.0 = severely contaminated]
    water_sources: dict[str, float] = dataclasses.field(default_factory=lambda: {
        "rio_suchiacel": 0.70,            # 0.70 cleanliness = acceptable
        "pozo_comunal_san_pedro": 0.85,   # protected well water
        "quebrada_el_zapote": 0.65,
    })

    # Terrestrial & Atmospheric Quality
    air_quality_index: float = 0.90       # 1.0 = clean mountain air
    soil_degradation_index: float = 0.25
    accumulated_waste_kg: float = 120.0   # Solid waste awaiting collection/composting
    resource_depletion_level: float = 0.15

    # Hazard Risks
    flood_risk_level: float = 0.10
    landslide_risk_level: float = 0.10
    is_drought: bool = False

    # Weather Parameters (Offline / Cacheable)
    temperature_celsius: float = 27.5
    rainfall_mm_per_hour: float = 0.0
    humidity_pct: float = 65.0
    season_name: str = "invierno_lluvioso" # "invierno_lluvioso" (May-Oct), "verano_seco" (Nov-Apr)

    def is_water_source_potable(self, source_name: str) -> bool:
        """Returns True if water source cleanliness exceeds potability threshold."""
        cleanliness = self.water_sources.get(source_name, 0.50)
        return cleanliness >= 0.55

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvironmentalHazardProfile":
        """Restore territorial state from a checkpoint dictionary."""
        profile = cls()
        profile.water_pollution_index = float(data.get("water_pollution_index", profile.water_pollution_index))
        if "water_sources" in data:
            profile.water_sources = {str(k): float(v) for k, v in data["water_sources"].items()}
        profile.air_quality_index = float(data.get("air_quality_index", profile.air_quality_index))
        profile.soil_degradation_index = float(data.get("soil_degradation_index", profile.soil_degradation_index))
        profile.accumulated_waste_kg = float(data.get("accumulated_waste_kg", profile.accumulated_waste_kg))
        profile.resource_depletion_level = float(data.get("resource_depletion_level", profile.resource_depletion_level))
        profile.flood_risk_level = float(data.get("flood_risk_level", profile.flood_risk_level))
        profile.landslide_risk_level = float(data.get("landslide_risk_level", profile.landslide_risk_level))
        profile.is_drought = bool(data.get("is_drought", profile.is_drought))
        profile.temperature_celsius = float(data.get("temperature_celsius", profile.temperature_celsius))
        profile.rainfall_mm_per_hour = float(data.get("rainfall_mm_per_hour", profile.rainfall_mm_per_hour))
        profile.humidity_pct = float(data.get("humidity_pct", profile.humidity_pct))
        profile.season_name = data.get("season_name", profile.season_name)
        return profile

    def to_dict(self) -> dict[str, Any]:
        return {
            "water_pollution_index": round(self.water_pollution_index, 2),
            "water_sources": {k: round(v, 2) for k, v in self.water_sources.items()},
            "air_quality_index": round(self.air_quality_index, 2),
            "soil_degradation_index": round(self.soil_degradation_index, 2),
            "accumulated_waste_kg": round(self.accumulated_waste_kg, 1),
            "resource_depletion_level": round(self.resource_depletion_level, 2),
            "flood_risk_level": round(self.flood_risk_level, 2),
            "landslide_risk_level": round(self.landslide_risk_level, 2),
            "is_drought": self.is_drought,
            "temperature_celsius": round(self.temperature_celsius, 1),
            "rainfall_mm_per_hour": round(self.rainfall_mm_per_hour, 1),
            "humidity_pct": round(self.humidity_pct, 1),
            "season_name": self.season_name,
        }
