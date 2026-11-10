"""Judicial tribunal: trials, evidence evaluation, verdicts, restitution, and enforcement."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID, Tick
from saltbor.institutions.legal.code import CommunityLegalCode, LegalStatuteType
from saltbor.institutions.legal.officers import PublicOfficer
from saltbor.institutions.model import SocialInstitution
from saltbor.population.human import SyntheticHuman
from saltbor.social.reputation.engine import ContextualReputationEngine

logger = logging.getLogger(__name__)


class VerdictOutcome(enum.Enum):
    """Binding judicial verdict rendered by a tribunal."""

    GUILTY_RESTITUTION_AND_FINE = "guilty_restitution_and_fine"
    GUILTY_COMPENSATION_ONLY = "guilty_compensation_only"
    ACQUITTED_INSUFFICIENT_EVIDENCE = "acquitted_insufficient_evidence"
    MUTUAL_COMPROMISE_SETTLEMENT = "mutual_compromise_settlement"
    DISMISSED_FRIVOLOUS = "dismissed_frivolous"


@dataclass
class LegalCase:
    """A formal lawsuit or criminal complaint filed before the community court."""

    case_id: str
    plaintiff_uid: HumanID
    defendant_uid: HumanID
    statute_type: LegalStatuteType
    claim_description: str
    claimed_damages: float
    filed_tick: Tick

    # Evidence & Trial
    evidence_strength: float = 0.5      # 0.0 (unsubstantiated rumor) to 1.0 (undeniable proof)
    presiding_officer_uid: Optional[HumanID] = None
    witness_uids: list[HumanID] = field(default_factory=list)

    # Resolution
    verdict: Optional[VerdictOutcome] = None
    awarded_restitution: float = 0.0
    court_fine: float = 0.0
    verdict_summary: str = ""
    resolved_tick: Optional[Tick] = None
    is_enforced: bool = False


class JudicialTribunal:
    """Deliberative court of justice: hears cases, delivers rulings, and executes restitution."""

    def __init__(self) -> None:
        self.cases: dict[str, LegalCase] = {}
        self.total_restitution_enforced: float = 0.0
        self.total_fines_collected: float = 0.0

    def file_case(
        self,
        case_id: str,
        plaintiff: SyntheticHuman,
        defendant: SyntheticHuman,
        statute_type: LegalStatuteType,
        claim_description: str,
        claimed_damages: float,
        evidence_strength: float,
        current_tick: Tick,
    ) -> LegalCase:
        """Lodge a formal complaint on the court docket."""
        case = LegalCase(
            case_id=case_id,
            plaintiff_uid=plaintiff.uid,
            defendant_uid=defendant.uid,
            statute_type=statute_type,
            claim_description=claim_description,
            claimed_damages=claimed_damages,
            evidence_strength=min(1.0, max(0.0, evidence_strength)),
            filed_tick=current_tick,
        )
        self.cases[case_id] = case
        logger.info("Court Case %s filed: %s vs %s for $%.2f", case_id, plaintiff.name, defendant.name, claimed_damages)
        return case

    def adjudicate_and_enforce(
        self,
        case_id: str,
        magistrate: SyntheticHuman,
        legal_code: CommunityLegalCode,
        plaintiff: SyntheticHuman,
        defendant: SyntheticHuman,
        municipal_institution: Optional[SocialInstitution],
        reputation_engine: Optional[ContextualReputationEngine],
        current_tick: Tick,
    ) -> VerdictOutcome:
        """Hold hearing, render verdict according to statutory law, and enforce financial transfers."""
        case = self.cases.get(case_id)
        if not case or case.verdict is not None:
            return VerdictOutcome.DISMISSED_FRIVOLOUS

        case.presiding_officer_uid = magistrate.uid
        statute = legal_code.get_statute_for_type(case.statute_type)

        # Adjudication probability: high evidence strength + magistrate conscientiousness
        judge_conscientiousness = (
            magistrate.personality.traits.get_trait_value("conscientiousness")
            if magistrate.personality
            else 0.5
        )
        effective_proof = case.evidence_strength * 0.7 + judge_conscientiousness * 0.3

        if effective_proof >= 0.50:
            # Defendant found liable / guilty
            restitution_mult = statute.restitution_multiplier if statute else 1.0
            fine_amount = statute.prescribed_fine if statute else 10.0

            awarded = round(case.claimed_damages * restitution_mult, 2)
            case.verdict = VerdictOutcome.GUILTY_RESTITUTION_AND_FINE
            case.awarded_restitution = awarded
            case.court_fine = fine_amount

            # Double-entry execution: deduct from defendant
            # Defendant pays what they have
            def_money = defendant.physical_state.money
            paid_restitution = min(def_money, awarded)
            defendant.physical_state.money = round(defendant.physical_state.money - paid_restitution, 2)
            plaintiff.physical_state.money = round(plaintiff.physical_state.money + paid_restitution, 2)

            # Fine to town treasury
            rem_money = defendant.physical_state.money
            paid_fine = min(rem_money, fine_amount)
            defendant.physical_state.money = round(defendant.physical_state.money - paid_fine, 2)
            if municipal_institution:
                municipal_institution.treasury_money = round(municipal_institution.treasury_money + paid_fine, 2)

            self.total_restitution_enforced += paid_restitution
            self.total_fines_collected += paid_fine
            case.is_enforced = True

            # Reputation penalty for defendant
            if reputation_engine:
                prof = reputation_engine.get_or_create(defendant.uid)
                prof.moral_standing = max(0.05, prof.moral_standing - (statute.reputation_penalty if statute else 0.2))
                prof.financial_integrity = max(0.05, prof.financial_integrity - 0.25)

            case.verdict_summary = (
                f"Guilty verdict: Ordered to pay ${paid_restitution:.2f} restitution to {plaintiff.name} "
                f"and ${paid_fine:.2f} civic fine to municipal treasury."
            )

        elif effective_proof >= 0.35:
            # Compromise settlement (partial restitution, no punitive fine)
            half_comp = round(case.claimed_damages * 0.5, 2)
            actual_paid = min(defendant.physical_state.money, half_comp)
            defendant.physical_state.money = round(defendant.physical_state.money - actual_paid, 2)
            plaintiff.physical_state.money = round(plaintiff.physical_state.money + actual_paid, 2)

            case.verdict = VerdictOutcome.MUTUAL_COMPROMISE_SETTLEMENT
            case.awarded_restitution = actual_paid
            case.is_enforced = True
            case.verdict_summary = f"Mutual compromise: Defendant settled ${actual_paid:.2f} without formal liability."

        else:
            # Acquitted
            case.verdict = VerdictOutcome.ACQUITTED_INSUFFICIENT_EVIDENCE
            case.verdict_summary = "Acquitted due to lack of verifiable evidence."

        case.resolved_tick = current_tick
        logger.info("Case %s resolved: %s (%s)", case_id, case.verdict.value, case.verdict_summary)
        return case.verdict
