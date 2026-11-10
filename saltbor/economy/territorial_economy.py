"""
Territorial Economy and Spatial Supply Chains for Saltbor (Phase 0.8).

Models authentic Salvadoran microeconomics anchored in real geography:
- Spatial transportation costs and road friction on commodity prices
- Three-tier agricultural distribution chain:
  Rural Producer -> Wholesale Hub (La Tiendona) -> Municipal Markets -> Neighborhood Stores
- Pupusería microenterprise unit economics:
  Real cost of ingredients (masa de maíz/arroz, quesillo, chicharrón, loroco, leña/gas, curtido),
  daily foot traffic linked to location, and operating margins
- Neighborhood informal micro-credit ('El Fiado') strictly constrained by walking proximity.
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional

from saltbor.world.geographic.engine import RealGeographicEngine
from saltbor.world.geographic.spatial_index import haversine_distance_km


@dataclasses.dataclass
class CommodityPriceQuote:
    """Pricing breakdown for a commodity delivered to a specific district."""
    commodity_name: str
    destination_district_id: str
    farmgate_base_price_usd: float
    transport_distance_km: float
    transport_cost_usd: float
    wholesale_margin_usd: float
    retail_margin_usd: float
    final_retail_price_usd: float
    supplier_district_id: str


@dataclasses.dataclass
class PupuseriaDailyPnl:
    """Daily profit and loss ledger for a pupusería microenterprise."""
    establishment_id: str
    name: str
    pupusas_sold: int
    price_per_pupusa_usd: float
    gross_revenue_usd: float
    ingredient_costs_usd: float
    fuel_gas_wood_cost_usd: float
    daily_rent_and_helpers_usd: float
    total_expenses_usd: float
    net_profit_usd: float
    operating_margin: float


class TerritorialEconomyEngine:
    """Coordinates spatial supply chains, commodity pricing, and pupusería economics."""

    # Freight transport cost per ton/quintal per km
    FREIGHT_COST_PER_KM_QUINTAL_USD: float = 0.045

    def __init__(self, geo_engine: RealGeographicEngine) -> None:
        self.geo = geo_engine

    def calculate_commodity_price(
        self,
        commodity: str,
        producer_district_id: str,
        consumer_district_id: str,
        base_farmgate_price_usd: float = 20.0,  # e.g. $20 per quintal of maize
        is_rainy_season: bool = False,
    ) -> CommodityPriceQuote:
        """Calculate consumer price reflecting road distance and transit friction."""
        route = self.geo.calculate_route(
            origin_district_id=producer_district_id,
            destination_district_id=consumer_district_id,
            transport_mode="pickup",
            is_rainy_season=is_rainy_season,
        )

        dist_km = route["total_distance_km"] if route["is_accessible"] else 120.0
        # Transit friction surcharge if bad roads / rain
        weather_friction_mult = 1.35 if is_rainy_season else 1.0

        transport_cost = dist_km * self.FREIGHT_COST_PER_KM_QUINTAL_USD * weather_friction_mult
        wholesale_margin = base_farmgate_price_usd * 0.12
        retail_margin = (base_farmgate_price_usd + transport_cost + wholesale_margin) * 0.15

        final_price = base_farmgate_price_usd + transport_cost + wholesale_margin + retail_margin

        return CommodityPriceQuote(
            commodity_name=commodity,
            destination_district_id=consumer_district_id,
            farmgate_base_price_usd=round(base_farmgate_price_usd, 2),
            transport_distance_km=round(dist_km, 2),
            transport_cost_usd=round(transport_cost, 2),
            wholesale_margin_usd=round(wholesale_margin, 2),
            retail_margin_usd=round(retail_margin, 2),
            final_retail_price_usd=round(final_price, 2),
            supplier_district_id=producer_district_id,
        )

    def evaluate_pupuseria_day(
        self,
        establishment_id: str,
        dough_type: str = "maiz",  # "maiz" or "arroz"
        daily_customers: int = 40,
        average_pupusas_per_customer: float = 3.5,
        price_per_pupusa_usd: float = 0.90,
    ) -> PupuseriaDailyPnl:
        """Simulate real pupusería unit economics and daily operating profit."""
        total_pupusas = int(daily_customers * average_pupusas_per_customer)

        # Ingredient cost breakdown per pupusa:
        # Masa: $0.10 (maíz) or $0.14 (arroz)
        # Quesillo salvadoreño & Chicharrón: $0.22
        # Loroco / frijoles: $0.06
        # Curtido & salsa: $0.05
        dough_cost = 0.14 if dough_type == "arroz" else 0.10
        ingredient_unit_cost = dough_cost + 0.22 + 0.06 + 0.05  # ~$0.43 - $0.47
        total_ingredients = total_pupusas * ingredient_unit_cost

        # Fixed daily overheads
        fuel_gas_wood = 7.50
        helpers_daily = 18.00  # Family helper stipend

        gross_revenue = total_pupusas * price_per_pupusa_usd
        total_expenses = total_ingredients + fuel_gas_wood + helpers_daily
        net_profit = gross_revenue - total_expenses
        margin = (net_profit / gross_revenue) if gross_revenue > 0 else 0.0

        place = self.geo.establishments.get_by_id(establishment_id)
        name = place.name if place else "Pupusería Tradicional"

        return PupuseriaDailyPnl(
            establishment_id=establishment_id,
            name=name,
            pupusas_sold=total_pupusas,
            price_per_pupusa_usd=price_per_pupusa_usd,
            gross_revenue_usd=round(gross_revenue, 2),
            ingredient_costs_usd=round(total_ingredients, 2),
            fuel_gas_wood_cost_usd=round(fuel_gas_wood, 2),
            daily_rent_and_helpers_usd=round(helpers_daily, 2),
            total_expenses_usd=round(total_expenses, 2),
            net_profit_usd=round(net_profit, 2),
            operating_margin=round(margin, 3),
        )

    def evaluate_fiado_eligibility(
        self,
        customer_lat: float,
        customer_lon: float,
        store_lat: float,
        store_lon: float,
        trust_score: float,
        max_walking_radius_m: float = 600.0,
    ) -> tuple[bool, float, str]:
        """Determine whether customer qualifies for local credit ('el fiado')."""
        dist_m = haversine_distance_km(customer_lat, customer_lon, store_lat, store_lon) * 1000.0

        if dist_m > max_walking_radius_m:
            return False, 0.0, f"Fuera del radio vecinal ({dist_m:.0f}m > {max_walking_radius_m:.0f}m). El fiado solo se otorga a vecinos inmediatos."

        if trust_score < 0.60:
            return False, 0.0, f"Confianza comunitaria insuficiente ({trust_score:.2f} < 0.60)."

        credit_limit = round(15.0 + (trust_score * 45.0), 2)  # $15 - $60 limit
        return True, credit_limit, f"Fiado aprobado con límite de ${credit_limit:.2f} USD."
