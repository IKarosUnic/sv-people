"""Unit and integration tests for Phase 0.9 Engines."""

import pytest
from saltbor.social.network.graph_engine import (
    SocialNetworkEngine,
    SocialRelationType,
    BondState,
)
from saltbor.social.community.engine import (
    CommunityFormationEngine,
    CommunityType,
    CommunityStatus,
    MembershipRole,
)
from saltbor.social.collective_intelligence.engine import (
    CollectiveIntelligenceEngine,
    SolutionProposal,
)
from saltbor.social.communication.engine import (
    SocialCommunicationEngine,
    CommunicationType,
)
from saltbor.social.reputation.reputation_system import (
    ReputationEngine,
    ReputationDomain,
)
from saltbor.social.conflict.engine import (
    ConflictCooperationEngine,
    ConflictDomain,
    ConflictStage,
)
from saltbor.social.organization.engine import (
    OrganizationalIntelligenceEngine,
    DecisionStatus,
)
from saltbor.social.culture.evolution import (
    CulturalEvolutionEngine,
    CulturalCategory,
)
from saltbor.social.economy.collective_economy import (
    CollectiveEconomyEngine,
    CollectiveOrgType,
)
from saltbor.social.institutions.emergent import (
    EmergentInstitutionEngine,
    InstitutionCategory,
)
from saltbor.social.knowledge_integration import SocialKnowledgeBridge
from saltbor.social.lod import SocialLODManager, SocialLODTier
from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


def test_social_network_engine_ties_and_indirect_influence():
    net = SocialNetworkEngine()
    # Path A -> B -> C
    net.record_interaction("a", "b", tick=10, valence=0.9, intensity=0.8, bidirectional=True)
    net.record_interaction("b", "c", tick=12, valence=0.9, intensity=0.8, bidirectional=True)

    edge_ab = net.get_edge("a", "b")
    assert edge_ab is not None
    assert edge_ab.trust > 0.60
    assert edge_ab.status == BondState.ACTIVE

    # Indirect influence A -> C
    influence_ac = net.get_indirect_influence("a", "c", max_depth=2)
    assert influence_ac > 0.25

    # Triadic closure candidates for A should include C
    candidates = net.find_triadic_closure_candidates("a")
    cand_ids = [cand for cand, bridge, score in candidates]
    assert "c" in cand_ids


def test_community_formation_and_fission():
    engine = CommunityFormationEngine()
    founders = ["f1", "f2", "f3", "f4"]
    comm = engine.form_community(
        name="Asociacion Barrial",
        community_type=CommunityType.NEIGHBORHOOD,
        collective_identity="Vecinos unidos",
        founder_uids=founders,
        tick=5,
    )
    assert comm.active_member_count == 4
    assert comm.cohesion > 0.7

    # Fission: split f3 and f4
    splinter = comm.trigger_fission(tick=20, dissident_uids=["f3", "f4"], new_name="Splinter Barrio")
    assert comm.active_member_count == 2
    assert splinter.active_member_count == 2
    assert splinter.resources.get("funds", 0.0) > 0


def test_collective_intelligence_evidence_weighted_deliberation():
    engine = CollectiveIntelligenceEngine()
    prob = Problem(
        problem_id="p1",
        description="Plaga en milpa",
        domain="agricultura",
        current_state={"plague": True},
        desired_state={"plague": False},
        constraints={"max_cost": 50.0},
        difficulty=0.75,
        required_capabilities=["agricultura"],
    )
    participants = [
        {"uid": "expert", "specialization": "agricultura", "skills": {"agricultura": 0.9}, "experience_years": 10.0, "knowledge_facts": ["caldo_sulfocalcico_elimina_acaro"]},
        {"uid": "novice", "specialization": "general", "skills": {"agricultura": 0.2}, "experience_years": 1.0, "knowledge_facts": ["rezar_para_lluvia"]},
    ]
    proposals = [
        SolutionProposal(
            proposal_id="prop_sulfocalcico",
            author_uid="expert",
            strategy_summary="Aplicacion de biofertilizante sulfocalcico",
            required_tasks=[{"task_name": "preparar_mezcla", "skill_needed": "agricultura", "cost": 15.0}],
            expected_success_probability=0.90,
            total_resource_cost=15.0,
        ),
        SolutionProposal(
            proposal_id="prop_costosa",
            author_uid="novice",
            strategy_summary="Comprar quimico importado prohibitivo",
            required_tasks=[{"task_name": "gastar", "skill_needed": "general", "cost": 250.0}],
            expected_success_probability=0.50,
            total_resource_cost=250.0,
        ),
    ]

    report = engine.coordinate_and_execute(
        session_id="s1",
        problem=prob,
        participants=participants,
        proposals=proposals,
        available_resources={"funds": 50.0},
        tick=10,
    )
    assert report.execution_success is True
    assert report.selected_proposal is not None
    assert report.selected_proposal.proposal_id == "prop_sulfocalcico"
    assert report.outcome == ProblemOutcome.SOLVED


