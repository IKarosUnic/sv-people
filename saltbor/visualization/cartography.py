"""
Cartographic Visualization Engine for Saltbor (Phase 0.8).

Provides lightweight, self-contained, 100% offline territorial rendering:
- Standalone HTML/SVG interactive map export with zoom, layers, and establishment markers
- Color differentiation for confirmed vs pending/unverified places
- Road network rendering (CA-1, CA-2, CA-4, and Ruta de las Flores)
- Terminal ASCII/ANSI territory overview for headless or console environments.
"""

from __future__ import annotations
import html
import math
from typing import Any, Optional

from saltbor.world.geographic.engine import RealGeographicEngine
from saltbor.world.geographic.models import RealPlace, ValidationState


class CartographicVisualizer:
    """Renders territorial maps of El Salvador in SVG/HTML and terminal formats."""

    def __init__(self, geo_engine: RealGeographicEngine) -> None:
        self.geo = geo_engine

    def render_ascii_map(self) -> str:
        """Render a compact ASCII map showing major cities, volcanoes, and highways."""
        lines = [
            "==========================================================================",
            "                SALTBOR TERRITORIO DE EL SALVADOR (FASE 0.8)              ",
            "==========================================================================",
            "  CHALATENANGO / EL PITAL (2730m)              [HONDURAS]                 ",
            "    ▲ Montecristo (SA)       * La Palma (CH)                             ",
            "         \\                      | CA-4 Troncal                            ",
            " [GUATEMALA] \\                  |                                         ",
            "   Ahuachapán *---* Santa Ana   * Aguilares       MORAZÁN                 ",
            "      |  \\     (Ilamatepec ▲)   |               * Perquín                ",
            "      |   * Ataco    |          * Apopa         |                         ",
            "      |              * El Congo |     Cojutepeque * Gotera               ",
            "  CA-1|              |          |         |       |                       ",
            "      * Sonsonate ---* S. Tecla * S.SALVADOR --* S.VICENTE ---* S.MIGUEL  ",
            "        (Izalco ▲)   | (Boquerón▲)   (Ilopango) (Chinchontepec▲) (Chaparrastique▲)",
            "        |            |                   |            |            | CA-1 ",
            "        * Acajutla   * La Libertad       * Zacatecoluca * Usulután * La Unión",
            "        (CA-2)       (CA-2 Litoral)      (CA-2)       (Jiquilisco) (Golfo)  ",
            "  ~~~~~~~~~~~~~~~~~~~~~~ OCÉANO PACÍFICO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
            "==========================================================================",
            f" Total Departamentos: 14 | Municipios: 44 | Distritos: 262                ",
            f" Establecimientos en Directorio: {len(self.geo.establishments)} (Confirmados: {len(self.geo.establishments.get_all(confirmed_only=True))})",
            "==========================================================================",
        ]
        return "\n".join(lines)

    def generate_svg_map(
        self,
        width: int = 1000,
        height: int = 550,
        include_establishments: bool = True,
        highlight_places: Optional[list[str]] = None,
    ) -> str:
        """Generate a complete, self-contained SVG map of El Salvador."""
        # Bounding box coordinates for projection
        min_lat, max_lat = 13.10, 14.48
        min_lon, max_lon = -90.15, -87.65

        def project(lat: float, lon: float) -> tuple[float, float]:
            x = (lon - min_lon) / (max_lon - min_lon) * width
            # Invert y because SVG y coordinates increase downwards
            y = (1.0 - (lat - min_lat) / (max_lat - min_lat)) * height
            return (round(x, 1), round(y, 1))

        elements: list[str] = []
        elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#0f172a; font-family:system-ui, sans-serif;">')

        # 1. Background grid & title
        elements.append('<rect width="100%" height="100%" fill="#090d16"/>')
        elements.append('<text x="30" y="40" fill="#38bdf8" font-size="20" font-weight="bold">SALTBOR — MAPA TERRITORIAL REAL DE EL SALVADOR</text>')
        elements.append('<text x="30" y="65" fill="#94a3b8" font-size="12">14 Departamentos | 44 Municipios | 262 Distritos | Red Vial Nacional y Puentes</text>')

        # 2. Roads (highways & secondary routes)
        road_colors = {
            "paved_highway": "#f59e0b",
            "secondary_asphalt": "#38bdf8",
            "cobblestone": "#a78bfa",
            "unpaved_dirt_road": "#78716c",
        }
        for seg in self.geo.navigation._segments.values():
            orig = self.geo.get_district(seg.from_district_id)
            dest = self.geo.get_district(seg.to_district_id)
            if orig and dest:
                x1, y1 = project(orig.latitude, orig.longitude)
                x2, y2 = project(dest.latitude, dest.longitude)
                color = road_colors.get(seg.road_type, "#94a3b8")
                stroke_width = 3.0 if seg.road_type == "paved_highway" else 1.8
                bridge_attr = ' stroke-dasharray="4,3"' if seg.is_bridge else ''
                elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{stroke_width}"{bridge_attr} opacity="0.7"><title>{seg.name} ({seg.distance_km} km)</title></line>')

        # 3. Major Volcanoes & Lakes
        for feat in self.geo.get_volcanoes():
            px, py = project(feat.latitude, feat.longitude)
            elements.append(f'<polygon points="{px},{py-12} {px-8},{py+6} {px+8},{py+6}" fill="#ef4444" stroke="#f87171" stroke-width="1.5"><title>{feat.name} ({feat.elevation_m}m)</title></polygon>')
            elements.append(f'<text x="{px+10}" y="{py}" fill="#fca5a5" font-size="9">{feat.name.split("(")[0].strip()}</text>')

        for lake in self.geo.get_lakes():
            px, py = project(lake.latitude, lake.longitude)
            elements.append(f'<circle cx="{px}" cy="{py}" r="14" fill="#0284c7" opacity="0.45" stroke="#38bdf8" stroke-width="1.2"><title>{lake.name}</title></circle>')
            elements.append(f'<text x="{px+16}" y="{py+4}" fill="#7dd3fc" font-size="9">{lake.name.split("(")[0].strip()}</text>')

        # 4. Department Cabeceras & Districts
        for dist in self.geo.get_all_districts():
            if dist.is_urban_core:
                px, py = project(dist.latitude, dist.longitude)
                elements.append(f'<circle cx="{px}" cy="{py}" r="4.5" fill="#e2e8f0" stroke="#0ea5e9" stroke-width="1.5"><title>{dist.name} ({dist.approx_population:,} hab)</title></circle>')
                elements.append(f'<text x="{px+6}" y="{py-4}" fill="#f1f5f9" font-size="10" font-weight="600">{dist.name}</text>')

        # 5. Establishments
        if include_establishments:
            status_colors = {
                ValidationState.CONFIRMADO.value: "#10b981",
                ValidationState.PENDIENTE_VALIDACION.value: "#eab308",
                ValidationState.DESACTUALIZADO.value: "#f97316",
                ValidationState.CERRADO.value: "#ef4444",
                ValidationState.DUPLICADO.value: "#a855f7",
            }
            for p in self.geo.establishments.get_all(confirmed_only=False):
                px, py = project(p.point.latitude, p.point.longitude)
                col = status_colors.get(p.validation_state.value, "#94a3b8")
                is_hl = highlight_places and p.place_id in highlight_places
                radius = 6.0 if is_hl else 3.5
                stroke = "#ffffff" if is_hl else "#000000"
                elements.append(f'<circle cx="{px}" cy="{py}" r="{radius}" fill="{col}" stroke="{stroke}" stroke-width="1"><title>[{p.validation_state.value}] {p.name} - {p.sub_category}</title></circle>')

        # 6. Legend
        elements.append('<g transform="translate(30, 430)">')
        elements.append('<rect width="280" height="95" rx="6" fill="#1e293b" opacity="0.85" stroke="#334155"/>')
        elements.append('<text x="12" y="20" fill="#f8fafc" font-size="11" font-weight="bold">Leyenda Cartográfica</text>')
        elements.append('<line x1="12" y1="36" x2="35" y2="36" stroke="#f59e0b" stroke-width="3"/><text x="45" y="40" fill="#cbd5e1" font-size="10">CA-1 / CA-2 / CA-4 Carreteras</text>')
        elements.append('<circle cx="18" cy="55" r="4" fill="#10b981"/><text x="30" y="58" fill="#cbd5e1" font-size="10">Establecimiento CONFIRMADO</text>')
        elements.append('<circle cx="18" cy="73" r="4" fill="#eab308"/><text x="30" y="76" fill="#cbd5e1" font-size="10">Establecimiento PENDIENTE</text>')
        elements.append('</g>')

        elements.append('</svg>')
        return "\n".join(elements)

    def export_html_map(self, output_path: str) -> str:
        """Export an interactive self-contained HTML page containing the SVG map."""
        svg_content = self.generate_svg_map()
        html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SALTBOR — Mapa Geográfico de El Salvador</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #0b0f19; color: #f8fafc; font-family: system-ui, sans-serif; }}
        .header {{ margin-bottom: 15px; }}
        .map-box {{ width: 100%; max-width: 1200px; margin: 0 auto; border: 1px solid #334155; border-radius: 8px; overflow: hidden; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Entorno Geográfico y Territorial de El Salvador (SALTBOR Fase 0.8)</h2>
        <p>14 Departamentos, 44 Municipios, 262 Distritos, Red Vial y Directorio de Establecimientos Reales.</p>
    </div>
    <div class="map-box">
        {svg_content}
    </div>
</body>
</html>"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        return output_path
