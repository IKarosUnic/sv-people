"""
CNR (Centro Nacional de Registros de El Salvador) Map Viewer Connector (Phase 0.8).

Connects to the official cartographic metadata of El Salvador:
Viewer reference: https://mapa.elsalvadormaps.sv/cnr/map/4

Technical Architecture:
- Platform: eCarto / CartoData web mapping infrastructure
- Official Projection: SIRGAS ES2007 (Lambert Conformal Conic, EPSG:5379 equivalent)
- Distribution format: Tiled Web Maps (XYZ raster tiles) & UTFGrid interaction layers
- 95 layers registered, including official administrative boundaries (Layers 91-94)
- Full legal disclaimer and terms compliance: No private endpoints, no unauthorized scraping.
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass(frozen=True)
class CNRLayerMetadata:
    layer_id: int
    name: str
    layer_type: str
    tile_url_pattern: str
    subdomains: tuple[str, ...]
    min_zoom: int
    max_zoom: int
    is_administrative: bool = False
    description: str = ""


# Official SIRGAS ES2007 Projection Parameters as published by CNR
CNR_SIRGAS_ES2007_PROJ4 = (
    "+proj=lcc +lat_0=13.78429934 +lon_0=-88.99998297 "
    "+lat_1=13.3176326733333 +lat_2=14.2509660066667 "
    "+x_0=500000 +y_0=295809.184 +ellps=GRS80 "
    "+towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs"
)

CNR_LEGAL_BORDER_DISCLAIMER = (
    "El trazo del límite de la frontera internacional terrestre con la República de Honduras, "
    "delimitado por el Tratado General de Paz del 30 de octubre de 1980 y por la Corte Internacional "
    "de Justicia el 11 de septiembre de 1992, no es oficial, al no haberse concluido formalmente "
    "el proceso de demarcación terrestre entre ambos Estados."
)


class CNRConnector:
    """Client and metadata catalog for Centro Nacional de Registros cartography."""

    VIEWER_BASE_URL = "https://mapa.elsalvadormaps.sv"
    MAP_ID = 4

    def __init__(self) -> None:
        self._layers: dict[int, CNRLayerMetadata] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Register officially discovered public layers in the CNR viewer."""
        # Key administrative and territorial reference layers
        self._layers[91] = CNRLayerMetadata(
            layer_id=91,
            name="Islas de El Salvador",
            layer_type="tile_utfgrid",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/hlyy38j2-33dda8d1c0e03ebb17da5a68871388bc4d5a2ce6/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3", "ec4", "ec5", "ec6", "ec7", "ec8", "ec9"),
            min_zoom=12,
            max_zoom=22,
            is_administrative=True,
            description="Islas costeras e insulares del Golfo de Fonseca y Bahía de Jiquilisco.",
        )
        self._layers[92] = CNRLayerMetadata(
            layer_id=92,
            name="Límites_Distritales",
            layer_type="tile",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/hlyy38j2-4b03ddb922c6bd630a693cf4e474c7dac7dbb4ac/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3", "ec4", "ec5", "ec6", "ec7", "ec8", "ec9"),
            min_zoom=0,
            max_zoom=22,
            is_administrative=True,
            description="Delimitación de los 262 distritos según reestructuración municipal.",
        )
        self._layers[93] = CNRLayerMetadata(
            layer_id=93,
            name="Límites_Municipales",
            layer_type="tile",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/hlyy38j2-b3f59eb00f27bba031ef2cdc6bb7c4c636e44cb1/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3", "ec4", "ec5", "ec6", "ec7", "ec8", "ec9"),
            min_zoom=0,
            max_zoom=22,
            is_administrative=True,
            description="Delimitación de los 44 municipios vigentes desde mayo 2024.",
        )
        self._layers[94] = CNRLayerMetadata(
            layer_id=94,
            name="Límites_Departamentales",
            layer_type="tile",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/hlyy38j2-2688b39e6a0c7580f4f62bf248941629d1564c3c/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3", "ec4", "ec5", "ec6", "ec7", "ec8", "ec9"),
            min_zoom=0,
            max_zoom=22,
            is_administrative=True,
            description="Límites de los 14 departamentos de la República.",
        )
        self._layers[16] = CNRLayerMetadata(
            layer_id=16,
            name="BINAES",
            layer_type="vant_drone",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/binaes/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3"),
            min_zoom=14,
            max_zoom=22,
            description="Ortofoto de alta resolución de la Biblioteca Nacional de El Salvador.",
        )
        self._layers[20] = CNRLayerMetadata(
            layer_id=20,
            name="Hospital Zacamil - VANT",
            layer_type="vant_drone",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/zacamil/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3"),
            min_zoom=14,
            max_zoom=22,
            description="Ortofoto de alta resolución del Hospital Nacional Zacamil.",
        )
        self._layers[21] = CNRLayerMetadata(
            layer_id=21,
            name="Presa Hidroeléctrica 3 de Febrero - VANT",
            layer_type="vant_drone",
            tile_url_pattern="https://{s}.elsalvadormaps.sv/tiles/chaparral/{z}/{x}/{y}.png",
            subdomains=("ec1", "ec2", "ec3"),
            min_zoom=14,
            max_zoom=22,
            description="Ortofoto del complejo hidroeléctrico El Chaparral sobre Río Torola.",
        )

    def get_layer(self, layer_id: int) -> Optional[CNRLayerMetadata]:
        return self._layers.get(layer_id)

    def get_administrative_layers(self) -> list[CNRLayerMetadata]:
        return [l for l in self._layers.values() if l.is_administrative]

    def get_proj4_definition(self) -> str:
        return CNR_SIRGAS_ES2007_PROJ4

    def get_border_disclaimer(self) -> str:
        return CNR_LEGAL_BORDER_DISCLAIMER

    def build_tile_url(self, layer_id: int, x: int, y: int, z: int, subdomain: str = "ec1") -> Optional[str]:
        """Construct authorized XYZ tile URL for Leaflet or GIS client."""
        layer = self.get_layer(layer_id)
        if not layer:
            return None
        return (
            layer.tile_url_pattern
            .replace("{s}", subdomain)
            .replace("{z}", str(z))
            .replace("{x}", str(x))
            .replace("{y}", str(y))
        )
