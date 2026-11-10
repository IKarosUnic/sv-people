"""Unit and integration tests for Phase 0.6 Statutory Law, Court Trials & Restitution."""

import pytest
from saltbor.institutions.legal.code import CommunityLegalCode, LegalStatute, LegalStatuteType
from saltbor.institutions.legal.court import JudicialTribunal, VerdictOutcome
from saltbor.institutions.model import SocialInstitution, InstitutionType
from saltbor.population.human import SyntheticHuman
from saltbor.social.reputation.engine import ContextualReputationEngine


def test_legal_code_statutes():
    code = CommunityLegalCode()
    statute = code.get_statute_for_type(LegalStatuteType.PROPERTY_RIGHTS)
    assert statute is not None
    assert statute.restitution_multiplier == 1.5


def test_judicial_tribunal_trial_and_restitution():
    code = CommunityLegalCode()
    tribunal = JudicialTribunal()
    rep = ContextualReputationEngine()

    council = SocialInstitution(
        institution_id="council_01",
        name="Town Council",
        institution_type=InstitutionType.COMMUNITY_COUNCIL,
        charter_description="Town governance",
        headquarters_location_id="casa_comunal",
        treasury_money=40.0,
    )

    judge = SyntheticHuman.create(name="Judge Carlos", serial=1, age=50.0, seed=1)
    plaintiff = SyntheticHuman.create(name="Victim Juan", serial=2, age=30.0, seed=2)
    defendant = SyntheticHuman.create(name="Culprit Diego", serial=3, age=32.0, seed=3)

    plaintiff.physical_state.money = 10.0
    defendant.physical_state.money = 80.0

    # File case
    case = tribunal.file_case(
        case_id="case_damage_01",
        plaintiff=plaintiff,
        defendant=defendant,
        statute_type=LegalStatuteType.PROPERTY_RIGHTS,
        claim_description="Crop destruction and tool vandalism",
        claimed_damages=20.0,
        evidence_strength=0.9,
        current_tick=10,
    )

    # Adjudicate
    verdict = tribunal.adjudicate_and_enforce(
        case_id=case.case_id,
        magistrate=judge,
        legal_code=code,
        plaintiff=plaintiff,
        defendant=defendant,
        municipal_institution=council,
        reputation_engine=rep,
        current_tick=12,
    )

    assert verdict == VerdictOutcome.GUILTY_RESTITUTION_AND_FINE
    # Restitution is 1.5 * 20 = $30.0; fine is $15.0 -> Total paid by defendant = $45.0
    assert case.awarded_restitution == 30.0
    assert case.court_fine == 15.0
    assert defendant.physical_state.money == 35.0  # 80 - 45
    assert plaintiff.physical_state.money == 40.0  # 10 + 30
    assert council.treasury_money == 55.0  # 40 + 15
    assert case.is_enforced is True
