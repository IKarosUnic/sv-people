"""
Geographic Information System (GIS) Engine for SALTBOR.

Provides:
- Zonal loading and memory caching of real-world cartographic layers
- High-performance spatial indexing using Shapely STRtree
- Point-in-polygon containment checks (finding building or district for an agent)
- Nearest road / street snapping
- Separation between REAL_WORLD_LAYER and SIMULATION_LAYER
- 100% offline self-containment with sub-millisecond query latencies
"""

from __future__ import annotations
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import shapely.geometry
from shapely.strtree import STRtree

from saltbor.world.gis.models import (
    LayerSystem,
    PilotZoneManifest,
    ProvenanceMetadata,
    ValidationState,
)

logger = logging.getLogger(__name__)


class GISEngine:
    """Core GIS Engine managing real cartographic layers and spatial queries."""

    def __init__(self, data_root: Optional[str] = None) -> None:
        if data_root is None:
            # Default to saltbor/datasets/gis
            data_root = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "datasets",
                "gis",
            )
        self.data_root = data_root

        # In-memory layer caches: {zone_id: {layer_name: GeoJSON dict}}
        self._layer_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Spatial indexes: {zone_id: {layer_name: (STRtree, list of geometries, list of features)}}
        self._spatial_indexes: Dict[str, Dict[str, Tuple[STRtree, List[shapely.geometry.base.BaseGeometry], List[Dict[str, Any]]]]] = {}

        # Manifests: {zone_id: PilotZoneManifest}
        self._manifests: Dict[str, PilotZoneManifest] = {}

        self._preload_available_zones()

    def _preload_available_zones(self) -> None:
        """Discover and load metadata for all available geographic zones."""
        if not os.path.exists(self.data_root):
            logger.warning("GIS data root does not exist: %s", self.data_root)
            return

        for entry in os.listdir(self.data_root):
            zone_path = os.path.join(self.data_root, entry)
            if os.path.isdir(zone_path):
                manifest_file = os.path.join(zone_path, "manifest.json")
                if os.path.exists(manifest_file):
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            bbox = data.get("bbox", {})
                            manifest = PilotZoneManifest(
                                zone_id=data.get("zone_id", entry),
                                name=data.get("name", entry),
                                min_lat=bbox.get("min_lat", 13.693),
                                min_lon=bbox.get("min_lon", -89.202),
                                max_lat=bbox.get("max_lat", 13.704),
                                max_lon=bbox.get("max_lon", -89.186),
                                center_lat=bbox.get("center_lat", 13.6978),
                                center_lon=bbox.get("center_lon", -89.1915),
                                projection=data.get("projection", "EPSG:4326"),
                                layers=data.get("layers", {}),
                            )
                            self._manifests[manifest.zone_id] = manifest
                            logger.info("Loaded GIS Zone Manifest: %s (%s)", manifest.zone_id, manifest.name)
                    except Exception as e:
                        logger.error("Failed to parse manifest for %s: %e", entry, e)

    def list_zones(self) -> List[Dict[str, Any]]:
        """Return summary of all registered zones."""
        return [
            {
                "zone_id": m.zone_id,
                "name": m.name,
                "bbox": {
                    "min_lat": m.min_lat,
                    "min_lon": m.min_lon,
                    "max_lat": m.max_lat,
                    "max_lon": m.max_lon,
                    "center_lat": m.center_lat,
                    "center_lon": m.center_lon,
                },
                "projection": m.projection,
                "layers": list(m.layers.keys()),
            }
            for m in self._manifests.values()
        ]

    def get_manifest(self, zone_id: str) -> Optional[PilotZoneManifest]:
        """Get manifest for a specific zone."""
        return self._manifests.get(zone_id)

    def get_layer(
        self,
        zone_id: str,
        layer_name: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a GeoJSON layer for a zone.
        Optionally filter features by bounding box (min_lon, min_lat, max_lon, max_lat).
        """
        if zone_id not in self._layer_cache:
            self._layer_cache[zone_id] = {}

        if layer_name not in self._layer_cache[zone_id]:
            # Load from file
            file_name = f"{layer_name}.geojson"
            file_path = os.path.join(self.data_root, zone_id, file_name)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"GIS layer {layer_name} not found in zone {zone_id} ({file_path})")

            with open(file_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
                self._layer_cache[zone_id][layer_name] = geojson_data
                self._build_spatial_index(zone_id, layer_name, geojson_data)

        full_geojson = self._layer_cache[zone_id][layer_name]

        if bbox is None:
            return full_geojson

        # Filter features using spatial index if available
        min_lon, min_lat, max_lon, max_lat = bbox
        bbox_geom = shapely.geometry.box(min_lon, min_lat, max_lon, max_lat)

        if zone_id in self._spatial_indexes and layer_name in self._spatial_indexes[zone_id]:
            tree, geoms, feats = self._spatial_indexes[zone_id][layer_name]
            matching_indices = tree.query(bbox_geom)
            filtered_features = [feats[idx] for idx in matching_indices]
        else:
            filtered_features = [
                f for f in full_geojson.get("features", [])
                if self._feature_intersects_bbox(f, bbox_geom)
            ]

        return {
            "type": "FeatureCollection",
            "name": f"{full_geojson.get('name', layer_name)}_filtered",
            "crs": full_geojson.get("crs"),
            "metadata": {
                **full_geojson.get("metadata", {}),
                "filtered": True,
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "feature_count": len(filtered_features),
            },
            "features": filtered_features,
        }

    def _build_spatial_index(
        self,
        zone_id: str,
        layer_name: str,
        geojson_data: Dict[str, Any],
    ) -> None:
        """Construct Shapely STRtree for ultra-fast spatial search."""
        if zone_id not in self._spatial_indexes:
            self._spatial_indexes[zone_id] = {}

        features = geojson_data.get("features", [])
        geoms: List[shapely.geometry.base.BaseGeometry] = []
        valid_features: List[Dict[str, Any]] = []

        for feat in features:
            geom_data = feat.get("geometry")
            if not geom_data:
                continue
            try:
                g = shapely.geometry.shape(geom_data)
                if not g.is_valid:
                    g = g.buffer(0)
                geoms.append(g)
                valid_features.append(feat)
            except Exception as e:
                logger.debug("Skipping invalid geometry in %s: %s", feat.get("id"), e)

        if geoms:
            tree = STRtree(geoms)
            self._spatial_indexes[zone_id][layer_name] = (tree, geoms, valid_features)
            logger.info("Built spatial STRtree for %s/%s (%d features)", zone_id, layer_name, len(geoms))

    def _feature_intersects_bbox(self, feature: Dict[str, Any], bbox_geom: shapely.geometry.base.BaseGeometry) -> bool:
        geom = feature.get("geometry")
        if not geom:
            return False
        try:
            return shapely.geometry.shape(geom).intersects(bbox_geom)
        except Exception:
            return False

    def find_containing_building(
        self,
        zone_id: str,
        lat: float,
        lon: float,
    ) -> Optional[Dict[str, Any]]:
        """Return the building polygon containing the given WGS84 point."""
        point = shapely.geometry.Point(lon, lat)
        self.get_layer(zone_id, "buildings")  # Ensure loaded & indexed

        if zone_id in self._spatial_indexes and "buildings" in self._spatial_indexes[zone_id]:
            tree, geoms, feats = self._spatial_indexes[zone_id]["buildings"]
            candidate_indices = tree.query(point)
            for idx in candidate_indices:
                if geoms[idx].contains(point):
                    return feats[idx]
        return None

    def find_nearest_street(
        self,
        zone_id: str,
        lat: float,
        lon: float,
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """Return (nearest_street_feature, distance_in_degrees)."""
        point = shapely.geometry.Point(lon, lat)
        self.get_layer(zone_id, "streets")  # Ensure loaded & indexed

        if zone_id in self._spatial_indexes and "streets" in self._spatial_indexes[zone_id]:
            tree, geoms, feats = self._spatial_indexes[zone_id]["streets"]
            nearest_idx = tree.nearest(point)
            if nearest_idx is not None:
                dist = geoms[nearest_idx].distance(point)
                return (feats[nearest_idx], dist)
        return None

    def get_building_by_id(self, zone_id: str, building_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve building feature details by its feature_id or osm_id."""
        bldgs = self.get_layer(zone_id, "buildings").get("features", [])
        for b in bldgs:
            props = b.get("properties", {})
            if props.get("feature_id") == building_id or str(props.get("osm_id")) == str(building_id):
                return b
        return None


# Global singleton instance
_gis_engine: Optional[GISEngine] = None


def get_gis_engine() -> GISEngine:
    """Return initialized GISEngine singleton."""
    global _gis_engine
    if _gis_engine is None:
        _gis_engine = GISEngine()
    return _gis_engine
