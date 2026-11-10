"""Unit and integration tests for Phase 0.5 Advanced Social Intelligence."""

import pytest
from uuid import uuid4
from saltbor.social.dimensions.relationship import MultiDimensionalRelationship, RelationshipType
from saltbor.social.network.analyzer import SocialNetworkAnalyzer
from saltbor.social.reputation.engine import ContextualReputationEngine
from saltbor.social.conflict.dispute import CollectiveConflictManager, DisputeCause, DisputeStage
from saltbor.population.human import SyntheticHuman


def test_multidimensional_relationship_and_asymmetry():
    u1, u2 = uuid4(), uuid4()
    rel = MultiDimensionalRelationship(relationship_id="r12", human_a_id=u1, human_b_id=u2)
    assert rel.trust == 0.5
    assert rel.resentment == 0.0

    # Betrayal event
    rel.record_interaction(
        tick=10,
        interaction_type="betrayal",
        description="Broke a vital trade promise",
        trust_delta=-0.45,
        conflict_delta=0.4,
    )
    assert rel.trust <= 0.05
    assert rel.resentment >= 0.5
    assert rel.conflict >= 0.4

    # Minor positive cooperation does not instantly erase resentment
    rel.record_interaction(
        tick=15,
        interaction_type="cooperate",
        description="Shared minor tool",
        trust_delta=0.05,
    )
    assert rel.resentment >= 0.45  # Lasting resentment remains


def test_social_network_analyzer_topology():
    analyzer = SocialNetworkAnalyzer()
    uids = [uuid4() for _ in range(5)]
    # Form cluster 1: [0, 1, 2] and cluster 2: [2, 3, 4] where node 2 is a social bridge
    rels = [
        MultiDimensionalRelationship("r01", uids[0], uids[1], trust=0.8, affection=0.7),
        MultiDimensionalRelationship("r02", uids[0], uids[2], trust=0.7, affection=0.6),
        MultiDimensionalRelationship("r12", uids[1], uids[2], trust=0.75, affection=0.65),
        MultiDimensionalRelationship("r23", uids[2], uids[3], trust=0.65, affection=0.60),
        MultiDimensionalRelationship("r34", uids[3], uids[4], trust=0.85, affection=0.80),
    ]

    report = analyzer.analyze_settlement_network(uids, rels)
    assert report.total_nodes == 5
    assert report.total_edges == 5

    adj = analyzer.build_graph(rels)
    bridge_metrics = analyzer.analyze_individual(uids[2], adj, rels)
    assert bridge_metrics.degree == 3


def test_contextual_reputation():
    rep_engine = ContextualReputationEngine()
    builder = SyntheticHuman.create(name="Builder Carlos", serial=1, age=40.0, seed=1)

    # Record positive craft deeds
    rep_engine.record_production_success(builder.uid, quality_boost=0.3)
    # Record default on loan
    rep_engine.record_loan_repayment(builder.uid, on_time=False)

    prof = rep_engine.get_or_create(builder.uid)
    assert prof.craft_competence > 0.7
    assert prof.financial_integrity < 0.4

    craft_inf = prof.calculate_influence_in_context("craft")
    econ_inf = prof.calculate_influence_in_context("economic")
    assert craft_inf > econ_inf


def test_collective_conflict_resolution():
    conflict_mgr = CollectiveConflictManager()
    p1 = SyntheticHuman.create(name="Farmer 1", serial=10, age=35.0, seed=10)
    p2 = SyntheticHuman.create(name="Farmer 2", serial=11, age=36.0, seed=11)
    elder = SyntheticHuman.create(name="Elder Sofia", serial=12, age=65.0, seed=12)

    disp = conflict_mgr.initiate_dispute(
        dispute_id="disp_water_1",
        cause=DisputeCause.RESOURCE_SCARCITY,
        description="Well Access Dispute",
        initiator_uid=p1.uid,
        respondent_uid=p2.uid,
        current_tick=50,
    )
    assert disp.stage == DisputeStage.GRIEVANCE

    # Attempt third-party mediation
    resolved = disp.mediate_by_third_party(elder, tick=55, mediator_respect=0.85)
    assert resolved is True
    assert disp.stage == DisputeStage.RESOLVED
