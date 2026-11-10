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


def test_infant_and_stage_persistence(temp_db: DatabaseManager):
    """Verify that newborns (age 0, stage INFANCY, birth_tick) persist and reload with high fidelity."""
    import uuid
    from saltbor.core.identity import HumanIdentity
    from saltbor.core.types import DataSource, Gender
    from saltbor.lifecycle.demographics.stages import DevelopmentalStage
    from saltbor.population.demographics import Demographics
    from saltbor.population.human import SyntheticHuman
    from saltbor.population.physical_state import PhysicalState
    from saltbor.cognition.personality.engine import PersonalityEngine
    from saltbor.cognition.personality.traits import PersonalityTraits
    from saltbor.cognition.emotions.engine import EmotionalEngine
    from saltbor.cognition.memory.engine import MemoryEngine

    h_repo = HumanRepository(temp_db)
    infant = SyntheticHuman(
        identity=HumanIdentity(uid=uuid.uuid4(), serial=99, given_name="Bebe", family_name="Prueba", data_source=DataSource.MOCK_GENERATED),
        demographics=Demographics(age=0, gender=Gender.FEMALE, stage=DevelopmentalStage.INFANCY, birth_tick=50),
        physical_state=PhysicalState(money=0.0, health=1.0),
        personality=PersonalityEngine(PersonalityTraits()),
        emotions=EmotionalEngine(),
        memory=MemoryEngine(),
    )

    h_repo.save(infant)
    reloaded = h_repo.load(infant.uid)

    assert reloaded is not None
    assert reloaded.demographics.age == 0
    assert reloaded.demographics.stage == DevelopmentalStage.INFANCY
    assert reloaded.demographics.birth_tick == 50
    assert reloaded.identity.full_name == "Bebe Prueba"
