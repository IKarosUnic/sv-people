"""Integrated life-course events: households, kinship, reproduction, care and death.

This module is the bridge between the component-level lifecycle engines and the
live simulation loop.  It deliberately owns *state transitions* (pregnancy,
birth, aging, caregiving, bereavement, inheritance) rather than inventing
dialogue or UI-only events.  Every transition that becomes visible is emitted
on the shared event bus and mirrored in the causal graph by the runtime.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional
import uuid

import numpy as np

from saltbor.core.config import SimulationConfig
from saltbor.core.types import Gender, HumanID, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.lifecycle.demographics.stages import get_stage_for_age
from saltbor.lifecycle.family.household import Household, HouseholdRegistry
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph, GenealogyRecord
from saltbor.lifecycle.mortality.death import MortalityEngine
from saltbor.lifecycle.reproduction.pregnancy import Pregnancy
from saltbor.population.factory import PopulationFactory

logger = logging.getLogger(__name__)

_FEMALE_NAMES = [
    "Ana", "Beatriz", "Camila", "Daniela", "Elena", "Fátima", "Gabriela",
    "Isabel", "Julia", "Luciana", "Marisol", "Natalia", "Rosa", "Sofía", "Valeria",
]
_MALE_NAMES = [
    "Alejandro", "Bruno", "Carlos", "Diego", "Emilio", "Fernando", "Gabriel",
    "Héctor", "Javier", "Luis", "Manuel", "Mateo", "Óscar", "Rafael", "Tomás",
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class LifeEventsCoordinator:
    """Owns the integrated demographic and family life-course state."""

    def __init__(self, config: Optional[SimulationConfig] = None, seed: Optional[int] = None) -> None:
        self.config = config or SimulationConfig()
        self.households = HouseholdRegistry()
        self.genealogy = GenealogicalGraph()
        self.mortality = MortalityEngine(rng=np.random.default_rng(seed))
        self.pregnancies: dict[str, Pregnancy] = {}
        self.pregnancy_event_ids: dict[str, str] = {}
        self.births_history: list[dict[str, Any]] = []
        self.deaths_history: list[dict[str, Any]] = []
        self.elder_care_history: list[dict[str, Any]] = []
        self.water_source_by_home: dict[str, str] = {}
        self.gestation_days: float = 270.0
        self._last_aging_year: int = -1
        self._identity_factory: Optional[Any] = None
        self._rng = np.random.default_rng(seed)
        self._synced = False

    # ------------------------------------------------------------------
    # Initial conditions and kinship
    # ------------------------------------------------------------------

    def sync(
        self,
        population: Any,
        social_engine: Any,
        romance_engine: Any,
        current_tick: Tick = 0,
        identity_factory: Optional[Any] = None,
    ) -> None:
        """Register the existing population, unions, households and kinship.

        This is initial-condition reconstruction, not a fabricated event: no
        romance/birth/death event is emitted for relationships that already
        existed before the run started.
        """
        self._identity_factory = identity_factory
        self._population = population
        self.households = HouseholdRegistry()
        self.genealogy = GenealogicalGraph()

        humans = population.get_all()
        tick = current_tick or 0
        for human in humans:
            birth_tick = max(0, int(tick - float(human.demographics.age) * self.config.ticks_per_year))
            self.genealogy.register_individual(human.uid, birth_tick=birth_tick)

        # Register explicit partnerships from the pre-existing social graph.
        for rel in social_engine.get_all_relationships():
            rel_type = getattr(rel, "relationship_type", None)
            rel_type_value = rel_type.value if hasattr(rel_type, "value") else str(rel_type)
            a = population.get_optional(rel.human_a_id)
            b = population.get_optional(rel.human_b_id)
            if not a or not b:
                continue
            if rel_type_value == "partner":
                self.genealogy.record_partnership(a.uid, b.uid)
                a.romantic_partner_id = str(b.uid)
                b.romantic_partner_id = str(a.uid)
                stage_value = "married" if a.physical_state.home_location_id == b.physical_state.home_location_id else "cohabiting"
                from saltbor.core.types import RomanceStage
                romance_engine.register_existing_relationship(
                    a,
                    b,
                    stage=RomanceStage(stage_value),
                    start_tick=0,
                    trust=float(getattr(rel, "trust", 0.7)),
                    affinity=float(getattr(rel, "affinity", 0.7)),
                    dates_count=8 if stage_value == "married" else 4,
                    marriage_tick=0 if stage_value == "married" else None,
                )

        # Infer parent-child links only when both a significant age gap and a
        # shared surname exist.  This avoids inventing parents for unrelated
        # "family" ties (for example cousins or in-laws).
        family_edges: list[tuple[Any, Any]] = []
        for rel in social_engine.get_all_relationships():
            rel_type = getattr(rel, "relationship_type", None)
            rel_type_value = rel_type.value if hasattr(rel_type, "value") else str(rel_type)
            if rel_type_value not in ("family", "parent", "child"):
                continue
            a = population.get_optional(rel.human_a_id)
            b = population.get_optional(rel.human_b_id)
            if a and b:
                family_edges.append((a, b))

        for a, b in family_edges:
            older, younger = (a, b) if a.demographics.age >= b.demographics.age else (b, a)
            if older.demographics.age - younger.demographics.age < 16:
                continue
            if not self._surnames_overlap(older.name, younger.name):
                continue
            self.genealogy.register_individual(
                younger.uid,
                parents=[older.uid],
                birth_tick=max(0, int(tick - float(younger.demographics.age) * self.config.ticks_per_year)),
            )

        # Build households from shared residence.
        by_home: dict[str, list[Any]] = {}
        for human in humans:
            home = human.physical_state.home_location_id or "casa_norte_1"
            by_home.setdefault(str(home), []).append(human)

        for home, members in by_home.items():
            head = max(members, key=lambda h: h.demographics.age)
            household = Household(
                household_id=f"hogar_{home}",
                name=f"Hogar {home}",
                residence_location_id=home,
            )
            for member in sorted(members, key=lambda h: h.demographics.age, reverse=True):
                household.add_member(
                    member.uid,
                    is_head=(member.uid == head.uid),
                    is_dependent=(member.demographics.age < 18),
                )
            self.households.register_household(household)
            if head.demographics.age >= 18:
                for member in household.dependents:
                    household.assign_caregiver(member, head.uid)

            self.water_source_by_home[home] = self._water_source_for_home(home)

        self._refresh_family_links(population)
        self._synced = True

    @staticmethod
    def _tokenise_name(name: str) -> set[str]:
        cleaned = name.lower().replace(" de ", " ").replace(" del ", " ")
        return {token for token in cleaned.split() if len(token) >= 3}

    @classmethod
    def _surnames_overlap(cls, name_a: str, name_b: str) -> bool:
        return bool(cls._tokenise_name(name_a) & cls._tokenise_name(name_b))

    @staticmethod
    def _water_source_for_home(home: str) -> str:
        if "sur" in home or "oeste" in home:
            return "rio_suchiacel"
        if "este" in home:
            return "quebrada_el_zapote"
        return "pozo_comunal_san_pedro"

    def _refresh_family_links(self, population: Any) -> None:
        """Keep denormalised family-link fields on humans in sync with genealogy."""
        for human in population.get_all():
            children = [
                c for c in self.genealogy.get_children(human.uid)
                if population.get_optional(c) is not None
            ]
            parents = [
                p for p in self.genealogy.get_parents(human.uid)
                if population.get_optional(p) is not None
            ]
            human.dependent_children_ids = [
                str(c) for c in children
                if population.get_optional(c).demographics.age < 18
            ]
            human.caregiver_ids = [str(p) for p in parents]
            human.elderly_dependents_ids = [
                str(p) for p in parents
                if population.get_optional(p).demographics.age >= 65
            ]

    # ------------------------------------------------------------------
    # Daily integrated life-course step
    # ------------------------------------------------------------------

    def step_daily(
        self,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any] = None,
        health_engine: Optional[Any] = None,
        caregiving_engine: Optional[Any] = None,
        romance_engine: Optional[Any] = None,
        location_geo: Optional[Callable[[str], tuple[float, float]]] = None,
    ) -> dict[str, Any]:
        """Advance aging, conception, gestation, care, and mortality by one day."""
        summary = {
            "births": 0,
            "deaths": 0,
            "pregnancies_started": 0,
            "childcare_events": 0,
            "elder_care_events": 0,
        }
        if not self._synced:
            return summary

        self._step_aging(current_tick, population)
        summary["pregnancies_started"] = self._step_conception(
            current_tick, population, event_bus, causal_graph, romance_engine, location_geo
        )
        births = self._step_pregnancies(
            current_tick, population, event_bus, causal_graph, health_engine, location_geo
        )
        summary["births"] = births
        if caregiving_engine is not None:
            summary["childcare_events"] = self._step_childcare(
                current_tick, population, event_bus, causal_graph, caregiving_engine
            )
            if (current_tick // self.config.ticks_per_day) % 7 == 0:
                summary["elder_care_events"] = self._step_elder_care(
                    current_tick, population, event_bus, causal_graph, caregiving_engine
                )
        summary["deaths"] = self._step_mortality(
            current_tick,
            population,
            event_bus,
            causal_graph,
            health_engine,
            caregiving_engine,
            romance_engine,
            location_geo,
        )
        self._refresh_family_links(population)
        return summary

    def _step_aging(self, current_tick: Tick, population: Any) -> None:
        year = int(current_tick // self.config.ticks_per_year)
        if self._last_aging_year < 0:
            self._last_aging_year = year
            return
        if year <= self._last_aging_year:
            return
        delta = year - self._last_aging_year
        for human in population.get_all():
            human.demographics.age = int(human.demographics.age + delta)
            human.demographics.stage = get_stage_for_age(float(human.demographics.age))
        self._last_aging_year = year

    # ------------------------------------------------------------------
    # Reproduction
    # ------------------------------------------------------------------

    def start_pregnancy(
        self,
        mother: Any,
        father: Optional[Any],
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        location_geo: Optional[Callable[[str], tuple[float, float]]] = None,
        gestation_days: Optional[float] = None,
    ) -> Optional[Pregnancy]:
        """Begin a pregnancy as an explicit state transition.

        Public so reproducible experiments and the runtime use exactly the same
        pathway instead of duplicating biology in test code.
        """
        if str(mother.uid) in self.pregnancies:
            return None
        days = self.gestation_days if gestation_days is None else gestation_days
        gestation_ticks = max(1, int(self.config.ticks_per_day * days))
        pregnancy = Pregnancy(
            mother_uid=mother.uid,
            father_uid=father.uid if father else None,
            start_tick=current_tick,
            gestation_duration_ticks=gestation_ticks,
        )
        self.pregnancies[str(mother.uid)] = pregnancy

        home = str(mother.physical_state.home_location_id or "casa_norte_1")
        coords = location_geo(home) if location_geo else (13.935, -89.028)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.PREGNANCY_STARTED,
                tick=current_tick,
                source_human_id=mother.uid,
                target_human_id=father.uid if father else None,
                location_id=home,
                coordinates=coords,
                data={
                    "mother_uid": str(mother.uid),
                    "father_uid": str(father.uid) if father else None,
                    "due_tick": current_tick + gestation_ticks,
                    "gestation_days": days,
                    "coordinate_provenance": "synthetic_local_map",
                },
                importance=0.85,
            )
            event_bus.emit(evt)
            self.pregnancy_event_ids[str(mother.uid)] = str(evt.event_id)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Embarazo de {mother.name}")
        return pregnancy

    def _step_conception(
        self,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any],
        romance_engine: Optional[Any],
        location_geo: Optional[Callable[[str], tuple[float, float]]],
    ) -> int:
        if romance_engine is None:
            return 0
        started = 0
        for rel in romance_engine.get_all_relationships():
            if not rel.is_active:
                continue
            from saltbor.core.types import RomanceStage
            if rel.stage not in (RomanceStage.COHABITING, RomanceStage.MARRIED):
                continue
            a = population.get_optional(uuid.UUID(rel.partner_a_id))
            b = population.get_optional(uuid.UUID(rel.partner_b_id))
            if not a or not b:
                continue
            mother, father = self._gestational_parent(a, b)
            if mother is None:
                continue
            if str(mother.uid) in self.pregnancies:
                continue
            if not (18 <= mother.demographics.age <= 45):
                continue

            existing_children = len([
                c for c in self.genealogy.get_children(mother.uid)
                if population.get_optional(c) is not None
            ])
            desire = 0.65
            desire += min(1.0, mother.physical_state.money / 220.0) * 0.35
            desire += 0.20 if rel.stage == RomanceStage.MARRIED else 0.0
            desire -= min(0.45, existing_children * 0.08)
            desire *= max(0.2, min(1.0, mother.physical_state.health))
            probability = _clamp(0.012 * desire, 0.001, 0.035)

            if self._rng.random() < probability:
                if self.start_pregnancy(
                    mother,
                    father,
                    current_tick,
                    event_bus=event_bus,
                    causal_graph=causal_graph,
                    location_geo=location_geo,
                ):
                    started += 1
        return started

    @staticmethod
    def _gestational_parent(a: Any, b: Any) -> tuple[Optional[Any], Optional[Any]]:
        """Return (gestating parent, other parent) for the modelled biology."""
        if getattr(a.demographics, "gender", None) == Gender.FEMALE:
            return a, b
        if getattr(b.demographics, "gender", None) == Gender.FEMALE:
            return b, a
        return None, None

    def _step_pregnancies(
        self,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any],
        health_engine: Optional[Any],
        location_geo: Optional[Callable[[str], tuple[float, float]]],
    ) -> int:
        births = 0
        for mother_uid, pregnancy in list(self.pregnancies.items()):
            mother = population.get_optional(uuid.UUID(mother_uid))
            if mother is None:
                self.pregnancies.pop(mother_uid, None)
                self.pregnancy_event_ids.pop(mother_uid, None)
                continue

            impact = pregnancy.get_physical_impact()
            mother.physical_state.energy = max(
                0.05, mother.physical_state.energy - float(impact.get("energy_penalty", 0.0)) * 0.08
            )
            mother.physical_state.hunger = min(
                1.0, mother.physical_state.hunger + float(impact.get("hunger_boost", 0.0)) * 0.10
            )

            due = pregnancy.advance(self.config.ticks_per_day)
            if not due:
                continue

            father = population.get_optional(uuid.UUID(str(pregnancy.father_uid))) if pregnancy.father_uid else None
            if self._rng.random() < min(0.35, pregnancy.complications_risk * 3.0):
                mother.physical_state.health = max(0.05, mother.physical_state.health - 0.12)
                if health_engine:
                    cond = health_engine.create_workplace_trauma(tick=current_tick, task="Parto")
                    cond.name = "Complicación del Parto"
                    cond.severity = 0.65
                    mother.active_health_conditions.append(cond)
                if event_bus:
                    evt_comp = SimulationEvent(
                        event_type=EventType.HEALTH_COMPLICATION,
                        tick=current_tick,
                        source_human_id=mother.uid,
                        location_id=mother.physical_state.home_location_id,
                        coordinates=location_geo(str(mother.physical_state.home_location_id))
                        if location_geo else (13.935, -89.028),
                        data={"condition": "Complicación del Parto", "mother_uid": mother_uid},
                        importance=0.9,
                        cause_event_id=self.pregnancy_event_ids.get(mother_uid),
                    )
                    event_bus.emit(evt_comp)
                    if causal_graph:
                        causal_graph.add_event(evt_comp, description=f"Complicación del parto de {mother.name}")

            child = self._create_child(mother, father, current_tick, event_bus, causal_graph, location_geo)
            if child is not None:
                births += 1
            self.pregnancies.pop(mother_uid, None)
            self.pregnancy_event_ids.pop(mother_uid, None)
        return births

    def _create_child(
        self,
        mother: Any,
        father: Optional[Any],
        current_tick: Tick,
        event_bus: Any,
        causal_graph: Optional[Any],
        location_geo: Optional[Callable[[str], tuple[float, float]]],
    ) -> Optional[Any]:
        if self._identity_factory is None:
            return None

        gender = Gender.FEMALE if self._rng.random() < 0.5 else Gender.MALE
        given = str(self._rng.choice(_FEMALE_NAMES if gender == Gender.FEMALE else _MALE_NAMES))
        father_surname = father.family_name.split()[0] if father and father.family_name else ""
        mother_surname = mother.family_name.split()[0] if mother.family_name else "Saltbor"
        family_name = f"{father_surname} {mother_surname}".strip() if father_surname else mother_surname

        home = str(mother.physical_state.home_location_id or "casa_norte_1")
        profile = {
            "given_name": given,
            "family_name": family_name,
            "age": 0,
            "gender": gender,
            "occupation": "Menor",
            "education_level": "Ninguna",
            "income_level": 0.0,
            "home_id": home,
            "work_id": home,
            "money": 0.0,
            "data_source": mother.identity.data_source,
        }
        children = PopulationFactory.create_from_profiles(
            profiles=[profile],
            config=self.config,
            identity_factory=self._identity_factory,
            rng=self._rng,
        )
        if not children:
            return None
        child = children[0]
        child.demographics.birth_tick = current_tick
        child.demographics.stage = get_stage_for_age(0.0)
        child.physical_state.home_location_id = home
        child.physical_state.current_location_id = home
        child.physical_state.work_location_id = home
        child.physical_state.energy = 0.75
        child.physical_state.hunger = 0.25
        child.physical_state.money = 0.0

        # Register in population and genealogy.
        population = getattr(self, "_population", None)
        if population is not None:
            population.register(child)
        parents = [mother.uid] + ([father.uid] if father else [])
        self.genealogy.record_birth(child.uid, mother.uid, father.uid if father else None, current_tick)

        household = self.households.get_for_human(mother.uid)
        if household is not None:
            household.add_member(child.uid, is_dependent=True)
            household.assign_caregiver(child.uid, mother.uid)
        mother.dependent_children_ids.append(str(child.uid))
        if father:
            father.dependent_children_ids.append(str(child.uid))
        child.caregiver_ids = [str(p) for p in parents]

        coords = location_geo(home) if location_geo else (13.935, -89.028)
        record = {
            "child_uid": str(child.uid),
            "child_name": child.name,
            "mother_uid": str(mother.uid),
            "father_uid": str(father.uid) if father else None,
            "birth_location_id": home,
            "tick": current_tick,
            "coordinate_provenance": "synthetic_local_map",
        }
        self.births_history.append(record)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.BIRTH,
                tick=current_tick,
                source_human_id=child.uid,
                target_human_id=mother.uid,
                location_id=home,
                coordinates=coords,
                data=record,
                importance=0.95,
                cause_event_id=self.pregnancy_event_ids.get(str(mother.uid)),
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Nacimiento de {child.name}, hijo/a de {mother.name}")
        logger.info("Birth: %s (child of %s)", child.name, mother.name)
        return child

    # ------------------------------------------------------------------
    # Caregiving
    # ------------------------------------------------------------------

    def _step_childcare(
        self,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any],
        caregiving_engine: Any,
    ) -> int:
        events = 0
        day = current_tick // self.config.ticks_per_day
        for child in population.get_all():
            if child.demographics.age >= 13:
                continue
            if child.demographics.age >= 3 and day % 2 != 0:
                continue
            household = self.households.get_for_human(child.uid)
            caregiver_uid = household.get_caregiver_for(child.uid) if household else None
            caregiver = population.get_optional(caregiver_uid) if caregiver_uid else None
            if caregiver is None:
                continue
            if child.physical_state.hunger <= 0.10:
                continue
            result = caregiving_engine.perform_childcare(
                caregiver,
                child,
                current_tick,
                event_bus=event_bus,
                causal_graph=causal_graph,
            )
            if result.get("success"):
                events += 1
        return events

    def _step_elder_care(
        self,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any],
        caregiving_engine: Any,
    ) -> int:
        events = 0
        for elder in population.get_all():
            if elder.demographics.age < 65:
                continue
            children = [
                population.get_optional(c)
                for c in self.genealogy.get_children(elder.uid)
                if population.get_optional(c) is not None
            ]
            adult_children = [c for c in children if c and c.demographics.age >= 18]
            if not adult_children:
                continue
            caregiver = max(adult_children, key=lambda h: h.physical_state.money)
            if caregiver.physical_state.money <= 15.0:
                continue
            result = caregiving_engine.perform_elder_care(
                caregiver,
                elder,
                financial_support_usd=1.50,
                current_tick=current_tick,
                event_bus=event_bus,
                causal_graph=causal_graph,
            )
            if result.get("success"):
                events += 1
                self.elder_care_history.append({
                    "caregiver_uid": str(caregiver.uid),
                    "elder_uid": str(elder.uid),
                    "tick": current_tick,
                    "support_usd": 1.50,
                })
        return events

    # ------------------------------------------------------------------
    # Mortality, bereavement and inheritance
    # ------------------------------------------------------------------

    def _step_mortality(
        self,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any],
        health_engine: Optional[Any],
        caregiving_engine: Optional[Any],
        romance_engine: Optional[Any],
        location_geo: Optional[Callable[[str], tuple[float, float]]],
    ) -> int:
        deaths = 0
        for human in list(population.get_all()):
            if self.mortality.is_deceased(human.uid):
                continue
            if not self.mortality.check_mortality(
                human,
                ticks_per_year=self.config.ticks_per_year,
                ticks_elapsed=self.config.ticks_per_day,
            ):
                continue
            self.process_death(
                human,
                current_tick,
                population,
                event_bus,
                causal_graph,
                health_engine,
                caregiving_engine,
                romance_engine,
                location_geo,
            )
            deaths += 1
        return deaths

    def process_death(
        self,
        deceased: Any,
        current_tick: Tick,
        population: Any,
        event_bus: Any,
        causal_graph: Optional[Any] = None,
        health_engine: Optional[Any] = None,
        caregiving_engine: Optional[Any] = None,
        romance_engine: Optional[Any] = None,
        location_geo: Optional[Callable[[str], tuple[float, float]]] = None,
    ) -> dict[str, Any]:
        """Execute a full death sequence with grief, inheritance and widowhood."""
        household = self.households.get_for_human(deceased.uid)
        survivor_uids: list[HumanID] = []
        if household is not None:
            survivor_uids.extend([m for m in household.members if m != deceased.uid])
        for child_uid in self.genealogy.get_children(deceased.uid):
            if child_uid != deceased.uid and child_uid not in survivor_uids:
                survivor_uids.append(child_uid)
        partner_uid = self.genealogy.get_record(deceased.uid).partner if self.genealogy.get_record(deceased.uid) else None
        if partner_uid and partner_uid not in survivor_uids:
            survivor_uids.append(partner_uid)
        survivors = [population.get_optional(uid) for uid in survivor_uids]
        survivors = [s for s in survivors if s is not None]

        # Resolve the concrete condition that made death possible, if any.
        cause_event_id: Optional[str] = None
        cause_name = "causa natural / senescencia"
        conditions = list(getattr(deceased, "active_health_conditions", []))
        if conditions:
            worst = max(conditions, key=lambda c: getattr(c, "severity", 0.0))
            cause_name = worst.name
            if causal_graph is not None:
                node = causal_graph.find_latest_node(
                    EventType.ILLNESS_CONTRACTED.value,
                    human_uid=str(deceased.uid),
                    predicate=lambda n: n.metadata.get("condition_id") == getattr(worst, "condition_id", None)
                    or n.metadata.get("condition") == worst.name,
                )
                if node is None:
                    node = causal_graph.find_latest_node(
                        EventType.INJURY_SUSTAINED.value, human_uid=str(deceased.uid)
                    )
                cause_event_id = node.event_id if node else None

        inheritance: dict[str, float] = {}
        if caregiving_engine is not None:
            result = caregiving_engine.handle_bereavement_and_succession(
                deceased,
                survivors,
                current_tick,
                household_registry=self.households,
                genealogy=self.genealogy,
                event_bus=event_bus,
                causal_graph=causal_graph,
            )
            inheritance = result.get("inheritance_distributed", {})

        # Close the union and attach the widowhood heartbreak to the survivor.
        if romance_engine is not None:
            active_rel = romance_engine.get_agent_relationship(str(deceased.uid))
            if active_rel is not None:
                romance_engine.handle_partner_death(
                    active_rel.relationship_id,
                    str(deceased.uid),
                    current_tick,
                    event_bus=event_bus,
                    causal_graph=causal_graph,
                )
                for survivor in survivors:
                    romance_engine.attach_pending_heartbreak(survivor)

        # Remove from household and mark genealogy before emitting the death.
        if household is not None:
            household.remove_member(deceased.uid)
        self.households.remove_human(deceased.uid)
        self.genealogy.record_death(deceased.uid, current_tick)
        self.mortality.mark_deceased(deceased.uid)

        home = str(deceased.physical_state.home_location_id or "casa_norte_1")
        coords = location_geo(home) if location_geo else (13.935, -89.028)
        record = {
            "uid": str(deceased.uid),
            "name": deceased.name,
            "age": deceased.demographics.age,
            "tick": current_tick,
            "cause": cause_name,
            "inheritance": inheritance,
            "coordinate_provenance": "synthetic_local_map",
        }
        self.deaths_history.append(record)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.DEATH,
                tick=current_tick,
                source_human_id=deceased.uid,
                location_id=home,
                coordinates=coords,
                data=record,
                importance=0.95,
                cause_event_id=cause_event_id,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, cause_event_id=cause_event_id, description=f"Fallecimiento de {deceased.name} ({cause_name})")

            # Bereavement can produce a genuine mental-distress condition.
            if health_engine is not None:
                for survivor in survivors:
                    if health_engine is None:
                        break
                    if getattr(survivor, "heartbreak_state", None) is not None or self._rng.random() < 0.5:
                        has_distress = any(
                            getattr(c, "category", None) is not None
                            and getattr(c.category, "value", "") == "mental_distress"
                            for c in getattr(survivor, "active_health_conditions", [])
                        )
                        if has_distress:
                            continue
                        cond = health_engine.create_mental_distress(
                            tick=current_tick, cause=f"bereavement:{deceased.uid}"
                        )
                        survivor.active_health_conditions.append(cond)
                        dist_evt = SimulationEvent(
                            event_type=EventType.ILLNESS_CONTRACTED,
                            tick=current_tick,
                            source_human_id=survivor.uid,
                            location_id=survivor.physical_state.home_location_id,
                            coordinates=location_geo(str(survivor.physical_state.home_location_id))
                            if location_geo else (13.935, -89.028),
                            data={
                                "condition_id": cond.condition_id,
                                "condition": cond.name,
                                "origin": f"bereavement:{deceased.uid}",
                                "coordinate_provenance": "synthetic_local_map",
                            },
                            importance=0.7,
                            cause_event_id=evt.event_id,
                        )
                        event_bus.emit(dist_evt)
                        if causal_graph:
                            causal_graph.add_event(
                                dist_evt,
                                cause_event_id=str(evt.event_id),
                                description=f"{survivor.name} desarrolló distrés por duelo de {deceased.name}",
                            )

        deceased.physical_state.health = 0.0
        deceased.physical_state.energy = 0.0
        population.unregister(deceased.uid)
        logger.info("Death processed: %s (age %d)", deceased.name, deceased.demographics.age)
        return record

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize all integrated life-course state."""
        households = []
        for h in self.households.all_households():
            households.append({
                "household_id": h.household_id,
                "name": h.name,
                "residence_location_id": h.residence_location_id,
                "members": sorted(str(m) for m in h.members),
                "head_of_household": str(h.head_of_household) if h.head_of_household else None,
                "dependents": sorted(str(d) for d in h.dependents),
                "caregiver_assignments": {
                    str(dep): str(cg) for dep, cg in h.caregiver_assignments.items()
                },
                "shared_funds": h.shared_funds,
            })
        return {
            "households": households,
            "genealogy": [r.to_dict() for r in self.genealogy.all_records()],
            "pregnancies": [p.to_dict() for p in self.pregnancies.values()],
            "pregnancy_event_ids": dict(self.pregnancy_event_ids),
            "births_history": list(self.births_history),
            "deaths_history": list(self.deaths_history),
            "elder_care_history": list(self.elder_care_history),
            "water_source_by_home": dict(self.water_source_by_home),
            "last_aging_year": self._last_aging_year,
            "gestation_days": self.gestation_days,
            "deceased_uids": sorted(str(u) for u in self.mortality._deceased_registry),
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore integrated life-course state from a checkpoint."""
        self.households = HouseholdRegistry()
        for h in data.get("households", []):
            household = Household(
                household_id=h["household_id"],
                name=h.get("name", "Hogar"),
                residence_location_id=h.get("residence_location_id", "casa_norte_1"),
                members={uuid.UUID(m) for m in h.get("members", [])},
                head_of_household=uuid.UUID(h["head_of_household"]) if h.get("head_of_household") else None,
                dependents={uuid.UUID(d) for d in h.get("dependents", [])},
                caregiver_assignments={
                    uuid.UUID(dep): uuid.UUID(cg)
                    for dep, cg in h.get("caregiver_assignments", {}).items()
                },
                shared_funds=float(h.get("shared_funds", 0.0)),
            )
            self.households.register_household(household)

        self.genealogy = GenealogicalGraph()
        for item in data.get("genealogy", []):
            record = GenealogyRecord.from_dict(item)
            self.genealogy._records[record.uid] = record

        self.pregnancies = {}
        for item in data.get("pregnancies", []):
            pregnancy = Pregnancy.from_dict(item)
            self.pregnancies[str(pregnancy.mother_uid)] = pregnancy
        self.pregnancy_event_ids = {str(k): str(v) for k, v in data.get("pregnancy_event_ids", {}).items()}
        self.births_history = list(data.get("births_history", []))
        self.deaths_history = list(data.get("deaths_history", []))
        self.elder_care_history = list(data.get("elder_care_history", []))
        self.water_source_by_home = {str(k): str(v) for k, v in data.get("water_source_by_home", {}).items()}
        self._last_aging_year = int(data.get("last_aging_year", -1))
        self.gestation_days = float(data.get("gestation_days", 270.0))
        self.mortality._deceased_registry = {uuid.UUID(u) for u in data.get("deceased_uids", [])}
        self._synced = True
