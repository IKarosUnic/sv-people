"""Tests for SQLite persistence, checkpoints, and state recovery."""

from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.repositories import (
    HumanRepository,
    RelationshipRepository,
    SimulationStateRepository,
)
from saltbor.population.factory import PopulationFactory
from saltbor.social.engine import SocialEngine


def test_full_persistence_lifecycle(temp_db: DatabaseManager, population_20):
    h_repo = HumanRepository(temp_db)
    r_repo = RelationshipRepository(temp_db)
    s_repo = SimulationStateRepository(temp_db)

    # 1. Save all humans
    h_repo.save_all(population_20)
    assert h_repo.count() == 20

    # 2. Re-load and verify
    reloaded_humans = h_repo.load_all()
    assert len(reloaded_humans) == 20
    for original, loaded in zip(population_20, reloaded_humans):
        assert original.uid == loaded.uid
        assert original.identity.serial == loaded.identity.serial
        assert original.demographics.age == loaded.demographics.age
        assert original.demographics.occupation == loaded.demographics.occupation

    # 3. Relationships persistence
    social = SocialEngine()
    PopulationFactory.setup_initial_relationships(population_20, social)
    rels = social.get_all_relationships()
    r_repo.save_all(rels)

    loaded_rels = r_repo.load_all()
    assert len(loaded_rels) == len(rels)

    # 4. State checkpointing
    s_repo.save_tick(192)
    assert s_repo.load_tick() == 192
