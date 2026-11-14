"""Agriculture and Local Markets Domain for SALTBOR.

Simulates smallholder and cooperative agricultural production in El Salvador:
- Basic grain cultivation (maize / *maíz*, red silk bean / *frijol seda*), sorghum (*maicillo*), and vegetables.
- Input procurement (fertilizer, certified seed, agrochemicals) and seasonal financing.
- Environmental vulnerability: *canícula* drought shocks, excess rainfall, and soil moisture stress.
- Harvest yield and local market commercialization across municipal wholesale markets (*La Tiendona*, local plazas).
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.domain.models import DomainCategory, DomainDefinition, DomainStatus

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FarmPlot:
    plot_id: str
    owner_id: str
    department: str
    crop_type: str  # "maiz", "frijol", "hortalizas"
    area_manzanas: float = 1.5  # 1 manzana ~ 0.70 hectares
    expected_yield_per_manzana: float = 45.0  # Quintales per manzana
    soil_moisture_level: float = 0.80  # 0.0 (bone dry) to 1.0 (saturated)
    fertilizer_applied: bool = True
    current_growth_stage: str = "vegetative"  # "planted", "vegetative", "flowering", "mature"
    harvested_quintales: float = 0.0


class AgricultureActivityDomain:
    """Specialized domain orchestrating agricultural production, environmental shocks, and grain markets."""

    def __init__(self) -> None:
        self.plots: Dict[str, FarmPlot] = {}
        self.market_prices_per_quintal: Dict[str, float] = {
            "maiz": 22.50,
            "frijol": 85.00,
            "hortalizas": 35.00,
        }
        self._seed_default_plots()

    def get_definition(self) -> DomainDefinition:
        return DomainDefinition(
            domain_id="agriculture",
            name="Agriculture and Local Markets Domain",
            category=DomainCategory.AGRICULTURE,
            purpose="Simulate smallholder basic grain production, climate vulnerability in the Corredor Seco, and agricultural market commercialization.",
            geographic_scope="El Salvador",
            resources=["arable_land", "certified_seed", "fertilizer", "soil_moisture"],
            infrastructure=["farm_plots", "storage_silos", "wholesale_markets", "irrigation_channels"],
            activities=[
                "agriculture.planting",
                "agriculture.harvesting",
                "agriculture.selling_production",
                "agriculture.buying_inputs",
                "agriculture.environmental_adaptation",
            ],
            entities=["FarmPlot", "GrainMarket", "AgrochemicalSupplier"],
            indicators=["crop_yield_quintales", "smallholder_net_income", "canicula_loss_ratio", "food_basket_grain_availability"],
            possible_interventions=["drought_resistant_seed_package", "agricultural_credit_facility", "community_grain_reserve"],
            data_sources=["MAG_anuario_estadistico", "CENTA_investigacion_granos", "FAOSTAT_el_salvador"],
            uncertainties=["mid_summer_canicula_duration", "international_fertilizer_cost_shocks"],
            version="1.0.0",
            status=DomainStatus.ACTIVE,
        )

    def register_plot(self, plot: FarmPlot) -> None:
        self.plots[plot.plot_id] = plot

    def simulate_crop_cycle(
        self,
        plot_id: str,
        has_severe_canicula: bool = False,
        fertilizer_deficit: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> Dict[str, Any]:
        """Simulate crop yield under environmental conditions and inputs."""
        plot = self.plots.get(plot_id)
        if not plot:
            raise ValueError(f"Plot '{plot_id}' not found.")

        rng_gen = rng or np.random.default_rng(42)
        base_yield = plot.expected_yield_per_manzana * plot.area_manzanas

        # Canícula drought penalty
        weather_factor = 1.0
        if has_severe_canicula:
            weather_factor = float(rng_gen.uniform(0.35, 0.55))  # 45% - 65% loss

        # Input penalty
        input_factor = 0.70 if fertilizer_deficit else 1.0

        actual_harvest = base_yield * weather_factor * input_factor
        plot.harvested_quintales = round(actual_harvest, 1)

        # Revenue if sold at market
        price_q = self.market_prices_per_quintal.get(plot.crop_type, 22.0)
        gross_revenue = actual_harvest * price_q

        # Estimated input cost
        input_cost = (60.0 if not fertilizer_deficit else 15.0) * plot.area_manzanas
        net_margin = gross_revenue - input_cost

        return {
            "plot_id": plot_id,
            "crop_type": plot.crop_type,
            "area_manzanas": plot.area_manzanas,
            "potential_yield_quintales": round(base_yield, 1),
            "actual_harvest_quintales": round(actual_harvest, 1),
            "loss_pct_due_to_drought": round((1.0 - weather_factor) * 100.0, 1),
            "gross_revenue_usd": round(gross_revenue, 2),
            "input_cost_usd": round(input_cost, 2),
            "net_margin_usd": round(net_margin, 2),
            "household_resilience_status": "Vulnerable to food insecurity" if net_margin < 50.0 else "Solvent smallholder",
        }

    def _seed_default_plots(self) -> None:
        self.register_plot(
            FarmPlot(
                plot_id="parcela_san_vicente_1",
                owner_id="human_agricultor_vicente",
                department="San Vicente",
                crop_type="maiz",
                area_manzanas=2.0,
                expected_yield_per_manzana=48.0,
            )
        )
        self.register_plot(
            FarmPlot(
                plot_id="parcela_morazan_corredor_seco",
                owner_id="human_agricultor_morazan",
                department="Morazán",
                crop_type="frijol",
                area_manzanas=1.2,
                expected_yield_per_manzana=16.0,
            )
        )
