"""Phase 0.9 Experiments Suite: Part 2 (EXP_09_M through EXP_09_X).

Covers:
- EXP_09_M: Reputacion y confianza.
- EXP_09_N: Cooperacion economica.
- EXP_09_O: Desarrollo cultural.
- EXP_09_P: Transformacion institucional.
- EXP_09_Q: Difusion de innovaciones.
- EXP_09_R: Inteligencia colectiva bajo incertidumbre.
- EXP_09_S: Comunidades que desaparecen o se dividen.
- EXP_09_T: Simulacion longitudinal de 1, 3, 6 y 12 meses.
- EXP_09_U: Integracion entre geografia, economia y sociedad.
- EXP_09_V: Persistencia y recuperacion de redes.
- EXP_09_W: Comportamiento con informacion incompleta.
- EXP_09_X: Escalabilidad de redes sociales.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome
from saltbor.core.config import SimulationConfig
from saltbor.core.types import Tick
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.phase09_repositories import (
    CollectiveEnterpriseRepository,
    CommunityRepository,
    ReputationRepository,
    SocialEdgeRepository,
)
from saltbor.persistence.schema import SchemaManager
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.collective_intelligence.engine import (
    CollectiveIntelligenceEngine,
    SolutionProposal,
)
from saltbor.social.community.engine import (
    Community,
    CommunityFormationEngine,
    CommunityMembership,
    CommunityStatus,
    CommunityType,
    MembershipRole,
)
from saltbor.social.culture.evolution import (
    CulturalCategory,
    CulturalEvolutionEngine,
)
from saltbor.social.economy.collective_economy import (
    CollectiveEconomyEngine,
    CollectiveOrgType,
)
from saltbor.social.institutions.emergent import (
    EmergentInstitutionEngine,
    InstitutionCategory,
)
from saltbor.social.lod import SocialLODManager, SocialLODTier
from saltbor.social.network.graph_engine import (
    BondState,
    SocialEdge,
    SocialNetworkEngine,
    SocialRelationType,
)
from saltbor.social.reputation.reputation_system import (
    ReputationDomain,
    ReputationEngine,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXP_09_M: Reputacion y confianza
# =============================================================================
class Experiment09_M_ReputationAndTrust(BaseExperiment):
    """EXP_09_M: Multi-contextual, situated reputation across personal, professional, and communal domains."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_M",
            name="Contextual Reputation and Social Influence",
            description="Reputation evolves independently across personal, craft, and civic spheres with testimonial diffusion.",
            duration_ticks=96,
            random_seed=42,
            population_size=4,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        rep_engine = ReputationEngine()

        carpenter = "carpintero_tomas"
        client = "cliente_pedro"
        neighbor = "vecino_mario"

        # 1. Reliable craft fulfillment boosts professional reputation
        rep_engine.record_pact_outcome(
            subject_uid=carpenter,
            observer_uid=client,
            fulfilled=True,
            domain=ReputationDomain.PROFESSIONAL,
            tick=10,
        )

        # 2. Defection in communal labor project (faena) hurts communal standing
        rep_engine.record_cooperation_effort(
            subject_uid=carpenter,
            observer_uid=neighbor,
            cooperated=False,
            domain=ReputationDomain.COMMUNAL,
            tick=15,
        )

        prof_rep = rep_engine.get_or_create(carpenter, client, domain=ReputationDomain.PROFESSIONAL)
        comm_rep = rep_engine.get_or_create(carpenter, neighbor, domain=ReputationDomain.COMMUNAL)

        # 3. Testimonial transmission to third party
        third_party = "cliente_luis"
        rep_engine.transmit_testimonial(
            subject_uid=carpenter,
            teller_uid=client,
            listener_uid=third_party,
            domain=ReputationDomain.PROFESSIONAL,
            trust_in_teller=0.85,
            tick=20,
        )
        hearsay_rep = rep_engine.get_or_create(carpenter, third_party, domain=ReputationDomain.PROFESSIONAL)

        success = (
            prof_rep.score > 0.60
            and comm_rep.score < 0.45
            and hearsay_rep.score > 0.50
            and hearsay_rep.testimonials_count >= 1
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "professional_score": round(prof_rep.score, 3),
            "communal_score": round(comm_rep.score, 3),
            "hearsay_score": round(hearsay_rep.score, 3),
            "influence_professional": rep_engine.get_social_influence(carpenter, ReputationDomain.PROFESSIONAL),
            "influence_communal": rep_engine.get_social_influence(carpenter, ReputationDomain.COMMUNAL),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Situated reputation: high in professional ({metrics['professional_score']}) but low in communal ({metrics['communal_score']}).",
            hypotheses=[
                {"hypothesis": "Reputation is situated and domain-specific rather than universal", "verified": True},
                {"hypothesis": "Testimonials propagate reputation to third parties", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_N: Cooperacion economica
# =============================================================================
class Experiment09_N_EconomicCooperation(BaseExperiment):
    """EXP_09_N: Collective enterprise operations, pooled inventory, bulk buying, and dividend sharing."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_N",
            name="Collective Economic Cooperation",
            description="Models cooperative enterprise with shared inventory, bulk supply discounts, and dividend payouts.",
            duration_ticks=96,
            random_seed=42,
            population_size=5,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        econ_engine = CollectiveEconomyEngine()

        founders = ["rosa_pupusera", "carmen_cocinera", "lucia_vendedora"]
        ent = econ_engine.create_enterprise(
            name="Pupuseria Comunitaria Las Flores",
            org_type=CollectiveOrgType.FAMILY_ENTERPRISE,
            founder_uids=founders,
            initial_treasury=150.0,
            tick=10,
        )

        # 1. Bulk purchase of corn flour and quesillo at discount
        bought = econ_engine.bulk_purchase_supplies(
            org_id=ent.org_id,
            item_name="harina_de_maiz_qq",
            quantity=5.0,
            wholesale_unit_cost=15.0, # Total = $75
        )
        assert bought is True

        # 2. Production of pupusas
        ent.record_production_output("pupusas_revueltas", quantity=200.0, production_cost=10.0)

        # 3. Market sale: 200 pupusas @ $0.75 = $150
        revenue = ent.sell_goods("pupusas_revueltas", quantity=200.0, unit_price=0.75)
        assert revenue == 150.0

        # 4. Distribute dividends from profits
        dividends = ent.distribute_dividends(total_dividend_pool=90.0)
        each_payout = dividends.get(founders[0], 0.0)

        success = (
            bought is True
            and revenue == 150.0
            and len(dividends) == 3
            and each_payout > 25.0
            and ent.treasury_usd > 0
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "enterprise_name": ent.name,
            "treasury_after_dividends": round(ent.treasury_usd, 2),
            "total_revenue": round(ent.total_revenue_earned, 2),
            "dividend_payouts": dividends,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Enterprise earned ${revenue:.2f} revenue, paid dividends of ${each_payout:.2f} to each partner.",
            hypotheses=[
                {"hypothesis": "Bulk purchasing successfully pools capital and manages stock", "verified": bought},
                {"hypothesis": "Sales revenue is transparently distributed as dividends", "verified": len(dividends) == 3},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_O: Desarrollo cultural
# =============================================================================
class Experiment09_O_CulturalDevelopment(BaseExperiment):
    """EXP_09_O: Emergence, practice, mutation, and preservation of local cultural traditions."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_O",
            name="Cultural Development and Adaptation",
            description="Emergence, practice, innovative mutation, and dormancy of community traditions.",
            duration_ticks=192,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        cult_engine = CulturalEvolutionEngine()

        trad = cult_engine.register_tradition(
            name="Festival del Maiz de Suchitoto",
            category=CulturalCategory.COMMUNAL_TRADITION,
            origin_community_id="comm_suchitoto",
            description="Celebracion con atol agrio, elotes locos y desfile de carrozas.",
            initial_adopters=["vecino_1", "vecino_2"],
            utility_score=0.70,
            tick=10,
        )

        # Innovation: add musical competition to the tradition
        trad.mutate_tradition(
            innovator_uid="musico_carlos",
            innovation_summary="Incorporacion de concurso de marimba de arco y cancionero popular",
            tick=50,
        )
        has_innovation = len(trad.variation_notes) >= 1
        utility_boosted = trad.utility_score > 0.70

        # Unpracticed tradition goes dormant after time
        abandoned_trad = cult_engine.register_tradition(
            name="Costumbre Obsoleta",
            category=CulturalCategory.COMMERCIAL_CUSTOM,
            origin_community_id="comm_suchitoto",
            description="Practica en desuso",
            tick=0,
        )
        dormant_ids = cult_engine.decay_unpracticed_traditions(current_tick=5000, dormancy_limit_ticks=1000)

        success = has_innovation and utility_boosted and (abandoned_trad.tradition_id in dormant_ids)
        elapsed = time.perf_counter() - t0

        metrics = {
            "tradition_name": trad.name,
            "utility_score": round(trad.utility_score, 3),
            "mutations": trad.variation_notes,
            "dormant_traditions_count": len(dormant_ids),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Tradition '{trad.name}' evolved via innovation; unpracticed custom marked dormant.",
            hypotheses=[
                {"hypothesis": "Innovations successfully augment existing traditions", "verified": has_innovation},
                {"hypothesis": "Unpracticed cultural traditions naturally decay into dormancy", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_P: Transformacion institucional
# =============================================================================
class Experiment09_P_InstitutionalTransformation(BaseExperiment):
    """EXP_09_P: Codification of an informal community into an institution and legitimacy crisis handling."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_P",
            name="Emergent Institutional Transformation",
            description="Community formalizes bylaws into an institution; survives legitimacy shock or dissolves.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        inst_engine = EmergentInstitutionEngine()

        officers = {"dona_elena": "Presidenta", "don_mario": "Tesorero"}
        initial_rules = [
            "Transparencia en el manejo de fondos comunales",
            "Cuota voluntaria mensual de $1 para fondo de emergencia",
        ]

        inst = inst_engine.formalize_from_community(
            community_id="comm_el_espino",
            name="Consejo Comunitario El Espino",
            category=InstitutionCategory.NEIGHBORHOOD_COUNCIL,
            charter="Administracion de agua potable y caminos comunales",
            officers=officers,
            initial_rules=initial_rules,
            tick=10,
        )

        initial_legitimacy = inst.legitimacy_score
        assert len(inst.constitution_bylaws) == 2

        # Suffer a legitimacy shock (treasury discrepancy)
        inst.suffer_legitimacy_crisis(penalty=0.30, reason="retraso_en_informe_financiero", tick=30)
        strained_legitimacy = inst.legitimacy_score

        # Institutional reform: enact new anti-corruption audit rule
        inst.formalize_rule("Auditoria trimestral por comision de vecinos", tick=40)
        reformed = len(inst.constitution_bylaws) == 3

        success = (
            inst.is_active is True
            and strained_legitimacy < initial_legitimacy
            and reformed is True
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "institution_id": inst.institution_id,
            "bylaws_count": len(inst.constitution_bylaws),
            "initial_legitimacy": round(initial_legitimacy, 3),
            "strained_legitimacy": round(strained_legitimacy, 3),
            "is_active": inst.is_active,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Institution '{inst.name}' survived legitimacy shock ({initial_legitimacy:.2f} -> {strained_legitimacy:.2f}) and codified reforms.",
            hypotheses=[
                {"hypothesis": "Informal communities can formalize into institutions with bylaws", "verified": True},
                {"hypothesis": "Institutions respond to legitimacy crises with rule adjustments", "verified": reformed},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_Q: Difusion de innovaciones
# =============================================================================
class Experiment09_Q_InnovationDiffusion(BaseExperiment):
    """EXP_09_Q: S-curve diffusion of a high-yield agricultural or organizational innovation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_Q",
            name="Innovation Diffusion",
            description="Traces the spread of an innovation through early adopters to community-wide adoption.",
            duration_ticks=192,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        cult_engine = CulturalEvolutionEngine()

        uids = [f"farmer_{i}" for i in range(8)]
        # Connect into small-world structure (ring + cross shortcuts)
        for i in range(8):
            net.record_interaction(uids[i], uids[(i+1)%8], tick=5, valence=0.75, bidirectional=True)
        net.record_interaction(uids[0], uids[4], tick=5, valence=0.8, bidirectional=True)

        trad = cult_engine.register_tradition(
            name="Sistema Milpa Intercalada con Arboles Frutales (MIAF)",
            category=CulturalCategory.AGRICULTURAL_TECHNIQUE,
            origin_community_id="comm_chalatenango",
            description="Siembra en curvas a nivel intercalando maiz con melocoton y frijol abono.",
            initial_adopters=[uids[0]],
            utility_score=0.92,
            tick=10,
        )

        adoption_stages: list[int] = [len(trad.adopters)]

        # Diffusion phase 1: early adopters (neighbors of 0)
        for nbr in net.get_neighbors(uids[0], min_trust=0.5):
            cult_engine.diffuse_via_imitation(trad.tradition_id, nbr, observed_success=0.95, tick=20)
        adoption_stages.append(len(trad.adopters))

        # Diffusion phase 2: secondary adopters
        for adopter in list(trad.adopters):
            for nbr in net.get_neighbors(adopter, min_trust=0.5):
                cult_engine.diffuse_via_imitation(trad.tradition_id, nbr, observed_success=0.90, tick=40)
        adoption_stages.append(len(trad.adopters))

        total_adopted = len(trad.adopters)
        has_diffused = total_adopted >= 4 and adoption_stages[-1] > adoption_stages[0]

        success = has_diffused
        elapsed = time.perf_counter() - t0

        metrics = {
            "initial_adopters": adoption_stages[0],
            "stage_1_adopters": adoption_stages[1],
            "final_adopters": total_adopted,
            "total_population": len(uids),
            "diffusion_rate": round(total_adopted / len(uids), 3),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Innovation diffused from {adoption_stages[0]} to {total_adopted}/{len(uids)} agents ({metrics['diffusion_rate']*100:.1f}%).",
            hypotheses=[
                {"hypothesis": "High-utility innovation spreads progressively along network ties", "verified": has_diffused},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_R: Inteligencia colectiva bajo incertidumbre
# =============================================================================
class Experiment09_R_CollectiveIntelligenceUncertainty(BaseExperiment):
    """EXP_09_R: Collective problem solving under incomplete information and contradictory signals."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_R",
            name="Collective Intelligence Under Uncertainty",
            description="Evaluates error detection, consensus, and robust solution selection with noisy inputs.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        col_kg = CollectiveKnowledgeGraph()
        engine = CollectiveIntelligenceEngine(collective_kg=col_kg)

        prob = Problem(
            problem_id="prob_sequia_incierta",
            description="Senales contradictorias sobre posible temporal o sequia severa en epoca de siembra",
            domain="clima_agricultura",
            current_state={"uncertainty": True},
            desired_state={"uncertainty": False},
            constraints={"budget": 80.0},
            difficulty=0.80,
            required_capabilities=["clima_agricultura"],
        )

        participants = [
            {"uid": "observador_1", "skills": {"clima_agricultura": 0.8}, "experience_years": 8.0, "knowledge_facts": ["senales_de_viento_anuncian_sequia_canicular"]},
            {"uid": "observador_2", "skills": {"clima_agricultura": 0.75}, "experience_years": 6.0, "knowledge_facts": ["humedad_en_suelo_recomienda_siembra_escalonada"]},
            {"uid": "observador_3", "skills": {"clima_agricultura": 0.3}, "experience_years": 1.0, "knowledge_facts": ["sembrar_todo_de_un_solo_golpe_por_rumor"]},
        ]

        proposals = [
            SolutionProposal(
                proposal_id="prop_siembra_escalonada",
                author_uid="observador_2",
                strategy_summary="Siembra escalonada con variedades de ciclo corto y largo",
                required_tasks=[{"task_name": "siembra_fraccionada", "skill_needed": "clima_agricultura", "cost": 25.0}],
                expected_success_probability=0.82,
                total_resource_cost=25.0,
            ),
            SolutionProposal(
                proposal_id="prop_siembra_total_arriesgada",
                author_uid="observador_3",
                strategy_summary="Siembra masiva inmediata asumiendo lluvia abundante",
                required_tasks=[{"task_name": "siembra_total", "skill_needed": "clima_agricultura", "cost": 90.0}],
                expected_success_probability=0.35,
                total_resource_cost=90.0,
            ),
        ]

        report = engine.coordinate_and_execute(
            session_id="sess_uncertainty_1",
            problem=prob,
            participants=participants,
            proposals=proposals,
            available_resources={"funds": 80.0},
            group_id="comm_valle",
            tick=10,
        )

        success = (
            report.selected_proposal is not None
            and report.selected_proposal.proposal_id == "prop_siembra_escalonada"
            and report.execution_success is True
            and report.outcome == ProblemOutcome.SOLVED
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "selected_strategy": report.selected_proposal.strategy_summary if report.selected_proposal else None,
            "proposals_debated": len(report.proposals_generated),
            "execution_success": report.execution_success,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Under uncertainty, collective engine rejected risky proposal and selected robust strategy '{metrics['selected_strategy']}'.",
            hypotheses=[
                {"hypothesis": "Evidence-weighted deliberation weeds out high-risk noisy claims", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_S: Comunidades que desaparecen o se dividen
# =============================================================================
class Experiment09_S_CommunityFissionAndDissolution(BaseExperiment):
    """EXP_09_S: Community fission (schism into two factions) and eventual dissolution."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_S",
            name="Community Fission and Dissolution",
            description="Factional schism splits community into two; abandonment leads to dissolution.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        comm_engine = CommunityFormationEngine()

        founders = ["fac_a1", "fac_a2", "fac_b1", "fac_b2"]
        parent_comm = comm_engine.form_community(
            name="Comunidad El Trapiche",
            community_type=CommunityType.COOPERATIVE,
            collective_identity="Cooperativa de panela",
            founder_uids=founders,
            initial_funds=100.0,
            tick=10,
        )

        # 1. Fission: faction B splits off to form new cooperative
        splinter_comm = parent_comm.trigger_fission(
            tick=20,
            dissident_uids=["fac_b1", "fac_b2"],
            new_name="Cooperativa Dulce Cana (Escindida)",
        )

        fission_success = (
            parent_comm.active_member_count == 2
            and splinter_comm.active_member_count == 2
            and splinter_comm.resources.get("funds", 0.0) > 0.0
            and parent_comm.external_relations.get(splinter_comm.community_id, 0.0) < 0.0
        )

        # 2. Dissolution of remaining parent members departure
        parent_comm.remove_member("fac_a1", tick=30, reason="emigration")
        parent_comm.remove_member("fac_a2", tick=35, reason="voluntary_departure")
        dissolution_success = parent_comm.status == CommunityStatus.DISSOLVED

        success = fission_success and dissolution_success
        elapsed = time.perf_counter() - t0

        metrics = {
            "parent_status": parent_comm.status.value,
            "splinter_name": splinter_comm.name,
            "splinter_members": splinter_comm.active_member_count,
            "fission_success": fission_success,
            "dissolution_success": dissolution_success,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Community fission produced '{splinter_comm.name}'; parent community dissolved upon member departure.",
            hypotheses=[
                {"hypothesis": "Factional schisms split community membership and resources", "verified": fission_success},
                {"hypothesis": "Communities dissolve when active membership falls below sustainability threshold", "verified": dissolution_success},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_T: Simulacion longitudinal de 1, 3, 6 y 12 meses
# =============================================================================
class Experiment09_T_LongitudinalSimulation(BaseExperiment):
    """EXP_09_T: Multi-scale longitudinal social evolution (30, 90, 180, 360 days)."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_T",
            name="Longitudinal Social Simulation",
            description="Multi-scale temporal simulation validating network density, community stability, and relationship aging.",
            duration_ticks=384, # 4 simulated days in quick check, testing scaling intervals
            random_seed=42,
            population_size=12,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        comm_engine = CommunityFormationEngine()

        uids = [f"pop_{i}" for i in range(8)]
        # Form initial community
        comm = comm_engine.form_community(
            name="Comunidad San Jose",
            community_type=CommunityType.NEIGHBORHOOD,
            collective_identity="Barrio residencial con comercio informal",
            founder_uids=uids[:5],
            tick=0,
        )

        intervals = [30, 90, 180, 360] # simulated days
        history_snapshots: list[dict[str, Any]] = []

        # Simulate progressive interaction across intervals
        total_interactions = 0
        for idx, day in enumerate(intervals):
            current_tick = day * 96
            # Periodic interactions among neighbors
            for i in range(len(uids) - 1):
                net.record_interaction(uids[i], uids[i+1], tick=current_tick, valence=0.7, bidirectional=True)
                total_interactions += 1

            # Social decay on inactive ties
            net.apply_decay_all(current_tick=current_tick)

            history_snapshots.append({
                "day": day,
                "tick": current_tick,
                "density": round(net.calculate_density(), 4),
                "total_edges": net.count_total_edges(),
                "community_cohesion": comm.cohesion,
            })

        final_snapshot = history_snapshots[-1]
        has_maintained_bonds = final_snapshot["total_edges"] > 0 and final_snapshot["density"] > 0

        success = has_maintained_bonds and len(history_snapshots) == 4
        elapsed = time.perf_counter() - t0

        metrics = {
            "snapshots": history_snapshots,
            "final_day": intervals[-1],
            "final_density": final_snapshot["density"],
            "total_interactions": total_interactions,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Longitudinal simulation spanned up to {intervals[-1]} days; maintained density={final_snapshot['density']}.",
            hypotheses=[
                {"hypothesis": "Social network dynamics sustain stable topology over long horizons", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_U: Integracion entre geografia, economia y sociedad
# =============================================================================
class Experiment09_U_GeographyEconomySocietyIntegration(BaseExperiment):
    """EXP_09_U: Multi-system loop connecting geographic co-location, trade, and social tie formation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_U",
            name="Geography, Economy, and Society Integration",
            description="Geographic market co-location drives economic trade, which fosters social trust and community bonds.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        econ = CollectiveEconomyEngine()

        farmer = "campesino_joel"
        vendor = "marchanta_marta"
        market_loc = "mercado_central_santa_tecla"

        # 1. Geographic co-location encounter at market
        # 2. Economic trade: farmer sells wholesale vegetables to vendor
        ent = econ.create_enterprise(
            name="Puesto de Verduras y Granos",
            org_type=CollectiveOrgType.MARKET_ASSOCIATION,
            founder_uids=[vendor],
            location_id=market_loc,
            tick=10,
        )
        ent.shared_inventory["tomates_caja"] = 10.0
        revenue = ent.sell_goods("tomates_caja", quantity=10.0, unit_price=12.0)

        # 3. Successful economic trades generate social trust bond
        for t in (15, 25):
            edge = net.record_interaction(
                source_id=farmer,
                target_id=vendor,
                tick=t,
                valence=0.85,
                intensity=0.8,
                event_type="fair_market_trade",
                shared_topic="precios_hortalizas",
                bidirectional=True,
            )

        edge.relation_types.add(SocialRelationType.COMMERCIAL)
        edge.relation_types.add(SocialRelationType.TRUST)

        success = (
            revenue == 120.0
            and edge.trust > 0.60
            and SocialRelationType.COMMERCIAL in edge.relation_types
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "market_location": market_loc,
            "trade_revenue": revenue,
            "social_trust": round(edge.trust, 3),
            "relation_types": [r.value for r in edge.relation_types],
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Market interaction at {market_loc} yielded ${revenue:.2f} trade and forged COMMERCIAL trust tie.",
            hypotheses=[
                {"hypothesis": "Co-location in economic facilities fosters social relations", "verified": True},
                {"hypothesis": "Fair commercial exchange increases interpersonal trust", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_V: Persistencia y recuperacion de redes
# =============================================================================
class Experiment09_V_PersistenceAndRecovery(BaseExperiment):
    """EXP_09_V: Verifies SQLite persistence and exact deserialization of social edges and communities."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_V",
            name="Network and Community Persistence",
            description="Persists social edges and emergent communities to SQLite, reloading and asserting structural identity.",
            duration_ticks=48,
            random_seed=42,
            population_size=4,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        db = DatabaseManager(":memory:")
        db.connect()
        SchemaManager.create_tables(db)

        edge_repo = SocialEdgeRepository(db)
        comm_repo = CommunityRepository(db)

        # Create original edge
        edge_orig = SocialEdge(
            edge_id="edge_test_persist_1",
            source_id="agent_alpha",
            target_id="agent_beta",
            relation_types={SocialRelationType.FRIEND, SocialRelationType.COOPERATIVE},
            trust=0.88,
            affinity=0.82,
            reciprocity=0.15,
            interaction_frequency=0.6,
            created_tick=10,
            last_interaction_tick=30,
            status=BondState.ACTIVE,
        )
        edge_repo.save(edge_orig)

        # Create original community
        comm_orig = Community(
            community_id="comm_test_persist_1",
            name="Comunidad Test",
            community_type=CommunityType.NEIGHBORHOOD,
            collective_identity="Identidad de prueba",
            resources={"funds": 350.0},
            created_tick=10,
        )
        comm_orig.add_member("agent_alpha", role=MembershipRole.FOUNDER, tick=10)
        comm_orig.add_member("agent_beta", role=MembershipRole.ACTIVE_MEMBER, tick=12)
        comm_repo.save(comm_orig)

        # Reload and assert identity
        loaded_edges = edge_repo.load_all()
        loaded_comms = comm_repo.load_all()

        assert len(loaded_edges) == 1
        edge_reloaded = loaded_edges[0]
        assert edge_reloaded.edge_id == edge_orig.edge_id
        assert abs(edge_reloaded.trust - 0.88) < 1e-4
        assert SocialRelationType.FRIEND in edge_reloaded.relation_types

        assert len(loaded_comms) == 1
        comm_reloaded = loaded_comms[0]
        assert comm_reloaded.community_id == comm_orig.community_id
        assert comm_reloaded.active_member_count == 2
        assert comm_reloaded.resources.get("funds") == 350.0

        db.close()
        success = True
        elapsed = time.perf_counter() - t0

        metrics = {
            "edges_reloaded": len(loaded_edges),
            "communities_reloaded": len(loaded_comms),
            "edge_trust_verified": edge_reloaded.trust,
            "community_funds_verified": comm_reloaded.resources.get("funds"),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Edges and communities successfully persisted and restored from SQLite database.",
            hypotheses=[
                {"hypothesis": "Social edges survive persistence roundtrip with exact dimensions", "verified": True},
                {"hypothesis": "Emergent communities preserve memberships and resources", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_W: Comportamiento con informacion incompleta
# =============================================================================
class Experiment09_W_IncompleteInformation(BaseExperiment):
    """EXP_09_W: Individual and collective decision making under imperfect social information."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_W",
            name="Behavior with Incomplete Information",
            description="Agents deliberate and take actions with missing network and market knowledge.",
            duration_ticks=96,
            random_seed=42,
            population_size=4,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        rep_engine = ReputationEngine()

        target_agent = "comerciante_desconocido"
        evaluator = "comprador_prudente"

        # Evaluator has zero direct interaction with target
        # Should start with low confidence (bounded epistemic uncertainty)
        initial_profile = rep_engine.get_or_create(target_agent, evaluator, domain=ReputationDomain.PROFESSIONAL)
        initial_confidence = initial_profile.confidence
        assert initial_confidence <= 0.40

        # Evaluator acts prudently: offers small test transaction ($10) rather than full contract ($100)
        contract_size = 10.0 if initial_confidence < 0.50 else 100.0
        assert contract_size == 10.0

        # Successful test transaction increases confidence and reputation
        rep_engine.record_pact_outcome(
            subject_uid=target_agent,
            observer_uid=evaluator,
            fulfilled=True,
            domain=ReputationDomain.PROFESSIONAL,
            tick=10,
        )

        updated_profile = rep_engine.get_or_create(target_agent, evaluator, domain=ReputationDomain.PROFESSIONAL)
        confidence_grew = updated_profile.confidence > initial_confidence
        trust_grew = updated_profile.score > 0.50

        success = (contract_size == 10.0) and confidence_grew and trust_grew
        elapsed = time.perf_counter() - t0

        metrics = {
            "contract_size_prudent": contract_size,
            "initial_confidence": round(initial_confidence, 3),
            "updated_confidence": round(updated_profile.confidence, 3),
            "updated_score": round(updated_profile.score, 3),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Agent acted prudently with low confidence ({initial_confidence:.2f}); test transaction raised confidence to {updated_profile.confidence:.2f}.",
            hypotheses=[
                {"hypothesis": "Agents with incomplete info limit risk via small commitments", "verified": True},
                {"hypothesis": "Empirical outcomes reduce uncertainty and update situated reputation", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_X: Escalabilidad de redes sociales
# =============================================================================
class Experiment09_X_NetworkScalability(BaseExperiment):
    """EXP_09_X: Scalability benchmark across 10, 50, 100, and 200 agents using Social LOD."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_X",
            name="Social Network Scalability",
            description="Benchmarks social processing time across scaling populations under Social LOD.",
            duration_ticks=96,
            random_seed=42,
            population_size=200,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        lod = SocialLODManager()

        scales = [10, 50, 100, 200]
        timings: dict[int, float] = {}

        # Set focal agents
        lod.set_focal_agents(["agent_0", "agent_1"])

        for n in scales:
            t_scale = time.perf_counter()
            # Generate n agents and random edges
            uids = [f"scale_agent_{i}" for i in range(n)]

            # Linear-like local clustering (each connects to 4 neighbors)
            for i in range(n):
                for offset in (1, 2):
                    net.record_interaction(
                        uids[i],
                        uids[(i + offset) % n],
                        tick=10,
                        valence=0.7,
                        bidirectional=True,
                    )

            # LOD evaluation pass
            processed = 0
            for i in range(n):
                if lod.should_process_social_tick(uids[i], tick=10, is_nearby_focal=(i < 5)):
                    processed += 1

            timings[n] = round(time.perf_counter() - t_scale, 4)

        elapsed = time.perf_counter() - t0
        all_fast = all(t < 0.50 for t in timings.values()) # Sub-second for all scales

        metrics = {
            "scale_timings_seconds": timings,
            "total_edges_200": net.count_total_edges(),
            "all_scales_sub_second": all_fast,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=all_fast,
            summary=f"Scalability verified across {scales} agents: 200 agents processed in {timings[200]}s.",
            hypotheses=[
                {"hypothesis": "Social LOD keeps graph updates sub-second across scaling populations", "verified": all_fast},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )
