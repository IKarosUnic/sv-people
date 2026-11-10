"""
Salvadoran Cultural Heritage, Traditional Crafts, and Folklore Engine (Section 19.3).

Models artisanal crafts, oral traditions, and heterogeneous cultural adoption:
- Traditional craft centers (Ilobasco clay miniatures, Guatajiagua black pottery, San Sebastián looms)
- Cultural identity, participation, and individual variation (not all individuals are identical)
- Oral traditions (Cuentos de la Siguanaba, el Cadejo, el Cipitío)
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass(frozen=True)
class TraditionalCraftSpecialty:
    """An artisanal craft deeply rooted in a Salvadoran locality."""
    craft_id: str
    name: str
    origin_municipality: str
    department_code: str
    raw_materials: list[str]
    production_method: str
    typical_sale_price_usd: float
    cultural_value: float


SALVADORAN_CRAFTS: dict[str, TraditionalCraftSpecialty] = {
    "barro_negro_guatajiagua": TraditionalCraftSpecialty(
        craft_id="barro_negro_guatajiagua",
        name="Cerámica Negra de Guatajiagua",
        origin_municipality="Guatajiagua",
        department_code="MO",
        raw_materials=["barro_comun", "semilla_de_jiote_para_tinte", "arena_fina"],
        production_method="Moldeado manual ancestral Lenca, bruñido con piedra de río y bañado en tinte natural caliente de jiote",
        typical_sale_price_usd=8.50,
        cultural_value=0.96,
    ),
    "alfareria_ilobasco": TraditionalCraftSpecialty(
        craft_id="alfareria_ilobasco",
        name="Alfarería y Miniaturas Sorpresa de Ilobasco",
        origin_municipality="Ilobasco",
        department_code="CA",
        raw_materials=["arcilla_roja_local", "anilinas_de_colores", "yeso"],
        production_method="Modelado de figuras diminutas ocultas en cáscaras de nuez o frutas de barro cocido",
        typical_sale_price_usd=3.50,
        cultural_value=0.92,
    ),
    "telares_san_sebastian": TraditionalCraftSpecialty(
        craft_id="telares_san_sebastian",
        name="Textiles en Telar de Madera de San Sebastián",
        origin_municipality="San Sebastián",
        department_code="SV",
        raw_materials=["hilo_de_algodon_mercerizado", "tintes_vivos"],
        production_method="Tejido artesanal rítmico en telares de pedal manuales de madera para hamacas y colchas",
        typical_sale_price_usd=25.00,
        cultural_value=0.94,
    ),
    "madera_la_palma": TraditionalCraftSpecialty(
        craft_id="madera_la_palma",
        name="Artesanía en Madera Estilo Naïf de La Palma",
        origin_municipality="La Palma",
        department_code="CH",
        raw_materials=["madera_de_pino", "semilla_de_copinol", "pintura_acrilica"],
        production_method="Pintado a mano con motivos coloridos de pájaros, casas rurales y vida campesina (herencia Fernando Llort)",
        typical_sale_price_usd=6.00,
        cultural_value=0.95,
    ),
}


class SalvadoranCulturalEngine:
    """Manages cultural identity, craft production, and traditional lore."""

    def __init__(self) -> None:
        self._crafts: dict[str, TraditionalCraftSpecialty] = dict(SALVADORAN_CRAFTS)

    def get_craft_info(self, craft_id: str) -> Optional[TraditionalCraftSpecialty]:
        return self._crafts.get(craft_id)

    def get_all_crafts(self) -> list[TraditionalCraftSpecialty]:
        return list(self._crafts.values())

    def produce_craft_item(
        self,
        artisan_uid: str,
        craft_id: str,
        skill_level: float = 0.5,
        available_materials: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Simulate an artisan producing an authentic craft item."""
        craft = self._crafts.get(craft_id)
        if not craft:
            return {"success": False, "reason": "Unknown craft"}

        # Quality depends on skill
        quality = round(min(1.0, 0.4 + (skill_level * 0.6)), 2)
        real_value = round(craft.typical_sale_price_usd * (0.8 + (quality * 0.4)), 2)

        return {
            "success": True,
            "craft": craft.name,
            "artisan": artisan_uid,
            "municipality": craft.origin_municipality,
            "quality_rating": quality,
            "estimated_market_value_usd": real_value,
            "cultural_heritage_score": craft.cultural_value,
        }

    def evaluate_individual_cultural_stance(
        self,
        age: float,
        is_rural: bool,
        openness: float = 0.5,
        religious_participation: float = 0.5,
    ) -> dict[str, Any]:
        """Compute heterogeneous cultural stance (avoiding treating everyone as culturally identical)."""
        # Elders and rural inhabitants typically retain deeper knowledge of folklore and traditional celebrations
        folklore_familiarity = min(0.98, 0.35 + (0.01 * min(60, age)) + (0.25 if is_rural else 0.0))
        patron_festivity_interest = min(0.95, 0.30 + (religious_participation * 0.50) + (0.15 if is_rural else 0.05))
        gastronomic_attachment = 0.95 # Pupusas and traditional food are near-universal across age and setting

        return {
            "folklore_familiarity": round(folklore_familiarity, 2),
            "patron_festivity_interest": round(patron_festivity_interest, 2),
            "gastronomic_attachment": round(gastronomic_attachment, 2),
            "openness_to_cultural_innovation": round(openness, 2),
        }
