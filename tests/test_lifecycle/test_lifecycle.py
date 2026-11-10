"""Comprehensive unit tests for the Biological Lifecycle system (Phase 0.4)."""

import uuid
from uuid import UUID
import pytest
import numpy as np

from saltbor.core.identity import HumanIdentity
from saltbor.core.types import DataSource, Gender
from saltbor.events.bus import EventBus
from saltbor.events.types import EventType
from saltbor.lifecycle.aging.clock import AgingEngine, BiologicalProfile
from saltbor.lifecycle.demographics.stages import (
    DevelopmentalStage,
    get_stage_for_age,
)
from saltbor.lifecycle.development.model import ChildDevelopmentEngine
from saltbor.lifecycle.family.household import Household, HouseholdRegistry
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph
from saltbor.lifecycle.genetics.inheritance import GeneticsEngine, Genome
from saltbor.lifecycle.mortality.death import MortalityEngine
from saltbor.lifecycle.mortality.grief import GriefEngine
from saltbor.lifecycle.reproduction.mating import ReproductionEngine
from saltbor.lifecycle.reproduction.pregnancy import Pregnancy
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.social.engine import SocialEngine


def _make_test_human(
    name: str = "Test Person",
    age: int = 25,
    gender: Gender = Gender.FEMALE,
    money: float = 100.0,
    health: float = 1.0,
) -> SyntheticHuman:
    uid = uuid.uuid4()
    ident = HumanIdentity(
        uid=uid,
        serial=1,
        given_name=name.split()[0],
        family_name=name.split()[-1],
        data_source=DataSource.MOCK_GENERATED,
    )
    demo = Demographics(
        age=age,
        gender=gender,
        occupation="farmer",
        birth_tick=0,
    )
    phys = PhysicalState(
        health=health,
        energy=1.0,
        hunger=0.0,
        money=money,
        current_location_id="casa_residencial_1",
        home_location_id="casa_residencial_1",
    )
    pers = PersonalityEngine(PersonalityTraits())
    emot = EmotionalEngine()
    mem = MemoryEngine()
    return SyntheticHuman(
        identity=ident,
        demographics=demo,
        physical_state=phys,
        personality=pers,
        emotions=emot,
        memory=mem,
    )


def test_developmental_stages():
    """Verify age-to-stage mappings across the human lifespan."""
    assert get_stage_for_age(0.5) == DevelopmentalStage.INFANCY
    assert get_stage_for_age(2.0) == DevelopmentalStage.INFANCY
    assert get_stage_for_age(4.0) == DevelopmentalStage.EARLY_CHILDHOOD
    assert get_stage_for_age(8.0) == DevelopmentalStage.CHILDHOOD
    assert get_stage_for_age(15.0) == DevelopmentalStage.ADOLESCENCE
    assert get_stage_for_age(22.0) == DevelopmentalStage.EARLY_ADULTHOOD
    assert get_stage_for_age(40.0) == DevelopmentalStage.ADULTHOOD
    assert get_stage_for_age(70.0) == DevelopmentalStage.OLDER_ADULTHOOD


def test_genetics_recombination_and_non_determinism():
    """Verify inheritance recombines parents with bounded variation without strict determinism."""
    rng = np.random.default_rng(42)
    engine = GeneticsEngine(mutation_rate=0.05, rng=rng)

    parent_a = Genome(temperament_openness=0.8, temperament_conscientiousness=0.3)
    parent_b = Genome(temperament_openness=0.2, temperament_conscientiousness=0.7)

    child = engine.recombine(parent_a, parent_b)

    # Child trait should lie in reasonable blend range plus/minus mutation
    assert 0.15 <= child.temperament_openness <= 0.85
    assert 0.25 <= child.temperament_conscientiousness <= 0.75
    # Must not be an exact copy of either parent
    assert child.temperament_openness != parent_a.temperament_openness
    assert child.temperament_openness != parent_b.temperament_openness


def test_genealogy_graph():
    """Verify bidirectional kinship tracking, ancestral paths, and kinship degrees."""
    g = GenealogicalGraph()
    p1 = uuid.uuid4()
    p2 = uuid.uuid4()
    child = uuid.uuid4()
    grandchild = uuid.uuid4()

    g.register_individual(p1, generation=0)
    g.register_individual(p2, generation=0)
    g.record_partnership(p1, p2)

    g.record_birth(child_uid=child, parent_a_uid=p1, parent_b_uid=p2, tick=10)
    g.record_birth(child_uid=grandchild, parent_a_uid=child, tick=20)

    assert g.get_parents(child) == [p1, p2]
    assert child in g.get_children(p1)
    assert child in g.get_children(p2)
    assert set(g.get_grandparents(grandchild)) == {p1, p2}

    # Kinship degree
    assert g.get_kinship_degree(child, p1) == 1
    assert g.get_kinship_degree(grandchild, p1) == 2
    assert g.is_related(p1, grandchild) is True

    # Generation calculation
    assert g.get_record(child).generation == 1
    assert g.get_record(grandchild).generation == 2


