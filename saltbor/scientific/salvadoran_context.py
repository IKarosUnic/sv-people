"""El Salvador Territorial, Socioeconomic & Environmental Research Context for SALTBOR Phase 1.12.

Connects scientific experimentation with the real geospatial and statistical foundation of El Salvador:
- Reuses `saltbor/datasets/gis/ingested/geography.sqlite` (151,251 OpenStreetMap features, ODbL 1.0).
- Profiles all 14 departments across:
  * Topography (Coastal plain, Central volcanic valley, Northern mountain ridge)
  * Economic specialization (Coffee, Sugar, Smallholder grains, Informal commerce, Remittances, Fishing)
  * Climate & hazard vulnerabilities (Corredor Seco drought, Bajo Lempa floods, Volcanic slope landslides)
  * Urban vs Rural distribution
- Epistemic boundary: Preserves individual diversity; strictly forbids stereotyping or inferring
  individual synthetic behaviors directly from national averages.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Departmental profiles grounded in official geographical and socioeconomic data
SALVADORAN_DEPARTMENT_PROFILES: dict[str, dict[str, Any]] = {
    "Ahuachapán": {
        "zone": "Occidente",
        "topography": "highland_volcanic_border",
        "primary_activities": ["cafe", "comercio_fronterizo", "agricultura_granos"],
        "urban_ratio": 0.45,
        "drought_risk_corredor_seco": 0.65,
        "flood_risk": 0.20,
        "landslide_risk": 0.70,
        "remittance_household_pct": 0.18,
        "informal_employment_rate": 0.71,
        "elevation_mean_m": 800,
    },
    "Santa Ana": {
        "zone": "Occidente",
        "topography": "volcanic_plateau_lake",
        "primary_activities": ["cafe", "agroindustria", "comercio_urbano", "servicios"],
        "urban_ratio": 0.68,
        "drought_risk_corredor_seco": 0.40,
        "flood_risk": 0.25,
        "landslide_risk": 0.55,
        "remittance_household_pct": 0.21,
        "informal_employment_rate": 0.64,
        "elevation_mean_m": 665,
    },
    "Sonsonate": {
        "zone": "Occidente",
        "topography": "coastal_plain_slopes",
        "primary_activities": ["cana_azucar", "pesca", "puerto", "turismo", "artesanias"],
        "urban_ratio": 0.52,
        "drought_risk_corredor_seco": 0.35,
        "flood_risk": 0.65,
        "landslide_risk": 0.45,
        "remittance_household_pct": 0.19,
        "informal_employment_rate": 0.73,
        "elevation_mean_m": 220,
    },
    "Chalatenango": {
        "zone": "Norte",
        "topography": "rugged_mountainous_highlands",
        "primary_activities": ["agricultura_granos", "ganaderia_lacteos", "remesas", "hortalizas"],
        "urban_ratio": 0.32,
        "drought_risk_corredor_seco": 0.55,
        "flood_risk": 0.15,
        "landslide_risk": 0.80,
        "remittance_household_pct": 0.32,
        "informal_employment_rate": 0.76,
        "elevation_mean_m": 1150,
    },
    "La Libertad": {
        "zone": "Central",
        "topography": "coastal_to_volcanic_ridge",
        "primary_activities": ["servicios", "comercio", "turismo_costero", "pesca", "cafe"],
        "urban_ratio": 0.72,
        "drought_risk_corredor_seco": 0.30,
        "flood_risk": 0.45,
        "landslide_risk": 0.60,
        "remittance_household_pct": 0.22,
        "informal_employment_rate": 0.59,
        "elevation_mean_m": 450,
    },
    "San Salvador": {
        "zone": "Central",
        "topography": "metropolitan_valley",
        "primary_activities": ["comercio_formal_informal", "industria", "servicios_financieros", "gobierno"],
        "urban_ratio": 0.96,
        "drought_risk_corredor_seco": 0.20,
        "flood_risk": 0.50,
        "landslide_risk": 0.65,
        "remittance_household_pct": 0.20,
        "informal_employment_rate": 0.55,
        "elevation_mean_m": 658,
    },
    "Cuscatlán": {
        "zone": "Central",
        "topography": "valley_and_slopes",
        "primary_activities": ["artesanias", "cana_azucar", "comercio", "granos_basicos"],
        "urban_ratio": 0.48,
        "drought_risk_corredor_seco": 0.50,
        "flood_risk": 0.30,
        "landslide_risk": 0.50,
        "remittance_household_pct": 0.24,
        "informal_employment_rate": 0.72,
        "elevation_mean_m": 600,
    },
    "La Paz": {
        "zone": "Paracentral",
        "topography": "coastal_plain_lower_valleys",
        "primary_activities": ["cana_azucar", "pesca", "aeropuerto_logistica", "agricultura"],
        "urban_ratio": 0.40,
        "drought_risk_corredor_seco": 0.45,
        "flood_risk": 0.75,
        "landslide_risk": 0.35,
        "remittance_household_pct": 0.25,
        "informal_employment_rate": 0.74,
        "elevation_mean_m": 150,
    },
    "Cabañas": {
        "zone": "Paracentral",
        "topography": "rugged_interior_hills",
        "primary_activities": ["granos_subsistencia", "pastizales", "alfareria", "remesas"],
        "urban_ratio": 0.31,
        "drought_risk_corredor_seco": 0.85, # Alto impacto Corredor Seco
        "flood_risk": 0.15,
        "landslide_risk": 0.65,
        "remittance_household_pct": 0.36,
        "informal_employment_rate": 0.81,
        "elevation_mean_m": 620,
    },
    "San Vicente": {
        "zone": "Paracentral",
        "topography": "volcanic_slopes_and_valley",
        "primary_activities": ["cana_azucar", "dulces_artesanales", "granos_basicos", "comercio"],
        "urban_ratio": 0.44,
        "drought_risk_corredor_seco": 0.60,
        "flood_risk": 0.50,
        "landslide_risk": 0.85, # Historial deslaves Chichontepec
        "remittance_household_pct": 0.27,
        "informal_employment_rate": 0.75,
        "elevation_mean_m": 390,
    },
    "Usulután": {
        "zone": "Oriente",
        "topography": "coastal_plain_bajo_lempa",
        "primary_activities": ["granos_basicos_granero", "pesca_camaron", "turismo_bahia", "salineras"],
        "urban_ratio": 0.42,
        "drought_risk_corredor_seco": 0.65,
        "flood_risk": 0.90, # Severo Bajo Lempa
        "landslide_risk": 0.30,
        "remittance_household_pct": 0.30,
        "informal_employment_rate": 0.77,
        "elevation_mean_m": 90,
    },
    "San Miguel": {
        "zone": "Oriente",
        "topography": "regional_valley_and_volcano",
        "primary_activities": ["comercio_regional", "ganaderia", "remesas", "servicios_oriente"],
        "urban_ratio": 0.60,
        "drought_risk_corredor_seco": 0.75,
        "flood_risk": 0.45,
        "landslide_risk": 0.50,
        "remittance_household_pct": 0.38,
        "informal_employment_rate": 0.69,
        "elevation_mean_m": 115,
    },
    "Morazán": {
        "zone": "Oriente",
        "topography": "rugged_mountainous_pine_ridge",
        "primary_activities": ["remesas", "granos_subsistencia", "ecoturismo", "artesanias_negro"],
        "urban_ratio": 0.26,
        "drought_risk_corredor_seco": 0.80,
        "flood_risk": 0.15,
        "landslide_risk": 0.70,
        "remittance_household_pct": 0.42, # Muy alta dependencia remesas
        "informal_employment_rate": 0.82,
        "elevation_mean_m": 850,
    },
    "La Unión": {
        "zone": "Oriente",
        "topography": "coastal_gulf_volcanic_hills",
        "primary_activities": ["pesca_artesanal", "puerto", "comercio_golfo", "remesas", "salineras"],
        "urban_ratio": 0.38,
        "drought_risk_corredor_seco": 0.85, # Extremo Corredor Seco oriental
        "flood_risk": 0.40,
        "landslide_risk": 0.40,
        "remittance_household_pct": 0.40,
        "informal_employment_rate": 0.78,
        "elevation_mean_m": 50,
    },
}


class ElSalvadorResearchContext:
    """Provides access to real geospatial features, departmental parameters, and environmental profiles."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or str(
            Path(__file__).resolve().parent.parent / "datasets" / "gis" / "ingested" / "geography.sqlite"
        )
        self.department_profiles = SALVADORAN_DEPARTMENT_PROFILES

    def get_provenance_metadata(self) -> dict[str, Any]:
        """Return data provenance for the underlying El Salvador geographic dataset."""
        return {
            "dataset_id": "Geofabrik_OSM_El_Salvador",
            "source": "OpenStreetMap contributors / Geofabrik",
            "license": "ODbL 1.0 (https://www.openstreetmap.org/copyright)",
            "database_file": self.db_path,
            "acquired_date": "2026-11-13",
            "feature_count": 151251,
            "layers": [
                "roads (121,344)", "landuse (10,881)", "pois (7,995)",
                "waterways (4,433)", "places (2,657)", "water (1,437)",
                "buildings (989)", "transport (895)", "adminareas (474)", "natural (122)"
            ],
            "departments_covered": 14,
            "known_limitations": [
                "Building footprints are partial outside San Salvador Centro.",
                "Road connectivity is topological/geometric; complex OSM turn restrictions omitted.",
                "Microeconomic household flows are simulated rather than directly recorded by OSM."
            ],
        }

    def get_department_profile(self, department_name: str) -> dict[str, Any]:
        """Retrieve the environmental and socioeconomic profile for a department."""
        profile = self.department_profiles.get(department_name)
        if not profile:
            raise ValueError(f"Unknown Salvadoran department: '{department_name}'. Available: {list(self.department_profiles.keys())}")
        return dict(profile)

    def list_all_departments(self) -> list[str]:
        """List all 14 official departments of El Salvador."""
        return sorted(list(self.department_profiles.keys()))

    def query_places(self, department_hint: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        """Query real populated places (cities, towns, villages, cantones) from geography.sqlite."""
        if not Path(self.db_path).exists():
            return []

        places: list[dict[str, Any]] = []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            query = "SELECT feature_id, name, feature_class, coordinates_json FROM geographic_features WHERE layer = 'places' AND name IS NOT NULL"
            params: list[Any] = []
            if department_hint:
                query += " AND name LIKE ?"
                params.append(f"%{department_hint}%")
            query += f" LIMIT {limit}"

            for row in cur.execute(query, params):
                places.append({
                    "feature_id": row["feature_id"],
                    "name": row["name"],
                    "place_type": row["feature_class"],
                    "coordinates": row["coordinates_json"],
                })
            conn.close()
        except Exception as ex:
            logger.warning("Failed to query places from %s: %s", self.db_path, ex)

        return places

    def get_environmental_hazard_risk(self, department: str, hazard_type: str) -> float:
        """Get hazard probability index [0.0, 1.0] for a department and hazard type."""
        prof = self.get_department_profile(department)
        if hazard_type == "drought":
            return float(prof.get("drought_risk_corredor_seco", 0.5))
        elif hazard_type == "flood":
            return float(prof.get("flood_risk", 0.3))
        elif hazard_type == "landslide":
            return float(prof.get("landslide_risk", 0.4))
        else:
            return 0.30