def test_communication_distortion_and_credibility():
    net = SocialNetworkEngine()
    comm = SocialCommunicationEngine(social_network=net)

    # Distort content
    original = "Habra pequeno ajuste de precio en granos"
    distorted = comm.distort_content(original, distortion_factor=0.30)
    assert "(dicen que se duplicara o habra escasez total)" in distorted

    # Direct message
    msg = comm.create_message(
        sender_id="s1",
        recipient_id="r1",
        communication_type=CommunicationType.WARNING,
        subject="sequia",
        content="Posible retraso en invierno",
    )
    delivered = comm.transmit_message(msg, recipient_skepticism=0.2)
    assert delivered.was_believed is True


def test_situated_reputation_and_testimonials():
    rep = ReputationEngine()
    # Good craft
    rep.record_pact_outcome("carlos", "mario", fulfilled=True, domain=ReputationDomain.PROFESSIONAL, tick=10)
    # Bad communal
    rep.record_cooperation_effort("carlos", "ana", cooperated=False, domain=ReputationDomain.COMMUNAL, tick=12)

    prof = rep.get_or_create("carlos", "mario", ReputationDomain.PROFESSIONAL)
    comm = rep.get_or_create("carlos", "ana", ReputationDomain.COMMUNAL)

    assert prof.score > comm.score


def test_conflict_negotiation_and_mediation():
    conflict = ConflictCooperationEngine()
    disp = conflict.initiate_dispute(
        initiator_uid="a",
        respondent_uid="b",
        domain=ConflictDomain.COMMERCIAL_DISPUTE,
        cause_description="Deuda impaga",
        tick=10,
    )
    offer = conflict.propose_offer(disp.dispute_id, proposer_uid="a", concession_summary="Descuento", compensation_value=20.0)
    assert offer is not None

    # Mediated compromise
    conflict.assign_mediator(disp.dispute_id, "elder_c")
    resolved = conflict.mediate_compromise(disp.dispute_id, "Pago de $15 en dos cuotas", tick=20)
    assert resolved is True
    assert disp.stage == ConflictStage.RESOLVED


def test_organizational_intelligence_and_voting():
    org = OrganizationalIntelligenceEngine()
    prop = org.submit_proposal("adesco_1", "lider_1", "Reparacion calle", "Bacheo comunal", cost_usd=30.0, tick=10)
    org.cast_vote(prop.proposal_id, "v1", in_favor=True)
    org.cast_vote(prop.proposal_id, "v2", in_favor=True)
    org.cast_vote(prop.proposal_id, "v3", in_favor=False)

    enacted = org.resolve_proposal(prop.proposal_id, quorum_required=3, tick=20)
    assert enacted is True
    assert prop.status == DecisionStatus.ENACTED


def test_collective_economy_and_dividends():
    econ = CollectiveEconomyEngine()
    ent = econ.create_enterprise("Cooperativa Maicera", CollectiveOrgType.AGRICULTURAL_COOP, ["m1", "m2"], initial_treasury=100.0)
    ent.record_production_output("maiz_quintal", quantity=10.0)
    rev = ent.sell_goods("maiz_quintal", quantity=10.0, unit_price=20.0)
    assert rev == 200.0
    assert ent.total_revenue_earned == 200.0

    payouts = ent.distribute_dividends(100.0)
    assert payouts["m1"] == 50.0
    assert payouts["m2"] == 50.0


def test_emergent_institution_and_bylaws():
    inst_engine = EmergentInstitutionEngine()
    inst = inst_engine.formalize_from_community(
        community_id="comm_1",
        name="Junta de Agua Rural",
        category=InstitutionCategory.NEIGHBORHOOD_COUNCIL,
        charter="Suministro de agua potable",
        officers={"pres": "Presidente"},
        initial_rules=["Cuota mensual $2"],
        tick=10,
    )
    assert inst.is_active is True
    assert len(inst.constitution_bylaws) == 1
    inst.formalize_rule("Reglamento de racionamiento", tick=20)
    assert len(inst.constitution_bylaws) == 2


def test_social_knowledge_bridge_provenance():
    bridge = SocialKnowledgeBridge()
    node = KnowledgeNode(
        node_id="k_craft_1",
        node_type=NodeType.SKILL,
        label="Curtido de Cuero",
        description="Tecnica de curado con taninos vegetales",
        created_tick=10,
        origin_type="discovery",
        origin_id="artisan_juan",
    )
    rec_kg = IndividualKnowledgeGraph(human_uid="learner_pedro")
    receipt = bridge.transmit_to_individual(
        node=node,
        sender_uid="artisan_juan",
        recipient_uid="learner_pedro",
        recipient_kg=rec_kg,
        rel_trust=0.8,
        tick=20,
    )
    assert receipt.was_accepted is True
    rec_node = rec_kg.get_node("k_craft_1")
    assert rec_node is not None
    assert rec_node.origin_type == "peer_transmission"
    assert rec_node.origin_id == "artisan_juan"


def test_social_lod_manager():
    lod = SocialLODManager()
    lod.set_focal_agents(["focal_1"])
    assert lod.get_tier("focal_1") == SocialLODTier.TIER_1_FOCAL
    assert lod.should_process_social_tick("focal_1", tick=1) is True

    # Background agent processes only on tick % 96 == 0
    assert lod.get_tier("bg_1") == SocialLODTier.TIER_3_BACKGROUND
    assert lod.should_process_social_tick("bg_1", tick=1) is False
    assert lod.should_process_social_tick("bg_1", tick=96) is True