def test_household_and_succession():
    """Verify household management, caregiver assignments, and inheritance upon death."""
    hreg = HouseholdRegistry()
    g = GenealogicalGraph()

    father = _make_test_human("Padre Perez", age=35, gender=Gender.MALE, money=200.0)
    mother = _make_test_human("Madre Perez", age=32, gender=Gender.FEMALE, money=50.0)
    infant = _make_test_human("Bebe Perez", age=1, gender=Gender.MALE, money=0.0)

    g.register_individual(father.uid)
    g.register_individual(mother.uid)
    g.record_partnership(father.uid, mother.uid)
    g.record_birth(infant.uid, father.uid, mother.uid)

    house = hreg.create_household(
        name="Familia Perez",
        residence_location_id="casa_residencial_1",
        members=[father.uid, mother.uid],
        head=father.uid,
    )
    house.add_member(infant.uid, is_dependent=True)
    house.assign_caregiver(infant.uid, mother.uid)

    assert house.get_caregiver_for(infant.uid) == mother.uid
    assert infant.uid in house.dependents

    # Father passes away: test inheritance
    distribution = house.process_succession_and_inheritance(
        deceased_uid=father.uid,
        personal_funds=father.physical_state.money,
        genealogy=g,
    )

    # 50% to spouse, 50% to child
    assert distribution[mother.uid] == pytest.approx(100.0, abs=1.0)
    assert distribution[infant.uid] == pytest.approx(100.0, abs=1.0)
    # New head should become mother
    assert house.head_of_household == mother.uid


def test_pregnancy_and_mating():
    """Verify courtship compatibility, conception, and gestation progression."""
    rng = np.random.default_rng(123)
    rep_eng = ReproductionEngine(gestation_ticks=10, conception_probability_base=1.0, rng=rng)
    g = GenealogicalGraph()

    female = _make_test_human("Maria Lopez", age=26, gender=Gender.FEMALE)
    male = _make_test_human("Carlos Lopez", age=28, gender=Gender.MALE)

    g.register_individual(female.uid)
    g.register_individual(male.uid)

    compat = rep_eng.evaluate_mating_compatibility(
        female, male, g, mutual_trust=0.8, mutual_affinity=0.8
    )
    assert compat > 0.65

    preg = rep_eng.attempt_conception(
        female, male, g, mutual_trust=0.9, mutual_affinity=0.9, current_tick=100
    )
    assert preg is not None
    assert rep_eng.is_pregnant(female.uid) is True

    # Advance gestation
    due_list = rep_eng.update_pregnancies(delta_ticks=5)
    assert len(due_list) == 0
    assert 0.49 <= preg.progress <= 0.51

    # Advance until due
    due_list = rep_eng.update_pregnancies(delta_ticks=5)
    assert len(due_list) == 1
    assert preg.is_due is True

    # Delivery
    rep_eng.complete_delivery(female.uid)
    assert rep_eng.is_pregnant(female.uid) is False


def test_aging_and_development():
    """Verify continuous biological aging and developmental transitions."""
    aging = AgingEngine(ticks_per_year=100.0) # 100 ticks per year for fast testing
    dev_eng = ChildDevelopmentEngine()

    prof = aging.create_profile(birth_tick=0, initial_age_years=2.9)
    assert prof.current_stage == DevelopmentalStage.INFANCY

    # Advance by 20 ticks (0.2 years -> age 3.1)
    changed = aging.step_individual(prof, current_tick=20)
    assert changed is True
    assert prof.current_stage == DevelopmentalStage.EARLY_CHILDHOOD
    assert prof.current_age_years == pytest.approx(3.1, abs=0.01)

    caps = dev_eng.get_capabilities(prof.current_stage)
    assert caps.requires_caregiver is True
    assert caps.school_readiness is False


def test_mortality_and_grief():
    """Verify mortality hazard evaluation, death processing, and survivor grief."""
    mort = MortalityEngine(base_makeham_hazard=0.0001, gompertz_alpha=0.0001, gompertz_gamma=0.08)
    grief_eng = GriefEngine()
    g = GenealogicalGraph()
    hreg = HouseholdRegistry()
    social = SocialEngine()
    bus = EventBus()

    young = _make_test_human("Young Person", age=22)
    elder = _make_test_human("Elder Person", age=88)

    hazard_young = mort.calculate_mortality_hazard(young, ticks_per_year=1000.0, ticks_elapsed=100)
    hazard_elder = mort.calculate_mortality_hazard(elder, ticks_per_year=1000.0, ticks_elapsed=100)
    assert hazard_elder > hazard_young * 5.0

    # Test death processing
    g.register_individual(young.uid)
    g.register_individual(elder.uid)
    g.record_birth(young.uid, parent_a_uid=elder.uid)
    social.record_interaction(young.uid, elder.uid, tick=1, positive=True, intensity=0.9)

    death_info = mort.process_death(
        human=elder,
        current_tick=500,
        genealogy=g,
        households=hreg,
        event_bus=bus,
    )
    assert mort.is_deceased(elder.uid) is True
    assert g.get_record(elder.uid).is_alive is False

    # Apply bereavement to child
    grief_intensity = grief_eng.apply_bereavement(
        survivor=young,
        deceased_uid=elder.uid,
        deceased_name=elder.name,
        social=social,
        genealogy=g,
        current_tick=500,
    )
    assert grief_intensity >= 0.70
    assert young.emotions.profile.get_intensity(young.emotions.profile.active_emotions[list(young.emotions.profile.active_emotions.keys())[0]].emotion_type) > 0.0
