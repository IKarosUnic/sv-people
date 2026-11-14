"""
Simulation Adapter for SALTBOR GIS-First Foundation.

Projects synthetic agents, simulated residences, businesses, and dynamic movements
onto real-world coordinates in the San Salvador Centro pilot zone.

Maintains strict separation between:
- REAL_WORLD_LAYER (immutable cartography)
- SIMULATION_LAYER (dynamic synthetic entities with validation_state = SIMULATED)
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

from saltbor.simulation.runner import SimulationRunner


# Mapping of simulation location IDs to verified real-world WGS84 coordinates in San Salvador Centro
LOCATION_WGS84_ANCHORS: Dict[str, Tuple[float, float, str]] = {
    "plaza_central": (13.6978, -89.1915, "Plaza Gerardo Barrios (Cívica Central)"),
    "comedor_dona_maria": (13.6980, -89.1925, "Portal de Occidente / Calle Rubén Darío"),
    "mercado_central": (13.6948, -89.1952, "Mercado Central de San Salvador (Edificio 4)"),
    "taller_artesanal": (13.6965, -89.1885, "Taller de Oficios Barrio San Esteban"),
    "escuela_comunal": (13.6988, -89.1895, "Escuela República de Costa Rica / Calle Delgado"),
    "clinica_salud": (13.7018, -89.2010, "Complejo de Salud Hospital Rosales / Calle Arce"),
    "binaes_estudio": (13.6975, -89.1905, "Biblioteca Nacional BINAES (Piso 3)"),
    "palacio_trabajo": (13.6979, -89.1923, "Palacio Nacional (Salón de Honor)"),
    "teatro_cultural": (13.6985, -89.1900, "Teatro Nacional (Gran Sala)"),
    "cafetal_santa_anita": (13.6935, -89.1980, "Vivero y Huerto Urbano Santa Anita"),
    "casa_norte_1": (13.7020, -89.1915, "Vivienda Residencial Barrio San Miguelito #12"),
    "casa_norte_2": (13.7005, -89.1940, "Casa Colonial 1ª Calle Poniente #24"),
    "casa_sur_1": (13.6940, -89.1910, "Residencia Barrio La Vega #8"),
    "casa_sur_2": (13.6935, -89.1960, "Vivienda Familiar Barrio Santa Anita #45"),
    "casa_este_1": (13.6970, -89.1870, "Casa Barrio Concepción #33"),
    "casa_oeste_1": (13.6990, -89.2010, "Edificio Residencial Alameda Roosevelt #102"),
    "casa_residencial_1": (13.7000, -89.1930, "Casa Residencial Centro Histórico"),
}


def get_anchor_point(loc_id: str, default: Tuple[float, float, str] = (13.6978, -89.1915, "Plaza Barrios")) -> Tuple[float, float, str]:
    """Retrieve WGS84 (lat, lon, label) for a simulation location ID."""
    if loc_id in LOCATION_WGS84_ANCHORS:
        return LOCATION_WGS84_ANCHORS[loc_id]
    for key, anchor in LOCATION_WGS84_ANCHORS.items():
        if key in loc_id:
            return anchor
    return default


class SimulationGISAdapter:
    """Translates dynamic simulation runner state into GeoJSON SIMULATION_LAYER."""

    def __init__(self, runner: Optional[SimulationRunner] = None) -> None:
        self.runner = runner

    def build_simulation_layer(self, current_tick: int) -> Dict[str, Any]:
        """
        Generate GeoJSON FeatureCollection containing all dynamic simulated entities:
        - Individuals (Point features with coordinates, orientation, activity, pulse)
        - Movement vectors (LineString features for traveling agents)
        - Occupied habitats & workplaces (Polygon / Point references)
        """
        if self.runner is None or self.runner.population is None:
            return {
                "type": "FeatureCollection",
                "name": "saltbor_simulation_layer_empty",
                "features": []
            }

        features: List[Dict[str, Any]] = []
        humans = self.runner.population.get_all()

        # Group agents per location for gentle radial dispersion so they don't overlap completely
        location_clusters: Dict[str, List[Any]] = {}
        for h in humans:
            loc = h.physical_state.current_location_id or "plaza_central"
            location_clusters.setdefault(loc, []).append(h)

        for loc_id, cluster_humans in location_clusters.items():
            base_lat, base_lon, loc_label = get_anchor_point(loc_id)
            count = len(cluster_humans)

            for idx, h in enumerate(cluster_humans):
                uid_str = str(h.uid)
                activity = h.physical_state.current_activity.value if h.physical_state.current_activity else "idle"
                is_traveling = activity == "travel"

                # Uniform disc dispersion (Fermat golden angle) bounded strictly to location footprint (~25m max)
                if count > 1:
                    golden_angle = 2.399963229728653  # pi * (3 - sqrt(5))
                    angle = idx * golden_angle
                    # Bounded radius: compact cluster inside building/plaza, maximum ~0.00025 deg (~28m)
                    radius_deg = min(0.00025, 0.000035 * math.sqrt(idx + 1))

                    # Micro-movement per tick so agents don't appear frozen like statues
                    uid_hash = abs(hash(uid_str)) % 1000 / 1000.0
                    drift_phase = current_tick * 0.25 + uid_hash * 6.283
                    drift_x = 0.000012 * math.cos(drift_phase)
                    drift_y = 0.000012 * math.sin(drift_phase)

                    agent_lat = base_lat + math.sin(angle) * radius_deg + drift_y
                    agent_lon = base_lon + math.cos(angle) * radius_deg + drift_x
                else:
                    agent_lat = base_lat
                    agent_lon = base_lon

                # If traveling, interpolate towards destination
                dest_loc_id = getattr(h.physical_state, "target_location_id", None) or "plaza_central"
                dest_lat, dest_lon, dest_label = get_anchor_point(dest_loc_id)

                # Check if integrated transportation engine has high-fidelity street trajectory
                integrated_w = getattr(self.runner, "integrated_world", None)
                active_j = None
                if integrated_w and hasattr(integrated_w, "transportation"):
                    active_j = integrated_w.transportation.active_journeys.get(uid_str)

                if active_j and active_j.status.value == "in_progress":
                    is_traveling = True
                    agent_lat, agent_lon = active_j.current_coordinate
                    vec_id = f"sim_vector_{uid_str[:8]}_{current_tick}"
                    poly_coords = (
                        [[p_lon, p_lat] for p_lat, p_lon in active_j.polyline]
                        if active_j.polyline
                        else [[base_lon, base_lat], [agent_lon, agent_lat], [dest_lon, dest_lat]]
                    )
                    features.append({
                        "type": "Feature",
                        "id": vec_id,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": poly_coords,
                        },
                        "properties": {
                            "feature_id": vec_id,
                            "layer_system": "SIMULATION_LAYER",
                            "agent_uid": uid_str,
                            "agent_name": h.identity.full_name,
                            "origin_location": loc_label,
                            "destination_location": dest_label,
                            "activity": "travel",
                            "mode": active_j.mode.value,
                            "progress_ratio": round(active_j.progress_ratio, 3),
                            "distance_km": round(active_j.total_distance_km, 3),
                            "validation_state": "SIMULATED",
                            "source": "SALTBOR_SIMULATION",
                            "license": "SALTBOR_AGENT_STATE",
                            "known_accuracy": "sub-meter",
                        }
                    })
                elif is_traveling:
                    ticks_rem = getattr(h.physical_state, "activity_ticks_remaining", 1)
                    progress = 0.5  # Midpoint during travel tick
                    agent_lat = base_lat + (dest_lat - base_lat) * progress
                    agent_lon = base_lon + (dest_lon - base_lon) * progress

                    # Add movement vector LineString
                    vec_id = f"sim_vector_{uid_str[:8]}_{current_tick}"
                    features.append({
                        "type": "Feature",
                        "id": vec_id,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [base_lon, base_lat],
                                [agent_lon, agent_lat],
                                [dest_lon, dest_lat],
                            ]
                        },
                        "properties": {
                            "feature_id": vec_id,
                            "layer_system": "SIMULATION_LAYER",
                            "agent_uid": uid_str,
                            "agent_name": h.identity.full_name,
                            "origin_location": loc_label,
                            "destination_location": dest_label,
                            "activity": "travel",
                            "validation_state": "SIMULATED",
                            "source": "SALTBOR_SIMULATION",
                            "license": "SALTBOR_AGENT_STATE",
                            "known_accuracy": "sub-meter",
                        }
                    })

                # Individual Point Feature
                goal_desc = "Mantenimiento diario"
                active_goals = h.autonomy.get_active_goals() if hasattr(h.autonomy, "get_active_goals") else []
                if active_goals:
                    goal_desc = active_goals[0].description

                feat = {
                    "type": "Feature",
                    "id": f"sim_agent_{uid_str}",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [agent_lon, agent_lat]
                    },
                    "properties": {
                        "feature_id": f"sim_agent_{uid_str}",
                        "layer_system": "SIMULATION_LAYER",
                        "uid": uid_str,
                        "serial": h.identity.serial,
                        "full_name": h.identity.full_name,
                        "age": h.demographics.age,
                        "gender": h.demographics.gender.value if hasattr(h.demographics.gender, "value") else str(h.demographics.gender),
                        "occupation": h.demographics.occupation,
                        "current_location_id": loc_id,
                        "current_location_name": loc_label,
                        "activity": activity,
                        "energy": round(h.physical_state.energy, 2),
                        "hunger": round(h.physical_state.hunger, 2),
                        "money": round(h.physical_state.money, 2),
                        "morale": round(h.emotions.get_mood(), 2) if hasattr(h.emotions, "get_mood") else 0.0,
                        "active_goal": goal_desc,
                        "is_traveling": is_traveling,
                        "validation_state": "SIMULATED",
                        "source": "SALTBOR_SIMULATION",
                        "license": "SALTBOR_AGENT_STATE",
                        "known_accuracy": "sub-meter",
                    }
                }
                features.append(feat)

        # Include active road blockages (hazards, floods, landslides)
        integrated_w = getattr(self.runner, "integrated_world", None)
        if integrated_w and hasattr(integrated_w, "transportation"):
            for b in integrated_w.transportation.blockages:
                features.append({
                    "type": "Feature",
                    "id": f"sim_blockage_{b.road_id}",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [b.lon, b.lat],
                    },
                    "properties": {
                        "feature_id": f"sim_blockage_{b.road_id}",
                        "layer_system": "SIMULATION_LAYER",
                        "hazard_type": "road_blockage",
                        "cause": b.cause,
                        "location_name": b.location_name,
                        "severity": b.severity,
                        "passable": b.passable,
                        "validation_state": "SIMULATED",
                        "source": "SALTBOR_SIMULATION",
                        "license": "SALTBOR_AGENT_STATE",
                    },
                })

        return {
            "type": "FeatureCollection",
            "name": f"saltbor_simulation_layer_tick_{current_tick}",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "metadata": {
                "tick": current_tick,
                "agent_count": len(humans),
                "layer_system": "SIMULATION_LAYER",
                "validation_state": "SIMULATED",
                "zone_id": "san_salvador_centro",
            },
            "features": features
        }
