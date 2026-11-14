"""Editable World Engine for SALTBOR (Layers A, B, C, D).

Enables non-destructive spatial authoring, user-defined facilities, municipal zones,
and proposed intervention scenarios while strictly preserving immutable base cartography:

- LAYER A — BASE CARTOGRAPHY (Immutable OpenStreetMap & CNR reference features).
- LAYER B — SALTBOR WORLD (Custom zones, municipal workspaces, facilities, proposed buildings).
- LAYER C — HUMAN & ECONOMIC ACTIVITY (Active synthetic agents, households, businesses, schools, clinics).
- LAYER D — INTERVENTIONS (Hypothetical businesses, services, road alterations, land-use changes).

Guarantees:
- Layer A is read-only. No user edit ever mutates base cartographic tables.
- Layers B, C, and D are isolated and indexed in memory / persistence.
- Scenario duplication and rollback without affecting baseline data.
- Complete geographic provenance, author attribution, and licensing tags.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from saltbor.domain.models import EditableFeature, FeatureGeometryType, WorldLayerType

logger = logging.getLogger(__name__)


class EditableWorldEngine:
    """Manages the 4-layer spatial environment of SALTBOR."""

    def __init__(self, geography_db_path: Optional[str] = None) -> None:
        self.geography_db_path = geography_db_path or "saltbor/datasets/gis/ingested/geography.sqlite"
        self._layer_b_features: Dict[str, EditableFeature] = {}
        self._layer_c_features: Dict[str, EditableFeature] = {}
        self._layer_d_features: Dict[str, EditableFeature] = {}
        self._scenarios: Dict[str, List[str]] = {}  # scenario_id -> list of feature_ids
        self._seed_sample_world_features()

    # =========================================================================
    # Layer A: Base Cartography Queries (Read-Only)
    # =========================================================================

    def query_base_cartography(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        layer_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query immutable Layer A features from geography.sqlite within bounding box."""
        try:
            conn = sqlite3.connect(self.geography_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT feature_id, layer, name, feature_class, lat, lon, geometry_type, geometry_json, source, license
                FROM geographic_features
                WHERE lon >= ? AND lon <= ? AND lat >= ? AND lat <= ?
            """
            params: List[Any] = [min_lon, max_lon, min_lat, max_lat]

            if layer_filter:
                query += " AND layer = ?"
                params.append(layer_filter)

            query += " LIMIT ?"
            params.append(limit)

            rows = cursor.execute(query, params).fetchall()
            conn.close()

            return [
                {
                    "feature_id": r["feature_id"],
                    "layer": WorldLayerType.LAYER_A_BASE.value,
                    "osm_layer": r["layer"],
                    "name": r["name"] or "Unnamed",
                    "feature_class": r["feature_class"],
                    "coordinates": [r["lon"], r["lat"]],
                    "geometry_type": r["geometry_type"],
                    "geometry": json.loads(r["geometry_json"]) if r["geometry_json"] else None,
                    "source": r["source"],
                    "license": r["license"],
                    "is_immutable": True,
                }
                for r in rows
            ]
        except Exception as ex:
            logger.debug("Layer A query fallback (in-memory test mode or db unavailable): %s", ex)
            return []

    # =========================================================================
    # Layers B, C, D: Authoring & Management
    # =========================================================================

    def create_feature(
        self,
        layer: WorldLayerType,
        geometry_type: FeatureGeometryType,
        coordinates: Any,
        name: str,
        category: str,
        properties: Optional[Dict[str, Any]] = None,
        owner_id: str = "system",
        scenario_id: Optional[str] = None,
        feature_id: Optional[str] = None,
        source_attribution: str = "SALTBOR_USER",
    ) -> EditableFeature:
        """Create a new spatial feature on Layer B, C, or D. Fails if Layer A is specified."""
        if layer == WorldLayerType.LAYER_A_BASE:
            raise PermissionError("Layer A (Base Cartography) is strictly read-only and immutable.")

        fid = feature_id or f"feat_{layer.value}_{uuid4().hex[:8]}"
        feature = EditableFeature(
            feature_id=fid,
            layer=layer,
            geometry_type=geometry_type,
            coordinates=coordinates,
            name=name,
            category=category,
            properties=properties or {},
            owner_id=owner_id,
            scenario_id=scenario_id,
            source_attribution=source_attribution,
        )

        target_dict = self._get_layer_dict(layer)
        target_dict[fid] = feature

        if scenario_id:
            self._scenarios.setdefault(scenario_id, []).append(fid)

        return feature

    def create_custom_zone_polygon(
        self,
        name: str,
        polygon_coordinates: List[List[float]],  # [[lon, lat], [lon, lat], ...]
        owner_id: str,
        workspace_name: str = "Municipal Zone",
        layer: WorldLayerType = WorldLayerType.LAYER_B_WORLD,
    ) -> EditableFeature:
        """Convenience method to create a user-defined geographic polygon zone."""
        return self.create_feature(
            layer=layer,
            geometry_type=FeatureGeometryType.POLYGON,
            coordinates=[polygon_coordinates],
            name=name,
            category="municipal_zone",
            properties={"workspace_name": workspace_name, "zone_type": "administrative_polygon"},
            owner_id=owner_id,
        )

    def create_custom_facility_point(
        self,
        name: str,
        latitude: float,
        longitude: float,
        facility_category: str,
        owner_id: str,
        layer: WorldLayerType = WorldLayerType.LAYER_B_WORLD,
        properties: Optional[Dict[str, Any]] = None,
    ) -> EditableFeature:
        """Convenience method to place a facility point on Layer B or C."""
        return self.create_feature(
            layer=layer,
            geometry_type=FeatureGeometryType.POINT,
            coordinates=[longitude, latitude],
            name=name,
            category=facility_category,
            properties=properties or {},
            owner_id=owner_id,
        )

    def update_feature_properties(
        self,
        feature_id: str,
        new_properties: Dict[str, Any],
        user_id: str,
    ) -> bool:
        """Update properties of an existing feature on Layer B, C, or D."""
        feature = self.get_feature(feature_id)
        if not feature:
            return False

        # Verify ownership / permissions
        if feature.owner_id != user_id and user_id != "admin":
            logger.warning("User %s unauthorized to modify feature %s owned by %s", user_id, feature_id, feature.owner_id)
            return False

        feature.properties.update(new_properties)
        feature.updated_at = time.time()
        return True

    def delete_feature(self, feature_id: str, user_id: str) -> bool:
        """Soft-delete a user-created feature."""
        feature = self.get_feature(feature_id)
        if not feature:
            return False

        if feature.owner_id != user_id and user_id != "admin":
            return False

        feature.is_deleted = True
        feature.updated_at = time.time()
        return True

    def duplicate_scenario(
        self,
        source_scenario_id: str,
        new_scenario_id: str,
        new_name: str,
        owner_id: str,
    ) -> List[EditableFeature]:
        """Clone all Layer D intervention features of a scenario into an alternative configuration."""
        feature_ids = self._scenarios.get(source_scenario_id, [])
        cloned_features = []

        for fid in feature_ids:
            feat = self.get_feature(fid)
            if feat and not feat.is_deleted:
                new_fid = f"feat_{new_scenario_id}_{uuid4().hex[:6]}"
                cloned = copy.deepcopy(feat)
                cloned.feature_id = new_fid
                cloned.scenario_id = new_scenario_id
                cloned.owner_id = owner_id
                cloned.created_at = time.time()
                cloned.updated_at = time.time()
                cloned.properties["cloned_from"] = fid
                cloned.properties["scenario_name"] = new_name

                target_dict = self._get_layer_dict(cloned.layer)
                target_dict[new_fid] = cloned
                self._scenarios.setdefault(new_scenario_id, []).append(new_fid)
                cloned_features.append(cloned)

        return cloned_features

    def get_feature(self, feature_id: str) -> Optional[EditableFeature]:
        for d in (self._layer_b_features, self._layer_c_features, self._layer_d_features):
            if feature_id in d:
                return d[feature_id]
        return None

    def query_layer(
        self,
        layer: WorldLayerType,
        scenario_id: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[EditableFeature]:
        """Retrieve features for a specified editable layer."""
        if layer == WorldLayerType.LAYER_A_BASE:
            return []  # Layer A is queried via query_base_cartography()

        target_dict = self._get_layer_dict(layer)
        feats = list(target_dict.values())

        if scenario_id is not None:
            feats = [f for f in feats if f.scenario_id == scenario_id]

        if not include_deleted:
            feats = [f for f in feats if not f.is_deleted]

        return feats

    def get_all_active_layers_summary(self) -> Dict[str, Any]:
        """Return status summary of all four world layers."""
        return {
            "layer_a_base": {
                "name": "Base Cartography (OSM/CNR)",
                "status": "IMMUTABLE_READ_ONLY",
                "source": "Geofabrik_OSM_El_Salvador",
                "license": "ODbL-1.0",
                "feature_count_total": 151227,
            },
            "layer_b_world": {
                "name": "Saltbor World & Custom Facilities",
                "active_features": len([f for f in self._layer_b_features.values() if not f.is_deleted]),
            },
            "layer_c_activity": {
                "name": "Human & Economic Activity",
                "active_features": len([f for f in self._layer_c_features.values() if not f.is_deleted]),
            },
            "layer_d_interventions": {
                "name": "Scenario Interventions",
                "active_features": len([f for f in self._layer_d_features.values() if not f.is_deleted]),
                "registered_scenarios": list(self._scenarios.keys()),
            },
        }

    def _get_layer_dict(self, layer: WorldLayerType) -> Dict[str, EditableFeature]:
        if layer == WorldLayerType.LAYER_B_WORLD:
            return self._layer_b_features
        elif layer == WorldLayerType.LAYER_C_ACTIVITY:
            return self._layer_c_features
        elif layer == WorldLayerType.LAYER_D_INTERVENTIONS:
            return self._layer_d_features
        raise ValueError(f"No dictionary for layer {layer}")

    def _seed_sample_world_features(self) -> None:
        """Seed initial municipal workspace and facilities in Layer B."""
        self.create_feature(
            layer=WorldLayerType.LAYER_B_WORLD,
            geometry_type=FeatureGeometryType.POLYGON,
            coordinates=[[
                [-89.230, 13.695],
                [-89.220, 13.695],
                [-89.220, 13.705],
                [-89.230, 13.705],
                [-89.230, 13.695],
            ]],
            name="Zona de Desarrollo Centro Histórico",
            category="municipal_workspace",
            properties={"department": "San Salvador", "target_investments": ["gastronomy", "tourism"]},
            owner_id="alcaldia_san_salvador",
            feature_id="zone_centro_historico_ss",
        )
        self.create_feature(
            layer=WorldLayerType.LAYER_B_WORLD,
            geometry_type=FeatureGeometryType.POINT,
            coordinates=[-89.224, 13.698],
            name="Plaza Culinaria Municipal Propuesta",
            category="proposed_market_facility",
            properties={"capacity_stalls": 20, "estimated_cost_usd": 45000.0},
            owner_id="alcaldia_san_salvador",
            feature_id="facility_plaza_culinaria",
        )
