"""Unit and integration tests for Phase 0.5 Institutions & Governance."""

import pytest
from saltbor.institutions.model import SocialInstitution, InstitutionType, MemberRole, InstitutionalPolicy
from saltbor.institutions.governance import GovernanceEngine, VotingProtocol
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry


def test_social_institution_dues_and_aid():
    pop = PopulationRegistry()
    m1 = SyntheticHuman.create(name="Farmer Juan", serial=1, age=35.0, seed=1)
    m2 = SyntheticHuman.create(name="Farmer Rosa", serial=2, age=40.0, seed=2)
    m1.physical_state.money = 20.0
    m2.physical_state.money = 20.0
    pop.register(m1)
    pop.register(m2)

    inst = SocialInstitution(
        institution_id="inst_coop",
        name="Saltbor Farmers Cooperative",
        institution_type=InstitutionType.AGRICULTURAL_COOPERATIVE,
        charter_description="Comunal seed and grain fund",
        headquarters_location_id="cooperativa_agricola",
        treasury_money=0.0,
        periodic_dues=5.0,
    )

    inst.add_member(m1.uid, role=MemberRole.PRESIDENT)
    inst.add_member(m2.uid, role=MemberRole.ACTIVE_MEMBER)

    # Collect dues (2 members * 5 = 10)
    collected = inst.collect_dues_from_members(pop, current_tick=20)
    assert collected == 10.0
    assert inst.treasury_money == 10.0
    assert m1.physical_state.money == 15.0
    assert m2.physical_state.money == 15.0

    # Disburse mutual aid
    paid = inst.disburse_mutual_aid(m1, amount=6.0, reason="Tool repair", current_tick=25)
    assert paid is True
    assert inst.treasury_money == 4.0
    assert m1.physical_state.money == 21.0


def test_governance_voting_and_feasibility():
    inst = SocialInstitution(
        institution_id="inst_council",
        name="Village Council",
        institution_type=InstitutionType.COMMUNITY_COUNCIL,
        charter_description="Neighborhood council",
        headquarters_location_id="casa_comunal",
        treasury_money=50.0,
    )

    elder1 = SyntheticHuman.create(name="Elder A", serial=10, age=60.0, seed=10)
    elder2 = SyntheticHuman.create(name="Elder B", serial=11, age=62.0, seed=11)
    elder3 = SyntheticHuman.create(name="Elder C", serial=12, age=65.0, seed=12)

    inst.add_member(elder1.uid, MemberRole.PRESIDENT)
    inst.add_member(elder2.uid, MemberRole.ACTIVE_MEMBER)
    inst.add_member(elder3.uid, MemberRole.ACTIVE_MEMBER)

    gov = GovernanceEngine()

    # Pass proposal (cost 20 <= treasury 50)
    prop_pass = gov.submit_proposal(
        proposal_id="prop_01",
        institution=inst,
        title="Grain Storage Expansion",
        description="Expand communal granary",
        proposer=elder1,
        required_funds=20.0,
        protocol=VotingProtocol.SIMPLE_MAJORITY,
        current_tick=30,
    )
    gov.cast_vote(prop_pass.proposal_id, elder1, in_favor=True)
    gov.cast_vote(prop_pass.proposal_id, elder2, in_favor=True)
    gov.cast_vote(prop_pass.proposal_id, elder3, in_favor=False)

    resolved, enacted, summary = gov.resolve_proposal(prop_pass.proposal_id, inst, current_tick=35)
    assert resolved is True
    assert enacted is True
    assert inst.treasury_money == 30.0

    # Reject infeasible proposal (cost 100 > treasury 30)
    prop_fail = gov.submit_proposal(
        proposal_id="prop_02",
        institution=inst,
        title="Expensive Gold Monument",
        description="Statue for square",
        proposer=elder1,
        required_funds=100.0,
        protocol=VotingProtocol.SIMPLE_MAJORITY,
        current_tick=36,
    )
    gov.cast_vote(prop_fail.proposal_id, elder1, in_favor=True)
    gov.cast_vote(prop_fail.proposal_id, elder2, in_favor=True)

    resolved_f, enacted_f, summary_f = gov.resolve_proposal(prop_fail.proposal_id, inst, current_tick=40)
    assert resolved_f is True
    assert enacted_f is False
    assert "exceed treasury balance" in summary_f
    assert inst.treasury_money == 30.0
