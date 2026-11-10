"""Macro-Demographic Simulation: 10 Generations of Societal Evolution.

Simulates ~250 to 300 years of continuous history with:
- Continuous biological aging and 7 developmental stages
- Genetics recombination without determinism
- Persistent genealogical tree tracking family dynasties
- Courtship, marriage, pregnancy, birth, and childcare
- Economic production, market prices, and inheritance upon death
- Gompertz-Makeham mortality and survivor bereavement
- Live census dashboard and lineage tracking
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import numpy as np

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import DataSource, Gender, LocationID
from saltbor.economy.household.ledger import HouseholdLedger
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.economy.market.exchange import MarketExchange
from saltbor.economy.production.facility import ProductionFacility
from saltbor.economy.production.recipe import STANDARD_RECIPES
from saltbor.events.bus import EventBus
from saltbor.lifecycle.aging.clock import AgingEngine, BiologicalProfile
from saltbor.lifecycle.demographics.stages import (
    DEFAULT_STAGE_CONFIGS,
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
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.social.engine import SocialEngine

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("macro_sim")


FOUNDER_FAMILIES = [
    ("Carlos", "Rivera", Gender.MALE, 24),
    ("Elena", "Gómez", Gender.FEMALE, 22),
    ("Mateo", "Mendoza", Gender.MALE, 26),
    ("Sofía", "Alvarado", Gender.FEMALE, 23),
    ("David", "Flores", Gender.MALE, 28),
    ("Rosa", "Santos", Gender.FEMALE, 25),
    ("Joaquín", "Castillo", Gender.MALE, 27),
    ("Lucía", "Pérez", Gender.FEMALE, 21),
    ("Héctor", "Montoya", Gender.MALE, 25),
    ("Carmen", "Cáceres", Gender.FEMALE, 24),
    ("Manuel", "Ramos", Gender.MALE, 29),
    ("Teresa", "Zelaya", Gender.FEMALE, 26),
    ("Antonio", "Mejía", Gender.MALE, 23),
    ("Adriana", "Quinteros", Gender.FEMALE, 22),
    ("Fernando", "Baires", Gender.MALE, 27),
    ("Claudia", "Navarro", Gender.FEMALE, 24),
    ("Emilio", "Choto", Gender.MALE, 25),
    ("Gabriela", "Orellana", Gender.FEMALE, 23),
    ("Óscar", "Portillo", Gender.MALE, 30),
    ("Valeria", "Benítez", Gender.FEMALE, 21),
]

RESIDENTIAL_LOCATIONS = [
    "casa_residencial_1", "casa_residencial_2", "casa_residencial_3",
    "casa_residencial_4", "casa_residencial_5", "casa_residencial_6",
]


class MacroSimulation:
    """Orchestrates multi-generational demographic, economic, and genealogical progression."""

    def __init__(
        self,
        seed: int = 42,
        ticks_per_year: int = 12,
        total_years: int = 250,
    ) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.ticks_per_year = ticks_per_year
        self.total_years = total_years
        self.total_ticks = total_years * ticks_per_year

        # Engines
        self.aging = AgingEngine(ticks_per_year=float(ticks_per_year))
        self.child_dev = ChildDevelopmentEngine(rng=self.rng)
        self.genetics = GeneticsEngine(mutation_rate=0.06, rng=self.rng)
        self.genealogy = GenealogicalGraph()
        self.households = HouseholdRegistry()
        self.reproduction = ReproductionEngine(
            gestation_ticks=max(2, ticks_per_year // 3), # ~4 months
            conception_probability_base=0.45,
            rng=self.rng,
        )
        self.mortality = MortalityEngine(
            base_makeham_hazard=0.0005,
            gompertz_alpha=0.0008,
            gompertz_gamma=0.075,
            rng=self.rng,
        )
        self.grief = GriefEngine()
        self.social = SocialEngine()
        self.bus = EventBus()

        # Economy
        self.market = MarketExchange(inventory_capacity=5000.0)
        self.workshop = ProductionFacility("taller_el_roble", "Taller El Roble", "taller_el_roble", 1000.0)
        self.farm = ProductionFacility("cooperativa_agricola", "Cooperativa Agrícola", "cooperativa_agricola", 2000.0)
        self.comedor = ProductionFacility("comedor_dona_maria", "Comedor Doña María", "comedor_dona_maria", 1000.0)

        # State storage
        self.humans: dict[uuid.UUID, SyntheticHuman] = {}
        self.bio_profiles: dict[uuid.UUID, BiologicalProfile] = {}
        self.genomes: dict[uuid.UUID, Genome] = {}
        self.household_ledgers: dict[str, HouseholdLedger] = {}
        self.lifespans: list[float] = []
        self.serial_counter = 1

        # Census telemetry logs
        self.census_history: list[dict[str, Any]] = []

    def initialize_population(self) -> None:
        """Seed 20 founder individuals, initial genetics, households, and economic stocks."""
        # Stock initial market goods
        self.market.stock_goods(ItemType.GRAIN, 400.0, UnitType.KG)
        self.market.stock_goods(ItemType.FOOD, 250.0, UnitType.MEAL)
        self.market.stock_goods(ItemType.WOOD, 150.0, UnitType.PIECE)
        self.market.stock_goods(ItemType.TOOL, 30.0, UnitType.PIECE)
        self.market.stock_goods(ItemType.SEEDS, 80.0, UnitType.KG)

        # Stock production facilities
        self.farm.inventory.add(InventoryItem(item_type=ItemType.SEEDS, quantity=50.0, unit=UnitType.KG))
        self.farm.inventory.add(InventoryItem(item_type=ItemType.TOOL, quantity=5.0, unit=UnitType.PIECE))
        self.workshop.inventory.add(InventoryItem(item_type=ItemType.WOOD, quantity=60.0, unit=UnitType.PIECE))
        self.workshop.inventory.add(InventoryItem(item_type=ItemType.TOOL, quantity=4.0, unit=UnitType.PIECE))

        # Create 20 founders (10 couples)
        couples = []
        for i in range(0, len(FOUNDER_FAMILIES), 2):
            male_info = FOUNDER_FAMILIES[i]
            female_info = FOUNDER_FAMILIES[i + 1]

            h_m = self._create_founder(*male_info)
            h_f = self._create_founder(*female_info)

            # Establish initial union
            self.social.record_interaction(h_m.uid, h_f.uid, tick=0, positive=True, intensity=0.9)
            self.social.record_interaction(h_f.uid, h_m.uid, tick=0, positive=True, intensity=0.9)
            self.genealogy.record_partnership(h_m.uid, h_f.uid)

            loc = RESIDENTIAL_LOCATIONS[(i // 2) % len(RESIDENTIAL_LOCATIONS)]
            house_name = f"Familia {male_info[1]}-{female_info[1]}"
            house = self.households.create_household(house_name, loc, [h_m.uid, h_f.uid], head=h_m.uid)
            ledger = HouseholdLedger(household_id=house.household_id, shared_savings=150.0)
            ledger.store_goods(InventoryItem(item_type=ItemType.FOOD, quantity=20.0, unit=UnitType.MEAL))
            self.household_ledgers[house.household_id] = ledger

            couples.append((h_m, h_f))

    def _create_founder(self, given: str, family: str, gender: Gender, age: int) -> SyntheticHuman:
        uid = uuid.uuid4()
        serial = self.serial_counter
        self.serial_counter += 1

        genome = self.genetics.generate_random_genome()
        self.genomes[uid] = genome

        ident = HumanIdentity(
            uid=uid, serial=serial, given_name=given, family_name=family, data_source=DataSource.MOCK_GENERATED
        )
        stage = get_stage_for_age(float(age))
        demo = Demographics(age=age, gender=gender, stage=stage, birth_tick=0)
        phys = PhysicalState(
            money=50.0, health=1.0, energy=1.0, hunger=0.1, home_location_id="casa_residencial_1"
        )
        pers = PersonalityEngine(PersonalityTraits(
            openness=TraitValue(base_value=genome.temperament_openness, current_value=genome.temperament_openness),
            conscientiousness=TraitValue(base_value=genome.temperament_conscientiousness, current_value=genome.temperament_conscientiousness),
            extraversion=TraitValue(base_value=genome.temperament_extraversion, current_value=genome.temperament_extraversion),
            agreeableness=TraitValue(base_value=genome.temperament_agreeableness, current_value=genome.temperament_agreeableness),
            neuroticism=TraitValue(base_value=genome.temperament_neuroticism, current_value=genome.temperament_neuroticism),
        ))
        emot = EmotionalEngine()
        mem = MemoryEngine()

        human = SyntheticHuman(
            identity=ident, demographics=demo, physical_state=phys, personality=pers, emotions=emot, memory=mem
        )
        self.humans[uid] = human

        bio = self.aging.create_profile(birth_tick=0, initial_age_years=float(age))
        self.bio_profiles[uid] = bio

        self.genealogy.register_individual(uid, generation=0)
        return human

    def step(self, current_tick: int) -> None:
        """Advance the macro society by 1 discrete tick."""
        living_uids = [uid for uid, h in self.humans.items() if not self.mortality.is_deceased(uid)]

        # ---------------------------------------------------------
        # 1. Biological Aging and Developmental Progression
        # ---------------------------------------------------------
        for uid in living_uids:
            h = self.humans[uid]
            bio = self.bio_profiles[uid]
            stage_changed = self.aging.step_individual(bio, current_tick)
            h.demographics.age = int(bio.current_age_years)
            h.demographics.stage = bio.current_stage

            # Sync physical state with age vitality
            h.physical_state.health = bio.vitality

        # ---------------------------------------------------------
        # 2. Economy: Production, Consumption, and Market
        # ---------------------------------------------------------
        # A. Facilities produce basic goods
        adult_workers = [
            uid for uid in living_uids
            if self.humans[uid].demographics.stage in (DevelopmentalStage.ADULTHOOD, DevelopmentalStage.EARLY_ADULTHOOD)
        ]

        if adult_workers:
            # Farm production (Food grains)
            farmer = adult_workers[current_tick % len(adult_workers)]
            if self.farm.can_produce(STANDARD_RECIPES["farm_grain_harvest"])[0]:
                self.farm.start_batch(STANDARD_RECIPES["farm_grain_harvest"], farmer, current_tick)
                self.farm.advance_work(farmer, ticks=2)

            # Comedor cooking (Meals)
            cook = adult_workers[(current_tick + 1) % len(adult_workers)]
            # Transfer grain from farm to comedor or market
            if self.farm.inventory.get_quantity(ItemType.GRAIN) >= 4.0:
                self.farm.inventory.transfer_to(self.comedor.inventory, ItemType.GRAIN, 4.0)

            if self.comedor.can_produce(STANDARD_RECIPES["cook_meals"])[0]:
                self.comedor.start_batch(STANDARD_RECIPES["cook_meals"], cook, current_tick)
                self.comedor.advance_work(cook, ticks=2)

            # Move prepared meals to market
            if self.comedor.inventory.get_quantity(ItemType.FOOD) >= 4.0:
                self.comedor.inventory.transfer_to(self.market.inventory, ItemType.FOOD, 4.0)

        # B. Household resource consumption
        for house in self.households.all_households():
            ledger = self.household_ledgers.get(house.household_id)
            if not ledger or not house.members:
                continue

            # Living members in house
            members_alive = [self.humans[m] for m in house.members if not self.mortality.is_deceased(m)]
            if not members_alive:
                continue

            stages = [m.demographics.stage for m in members_alive]
            food_needed = ledger.calculate_daily_food_demand(stages) / 30.0 # Per tick fraction

            # Consume from pantry or purchase from market
            got = ledger.retrieve_food(food_needed)
            if got < food_needed:
                # Buy from market
                head = house.head_of_household or members_alive[0].uid
                head_h = self.humans[head]
                success, bought, cost, _ = self.market.buy_from_market(
                    head, ledger.inventory, ledger.shared_savings, ItemType.FOOD, food_needed * 4.0, current_tick
                )
                if success:
                    ledger.pay_expense(cost, "food_purchase")
                    ledger.retrieve_food(food_needed)
                else:
                    # Food scarcity: members experience slight hunger
                    for m in members_alive:
                        m.physical_state.hunger = min(1.0, m.physical_state.hunger + 0.05)

            # Adults earn modest wage to support household
            for m in members_alive:
                if m.demographics.stage in (DevelopmentalStage.ADULTHOOD, DevelopmentalStage.EARLY_ADULTHOOD):
                    ledger.deposit_income(m.uid, 1.5)

        # ---------------------------------------------------------
        # 3. Courtship and New Unions
        # ---------------------------------------------------------
        # Eligible single adults
        single_males = [
            h for h in [self.humans[uid] for uid in living_uids]
            if h.demographics.gender == Gender.MALE
            and 18 <= h.demographics.age <= 55
            and not (self.genealogy.get_record(h.uid) and self.genealogy.get_record(h.uid).partner and not self.mortality.is_deceased(self.genealogy.get_record(h.uid).partner))
        ]
        single_females = [
            h for h in [self.humans[uid] for uid in living_uids]
            if h.demographics.gender == Gender.FEMALE
            and 18 <= h.demographics.age <= 45
            and not (self.genealogy.get_record(h.uid) and self.genealogy.get_record(h.uid).partner and not self.mortality.is_deceased(self.genealogy.get_record(h.uid).partner))
        ]

        self.rng.shuffle(single_males)
        self.rng.shuffle(single_females)

        # Match up to 3 compatible couples per tick
        matched = 0
        for m in single_males:
            if matched >= 3:
                break
            for f in single_females:
                rec_f = self.genealogy.get_record(f.uid)
                if rec_f and rec_f.partner and not self.mortality.is_deceased(rec_f.partner):
                    continue
                compat = self.reproduction.evaluate_mating_compatibility(
                    f, m, self.genealogy, mutual_trust=0.75, mutual_affinity=0.75
                )
                if compat >= 0.50:
                    self.genealogy.record_partnership(m.uid, f.uid)
                    self.social.record_interaction(m.uid, f.uid, current_tick, positive=True, intensity=0.8)

                    # Form or join household
                    new_house_name = f"Familia {m.identity.family_name}-{f.identity.family_name}"
                    loc = RESIDENTIAL_LOCATIONS[len(self.households.all_households()) % len(RESIDENTIAL_LOCATIONS)]
                    new_h = self.households.create_household(new_house_name, loc, [m.uid, f.uid], head=m.uid)
                    self.household_ledgers[new_h.household_id] = HouseholdLedger(household_id=new_h.household_id, shared_savings=80.0)
                    matched += 1
                    break

        # ---------------------------------------------------------
        # 4. Reproduction: Conception, Gestation, and Birth
        # ---------------------------------------------------------
        # Dynamic reproductive density regulation: as population nears carrying capacity, birth probability scales down
        carrying_capacity = 300.0
        pop_density_factor = max(0.05, 1.0 - (len(living_uids) / carrying_capacity))

        # Attempt conception for partnered women (once a year per woman or modulated by density)
        for uid in living_uids:
            woman = self.humans[uid]
            if woman.demographics.gender != Gender.FEMALE or not (18 <= woman.demographics.age <= 42):
                continue
            if self.reproduction.is_pregnant(woman.uid):
                continue

            rec = self.genealogy.get_record(woman.uid)
            if rec and rec.partner and not self.mortality.is_deceased(rec.partner):
                # Check maximum desired offspring per couple (e.g. 2-3 children)
                if len(rec.children) >= 3:
                    continue
                # Spacing births: require at least 24 ticks (2 years) since last delivery
                if rec.children:
                    last_child_rec = self.genealogy.get_record(rec.children[-1])
                    if last_child_rec and (current_tick - last_child_rec.birth_tick) < 24:
                        continue

                if self.rng.random() > pop_density_factor:
                    continue

                partner = self.humans[rec.partner]
                self.reproduction.attempt_conception(
                    woman, partner, self.genealogy, mutual_trust=0.85, mutual_affinity=0.80, current_tick=current_tick
                )

        # Advance active pregnancies
        due_pregnancies = self.reproduction.update_pregnancies(delta_ticks=1)
        for preg in due_pregnancies:
            self._deliver_child(preg, current_tick)

        # ---------------------------------------------------------
        # 5. Mortality & Succession
        # ---------------------------------------------------------
        for uid in living_uids:
            h = self.humans[uid]
            died = self.mortality.check_mortality(h, ticks_per_year=self.ticks_per_year, ticks_elapsed=1)
            if died:
                self._process_death(h, current_tick)

        # Update market prices at end of simulated year
        if current_tick % self.ticks_per_year == 0:
            self.market.update_cycle()

    def _deliver_child(self, preg: Pregnancy, current_tick: int) -> SyntheticHuman:
        """Handle birth event, genetics transmission, naming, and family assignment."""
        mother = self.humans[preg.mother_uid]
        father = self.humans[preg.father_uid] if preg.father_uid else None

        child_uid = uuid.uuid4()
        serial = self.serial_counter
        self.serial_counter += 1

        # Determine gender
        gender = Gender.MALE if self.rng.random() < 0.5 else Gender.FEMALE

        # Spanish naming conventions
        patronymic = father.identity.family_name if father else "Flores"
        matronymic = mother.identity.family_name
        full_surname = f"{patronymic} {matronymic}"

        boy_names = ["Mateo", "Santiago", "Sebastián", "Diego", "Alejandro", "Emilio", "Samuel", "Nicolás", "Daniel", "Lucas"]
        girl_names = ["Sofía", "Valentina", "Camila", "Lucía", "Isabella", "Mariana", "Elena", "Valeria", "Victoria", "Gabriela"]
        name_pool = boy_names if gender == Gender.MALE else girl_names
        given_name = str(self.rng.choice(name_pool))

        # Genetic inheritance
        genome_m = self.genomes.get(mother.uid, self.genetics.generate_random_genome())
        genome_f = self.genomes.get(father.uid, self.genetics.generate_random_genome()) if father else None
        child_genome = self.genetics.recombine(genome_m, genome_f)
        self.genomes[child_uid] = child_genome

        ident = HumanIdentity(
            uid=child_uid, serial=serial, given_name=given_name, family_name=full_surname, data_source=DataSource.SIMULATION_GENERATED
        )
        demo = Demographics(age=0, gender=gender, stage=DevelopmentalStage.INFANCY, birth_tick=current_tick)
        phys = PhysicalState(money=0.0, health=1.0, energy=1.0, home_location_id=mother.physical_state.home_location_id)

        pers = PersonalityEngine(PersonalityTraits(
            openness=TraitValue(base_value=child_genome.temperament_openness, current_value=child_genome.temperament_openness),
            conscientiousness=TraitValue(base_value=child_genome.temperament_conscientiousness, current_value=child_genome.temperament_conscientiousness),
            extraversion=TraitValue(base_value=child_genome.temperament_extraversion, current_value=child_genome.temperament_extraversion),
            agreeableness=TraitValue(base_value=child_genome.temperament_agreeableness, current_value=child_genome.temperament_agreeableness),
            neuroticism=TraitValue(base_value=child_genome.temperament_neuroticism, current_value=child_genome.temperament_neuroticism),
        ))
        child = SyntheticHuman(
            identity=ident, demographics=demo, physical_state=phys, personality=pers, emotions=EmotionalEngine(), memory=MemoryEngine()
        )
        self.humans[child_uid] = child

        bio = self.aging.create_profile(birth_tick=current_tick, initial_age_years=0.0)
        self.bio_profiles[child_uid] = bio

        # Genealogical pedigree
        self.genealogy.record_birth(child_uid, mother.uid, father.uid if father else None, tick=current_tick)

        # Household integration
        house = self.households.get_for_human(mother.uid)
        if house:
            house.add_member(child_uid, is_dependent=True)
            house.assign_caregiver(child_uid, mother.uid)

        self.reproduction.complete_delivery(mother.uid)
        return child

    def _process_death(self, human: SyntheticHuman, current_tick: int) -> None:
        """Process mortality, record lifespan, inheritance, and survivor grief."""
        bio = self.bio_profiles[human.uid]
        self.lifespans.append(bio.current_age_years)

        # Succession in household
        self.mortality.process_death(human, current_tick, self.genealogy, self.households, self.bus)

        # Bereavement grief to surviving kin
        kin_uids = (
            self.genealogy.get_children(human.uid)
            + self.genealogy.get_parents(human.uid)
        )
        rec = self.genealogy.get_record(human.uid)
        if rec and rec.partner and not self.mortality.is_deceased(rec.partner):
            kin_uids.append(rec.partner)

        for k_uid in kin_uids:
            if k_uid in self.humans and not self.mortality.is_deceased(k_uid):
                survivor = self.humans[k_uid]
                self.grief.apply_bereavement(
                    survivor=survivor,
                    deceased_uid=human.uid,
                    deceased_name=human.name,
                    social=self.social,
                    genealogy=self.genealogy,
                    current_tick=current_tick,
                )

    def capture_census(self, year: int) -> dict[str, Any]:
        """Capture demographic, lineage, and economic census snapshot."""
        living = [h for uid, h in self.humans.items() if not self.mortality.is_deceased(uid)]
        deceased_count = len(self.humans) - len(living)

        # Breakdown by developmental stages
        stage_counts = {stage.value: 0 for stage in DevelopmentalStage}
        for h in living:
            stage_counts[h.demographics.stage.value] += 1

        # Lineages: count living individuals by ancestral founder patronymic
        dynasty_counts: dict[str, int] = {}
        for h in living:
            root_surname = h.identity.family_name.split()[0]
            dynasty_counts[root_surname] = dynasty_counts.get(root_surname, 0) + 1

        sorted_dynasties = sorted(dynasty_counts.items(), key=lambda x: x[1], reverse=True)

        avg_age = float(np.mean([h.demographics.age for h in living])) if living else 0.0
        avg_lifespan = float(np.mean(self.lifespans)) if self.lifespans else 0.0

        # Trait averages
        avg_agree = float(np.mean([h.personality.get_trait("agreeableness") for h in living])) if living else 0.5
        avg_consc = float(np.mean([h.personality.get_trait("conscientiousness") for h in living])) if living else 0.5

        snapshot = {
            "year": year,
            "approx_generation": round(year / 25.0, 1),
            "living_population": len(living),
            "total_births": len(self.humans),
            "total_deaths": deceased_count,
            "stage_breakdown": stage_counts,
            "average_age_living": round(avg_age, 1),
            "average_life_expectancy": round(avg_lifespan, 1),
            "top_dynasties": sorted_dynasties[:5],
            "market_food_price": self.market.get_price(ItemType.FOOD),
            "market_food_stock": round(self.market.get_stock(ItemType.FOOD), 1),
            "population_agreeableness": round(avg_agree, 3),
            "population_conscientiousness": round(avg_consc, 3),
        }
        self.census_history.append(snapshot)
        return snapshot

    def render_dashboard(self, snapshot: dict[str, Any]) -> str:
        """Render a formatted console dashboard for the current census period."""
        lines = [
            "\n" + "=" * 80,
            f"  SALTBOR MACRO CENSUS — AÑO {snapshot['year']:4d} (Generación ~{snapshot['approx_generation']})",
            "=" * 80,
            f"  Población Viva:   {snapshot['living_population']:4d} habitantes | Nacimientos Totales: {snapshot['total_births']:4d} | Defunciones: {snapshot['total_deaths']:4d}",
            f"  Edad Promedio:    {snapshot['average_age_living']:4.1f} años   | Esperanza de Vida:   {snapshot['average_life_expectancy']:4.1f} años",
            "-" * 80,
            "  Pirámide Demográfica:",
            f"    * Lactantes (0-2):     {snapshot['stage_breakdown']['infancy']:3d} | Niñez (3-11):       {snapshot['stage_breakdown']['early_childhood'] + snapshot['stage_breakdown']['childhood']:3d}",
            f"    * Adolescencia (12-17): {snapshot['stage_breakdown']['adolescence']:3d} | Adultos (18-64):    {snapshot['stage_breakdown']['early_adulthood'] + snapshot['stage_breakdown']['adulthood']:3d}",
            f"    * Adultos Mayores (65+):{snapshot['stage_breakdown']['older_adulthood']:3d}",
            "-" * 80,
            "  Dinastías Familiares Dominantes (Linajes con más descendientes vivos):",
        ]
        for name, count in snapshot["top_dynasties"]:
            bar = "#" * min(30, count)
            lines.append(f"    - Familia {name:<12}: {count:3d} personas {bar}")

        lines.extend([
            "-" * 80,
            f"  Economía & Mercado: Precio Comida: ${snapshot['market_food_price']:.2f} | Stock Alimentos: {snapshot['market_food_stock']} unidades",
            f"  Deriva Psicosocial: Afabilidad Promedio: {snapshot['population_agreeableness']:.3f} | Laboriosidad: {snapshot['population_conscientiousness']:.3f}",
            "=" * 80 + "\n",
        ])
        return "\n".join(lines)


def run_macro_simulation(
    total_years: int = 250,
    ticks_per_year: int = 12,
    census_interval_years: int = 25,
    seed: int = 42,
    export_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Execute complete 10-generation macro-simulation."""
    print(f"\n[*] INICIANDO SIMULACIÓN MACRO-DEMOGRÁFICA DE SALTBOR")
    print(f"[*] Meta: {total_years} años de evolución social (~{total_years / 25.0:.0f} generaciones) | Semilla: {seed}")
    print(f"[*] Escala Temporal: {ticks_per_year} ticks por año (Total: {total_years * ticks_per_year} ticks)")
    print(f"[*] Generando población inicial de 20 fundadores (10 linajes)...")

    sim = MacroSimulation(seed=seed, ticks_per_year=ticks_per_year, total_years=total_years)
    sim.initialize_population()

    # Initial census (Year 0)
    snap0 = sim.capture_census(0)
    print(sim.render_dashboard(snap0))

    t_start = time.perf_counter()
    last_report_year = 0

    for current_tick in range(1, sim.total_ticks + 1):
        sim.step(current_tick)

        if current_tick % sim.ticks_per_year == 0:
            current_year = current_tick // sim.ticks_per_year

            # Periodic census report
            if (current_year - last_report_year) >= census_interval_years or current_year == total_years:
                last_report_year = current_year
                snap = sim.capture_census(current_year)
                print(sim.render_dashboard(snap))

    t_elapsed = time.perf_counter() - t_start
    final_snap = sim.census_history[-1]

    print("\n" + "=" * 80)
    print("  SIMULACIÓN MACRO-DEMOGRÁFICA COMPLETADA CON ÉXITO")
    print(f"  * Años Simulados:        {total_years} años (~{total_years / 25.0:.1f} generaciones)")
    print(f"  * Tiempo Real CPU:       {t_elapsed:.2f} segundos")
    print(f"  * Velocidad:             {(sim.total_ticks / t_elapsed):.1f} ticks/seg ({total_years / t_elapsed:.1f} años simulados/segundo real)")
    print(f"  * Población Final:       {final_snap['living_population']} habitantes")
    print(f"  * Linajes Totales:       {len(final_snap['top_dynasties'])} familias activas")
    top_dynasty_str = (
        f"Familia {final_snap['top_dynasties'][0][0]} ({final_snap['top_dynasties'][0][1]} miembros vivos)"
        if final_snap["top_dynasties"]
        else "Ninguno (Población extinta)"
    )
    print(f"  * Linaje Más Próspero:   {top_dynasty_str}")
    print("=" * 80 + "\n")

    summary_data = {
        "total_years_simulated": total_years,
        "elapsed_seconds": round(t_elapsed, 2),
        "ticks_per_second": round(sim.total_ticks / t_elapsed, 1),
        "final_census": final_snap,
        "census_timeline": sim.census_history,
    }

    if export_path:
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Reporte demográfico exportado a: {export_path}")

    return summary_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulación Macro-Demográfica de 10 Generaciones en Saltbor")
    parser.add_argument("--years", type=int, default=250, help="Años a simular (default: 250 años = ~10 generaciones)")
    parser.add_argument("--ticks-per-year", type=int, default=12, help="Resolución temporal: ticks por año (default: 12)")
    parser.add_argument("--interval", type=int, default=25, help="Intervalo de reporte de censo en años (default: 25)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria maestra")
    parser.add_argument("--export", type=str, default="experiments/results/macro_10_generations.json", help="Ruta de exportación JSON")

    args = parser.parse_args()
    run_macro_simulation(
        total_years=args.years,
        ticks_per_year=args.ticks_per_year,
        census_interval_years=args.interval,
        seed=args.seed,
        export_path=Path(args.export) if args.export else None,
    )
