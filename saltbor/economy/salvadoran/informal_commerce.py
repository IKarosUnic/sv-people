"""
Salvadoran Informal Commerce and Microenterprise Engine (Section 19.4).

Models authentic microeconomic structures of El Salvador:
- Mercados municipales: canasteras, marchantas, ambulantes, narrow margins
- Tiendas de esquina / Pulperías: micro-retailing by fractions ("una cora de queso")
- "El Fiado": informal community credit ledger based on trust and local reputation
- "El Diario": daily cash flow constraints and subsistence purchase strategies
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class FiadoCreditAccount:
    """An informal credit record in a corner store's notebook ('el cuaderno de fiado')."""
    customer_uid: str
    store_id: str
    current_balance_usd: float = 0.0
    credit_limit_usd: float = 25.0
    trust_score: float = 0.80             # [0.0, 1.0] History of timely repayment on Saturdays/paydays
    consecutive_defaults: int = 0
    transaction_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CornerStorePulperia:
    """A neighborhood grocery store ('Tienda de esquina / Pulpería')."""
    store_id: str
    name: str
    owner_uid: str
    location_id: str
    cash_box_usd: float = 65.0
    inventory_items: dict[str, float] = dataclasses.field(default_factory=dict)
    active_credit_accounts: dict[str, FiadoCreditAccount] = dataclasses.field(default_factory=dict)
    daily_sales_volume_usd: float = 0.0


class InformalCommerceEngine:
    """Simulates market vendors, corner stores, and the informal credit economy."""

    def __init__(self) -> None:
        self._stores: dict[str, CornerStorePulperia] = {}

    def register_corner_store(
        self,
        store_id: str,
        name: str,
        owner_uid: str,
        location_id: str,
        starting_cash: float = 50.0,
    ) -> CornerStorePulperia:
        """Open a neighborhood tiendita."""
        store = CornerStorePulperia(
            store_id=store_id,
            name=name,
            owner_uid=owner_uid,
            location_id=location_id,
            cash_box_usd=starting_cash,
            inventory_items={
                "frijol_rojo_lb": 40.0,
                "arroz_lb": 35.0,
                "azucar_lb": 30.0,
                "huevos_unidad": 60.0,
                "pan_frances": 50.0,
                "queso_duro_lb": 15.0,
                "manteca_o_aceite_botella": 12.0,
                "soda_o_jugo_unidad": 24.0,
            },
        )
        self._stores[store_id] = store
        return store

    # -------------------------------------------------------------------------
    # 'El Diario': Daily Cash-in-Hand Retail Purchasing
    # -------------------------------------------------------------------------

    def purchase_del_diario(
        self,
        store_id: str,
        customer_uid: str,
        customer_cash: float,
        needed_items: list[str],
    ) -> dict[str, Any]:
        """Simulate a household buying daily essentials with scarce pocket cash ('el diario')."""
        store = self._stores.get(store_id)
        if not store:
            return {"success": False, "reason": "Tienda no encontrada"}

        item_prices = {
            "frijol_rojo_lb": 1.10,
            "arroz_lb": 0.60,
            "azucar_lb": 0.55,
            "huevos_unidad": 0.20,
            "pan_frances": 0.10,
            "queso_duro_lb": 4.50,
            "manteca_o_aceite_botella": 1.75,
            "soda_o_jugo_unidad": 0.50,
        }

        purchased = {}
        total_spent = 0.0
        remaining_cash = customer_cash

        for item in needed_items:
            unit_price = item_prices.get(item, 0.50)
            if remaining_cash >= unit_price and store.inventory_items.get(item, 0.0) >= 1.0:
                store.inventory_items[item] -= 1.0
                purchased[item] = 1.0
                remaining_cash -= unit_price
                total_spent += unit_price

        store.cash_box_usd += total_spent
        store.daily_sales_volume_usd += total_spent

        return {
            "success": True,
            "store": store.name,
            "total_spent_usd": round(total_spent, 2),
            "remaining_customer_cash": round(remaining_cash, 2),
            "purchased_items": purchased,
        }

    # -------------------------------------------------------------------------
    # 'El Fiado': Informal Credit Management
    # -------------------------------------------------------------------------

    def request_fiado_credit(
        self,
        store_id: str,
        customer_uid: str,
        item_amount_usd: float,
        customer_reputation: float = 0.75,
    ) -> dict[str, Any]:
        """Request store owner to write purchase onto informal credit notebook."""
        store = self._stores.get(store_id)
        if not store:
            return {"approved": False, "reason": "Tienda no encontrada"}

        account = store.active_credit_accounts.get(customer_uid)
        if not account:
            # Grant initial credit account if customer is known and has decent reputation
            if customer_reputation >= 0.50:
                account = FiadoCreditAccount(
                    customer_uid=customer_uid,
                    store_id=store_id,
                    credit_limit_usd=15.0 + (customer_reputation * 20.0),
                    trust_score=customer_reputation,
                )
                store.active_credit_accounts[customer_uid] = account
            else:
                return {
                    "approved": False,
                    "reason": "Dueña de tienda no fía a desconocidos o clientes con mala reputación",
                }

        # Check credit limit
        if account.current_balance_usd + item_amount_usd > account.credit_limit_usd:
            return {
                "approved": False,
                "reason": f"Límite de fiado superado (${account.current_balance_usd:.2f}/${account.credit_limit_usd:.2f})",
            }

        account.current_balance_usd += item_amount_usd
        account.transaction_history.append({
            "type": "credit_purchase",
            "amount": item_amount_usd,
            "balance": account.current_balance_usd,
        })

        return {
            "approved": True,
            "customer_uid": customer_uid,
            "charged_usd": round(item_amount_usd, 2),
            "new_balance_usd": round(account.current_balance_usd, 2),
            "trust_score": round(account.trust_score, 2),
            "status": "Apuntado en el cuaderno para pagar el sábado",
        }

    def settle_fiado_balance(
        self,
        store_id: str,
        customer_uid: str,
        payment_amount_usd: float,
    ) -> dict[str, Any]:
        """Customer comes to settle their informal debt (e.g. after receiving wage or remittance)."""
        store = self._stores.get(store_id)
        if not store or customer_uid not in store.active_credit_accounts:
            return {"success": False, "reason": "No active credit account"}

        account = store.active_credit_accounts[customer_uid]
        paid = min(account.current_balance_usd, payment_amount_usd)
        account.current_balance_usd -= paid
        store.cash_box_usd += paid

        # Repaying boosts trust and raises credit limit
        account.trust_score = min(1.0, account.trust_score + 0.05)
        account.credit_limit_usd = min(60.0, account.credit_limit_usd + 2.50)

        return {
            "success": True,
            "amount_paid_usd": round(paid, 2),
            "remaining_debt_usd": round(account.current_balance_usd, 2),
            "updated_trust_score": round(account.trust_score, 2),
            "new_credit_limit_usd": round(account.credit_limit_usd, 2),
        }
