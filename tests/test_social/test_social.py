"""Tests for social relationships and group dynamics."""

from saltbor.core.identity import HumanIdentity
from saltbor.core.types import RelationshipType
from saltbor.social.engine import SocialEngine


def test_social_relationship_evolution():
    social = SocialEngine()
    id_a = HumanIdentity().uid
    id_b = HumanIdentity().uid

    # Initially stranger
    rel = social.get_relationship(id_a, id_b)
    assert rel.relationship_type == RelationshipType.STRANGER
    assert rel.interaction_count == 0

    # Record repeated positive interactions
    for t in range(1, 6):
        social.record_interaction(id_a, id_b, tick=t * 10, positive=True, intensity=0.7)

    updated_rel = social.get_relationship(id_a, id_b)
    assert updated_rel.interaction_count == 5
    assert updated_rel.trust > 0.55
    assert updated_rel.affinity > 0.55
    assert updated_rel.relationship_type in (RelationshipType.ACQUAINTANCE, RelationshipType.FRIEND)
