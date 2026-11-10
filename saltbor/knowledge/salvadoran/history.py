"""
Salvadoran Historical and Social Memory Engine (Section 19.6).

Models key historical processes and collective memory in El Salvador:
- 1932 Indigena/Campesino Uprising and Cultural Impact in Western El Salvador
- Agrarian Reforms and Cooperativism (1980)
- Armed Conflict (1980-1992) and 1992 Chapultepec Peace Accords
- Mass International Migration and the Rise of Family Remittances
- Dolarización (2001): Transition from Salvadoran Colón to US Dollar
- Community Re-population and Growth of ADESCOs

Enforces epistemic bounding: Knowledge depends on age cohort, educational level,
and familial transmission rather than omniscient national history.
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass(frozen=True)
class HistoricalProcessMilestone:
    """A major historical event or structural transformation in El Salvador."""
    milestone_id: str
    name: str
    year: int
    era: str                             # "early_20th", "conflict_era", "post_peace_accords", "modern_era"
    summary: str
    affected_sectors: list[str]          # "campesinado", "urban_commerce", "currency", "migration"
    lasting_consequences: list[str]
    typical_awareness_by_cohort: dict[str, float] # e.g. {"elders_rural": 0.95, "youth_urban": 0.50}


SALVADORAN_HISTORICAL_MILESTONES: dict[str, HistoricalProcessMilestone] = {
    "levantamiento_1932": HistoricalProcessMilestone(
        milestone_id="levantamiento_1932",
        name="Acontecimientos Campesinos e Indígenas de 1932",
        year=1932,
        era="early_20th",
        summary="Levantamiento de jornaleros y comunidades indígenas en occidente (Izalco, Nahuizalco, Tacuba) reprimido severamente.",
        affected_sectors=["indigenous_communities", "coffee_oligarchy", "campesinado"],
        lasting_consequences=[
            "Declive forzado de la vestimenta tradicional (refajo) y del idioma Náhuat por temor",
            "Consolidación del poder militar y la estructura de tenencia de la tierra",
        ],
        typical_awareness_by_cohort={"elders_rural": 0.90, "elders_urban": 0.80, "youth_rural": 0.65, "youth_urban": 0.55},
    ),
    "reforma_agraria_1980": HistoricalProcessMilestone(
        milestone_id="reforma_agraria_1980",
        name="Proceso de Reforma Agraria (1980)",
        year=1980,
        era="conflict_era",
        summary="Intervención estatal de grandes haciendas para constituir cooperativas agrícolas campesinas (Fase I y Fase III).",
        affected_sectors=["campesinado", "landlords", "agricultural_cooperatives"],
        lasting_consequences=[
            "Creación de cooperativas agrícolas de caña y granos básicos",
            "Fragmentación de tierras y cambios en la propiedad rural",
        ],
        typical_awareness_by_cohort={"elders_rural": 0.92, "elders_urban": 0.75, "youth_rural": 0.60, "youth_urban": 0.45},
    ),
    "acuerdos_de_paz_1992": HistoricalProcessMilestone(
        milestone_id="acuerdos_de_paz_1992",
        name="Firma de los Acuerdos de Paz de Chapultepec (1992)",
        year=1992,
        era="post_peace_accords",
        summary="Conclusión negociada de doce años de guerra civil salvadoreña, reformas a la Fuerza Armada y creación de la PNC.",
        affected_sectors=["all_society", "military", "political_institutions", "repoblaciones"],
        lasting_consequences=[
            "Transición a la democracia electoral sin violencia armada organizada",
            "Reasentamiento de comunidades repobladas en Chalatenango y Morazán",
        ],
        typical_awareness_by_cohort={"elders_rural": 0.95, "elders_urban": 0.95, "youth_rural": 0.85, "youth_urban": 0.85},
    ),
    "dolarizacion_2001": HistoricalProcessMilestone(
        milestone_id="dolarizacion_2001",
        name="Ley de Integración Monetaria / Dolarización (2001)",
        year=2001,
        era="post_peace_accords",
        summary="Sustitución del Colón Salvadoreño (SVC) por el Dólar Estadounidense (USD) a tipo de cambio fijo de 8.75 colones.",
        affected_sectors=["currency", "urban_commerce", "household_budgets", "informal_economy"],
        lasting_consequences=[
            "Uso cotidiano de monedas estadounidenses ('coras', 'cuatros', 'pesos')",
            "Pérdida de soberanía de política monetaria pero facilitación de remesas y comercio internacional",
            "Impacto inicial de redondeo en precios de subsistencia en mercados municipales",
        ],
        typical_awareness_by_cohort={"elders_rural": 0.98, "elders_urban": 0.98, "youth_rural": 0.90, "youth_urban": 0.95},
    ),
    "ola_migratoria_remesas": HistoricalProcessMilestone(
        milestone_id="ola_migratoria_remesas",
        name="Éxodo Migratorio y Consolidación de la Economía de Remesas",
        year=1985,
        era="post_peace_accords",
        summary="Migración masiva de millones de salvadoreños hacia EE.UU. que transformó a las remesas en el 20-25% del PIB nacional.",
        affected_sectors=["household_budgets", "family_structures", "construction", "rural_villages"],
        lasting_consequences=[
            "Transición de economías campesinas agrícolas a economías familiares dependientes de remesas",
            "Construcción generalizada de casas de bloque y concreto en cantones remotos",
            "Separación transnacional de familias (abuelas criando a sus nietos)",
        ],
        typical_awareness_by_cohort={"elders_rural": 0.98, "elders_urban": 0.98, "youth_rural": 0.95, "youth_urban": 0.98},
    ),
}


class SalvadoranHistoricalMemoryEngine:
    """Evaluates individual acquaintance and episodic memory of national historical milestones."""

    def __init__(self) -> None:
        self._milestones: dict[str, HistoricalProcessMilestone] = dict(SALVADORAN_HISTORICAL_MILESTONES)

    def evaluate_historical_knowledge(
        self,
        age: float,
        is_rural: bool,
        education_level: float = 0.5, # [0.0, 1.0]
    ) -> list[dict[str, Any]]:
        """Determine which historical events an individual knows and their degree of detail."""
        known = []
        is_elder = age >= 50.0

        if is_elder:
            cohort_key = "elders_rural" if is_rural else "elders_urban"
        else:
            cohort_key = "youth_rural" if is_rural else "youth_urban"

        for m in self._milestones.values():
            base_prob = m.typical_awareness_by_cohort.get(cohort_key, 0.70)
            adjusted_prob = min(0.99, base_prob + (education_level * 0.15))

            # Personal lived experience vs. heard from elders/school
            lived_experience = (2026 - age) <= m.year

            known.append({
                "milestone_id": m.milestone_id,
                "name": m.name,
                "year": m.year,
                "awareness_level": round(adjusted_prob, 2),
                "is_personal_memory": lived_experience,
                "source": "vivencia_personal" if lived_experience else ("tradicion_oral_familiar" if is_rural else "educacion_formal"),
            })

        return known
