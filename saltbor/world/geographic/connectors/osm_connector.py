"""
OpenStreetMap / Overpass Connector for Saltbor (Phase 0.8).

Compliant connector for OpenStreetMap (ODbL 1.0 license):
- Manages Overpass query generation for roads, amenities, and boundaries
- Provides local cached snapshot parser for offline operation
- Includes official OpenStreetMap attribution.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

OSM_ATTRIBUTION = "© OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)"


class OSMConnector:
    """OpenStreetMap connector with offline snapshot support and ODbL attribution."""

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, offline_snapshot_path: Optional[str] = None) -> None:
        self.offline_snapshot_path = offline_snapshot_path
        self._cached_elements: list[dict[str, Any]] = []

    def get_attribution(self) -> str:
        return OSM_ATTRIBUTION

    def build_overpass_query_for_district(self, district_name: str, amenity: str = "hospital") -> str:
        """Build an Overpass QL query string for a Salvadoran district."""
        return (
            f'[out:json][timeout:25];'
            f'area["name"="El Salvador"]["admin_level"="2"]->.sv;'
            f'area["name"="{district_name}"](area.sv)->.searchArea;'
            f'('
            f'  node["amenity"="{amenity}"](area.searchArea);'
            f'  way["amenity"="{amenity}"](area.searchArea);'
            f');'
            f'out center;'
        )

    def load_snapshot(self, geojson_data: dict[str, Any]) -> int:
        """Load an offline GeoJSON snapshot extracted from OSM."""
        features = geojson_data.get("features", [])
        self._cached_elements.extend(features)
        return len(features)
