"""Place Capabilities & Structured Functional Hierarchies (Phase 1.8).

Defines the 8-tier hierarchy of place capabilities:
1. IDENTIFIABLE
2. NAVIGABLE
3. VISITABLE
4. SCHEDULED
5. SERVICE_PROVIDER
6. INVENTORY_STORAGE
7. SOCIAL_INTERACTION
8. ECONOMIC_CONSEQUENCES

Covers all 24 place categories (viviendas, habitaciones, calles, mercados,
pupuserías, clínicas, hospitales, escuelas, talleres, terminales, etc.).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class PlaceCapability(enum.IntFlag):
    """Verifiable capability flags for physical places in SALTBOR."""
    NONE = 0
    IDENTIFIABLE = 1 << 0          # Tier 1: Canonical identity, coordinates, and provenance
    NAVIGABLE = 1 << 1             # Tier 2: Connected to OSM road network, walkable/drivable entrance
    VISITABLE = 1 << 2             # Tier 3: Has doors/access, aforo limits, entry requirements
    SCHEDULED = 1 << 3             # Tier 4: Opening & closing hours, curfews, shifts
    SERVICE_PROVIDER = 1 << 4      # Tier 5: Finite medical, educational, religious, repair services
    INVENTORY_STORAGE = 1 << 5     # Tier 6: Physical stock, finite supplies, perishables
    SOCIAL_INTERACTION = 1 << 6    # Tier 7: Encounters, conversations, collective activities
    ECONOMIC_CONSEQUENCES = 1 << 7 # Tier 8: Rents, wages, retail transactions, prices, operating costs


class PlaceCategory(str, enum.Enum):
    """Categorization of urban and rural locations in El Salvador."""
    HOUSING = "housing"
    ROOM = "room"
    STREET = "street"
    SIDEWALK = "sidewalk"
    PARK = "park"
    MARKET = "market"
    SUPERMARKET = "supermarket"
    STORE = "store"
    SHOPPING_CENTER = "shopping_center"
    RESTAURANT = "restaurant"
    PUPUSERIA = "pupuseria"
    SCHOOL = "school"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    PHARMACY = "pharmacy"
    CHURCH = "church"
    WORKSHOP = "workshop"
    OFFICE = "office"
    FACTORY = "factory"
    TRANSIT_STOP = "transit_stop"
    TERMINAL = "terminal"
    RECREATIONAL = "recreational"
    NATURAL_AREA = "natural_area"


@dataclass
class PlaceService:
    """A discrete service delivered at a location."""
    service_id: str
    name: str
    cost_usd: float = 0.0
    duration_ticks: int = 1
    health_recovery: float = 0.0
    energy_recovery: float = 0.0
    hunger_reduction: float = 0.0
    stress_reduction: float = 0.0
    required_staff_role: Optional[str] = None
    max_simultaneous_clients: int = 4
    current_clients: list[str] = field(default_factory=list)

    def is_available(self) -> bool:
        return len(self.current_clients) < self.max_simultaneous_clients


@dataclass
class PlaceProfile:
    """Verifiable functional capabilities and physical state of a place."""
    place_id: str
    name: str
    category: PlaceCategory
    capabilities: PlaceCapability = PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE
    wgs84_coords: Tuple[float, float] = (13.6978, -89.1915)
    parent_place_id: Optional[str] = None
    sub_places: List[str] = field(default_factory=list)
    capacity: int = 15
    current_occupants: List[str] = field(default_factory=list)
    opening_hour: int = 6
    closing_hour: int = 21
    always_open: bool = False
    is_outdoor: bool = False
    material_condition: float = 1.0  # 0.0 (destroyed) to 1.0 (pristine)
    environmental_exposure: float = 0.20
    operating_cost_per_day: float = 2.0
    cash_box_usd: float = 50.0

    # Services & Inventories
    services: Dict[str, PlaceService] = field(default_factory=dict)
    inventory: Dict[str, int] = field(default_factory=dict)
    price_catalog: Dict[str, float] = field(default_factory=dict)
    staff_uids: List[str] = field(default_factory=list)
    owner_uid: Optional[str] = None
    resident_uids: List[str] = field(default_factory=list)

    def has_capability(self, cap: PlaceCapability) -> bool:
        return bool(self.capabilities & cap)

    def is_open_at(self, hour: int) -> bool:
        if self.always_open or self.category in (PlaceCategory.PARK, PlaceCategory.STREET, PlaceCategory.SIDEWALK, PlaceCategory.NATURAL_AREA):
            return True
        if self.closing_hour > self.opening_hour:
            return self.opening_hour <= hour < self.closing_hour
        # Overnight schedule (e.g., 20h to 4h)
        return hour >= self.opening_hour or hour < self.closing_hour

    def can_enter(self, human_uid: str, hour: int) -> Tuple[bool, str]:
        """Check if a human can legally and physically enter this place."""
        if not self.has_capability(PlaceCapability.VISITABLE):
            return False, "Lugar no visitable físicamente"

        if not self.is_open_at(hour):
            return False, f"Cerrado por horario (Abre a las {self.opening_hour}:00, cierra a las {self.closing_hour}:00)"

        if len(self.current_occupants) >= self.capacity and human_uid not in self.current_occupants:
            return False, f"Lugar saturado (Capacidad máxima {self.capacity} ocupantes alcanzada)"

        # Residential privacy check
        if self.category == PlaceCategory.HOUSING:
            if self.resident_uids and human_uid not in self.resident_uids and human_uid != self.owner_uid:
                # Private home: only residents or invited guests
                return False, "Vivienda privada restringida a sus residentes"

        return True, "Acceso concedido"

    def enter(self, human_uid: str) -> bool:
        if human_uid not in self.current_occupants and len(self.current_occupants) < self.capacity:
            self.current_occupants.append(human_uid)
            return True
        return False

    def leave(self, human_uid: str) -> bool:
        if human_uid in self.current_occupants:
            self.current_occupants.remove(human_uid)
            return True
        return False

    def request_service(self, service_id: str, client_uid: str, client_money: float) -> Dict[str, Any]:
        """Request and execute a service (medical consultation, repairs, dining)."""
        if not self.has_capability(PlaceCapability.SERVICE_PROVIDER):
            return {"success": False, "reason": "Este lugar no presta servicios especializados"}

        srv = self.services.get(service_id)
        if srv is None:
            return {"success": False, "reason": f"Servicio '{service_id}' no disponible"}

        if not srv.is_available():
            return {"success": False, "reason": f"Servicio saturado ({len(srv.current_clients)}/{srv.max_simultaneous_clients} en atención)"}

        if client_money < srv.cost_usd:
            return {"success": False, "reason": f"Fondos insuficientes: requiere ${srv.cost_usd:.2f}, tiene ${client_money:.2f}"}

        # Check for required staff present
        if srv.required_staff_role and not self.staff_uids:
            return {"success": False, "reason": f"Personal ausente: no hay {srv.required_staff_role} de turno"}

        # Consume inventory if this service requires supplies (e.g. medical materials)
        if self.category in (PlaceCategory.CLINIC, PlaceCategory.HOSPITAL):
            med_stock = self.inventory.get("medicamentos", 0)
            if med_stock <= 0:
                return {"success": False, "reason": "Agotado: no hay medicamentos o insumos clínicos disponibles"}
            self.inventory["medicamentos"] = med_stock - 1

        # Execute transaction
        self.cash_box_usd += srv.cost_usd
        return {
            "success": True,
            "cost_usd": srv.cost_usd,
            "health_recovery": srv.health_recovery,
            "energy_recovery": srv.energy_recovery,
            "hunger_reduction": srv.hunger_reduction,
            "stress_reduction": srv.stress_reduction,
            "duration_ticks": srv.duration_ticks,
        }

    def purchase_product(self, product_id: str, quantity: int, buyer_money: float) -> Dict[str, Any]:
        """Purchase goods from this establishment's finite inventory."""
        if not self.has_capability(PlaceCapability.INVENTORY_STORAGE) or not self.has_capability(PlaceCapability.ECONOMIC_CONSEQUENCES):
            return {"success": False, "reason": "Este establecimiento no realiza ventas de inventario"}

        stock = self.inventory.get(product_id, 0)
        if stock <= 0:
            return {"success": False, "reason": f"Producto '{product_id}' agotado"}

        qty_to_buy = min(quantity, stock)
        unit_price = self.price_catalog.get(product_id, 1.0)
        total_cost = unit_price * qty_to_buy

        if buyer_money < total_cost:
            # Check if buyer can afford partial quantity
            affordable_qty = int(buyer_money // unit_price)
            if affordable_qty <= 0:
                return {"success": False, "reason": f"Dinero insuficiente: total ${total_cost:.2f}, disponible ${buyer_money:.2f}"}
            qty_to_buy = affordable_qty
            total_cost = unit_price * qty_to_buy

        self.inventory[product_id] -= qty_to_buy
        self.cash_box_usd += total_cost
        return {
            "success": True,
            "product_id": product_id,
            "quantity_bought": qty_to_buy,
            "unit_price": unit_price,
            "total_cost": total_cost,
            "remaining_stock": self.inventory[product_id],
        }

    def restock(self, product_id: str, quantity: int, cost_per_unit: float = 0.5) -> bool:
        """Restock inventory from commercial supplier."""
        total_cost = cost_per_unit * quantity
        if self.cash_box_usd >= total_cost:
            self.cash_box_usd -= total_cost
            self.inventory[product_id] = self.inventory.get(product_id, 0) + quantity
            return True
        return False

    def apply_environmental_damage(self, amount: float) -> None:
        """Apply structural wear or storm damage."""
        self.material_condition = max(0.0, self.material_condition - amount)

    def repair(self, amount: float, cost_usd: float) -> bool:
        """Repair building structure."""
        if self.cash_box_usd >= cost_usd:
            self.cash_box_usd -= cost_usd
            self.material_condition = min(1.0, self.material_condition + amount)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "category": self.category.value,
            "capabilities": int(self.capabilities),
            "wgs84_coords": [round(c, 6) for c in self.wgs84_coords],
            "parent_place_id": self.parent_place_id,
            "sub_places": list(self.sub_places),
            "capacity": self.capacity,
            "occupant_count": len(self.current_occupants),
            "current_occupants": list(self.current_occupants),
            "opening_hour": self.opening_hour,
            "closing_hour": self.closing_hour,
            "always_open": self.always_open,
            "is_outdoor": self.is_outdoor,
            "material_condition": round(self.material_condition, 2),
            "cash_box_usd": round(self.cash_box_usd, 2),
            "inventory": dict(self.inventory),
            "price_catalog": {k: round(v, 2) for k, v in self.price_catalog.items()},
            "staff_count": len(self.staff_uids),
            "resident_count": len(self.resident_uids),
            "services": {
                s_id: {
                    "name": s.name,
                    "cost_usd": s.cost_usd,
                    "available": s.is_available(),
                    "clients": len(s.current_clients),
                }
                for s_id, s in self.services.items()
            },
        }
