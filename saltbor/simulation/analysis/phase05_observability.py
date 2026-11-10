"""Phase 0.5 Observability and Causal Provenance Analysis Suite.

Provides transparent inspection tools for cultural lineages, credit ledgers,
business accounting, multi-dimensional relationship arcs, and causal event chains.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from saltbor.core.types import HumanID, Tick
from saltbor.culture.element import CulturalElement
from saltbor.economy.business.enterprise import BusinessEnterprise
from saltbor.economy.credit.loan import LoanContract
from saltbor.institutions.model import SocialInstitution
from saltbor.social.dimensions.relationship import MultiDimensionalRelationship

logger = logging.getLogger(__name__)


class Phase05Observability:
    """Diagnostic inspector rendering interpretable provenance for emergent societal phenomena."""

    @staticmethod
    def inspect_cultural_element(element: CulturalElement) -> dict[str, Any]:
        """Trace the generational lineage, authenticity drift, and adoption spread of a tradition."""
        chain = []
        for evt in element.transmission_history:
            chain.append({
                "tick": evt.tick,
                "from_human": str(evt.from_human_id) if evt.from_human_id else "origin",
                "to_human": str(evt.to_human_id),
                "channel": evt.channel,
                "accepted": evt.accepted,
                "modified": evt.modified,
                "notes": evt.notes,
            })

        return {
            "element_id": element.element_id,
            "name": element.name,
            "element_type": element.element_type.value,
            "description": element.description,
            "origin_human": str(element.origin_human_id) if element.origin_human_id else "foundational",
            "created_tick": element.created_tick,
            "parent_variant_of": element.variant_of_id,
            "authenticity": element.authenticity,
            "confidence": element.confidence,
            "is_abandoned": element.is_abandoned,
            "adoption_count": element.adoption_count,
            "practitioner_uids": [str(u) for u in element.practitioners],
            "geographic_distribution": {str(k): v for k, v in element.geographic_distribution.items()},
            "transmission_chain_length": len(chain),
            "transmission_events": chain,
        }

    @staticmethod
    def inspect_loan_ledger(loan: LoanContract) -> dict[str, Any]:
        """Detailed audit trail of a debt contract, payments, and risk status."""
        return {
            "loan_id": loan.loan_id,
            "borrower_uid": str(loan.borrower_uid),
            "lender_uid": str(loan.lender_uid) if loan.lender_uid else None,
            "lender_institution": loan.lender_institution_id,
            "loan_type": loan.loan_type.value,
            "principal": loan.principal,
            "interest_rate": loan.interest_rate,
            "total_due": loan.total_due,
            "balance_remaining": loan.balance_remaining,
            "status": loan.status.value,
            "issued_tick": loan.issued_tick,
            "due_tick": loan.due_tick,
            "consecutive_missed_payments": loan.consecutive_missed_payments,
            "renegotiations_count": loan.renegotiations_count,
            "payments_history": [
                {
                    "tick": p.tick,
                    "amount": p.amount,
                    "principal_portion": p.principal_portion,
                    "interest_portion": p.interest_portion,
                    "remaining_balance": p.remaining_balance,
                }
                for p in loan.payments
            ],
        }

    @staticmethod
    def inspect_business(biz: BusinessEnterprise) -> dict[str, Any]:
        """Financial and operational overview of an enterprise."""
        return {
            "business_id": biz.business_id,
            "name": biz.name,
            "type": biz.business_type.value,
            "owner_uid": str(biz.owner_uid),
            "location_id": biz.location_id,
            "status": biz.status.value,
            "cash_reserve": round(biz.cash_reserve, 2),
            "accumulated_debt": round(biz.accumulated_debt, 2),
            "employee_count": biz.employee_count,
            "employees": {str(k): v for k, v in biz.employees.items()},
            "inventory_items": {k.value: item.quantity for k, item in biz.inventory._items.items()},
            "total_lifetime_revenue": round(biz.total_lifetime_revenue, 2),
            "total_lifetime_expenses": round(biz.total_lifetime_expenses, 2),
            "reputation": round(biz.reputation, 2),
            "recent_accounting_periods": len(biz.financial_history),
        }

    @staticmethod
    def inspect_relationship(rel: MultiDimensionalRelationship) -> dict[str, Any]:
        """Deep 10-dimensional social inspection of an interpersonal bond."""
        return {
            "relationship_id": rel.relationship_id,
            "human_a": str(rel.human_a_id),
            "human_b": str(rel.human_b_id),
            "qualitative_type": rel.relationship_type.value,
            "dimensions": {
                "affection": round(rel.affection, 3),
                "trust": round(rel.trust, 3),
                "respect": round(rel.respect, 3),
                "familiarity": round(rel.familiarity, 3),
                "cooperation": round(rel.cooperation, 3),
                "dependence": round(rel.dependence, 3),
                "conflict": round(rel.conflict, 3),
                "resentment": round(rel.resentment, 3),
                "reciprocity_balance": round(rel.reciprocity_balance, 2),
                "social_obligation": round(rel.social_obligation, 3),
            },
            "interactions_logged": rel.interaction_count,
            "recent_events": [
                {
                    "tick": e.tick,
                    "type": e.interaction_type,
                    "desc": e.description,
                    "aff_impact": e.impact_affection,
                    "trust_impact": e.impact_trust,
                    "resent_impact": e.impact_resentment,
                }
                for e in rel.history[-5:]
            ],
        }

    @staticmethod
    def inspect_institution(inst: SocialInstitution) -> dict[str, Any]:
        """Governance, legitimacy, and asset health of an institution."""
        return {
            "institution_id": inst.institution_id,
            "name": inst.name,
            "type": inst.institution_type.value,
            "headquarters": inst.headquarters_location_id,
            "member_count": inst.member_count,
            "members": {str(k): v.value for k, v in inst.members.items()},
            "treasury_money": round(inst.treasury_money, 2),
            "reputation": round(inst.reputation, 2),
            "legitimacy": round(inst.legitimacy, 2),
            "active_policies_count": len(inst.enacted_policies),
            "recent_history": inst.history_log[-10:],
        }
