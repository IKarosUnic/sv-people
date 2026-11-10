"""Population factory — initializes and differentiates synthetic humans.

Assembles 20 unique individuals with realistic profiles, diverse occupations,
varied psychological starting conditions, skills, and pre-existing relationships.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from saltbor.cognition.autonomy.engine import AutonomyEngine
from saltbor.cognition.cognitive.engine import CognitiveEngine
from saltbor.cognition.decision.engine import DecisionEngine
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.emotions.models import EmotionalProfile
from saltbor.cognition.learning.engine import LearningEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.procedural import Skill
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import HumanIdentity, IdentityFactory
from saltbor.core.types import DataSource, RelationshipType, SkillCategory
from saltbor.datasets.mock_data import MockDataGenerator
from saltbor.datasets.nemotron_adapter import NemotronAdapter
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.social.engine import SocialEngine
from saltbor.social.relationship import Relationship

logger = logging.getLogger(__name__)


class PopulationFactory:
    """Instantiates and configures the initial population of Saltbor."""

    @classmethod
    def create_population(
        cls,
        config: Optional[SimulationConfig] = None,
        identity_factory: Optional[IdentityFactory] = None,
        rng: Optional[np.random.Generator] = None,
        try_nemotron: bool = True,
    ) -> list[SyntheticHuman]:
        """Generate the first 20 differentiated synthetic humans of Saltbor."""
        cfg = config or SimulationConfig()
        id_factory = identity_factory or IdentityFactory()
        master_rng = rng or (
            np.random.default_rng(cfg.random_seed)
            if cfg.random_seed is not None
            else np.random.default_rng()
        )

        # 1. Check for Nemotron dataset; fallback to mock generator
        adapter = NemotronAdapter()
        dataset_available = try_nemotron and adapter.try_load()
        if dataset_available:
            logger.info("Using NVIDIA Nemotron Personas El Salvador dataset.")
            profiles = adapter.get_profiles(cfg.initial_population_size)
        else:
            logger.info("Using curated Saltbor mock personas (differentiated profiles).")
            profiles = MockDataGenerator.get_personas(cfg.initial_population_size)

        humans: list[SyntheticHuman] = []

        for p_data in profiles:
            agent_rng = np.random.default_rng(master_rng.integers(0, 2**31 - 1))

            # Identity
            ident = id_factory.create(
                given_name=p_data["given_name"],
                family_name=p_data["family_name"],
                nickname=p_data.get("nickname"),
                data_source=p_data.get("data_source", DataSource.MOCK_GENERATED),
            )

            # Demographics
            demo = Demographics(
                age=p_data["age"],
                gender=p_data["gender"],
                occupation=p_data["occupation"],
                education_level=p_data.get("education_level", "Secundaria"),
                income_level=p_data.get("income_level", 0.5),
                data_source=p_data.get("data_source", DataSource.MOCK_GENERATED),
            )

            # Physical State
            home_loc = p_data.get("home_id", "casa_norte_1")
            work_loc = p_data.get("work_id", "plaza_central")
            phys = PhysicalState(
                energy=float(agent_rng.uniform(0.85, 1.0)),
                hunger=float(agent_rng.uniform(0.10, 0.25)),
                health=1.0,
                current_location_id=home_loc,
                money=p_data.get("money", 100.0),
                home_location_id=home_loc,
                work_location_id=work_loc,
            )

            # Personality
            raw_traits = p_data.get("personality", {})
            trait_values = {}
            for t_name in [
                "openness", "conscientiousness", "extraversion", "agreeableness",
                "neuroticism", "risk_tolerance", "patience", "persistence"
            ]:
                base = raw_traits.get(t_name, 0.5)
                # Add subtle individual variance (±0.04)
                jittered = max(0.05, min(0.95, base + float(agent_rng.normal(0.0, 0.03))))
                trait_values[t_name] = TraitValue(base_value=jittered, current_value=jittered)

            traits = PersonalityTraits(**trait_values)
            personality_eng = PersonalityEngine(traits)

            # Emotions
            profile = EmotionalProfile()
            emotional_eng = EmotionalEngine(profile=profile)

            # Memory
            mem_eng = MemoryEngine(config=cfg)

            # Seed starting trade/professional skills
            occ_skill = Skill(
                skill_id=f"skill_{p_data['occupation'].lower().replace(' ', '_')[:20]}",
                name=p_data["occupation"],
                category=SkillCategory.TECHNICAL,
                level=0.55 if demo.age > 30 else 0.30,
                experience_points=120.0 if demo.age > 30 else 40.0,
            )
            mem_eng.procedural.add_skill(occ_skill)

            # General social skill
            social_skill = Skill(
                skill_id="skill_social_conversation",
                name="Conversación Vecinal",
                category=SkillCategory.SOCIAL,
                level=0.40,
                experience_points=60.0,
            )
            mem_eng.procedural.add_skill(social_skill)

            # Human aggregate root
            human = SyntheticHuman(
                identity=ident,
                demographics=demo,
                physical_state=phys,
                personality=personality_eng,
                emotions=emotional_eng,
                memory=mem_eng,
                cognition=CognitiveEngine(),
                learning=LearningEngine(),
                autonomy=AutonomyEngine(),
                decision=DecisionEngine(),
                rng=agent_rng,
            )
            humans.append(human)

        return humans

    @classmethod
    def setup_initial_relationships(
        cls,
        humans: list[SyntheticHuman],
        social_engine: SocialEngine,
    ) -> None:
        """Connect individuals through pre-existing family, colleague, and neighbor ties."""
        serial_to_id = {h.identity.serial: h.uid for h in humans}
        rel_specs = MockDataGenerator.get_initial_relationships()

        for spec in rel_specs:
            sa = spec["serial_a"]
            sb = spec["serial_b"]
            if sa in serial_to_id and sb in serial_to_id:
                uid_a = serial_to_id[sa]
                uid_b = serial_to_id[sb]

                rel_type_map = {
                    "partner": RelationshipType.PARTNER,
                    "family": RelationshipType.FAMILY,
                    "close_friend": RelationshipType.CLOSE_FRIEND,
                    "friend": RelationshipType.FRIEND,
                    "colleague": RelationshipType.COLLEAGUE,
                }
                r_type = rel_type_map.get(spec["type"], RelationshipType.ACQUAINTANCE)

                rel = Relationship(
                    human_a_id=uid_a,
                    human_b_id=uid_b,
                    relationship_type=r_type,
                    trust=spec["trust"],
                    affinity=spec["affinity"],
                    familiarity=spec["familiarity"],
                    interaction_count=5,
                    history=[f"Relación inicial establecida como {r_type.value}."],
                )
                social_engine.add_relationship(rel)
