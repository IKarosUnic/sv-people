"""Regional settlement nodes: regional ecology, production specializations, and price differentials."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from saltbor.economy.inventory.item import ItemType


class SettlementEcology(enum.Enum):
    """Ecological biome and economic specialization of a regional settlement."""

    VALLEY_CORE = "valley_core"            # Mixed agriculture, administrative core (Saltbor)
    HIGHLAND_FOREST = "highland_forest"    # Heavy timber, resin, charcoal (Monte Verde)
    COASTAL_PORT = "coastal_port"          # Sea salt, dried fish, shellcraft (Puerto Sal)
    MINERAL_RIDGE = "mineral_ridge"        # Stone, iron ore, clay, obsidian (La Cima)
    ALLUVIAL_PLAINS = "alluvial_plains"    # Intensive maize, beans, squash (Valle Fértil)


@dataclass
class RegionalSettlement:
    """An external or primary community node in the regional geographic network."""

    settlement_id: str
    name: str
    ecology: SettlementEcology
    coordinates_km: tuple[float, float] = (0.0, 0.0)  # Relative to Saltbor at (0, 0)
    population_estimate: int = 150
    cultural_affinity_with_saltbor: float = 0.70      # 0.0 (foreign/hostile) to 1.0 (close kin)

    # Economic Specialization & Commodity Reserves
    primary_exports: list[ItemType] = field(default_factory=list)
    primary_imports: list[ItemType] = field(default_factory=list)
    commodity_surpluses: dict[ItemType, float] = field(default_factory=dict)
    price_multipliers: dict[ItemType, float] = field(default_factory=dict)

    # Treasury & Trade Statistics
    trade_treasury: float = 500.0
    lifetime_goods_exported: float = 0.0
    lifetime_goods_imported: float = 0.0

    def get_local_price(self, item_type: ItemType, base_price: float = 5.0) -> float:
        """Calculate local equilibrium price for an item type based on regional scarcity."""
        mult = self.price_multipliers.get(item_type, 1.0)
        # Higher surplus reduces price; severe shortage increases price
        stock = self.commodity_surpluses.get(item_type, 10.0)
        scarcity_factor = max(0.4, min(2.5, 20.0 / max(1.0, stock)))
        return round(base_price * mult * scarcity_factor, 2)

    def produce_periodic_surplus(self, tick_interval: int = 96) -> None:
        """Autonomous regional node production: generates specialized exports."""
        if self.ecology == SettlementEcology.HIGHLAND_FOREST:
            self.commodity_surpluses[ItemType.WOOD] = self.commodity_surpluses.get(ItemType.WOOD, 0.0) + 15.0
        elif self.ecology == SettlementEcology.COASTAL_PORT:
            # Coastal port produces salt and preserved food
            self.commodity_surpluses[ItemType.PRESERVED_FOOD] = (
                self.commodity_surpluses.get(ItemType.PRESERVED_FOOD, 0.0) + 12.0
            )
        elif self.ecology == SettlementEcology.ALLUVIAL_PLAINS:
            self.commodity_surpluses[ItemType.GRAIN] = self.commodity_surpluses.get(ItemType.GRAIN, 0.0) + 20.0
        elif self.ecology == SettlementEcology.MINERAL_RIDGE:
            self.commodity_surpluses[ItemType.TOOL] = self.commodity_surpluses.get(ItemType.TOOL, 0.0) + 4.0
