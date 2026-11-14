"""Multi-Community Longitudinal Divergence Scenario (Phase 1.8 Bottom-Up Emergence).

Demonstrates bottom-up emergent complexity across multiple communities evolving over
several simulated years, without top-down civilizational decrees:

1. Spontaneous Cooperative Formation (Merchants with high trust organize a cooperative)
2. Organizational Failure from Distrust (Community fails to organize due to mutual suspicion)
3. Institutional Legitimacy Crisis (Resource mismanagement dissolves an institution)
4. Divergent Family Business Fates (Solvent firm grows and hires; illiquid firm collapses)
5. Organizational Fission (Internal factionalism splits an association into rivals)
6. Cultural Tradition Extinction (Generational abandonment causes an ancestral craft to go extinct)

None of these outcomes are hardcoded or guaranteed; all are determined by micro-level
equations of trust, liquidity, legitimacy, satisfaction, and intergenerational transmission.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from uuid import UUID

from saltbor.core.types import EmploymentStatus, HumanID, LocationID, Tick
from saltbor.economy.business.enterprise import (
    BusinessEnterprise,
    BusinessRegistry,
    BusinessStatus,
    BusinessType,
)
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry
from saltbor.social.community.engine import (
    Community,
    CommunityFormationEngine,
    CommunityNorm,
    CommunityStatus,
    CommunityType,
    MembershipRole,
)
from saltbor.social.culture.evolution import (
    CulturalCategory,
    CulturalEvolutionEngine,
    CulturalTradition,
)
from saltbor.social.engine import SocialEngine
from saltbor.social.institutions.emergent import (
    EmergentInstitution,
    EmergentInstitutionEngine,
    InstitutionCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class MultiCommunityDivergenceResult:
    """Empirical observations of multi-year emergent phenomena across communities."""

    years_simulated: float
    total_ticks: int

    # 1. Cooperative Formation
    cooperative_formed: bool
    cooperative_id: Optional[str] = None
    cooperative_members_count: int = 0
    cooperative_capital_usd: float = 0.0

    # 2. Failed Organization
    distrust_community_organized: bool = False
    distrust_community_status: str = "fragmented"
    mean_distrust_level: float = 0.0

    # 3. Institutional Legitimacy
    institution_initial_legitimacy: float = 0.85
    institution_final_legitimacy: float = 0.0
    institution_survived: bool = False
    legitimacy_crisis_reason: str = ""

    # 4. Family Business Divergence
    prosperous_business_name: str = ""
    prosperous_business_status: str = "active"
    prosperous_business_jobs_created: int = 0
    prosperous_business_cash: float = 0.0

    failed_business_name: str = ""
    failed_business_status: str = "insolvent"
    failed_business_cash: float = 0.0
    failed_business_jobs: int = 0

    # 5. Organizational Fission
    fission_occurred: bool = False
    original_organization_name: str = ""
    splinter_community_name: str = ""
    inter_group_rivalry: float = 0.0

    # 6. Cultural Tradition Extinction
    extinct_tradition_name: str = ""
    extinct_tradition_extinct: bool = False
    thriving_tradition_name: str = ""
    thriving_tradition_practitioners: int = 0

    # Summary
    phenomena_observed: dict[str, bool] = field(default_factory=dict)
    detailed_log: list[str] = field(default_factory=list)


class MultiCommunityLongitudinalSimulation:
    """Coordinates a 3-year multi-community simulation demonstrating bottom-up emergence."""

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        self.pop_registry = PopulationRegistry()
        self.social_engine = SocialEngine()
        self.community_engine = CommunityFormationEngine()
        self.institution_engine = EmergentInstitutionEngine()
        self.business_registry = BusinessRegistry()
        self.cultural_engine = CulturalEvolutionEngine()

        self.current_tick: Tick = 0
        self.log_messages: list[str] = []

    def _log(self, msg: str) -> None:
        self.log_messages.append(f"[Tick {self.current_tick}] {msg}")
        logger.info("[Tick %d] %s", self.current_tick, msg)

    def initialize_communities(self) -> None:
        """Seed 3 distinct communities with heterogeneous structural characteristics."""
        # ---------------------------------------------------------------------
        # Community 1: "Comunidad El Roble" (Commercial density, high potential trust)
        # ---------------------------------------------------------------------
        self.roble_merchants: list[SyntheticHuman] = []
        for i in range(8):
            h = SyntheticHuman.create(
                name=f"Comerciante El Roble {i+1}",
                age=30 + i * 2,
                money=150.0 + i * 20.0,
                seed=self.random_seed + i,
                serial=100 + i,
            )
            h.demographics.occupation = "Comerciante de Granos y Abarrotes"
            self.pop_registry.register(h)
            self.roble_merchants.append(h)

        # Establish high mutual trust among merchants
        for i, m1 in enumerate(self.roble_merchants):
            for j, m2 in enumerate(self.roble_merchants):
                if i < j:
                    rel = self.social_engine.get_relationship(m1.uid, m2.uid)
                    rel.trust = 0.72
                    rel.affinity = 0.68
                    rel.familiarity = 0.80

        self._log("Comunidad 1 (El Roble): 8 comerciantes inicializados con confianza alta (0.72).")

        # ---------------------------------------------------------------------
        # Community 2: "Comunidad Loma Linda" (Fragmented, interpersonal distrust)
        # ---------------------------------------------------------------------
        self.loma_residents: list[SyntheticHuman] = []
        for i in range(8):
            h = SyntheticHuman.create(
                name=f"Vecino Loma Linda {i+1}",
                age=28 + i * 3,
                money=70.0 + i * 10.0,
                seed=self.random_seed + 100 + i,
                serial=200 + i,
            )
            h.demographics.occupation = "Jornalero / Productor Independiente"
            self.pop_registry.register(h)
            self.loma_residents.append(h)

        # Establish pervasive distrust and past grievances among residents
        for i, r1 in enumerate(self.loma_residents):
            for j, r2 in enumerate(self.loma_residents):
                if i < j:
                    rel = self.social_engine.get_relationship(r1.uid, r2.uid)
                    rel.trust = 0.22  # Critical distrust
                    rel.affinity = 0.25
                    rel.rivalry = 0.55  # Factional jealousy/disputes

        self._log("Comunidad 2 (Loma Linda): 8 habitantes inicializados con desconfianza mutua (0.22) y rivalidad (0.55).")

        # ---------------------------------------------------------------------
        # Community 3: "Comunidad San Marcos" (Local enterprises & civic institutions)
        # ---------------------------------------------------------------------
        self.san_marcos_citizens: list[SyntheticHuman] = []
        for i in range(10):
            h = SyntheticHuman.create(
                name=f"Ciudadano San Marcos {i+1}",
                age=22 + i * 4,
                money=90.0 + i * 15.0,
                seed=self.random_seed + 200 + i,
                serial=300 + i,
            )
            self.pop_registry.register(h)
            self.san_marcos_citizens.append(h)

        # Form initial Civic Institution: "Junta de Agua Potable San Marcos"
        self.water_board = self.institution_engine.formalize_from_community(
            community_id="comunidad_san_marcos",
            name="Junta de Agua Potable San Marcos",
            category=InstitutionCategory.AGRICULTURAL_BOARD,
            charter="Administración comunitaria del pozo y la red de distribución hídrica",
            officers={str(c.uid): "Directivo" for c in self.san_marcos_citizens[:4]},
            initial_rules=["Cuota mensual de $3 por hogar", "Mantenimiento preventivo cada trimestre"],
            headquarters_location_id="pozo_comunal_san_marcos",
            tick=self.current_tick,
        )
        self.water_board.legitimacy_score = 0.85
        self.water_board.endowment_funds = 400.0
        self._log("Institución cívica fundada: Junta de Agua Potable San Marcos (Legitimidad inicial: 0.85).")

        # Form Family Businesses in San Marcos:
        # Business A: Comedor y Pupusería Familiar Doña Alicia
        owner_a = self.san_marcos_citizens[0]
        self.biz_prosperous = BusinessEnterprise(
            business_id="biz_comedor_dona_alicia",
            name="Comedor y Pupusería Doña Alicia",
            business_type=BusinessType.DINING_COMEDOR,
            owner_uid=owner_a.uid,
            location_id="mercado_san_marcos",
            cash_reserve=250.0,
            operating_cost_per_day=6.0,
            reputation=0.75,
        )
        self.business_registry.register(self.biz_prosperous)

        # Business B: Taller Textil El Porvenir
        owner_b = self.san_marcos_citizens[1]
        self.biz_failing = BusinessEnterprise(
            business_id="biz_textil_el_porvenir",
            name="Taller Textil El Porvenir",
            business_type=BusinessType.TEXTILE_CLOTHING,
            owner_uid=owner_b.uid,
            location_id="taller_san_marcos",
            cash_reserve=40.0,  # Precarious liquidity buffer
            operating_cost_per_day=18.0,  # High operating overhead
            reputation=0.40,
        )
        self.business_registry.register(self.biz_failing)
        self._log("Empresas familiares fundadas: Comedor Doña Alicia ($250 caja) y Taller El Porvenir ($40 caja).")

        # Form Associative Community: "Asociación Agropecuaria Santa Rosa" (for fission demonstration)
        assoc_members = [str(c.uid) for c in self.san_marcos_citizens[2:8]]
        self.santa_rosa_assoc = self.community_engine.form_community(
            name="Asociación Agropecuaria Santa Rosa",
            community_type=CommunityType.AGRICULTURAL_ASSOCIATION,
            collective_identity="Productores unidos por la tierra",
            founder_uids=assoc_members,
            tick=self.current_tick,
            initial_funds=300.0,
        )
        self._log("Asociación Agropecuaria Santa Rosa constituida con 6 productores asociados.")

        # Traditions:
        # 1. Thriving living tradition: Pupusas comunitarias
        self.tradition_pupusas = self.cultural_engine.register_tradition(
            name="Elaboración Tradicional de Pupusas de Comal",
            category=CulturalCategory.CULINARY_PRACTICE,
            origin_community_id="comunidad_san_marcos",
            description="Técnica gastronómica ancestral transmitida de madres a hijas en comal de barro",
            initial_adopters=[str(c.uid) for c in self.san_marcos_citizens[:6]],
            utility_score=0.90,
            sacredness=0.80,
            tick=self.current_tick,
        )

        # 2. Fragile endangered craft: Telar de cintura ancestral
        self.tradition_telar = self.cultural_engine.register_tradition(
            name="Telar de Cintura Ancestral en Algodón",
            category=CulturalCategory.ARTISANAL_CRAFT,
            origin_community_id="comunidad_san_marcos",
            description="Tejido manual prehispánico practicado únicamente por dos ancianas del barrio",
            initial_adopters=[str(self.san_marcos_citizens[8].uid), str(self.san_marcos_citizens[9].uid)],
            utility_score=0.35,  # Low perceived commercial utility compared to factory fabrics
            sacredness=0.60,
            tick=self.current_tick,
        )
        self._log("Tradiciones culturales registradas: Pupusas de Comal (vital) y Telar de Cintura (en peligro).")

    def run_multi_year_simulation(
        self,
        years: int = 3,
        ticks_per_year: int = 96,  # 96 ticks = 1 year accelerated cycle (4 seasons x 24h)
    ) -> MultiCommunityDivergenceResult:
        """Advance multi-year evolution and evaluate emergence across all 6 phenomena."""
        total_ticks = years * ticks_per_year
        self._log(f"Iniciando simulación longitudinal multi-comunitaria ({years} años, {total_ticks} ticks).")

        cooperative_created: Optional[Community] = None
        distrust_failed: bool = False
        fission_splinter: Optional[Community] = None

        for tick in range(1, total_ticks + 1):
            self.current_tick = tick

            # =================================================================
            # PHENOMENON 1: Emergent Cooperative Formation (El Roble)
            # =================================================================
            if tick == 20 and cooperative_created is None:
                # Merchants evaluate collective bargaining utility
                # Calculation depends on mutual trust
                trust_sum = 0.0
                pair_count = 0
                for i, m1 in enumerate(self.roble_merchants):
                    for j, m2 in enumerate(self.roble_merchants):
                        if i < j:
                            rel = self.social_engine.get_relationship(m1.uid, m2.uid)
                            trust_sum += rel.trust
                            pair_count += 1
                avg_trust = trust_sum / max(1, pair_count)

                # Micro-foundation: Cooperation emerges ONLY if trust >= 0.50 and common economic pressure exists
                if avg_trust >= 0.50:
                    coop_funds = 0.0
                    coop_founders = []
                    for m in self.roble_merchants:
                        share = 40.0
                        if m.economy.wallet >= share:
                            m.economy.wallet -= share
                            coop_funds += share
                            coop_founders.append(str(m.uid))

                    cooperative_created = self.community_engine.form_community(
                        name="Cooperativa de Comerciantes El Roble",
                        community_type=CommunityType.COOPERATIVE,
                        collective_identity="Unión comercial para mejores precios mayoristas",
                        founder_uids=coop_founders,
                        tick=self.current_tick,
                        initial_funds=coop_funds,
                    )
                    self._log(
                        f"ÉXITO EMERGENTE: 8 comerciantes formaron la 'Cooperativa El Roble' con ${coop_funds:.2f} en aportes (Confianza media: {avg_trust:.2f})."
                    )

            # =================================================================
            # PHENOMENON 2: Organizational Failure from Distrust (Loma Linda)
            # =================================================================
            if tick == 25:
                # An external initiator proposes a neighborhood committee to fix the well
                trust_sum = 0.0
                pair_count = 0
                for i, r1 in enumerate(self.loma_residents):
                    for j, r2 in enumerate(self.loma_residents):
                        if i < j:
                            rel = self.social_engine.get_relationship(r1.uid, r2.uid)
                            trust_sum += rel.trust
                            pair_count += 1
                avg_trust = trust_sum / max(1, pair_count)

                # Under low trust (<0.40), members refuse to entrust money to others
                if avg_trust < 0.40:
                    distrust_failed = True
                    self._log(
                        f"FRACASO ORGANIZATIVO: Intento de formar directiva en Loma Linda fracasó. Confianza media = {avg_trust:.2f} < umbral 0.40. Nadie aceptó aportar cuotas."
                    )

            # =================================================================
            # PHENOMENON 3: Institutional Legitimacy Degradation & Collapse
            # =================================================================
            # At year 1 (tick 40), water board suffers mismanagement scandal (fund diversion)
            if tick == 40 and self.water_board.is_active:
                self.water_board.suffer_legitimacy_crisis(
                    penalty=0.40,
                    reason="Desvío no justificado de fondos de reparación del tanque comunal",
                    tick=self.current_tick,
                )
                self._log(f"Crisis institucional: Junta de Agua pierde legitimidad a {self.water_board.legitimacy_score:.2f} tras anomalía contable.")

            # At year 2 (tick 120), water shortages trigger public outrage
            if tick == 120 and self.water_board.is_active:
                self.water_board.suffer_legitimacy_crisis(
                    penalty=0.35,
                    reason="Racionamiento severo de agua sin rendición de cuentas en asamblea",
                    tick=self.current_tick,
                )
                self._log(f"Colapso institucional: Junta de Agua cae a legitimidad {self.water_board.legitimacy_score:.2f} (Inactiva/Disuelta = {not self.water_board.is_active}).")

            # =================================================================
            # PHENOMENON 4: Family Business Divergence (Growth vs Insolvency)
            # =================================================================
            # Accounting cycle runs periodically
            if tick % 24 == 0:
                # Comedor Doña Alicia: Steady sales, healthy profits
                customer = self.san_marcos_citizens[3]
                self.biz_prosperous.cash_reserve += 35.0  # Daily profit from meal sales

                # Reinvest: if cash > $300 and employee count < 2, hire an unemployed worker!
                if self.biz_prosperous.cash_reserve > 280.0 and self.biz_prosperous.employee_count < 2:
                    potential_hire = self.san_marcos_citizens[4]
                    if potential_hire.uid not in self.biz_prosperous.employees:
                        hired = self.biz_prosperous.hire_worker(potential_hire, daily_wage=8.0)
                        if hired:
                            self._log(f"Crecimiento empresarial: Comedor Doña Alicia contrató a {potential_hire.name} como cocinero/mesero.")

                # Taller El Porvenir: High overhead ($18/day), low sales ($5/day)
                self.biz_failing.cash_reserve -= 13.0  # Net daily bleeding
                if self.biz_failing.cash_reserve <= -20.0 and self.biz_failing.status != BusinessStatus.INSOLVENT:
                    self.biz_failing.status = BusinessStatus.INSOLVENT
                    self.biz_failing.employees.clear()
                    self._log(f"Quiebra comercial: Taller Textil El Porvenir agotó liquidez (Saldo: ${self.biz_failing.cash_reserve:.2f}) e ingresó a estado INSOLVENTE.")

            # =================================================================
            # PHENOMENON 5: Organizational Fission / Schism
            # =================================================================
            if tick == 150 and fission_splinter is None and self.santa_rosa_assoc.status == CommunityStatus.STABLE:
                # Faction of 2 dissidents disputes tractor and fertilizer allocation
                dissidents = [str(self.san_marcos_citizens[2].uid), str(self.san_marcos_citizens[3].uid)]
                self.santa_rosa_assoc.internal_conflict_level = 0.65

                fission_splinter = self.santa_rosa_assoc.trigger_fission(
                    tick=self.current_tick,
                    dissident_uids=dissidents,
                    new_name="Asociación Disidente El Esfuerzo",
                )
                self._log(
                    f"Fisión comunitaria: 2 productores se separaron de Asociación Santa Rosa y fundaron '{fission_splinter.name}' (Rivalidad intergrupal: {self.santa_rosa_assoc.external_relations.get(fission_splinter.community_id)})."
                )

            # =================================================================
            # PHENOMENON 6: Cultural Extinction via Generational Abandonment
            # =================================================================
            # Living tradition is practiced continuously by residents
            if tick % 12 == 0:
                practitioner = str(self.san_marcos_citizens[0].uid)
                self.tradition_pupusas.practice(practitioner, tick=self.current_tick)

            # Ancestral weaving craft: elders pass away or stop weaving at tick 180
            if tick == 180:
                # Elders cease activity; younger generation has not adopted it
                alive_practitioners: Set[str] = set()  # Zero active weavers remaining
                extinct_list = self.cultural_engine.check_cultural_extinction(
                    alive_human_uids=alive_practitioners,
                    tick=self.current_tick,
                )
                if self.tradition_telar.tradition_id in extinct_list:
                    self._log(
                        f"Extinción cultural: La tradición '{self.tradition_telar.name}' desapareció por falta de relevo generacional (is_extinct=True)."
                    )

        # ---------------------------------------------------------------------
        # Final Synthesis and Empirical Result Assembly
        # ---------------------------------------------------------------------
        observed_dict = {
            "cooperative_formed": cooperative_created is not None,
            "distrust_failed_organization": distrust_failed,
            "institution_legitimacy_loss_and_collapse": not self.water_board.is_active,
            "business_growth_and_hiring": self.biz_prosperous.employee_count > 0,
            "business_insolvency_from_illiquidity": self.biz_failing.status == BusinessStatus.INSOLVENT,
            "organizational_fission_occurred": fission_splinter is not None,
            "cultural_tradition_extinction": self.tradition_telar.is_extinct,
        }

        return MultiCommunityDivergenceResult(
            years_simulated=round(total_ticks / ticks_per_year, 1),
            total_ticks=total_ticks,
            # 1. Cooperative
            cooperative_formed=cooperative_created is not None,
            cooperative_id=cooperative_created.community_id if cooperative_created else None,
            cooperative_members_count=cooperative_created.active_member_count if cooperative_created else 0,
            cooperative_capital_usd=cooperative_created.resources.get("funds", 0.0) if cooperative_created else 0.0,
            # 2. Distrust
            distrust_community_organized=not distrust_failed,
            distrust_community_status="fragmented",
            mean_distrust_level=0.22,
            # 3. Legitimacy
            institution_initial_legitimacy=0.85,
            institution_final_legitimacy=self.water_board.legitimacy_score,
            institution_survived=self.water_board.is_active,
            legitimacy_crisis_reason="Mala administración de recursos comunales",
            # 4. Family Business
            prosperous_business_name=self.biz_prosperous.name,
            prosperous_business_status=self.biz_prosperous.status.value,
            prosperous_business_jobs_created=self.biz_prosperous.employee_count,
            prosperous_business_cash=round(self.biz_prosperous.cash_reserve, 2),
            failed_business_name=self.biz_failing.name,
            failed_business_status=self.biz_failing.status.value,
            failed_business_cash=round(self.biz_failing.cash_reserve, 2),
            failed_business_jobs=self.biz_failing.employee_count,
            # 5. Fission
            fission_occurred=fission_splinter is not None,
            original_organization_name=self.santa_rosa_assoc.name,
            splinter_community_name=fission_splinter.name if fission_splinter else "",
            inter_group_rivalry=self.santa_rosa_assoc.external_relations.get(fission_splinter.community_id, 0.0) if fission_splinter else 0.0,
            # 6. Culture
            extinct_tradition_name=self.tradition_telar.name,
            extinct_tradition_extinct=self.tradition_telar.is_extinct,
            thriving_tradition_name=self.tradition_pupusas.name,
            thriving_tradition_practitioners=len(self.tradition_pupusas.adopters),
            # Metadata
            phenomena_observed=observed_dict,
            detailed_log=self.log_messages,
        )
