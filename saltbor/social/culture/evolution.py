"""Cultural Evolution and Collective Learning Engine for SALTBOR Phase 0.9 & Phase 1.3 (Section 7).

Models cultural elements, dynamic adoption, intergenerational transmission,
imitation, innovation, mutation, conservation, cultural fragmentation, and extinction of traditions.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import math
import uuid
from typing import Any, Dict, List, Optional, Set
import numpy as np

from saltbor.cognition.development.profile import CognitiveCapability, CognitiveProfile
from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class CulturalCategory(str, enum.Enum):
    """Domains of shared cultural practices and traditions."""

    # Core & Expanded Phase 1.3 Categories
    CULINARY_PRACTICE = "culinary_practice"       # Gastronomía: pupusas revueltas, comal de barro, nixtamalización
    COMMERCIAL_CUSTOM = "commercial_custom"       # Comercio: regateo, fiado de confianza en mercados
    COMMUNAL_TRADITION = "communal_tradition"     # Tradiciones comunitarias: cofradías, faenas comunales
    AGRICULTURAL_TECHNIQUE = "agricultural_technique" # Técnicas agrícolas: milpa intercalada, captación de agua
    ARTISANAL_CRAFT = "artisanal_craft"           # Artesanías: alfarería de Ilobasco, telar de San Sebastián
    LANGUAGE_EXPRESSION = "language_expression"   # Expresiones lingüísticas, modismos salvadoreños
    TEACHING_SYSTEM = "teaching_system"           # Métodos de enseñanza, aprendizaje en taller
    SOCIAL_NORM = "social_norm"                   # Normas sociales: reciprocidad, respeto a ancianos
    ORGANIZATION_FORM = "organization_form"       # Formas de organización: ADESCO, comités de agua
    ENVIRONMENTAL_KNOWLEDGE = "environmental_knowledge" # Saberes climáticos: canícula, temporales
    ARTS_RECREATION = "arts_recreation"           # Prácticas artísticas y festivas: danzas tradicionales


@dataclasses.dataclass
class CulturalTradition:
    """A cultural practice or meme evolving across community generations."""

    tradition_id: str
    name: str
    category: CulturalCategory
    origin_community_id: str
    description: str
    adopters: set[str] = dataclasses.field(default_factory=set)
    utility_score: float = 0.70        # [0.0, 1.0] Perceived functional or social value
    sacredness: float = 0.50           # [0.0, 1.0] Resistance to change / emotional reverence
    fidelity: float = 1.00             # [0.0, 1.0] Transmission fidelity relative to ancestral prototype
    parameters: dict[str, float] = dataclasses.field(default_factory=dict) # Quantitative aspects (e.g. ratios, frequency)
    parent_tradition_id: Optional[str] = None
    variation_notes: list[str] = dataclasses.field(default_factory=list)
    created_tick: int = 0
    last_practiced_tick: int = 0
    is_active: bool = True
    is_extinct: bool = False

    def practice(self, practitioner_uid: str, tick: int) -> None:
        """Practice the tradition, sustaining its vitality."""
        self.adopters.add(str(practitioner_uid))
        self.last_practiced_tick = tick

    def mutate_tradition(self, innovator_uid: str, innovation_summary: str, tick: int) -> None:
        """Introduce an innovation or adaptive tweak to an existing tradition."""
        self.variation_notes.append(f"Tick {tick} by {innovator_uid}: {innovation_summary}")
        self.utility_score = min(1.0, self.utility_score + 0.08)
        self.fidelity = max(0.20, self.fidelity * 0.90)


class CulturalEvolutionEngine:
    """Coordinates collective cultural adoption, innovation, imperfect transmission, and generational drift."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self._traditions: dict[str, CulturalTradition] = {}

    def register_tradition(
        self,
        name: str,
        category: CulturalCategory,
        origin_community_id: str,
        description: str,
        initial_adopters: Optional[list[str]] = None,
        utility_score: float = 0.75,
        sacredness: float = 0.5,
        parameters: Optional[dict[str, float]] = None,
        tick: int = 0,
    ) -> CulturalTradition:
        """Introduce or formalize a cultural tradition."""
        trad_id = f"trad_{category.value[:4]}_{uuid.uuid4().hex[:6]}"
        trad = CulturalTradition(
            tradition_id=trad_id,
            name=name,
            category=category,
            origin_community_id=origin_community_id,
            description=description,
            utility_score=utility_score,
            sacredness=sacredness,
            parameters=parameters or {"practice_intensity": 1.0},
            created_tick=tick,
            last_practiced_tick=tick,
        )
        if initial_adopters:
            trad.adopters.update(str(u) for u in initial_adopters)
        self._traditions[trad_id] = trad
        return trad

    def get_tradition(self, tradition_id: str) -> Optional[CulturalTradition]:
        return self._traditions.get(tradition_id)

    def get_all_traditions(self, active_only: bool = True) -> list[CulturalTradition]:
        if not active_only:
            return list(self._traditions.values())
        return [t for t in self._traditions.values() if t.is_active and not t.is_extinct]

    def transmit_intergenerational(
        self,
        tradition_id: str,
        mentor_uid: str | HumanID,
        apprentice_uid: str | HumanID,
        teaching_quality: float = 0.8,
        tick: int = 0,
    ) -> bool:
        """Pass tradition from elder/mentor to younger apprentice (backward compatibility)."""
        trad = self.get_tradition(tradition_id)
        if not trad or str(mentor_uid) not in trad.adopters:
            return False

        if teaching_quality >= 0.40:
            trad.practice(str(apprentice_uid), tick)
            return True
        return False

    def transmit_imperfect(
        self,
        tradition_id: str,
        source_uid: str,
        learner_uid: str,
        source_profile: Optional[CognitiveProfile] = None,
        learner_profile: Optional[CognitiveProfile] = None,
        trust: float = 0.70,
        prestige: float = 0.60,
        social_closeness: float = 0.80,
        interaction_frequency: int = 2,
        tick: int = 0,
        allow_mutation: bool = True,
    ) -> tuple[bool, str, Optional[CulturalTradition]]:
        """Conduct imperfect cultural transmission taking cognitive capacities into account.

        Factors:
        - Source communication efficacy
        - Learner social learning fidelity and domain comprehension
        - Trust, prestige, and social proximity
        - Interaction frequency (repeated exposures)
        - Possibility of fidelity loss (distortion) or creative mutation
        """
        trad = self.get_tradition(tradition_id)
        if not trad or not trad.is_active:
            return False, "Tradition inactive or not found", None

        if str(learner_uid) in trad.adopters:
            trad.practice(str(learner_uid), tick)
            return True, "Already practicing", trad

        # Teaching skill
        teacher_comm = 0.50
        if source_profile:
            teacher_comm = source_profile.get_level(CognitiveCapability.COMMUNICATION_EFFICACY)

        # Learner fidelity & comprehension
        learner_fid = 0.50
        learner_env = 0.50
        if learner_profile:
            learner_fid = learner_profile.get_level(CognitiveCapability.SOCIAL_LEARNING_FIDELITY)
            learner_env = learner_profile.get_level(CognitiveCapability.ENVIRONMENTAL_ADAPTABILITY)

        # Adoption probability formula
        base_p = (
            0.25 * trust
            + 0.20 * prestige
            + 0.20 * social_closeness
            + 0.15 * teacher_comm
            + 0.20 * learner_fid
        )
        base_p = float(np.clip(base_p * trad.utility_score, 0.05, 0.95))

        # Repeated interaction opportunities
        effective_p = 1.0 - (1.0 - base_p) ** max(1, interaction_frequency)

        # Roll adoption
        if self.rng.random() >= effective_p:
            return False, "Transmission declined or failed to comprehend", None

        # Determine mutation / distortion probability
        # Lower teacher comm or lower learner fidelity increases copy error / mutation
        mutation_rate = max(0.12, 0.35 * (1.0 - (teacher_comm * 0.5 + learner_fid * 0.5)))
        if allow_mutation and (self.rng.random() < mutation_rate):
            # Create a localized variant
            variant_id = f"var_{trad.tradition_id}_{uuid.uuid4().hex[:4]}"
            mutated_params = {
                k: max(0.1, v * (1.0 + float(self.rng.normal(0.0, 0.15))))
                for k, v in trad.parameters.items()
            }
            variant = CulturalTradition(
                tradition_id=variant_id,
                name=f"{trad.name} (Variante local)",
                category=trad.category,
                origin_community_id=trad.origin_community_id,
                description=f"Local adaptation of '{trad.name}' by agent {learner_uid}",
                utility_score=float(np.clip(trad.utility_score + self.rng.normal(0.0, 0.08), 0.20, 0.98)),
                sacredness=max(0.10, trad.sacredness * 0.90),
                fidelity=max(0.30, trad.fidelity * 0.85),
                parameters=mutated_params,
                parent_tradition_id=trad.tradition_id,
                created_tick=tick,
                last_practiced_tick=tick,
            )
            variant.practice(str(learner_uid), tick)
            self._traditions[variant_id] = variant
            return True, "Adopted with variation/mutation", variant

        # Faithful adoption
        trad.practice(str(learner_uid), tick)
        return True, "Adopted faithfully", trad

    def diffuse_via_imitation(
        self,
        tradition_id: str,
        observer_uid: str | HumanID,
        observed_success: float,
        tick: int = 0,
    ) -> bool:
        """Adopt practice through observational imitation if proven beneficial."""
        trad = self.get_tradition(tradition_id)
        if not trad:
            return False

        if observed_success * trad.utility_score >= 0.45:
            trad.practice(str(observer_uid), tick)
            return True
        return False

    def fragment_tradition(
        self,
        tradition_id: str,
        split_group_a: set[str],
        split_group_b: set[str],
        sub_community_b_id: str,
        divergence_intensity: float = 0.25,
        tick: int = 0,
    ) -> Optional[CulturalTradition]:
        """Fragment a tradition into divergent regional branches following community fission."""
        trad = self.get_tradition(tradition_id)
        if not trad:
            return None

        # Group A preserves original tradition
        trad.adopters = set(split_group_a)

        # Group B develops an independent divergent branch
        variant_id = f"frag_{trad.tradition_id}_{uuid.uuid4().hex[:4]}"
        divergent_params = {
            k: max(0.1, v * (1.0 + divergence_intensity))
            for k, v in trad.parameters.items()
        }
        divergent_trad = CulturalTradition(
            tradition_id=variant_id,
            name=f"{trad.name} de {sub_community_b_id}",
            category=trad.category,
            origin_community_id=sub_community_b_id,
            description=f"Branch of '{trad.name}' diverging in {sub_community_b_id}",
            utility_score=trad.utility_score,
            sacredness=trad.sacredness,
            fidelity=max(0.20, trad.fidelity - divergence_intensity),
            parameters=divergent_params,
            parent_tradition_id=trad.tradition_id,
            adopters=set(split_group_b),
            created_tick=tick,
            last_practiced_tick=tick,
        )
        self._traditions[variant_id] = divergent_trad
        return divergent_trad

    def decay_unpracticed_traditions(self, current_tick: int, dormancy_limit_ticks: int = 4000) -> list[str]:
        """Flag traditions that haven't been practiced as obsolete or dormant."""
        dormant_ids: list[str] = []
        for t in self._traditions.values():
            if t.is_active and not t.is_extinct and (current_tick - t.last_practiced_tick) > dormancy_limit_ticks:
                t.is_active = False
                dormant_ids.append(t.tradition_id)
        return dormant_ids

    def check_cultural_extinction(self, alive_human_uids: set[str], tick: int) -> list[str]:
        """Detect and mark cultural traditions as permanently extinct if all practitioners have perished."""
        extinct_ids: list[str] = []
        for t in self._traditions.values():
            if t.is_active and not t.is_extinct:
                living_adopters = t.adopters.intersection(alive_human_uids)
                if len(living_adopters) == 0:
                    t.is_active = False
                    t.is_extinct = True
                    extinct_ids.append(t.tradition_id)
        return extinct_ids
