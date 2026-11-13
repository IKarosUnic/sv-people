"""
Data models and provenance metadata for SALTBOR GIS-First World Foundation.

Separates:
1. REAL_WORLD_LAYER: Streets, building footprints, waterways, boundaries, parks.
2. SIMULATION_LAYER: Agents, simulated residences, businesses, movements, events.
3. RENDERING_LAYER: 2.5D extrusion parameters, shaders, camera views, sun lighting.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class LayerSystem(str, Enum):
    """The three fundamental geographic architectures."""
    REAL_WORLD_LAYER = "REAL_WORLD_LAYER"
    SIMULATION_LAYER = "SIMULATION_LAYER"
    RENDERING_LAYER = "RENDERING_LAYER"


class ValidationState(str, Enum):
    """
    Validation state according to Section 7:
    - VERIFIED_REAL: Ground-truth verified against official cadastre/IGN/ground surveys.
    - IMPORTED_UNVERIFIED: Ingested from external data source, pending on-site verification.
    - ESTIMATED: Statistically or typologically inferred (e.g. height from levels).
    - SIMULATED: Generated and maintained by the agent-based simulation dynamics.
    - GENERATED: Procedurally synthesized spatial layout.
    """
    VERIFIED_REAL = "VERIFIED_REAL"
    IMPORTED_UNVERIFIED = "IMPORTED_UNVERIFIED"
    ESTIMATED = "ESTIMATED"
    SIMULATED = "SIMULATED"
    GENERATED = "GENERATED"


@dataclasses.dataclass(frozen=True)
class ProvenanceMetadata:
    """Strict metadata tracking data provenance, licensing, and accuracy."""
    feature_id: str
    source: str
    fetch_date: str
    license: str
    known_accuracy: str
    validation_state: ValidationState
    geometry_type: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "source": self.source,
            "fetch_date": self.fetch_date,
            "license": self.license,
            "known_accuracy": self.known_accuracy,
            "validation_state": self.validation_state.value,
            "geometry_type": self.geometry_type,
            "notes": self.notes,
        }


@dataclasses.dataclass(frozen=True)
class BuildingProperties:
    """Attributes for 2.5D building extrusion and semantic classification."""
    feature_id: str
    osm_id: Optional[int]
    name: str
    building_type: str
    category: str
    height_m: float
    levels: int
    min_height_m: float = 0.0
    height_source: str = "inferred"
    provenance: Optional[ProvenanceMetadata] = None


@dataclasses.dataclass(frozen=True)
class StreetProperties:
    """Attributes for real street network alignment and routing."""
    feature_id: str
    osm_id: Optional[int]
    name: str
    road_type: str
    surface: str
    lanes: int
    oneway: bool
    maxspeed_kmh: int
    provenance: Optional[ProvenanceMetadata] = None


@dataclasses.dataclass
class PilotZoneManifest:
    """Metadata manifest of a delimited GIS pilot zone."""
    zone_id: str
    name: str
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    center_lat: float
    center_lon: float
    projection: str
    layers: Dict[str, Dict[str, Any]]
