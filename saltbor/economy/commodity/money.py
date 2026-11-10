"""Commodity-money standards: tangible numeraire units, decay/spoilage, and storage weight."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from saltbor.economy.inventory.item import ItemType


class CommodityCurrencyType(enum.Enum):
    """Historical tangible commodity numeraire standards."""

    CACAO_MEASURE = "cacao_measure"          # Traditional Mesoamerican currency standard
    MAIZE_GRAIN = "maize_grain"              # Staple food numeraire
    SILVER_INGOT = "silver_ingot"            # Precious metal store of value


@dataclass(frozen=True)
class CommodityMoneyStandard:
    """Standardized physical commodity serving as currency with intrinsic properties."""

    standard_type: CommodityCurrencyType
    name: str
    underlying_item_type: ItemType
    units_per_abstract_dollar: float         # e.g. 5.0 units of CACAO = $1.0 abstract currency
    spoilage_rate_per_day: float = 0.005     # Daily organic decay/loss
    volumetric_density_m3: float = 0.02      # Storage space per unit

    def convert_to_currency(self, physical_quantity: float) -> float:
        """Calculate abstract currency value of physical commodity amount."""
        if self.units_per_abstract_dollar <= 0:
            return 0.0
        return round(physical_quantity / self.units_per_abstract_dollar, 2)

    def convert_from_currency(self, currency_value: float) -> float:
        """Calculate physical commodity quantity required to represent currency value."""
        return round(currency_value * self.units_per_abstract_dollar, 3)


# Standard definitions
STANDARD_CACAO = CommodityMoneyStandard(
    standard_type=CommodityCurrencyType.CACAO_MEASURE,
    name="Medida Estándar de Cacao",
    underlying_item_type=ItemType.SEEDS,
    units_per_abstract_dollar=4.0,
    spoilage_rate_per_day=0.002,
)

STANDARD_MAIZE = CommodityMoneyStandard(
    standard_type=CommodityCurrencyType.MAIZE_GRAIN,
    name="Fanega de Maíz de Pago",
    underlying_item_type=ItemType.GRAIN,
    units_per_abstract_dollar=0.5,           # 1 grain unit = $2.0 currency value
    spoilage_rate_per_day=0.008,
)
