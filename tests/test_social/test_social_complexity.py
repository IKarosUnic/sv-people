"""Unit tests for Social Complexity: Dialogue NLG, Rumor Propagation, Groups & Institutions (Phase 0.4)."""

import uuid
import pytest
import numpy as np

from saltbor.social.language.intent import DialogueIntent, Utterance
from saltbor.social.language.nlg import LocalDialogueGenerator
from saltbor.social.language.conversation import ConversationManager
from saltbor.social.information.rumor import RumorEngine
from saltbor.social.institutions.group import EnhancedSocialGroup, GroupType
from saltbor.social.institutions.assembly import CommunityAssembly


def test_offline_dialogue_nlg_variety():
    """Verify offline Spanish NLG generates contextual utterances without external APIs."""
    rng = np.random.default_rng(42)
    nlg = LocalDialogueGenerator(rng=rng)

    speaker = uuid.uuid4()
    listener = uuid.uuid4()

    # Close greeting
    utt_close = Utterance(
        speaker_uid=speaker,
        listener_uid=listener,
        intent=DialogueIntent.GREETING,
        topic="la cosecha",
    )
    text_close = nlg.generate_surface_text(utt_close, trust=0.8, affinity=0.8)
    assert len(text_close) > 10

    # Formal greeting
    utt_formal = Utterance(
        speaker_uid=speaker,
        listener_uid=listener,
        intent=DialogueIntent.GREETING,
        topic="la cosecha",
    )
    text_formal = nlg.generate_surface_text(utt_formal, trust=0.3, affinity=0.3)
    assert ("Buenos" in text_formal or "Buenas" in text_formal or "Saludos" in text_formal)

    # Bereavement condolence
    utt_cond = Utterance(
        speaker_uid=speaker,
        listener_uid=listener,
        intent=DialogueIntent.BEREAVEMENT_CONDOLENCE,
        topic="duelo",
        content_data={"name": "Don Jose"},
    )
    text_cond = nlg.generate_surface_text(utt_cond)
    assert "Don Jose" in text_cond


def test_rumor_propagation_and_belief_dynamics():
    """Verify rumor spreads with provenance, trust-weighted belief, and verification."""
    rng = np.random.default_rng(123)
    engine = RumorEngine(distortion_rate=0.0, rng=rng)

    alice = uuid.uuid4()
    bob = uuid.uuid4()
    charlie = uuid.uuid4()

    # Alice witnesses an event
    item = engine.register_origin_knowledge(
        human_id=alice,
        info_id="market_fire",
        topic="seguridad",
        statement="Hubo un pequeño conato de incendio en el mercado",
        is_true=True,
        current_tick=50,
    )
    assert engine.has_knowledge(alice, "market_fire") is True

    # Alice tells Bob; Bob trusts Alice highly (0.85) -> Believes
    acc, react, item_bob = engine.transmit(
        sender_id=alice,
        receiver_id=bob,
        info_id="market_fire",
        trust_in_sender=0.85,
        current_tick=52,
    )
    assert acc is True
    assert react == "believe"
    assert item_bob.generation == 1
    assert len(item_bob.transmission_chain) == 1

    # Bob tells Charlie; Charlie distrussts Bob (0.2) -> Disbelieves/Rejects
    acc2, react2, _ = engine.transmit(
        sender_id=bob,
        receiver_id=charlie,
        info_id="market_fire",
        trust_in_sender=0.20,
        current_tick=55,
    )
    assert acc2 is False
    assert react2 == "disbelieve"
    assert engine.has_knowledge(charlie, "market_fire") is False


def test_community_assembly_proposals_and_voting():
    """Verify community assembly proposal tabling, quorum, and voting mechanics."""
    assembly = CommunityAssembly()
    proposer = uuid.uuid4()
    member1 = uuid.uuid4()
    member2 = uuid.uuid4()
    member3 = uuid.uuid4()

    prop = assembly.submit_proposal(
        proposal_id="prop_granary",
        title="Construcción de Granero Comunal",
        description="Fondo cooperativo para almacenar reservas de maíz",
        proposer_uid=proposer,
        current_tick=100,
    )
    assert prop.total_votes == 1 # Proposer voted in favor

    # Cast votes
    assembly.cast_vote(prop.proposal_id, member1, vote_in_favor=True)
    assembly.cast_vote(prop.proposal_id, member2, vote_in_favor=True)
    assembly.cast_vote(prop.proposal_id, member3, vote_in_favor=False)

    assert prop.total_votes == 4 # 3 for, 1 against

    # Tally and resolve
    resolved, enacted, summary = assembly.tally_and_resolve(
        proposal_id=prop.proposal_id,
        current_tick=120,
        quorum=3,
        threshold=0.50,
    )
    assert resolved is True
    assert enacted is True
    assert "Passed" in summary
    assert len(assembly.enacted_policies) == 1
