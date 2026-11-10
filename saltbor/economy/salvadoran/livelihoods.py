"""
Salvadoran Rural Livelihoods, Coffee Harvest, and Artisanal Work (Section 19.4).

Models representative economic occupations of El Salvador:
- Smallholder agriculture (milperos de maíz y frijol, arriendo de tierra, jornales)
- Seasonal coffee picking (cortadores de café, pago por canasto / arroba)
- Coastal artisanal fishing (lancheros, trasmalleros en muelle o estero)
- Informal transport (mototaxis 'toritos', picops rurales)
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class AgriculturalMilpaPlot:
    """A smallholder farming plot ('la milpa') cultivated by a campesino family."""
    plot_id: str
    cultivator_uid: str
    location_id: str
    area_manzanas: float = 1.0           # 1 manzana = ~0.7 hectares
    is_rented: bool = True               # Most poor smallholders rent land
    annual_rent_usd: float = 120.0       # Typical rent for 1 manzana per year
    fertilizer_invested_usd: float = 85.0
    crop_primary: str = "maiz"           # "maiz" or "frijol"
    expected_harvest_quintales: float = 35.0 # ~35 quintales of maize per manzana in good year


class SalvadoranLivelihoodsEngine:
    """Simulates campesino milpas, coffee harvest wages, and fishing daily yields."""

    def __init__(self) -> None:
        self._milpas: dict[str, AgriculturalMilpaPlot] = {}

    def register_milpa(
        self,
        plot_id: str,
        cultivator_uid: str,
        location_id: str,
        area_manzanas: float = 1.0,
        is_rented: bool = True,
    ) -> AgriculturalMilpaPlot:
        """Register a family milpa plot."""
        plot = AgriculturalMilpaPlot(
            plot_id=plot_id,
            cultivator_uid=cultivator_uid,
            location_id=location_id,
            area_manzanas=area_manzanas,
            is_rented=is_rented,
        )
        self._milpas[plot_id] = plot
        return plot

    def harvest_milpa(
        self,
        plot_id: str,
        weather_yield_multiplier: float = 1.0,
    ) -> dict[str, Any]:
        """Harvest the milpa factoring in seasonal weather impact (canícula, temporal)."""
        plot = self._milpas.get(plot_id)
        if not plot:
            return {"success": False, "reason": "Plot not found"}

        actual_yield = round(plot.expected_harvest_quintales * weather_yield_multiplier, 1)
        market_price_per_quintal = 22.0 # ~$22 per quintal of dry maize

        # Family retains portion for domestic consumption (~15 quintales per year for a family of 4)
        domestic_reserve = min(actual_yield, 15.0)
        surplus_marketed = max(0.0, actual_yield - domestic_reserve)
        cash_earned = round(surplus_marketed * market_price_per_quintal, 2)
        total_costs = plot.fertilizer_invested_usd + (plot.annual_rent_usd if plot.is_rented else 0.0)
        net_cash_balance = round(cash_earned - total_costs, 2)

        return {
            "plot_id": plot.plot_id,
            "cultivator": plot.cultivator_uid,
            "total_harvest_quintales": actual_yield,
            "domestic_subsistence_reserve_quintales": domestic_reserve,
            "commercial_surplus_sold_quintales": surplus_marketed,
            "gross_cash_earned_usd": cash_earned,
            "production_costs_usd": total_costs,
            "net_cash_balance_usd": net_cash_balance,
            "family_food_secure": domestic_reserve >= 12.0,
        }

    def simulate_coffee_picking_day(
        self,
        worker_uid: str,
        canastos_picked: int = 4,
        pay_per_canasto_usd: float = 2.50,
    ) -> dict[str, Any]:
        """Simulate a day of seasonal coffee picking in highland fincas."""
        earned = round(canastos_picked * pay_per_canasto_usd, 2)
        return {
            "worker_uid": worker_uid,
            "canastos_harvested": canastos_picked,
            "rate_per_canasto_usd": pay_per_canasto_usd,
            "daily_wage_earned_usd": earned,
            "activity": "Corta de café en finca de sombra",
        }

    def simulate_artisanal_fishing_trip(
        self,
        fisherman_uid: str,
        is_safe_sea: bool = True,
        fuel_cost_usd: float = 12.0,
    ) -> dict[str, Any]:
        """Simulate an artisanal fishing expedition from a coastal port."""
        if not is_safe_sea:
            return {
                "success": False,
                "reason": "Salida suspendida por alerta de mar picado y vientos de norte",
                "catch_lbs": 0.0,
                "net_profit_usd": 0.0,
            }

        # Typical catch in coastal waters
        catch_lbs = 35.0
        sale_price_per_lb = 1.25 # ~$1.25 per lb of corvina, pargo, or curvinas
        gross_sales = round(catch_lbs * sale_price_per_lb, 2)
        net_profit = round(gross_sales - fuel_cost_usd, 2)

        return {
            "success": True,
            "fisherman_uid": fisherman_uid,
            "catch_lbs": catch_lbs,
            "gross_sales_usd": gross_sales,
            "fuel_cost_usd": fuel_cost_usd,
            "net_profit_usd": net_profit,
        }
