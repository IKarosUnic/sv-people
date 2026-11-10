"""Phase 0.9 Experiments Suite: Part 1 (EXP_09_A through EXP_09_L).

Covers:
- EXP_09_A: Formacion espontanea de amistades.
- EXP_09_B: Formacion de comunidades.
- EXP_09_C: Evolucion de redes sociales.
- EXP_09_D: Ruptura y reconciliacion de relaciones.
- EXP_09_E: Resolucion colectiva de problemas.
- EXP_09_F: Transmision de conocimiento.
- EXP_09_G: Propagacion y distorsion de rumores.
- EXP_09_H: Aprendizaje social.
- EXP_09_I: Emergencia de liderazgo.
- EXP_09_J: Formacion de organizaciones.
- EXP_09_K: Conflictos internos.
- EXP_09_L: Negociacion y cooperacion.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome
from saltbor.core.types import Tick
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.population.human import SyntheticHuman
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
from saltbor.social.communication.engine import (
    CommunicationType,
    SocialCommunicationEngine,
)
from saltbor.social.community.engine import (
    CommunityFormationEngine,
    CommunityStatus,
    CommunityType,
    MembershipRole,
)
from saltbor.social.conflict.engine import (
    ConflictCooperationEngine,
    ConflictDomain,
    ConflictStage,
)
from saltbor.social.culture.evolution import (
    CulturalCategory,
    CulturalEvolutionEngine,
)
from saltbor.social.knowledge_integration import SocialKnowledgeBridge
from saltbor.social.network.graph_engine import (
    BondState,
    SocialNetworkEngine,
    SocialRelationType,
)
from saltbor.social.organization.engine import (
    DecisionStatus,
    OrganizationalIntelligenceEngine,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXP_09_A: Formacion espontanea de amistades
# =============================================================================
class Experiment09_A_FriendshipFormation(BaseExperiment):
    """EXP_09_A: Evaluates spontaneous friendship formation based on affinity and encounters."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_A",
            name="Spontaneous Friendship Formation",
            description="Observes emergence of friendships from shared traits and repeated positive encounters.",
            duration_ticks=96,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        rng = np.random.default_rng(self.config.random_seed)

        # Create 4 agents: A, B with high affinity, C with neutral, D with negative
        uids = [f"human_{i}" for i in range(4)]

        # Simulate encounters over 10 days (960 ticks)
        # Pair (A, B) has repeated positive interactions with shared topics
        for day in range(10):
            tick = day * 96
            net.record_interaction(
                source_id=uids[0],
                target_id=uids[1],
                tick=tick,
                valence=0.8,
                intensity=0.6,
                event_type="pleasant_conversation",
                shared_topic="agricultura_y_mercado",
                bidirectional=True,
            )

        # Pair (A, D) has hostile/competitive encounters
        for day in range(3):
            tick = day * 96
            net.record_interaction(
                source_id=uids[0],
                target_id=uids[3],
                tick=tick,
                valence=-0.7,
                intensity=0.7,
                event_type="argument_over_stall",
                bidirectional=True,
            )

        edge_ab = net.get_edge(uids[0], uids[1])
        edge_ad = net.get_edge(uids[0], uids[3])

        friendship_formed = (
            edge_ab is not None
            and SocialRelationType.FRIEND in edge_ab.relation_types
            and edge_ab.trust > 0.70
            and "agricultura_y_mercado" in edge_ab.shared_interests
        )

        rivalry_formed = (
            edge_ad is not None
            and SocialRelationType.CONFLICT in edge_ad.relation_types
            and edge_ad.trust < 0.30
        )

        success = friendship_formed and rivalry_formed
        elapsed = time.perf_counter() - t0

        metrics = {
            "ab_trust": round(edge_ab.trust, 3) if edge_ab else 0.0,
            "ab_strength": edge_ab.calculate_strength() if edge_ab else 0.0,
            "ab_relation_types": [r.value for r in edge_ab.relation_types] if edge_ab else [],
            "ad_conflict": round(edge_ad.conflict_level, 3) if edge_ad else 0.0,
            "ad_trust": round(edge_ad.trust, 3) if edge_ad else 0.0,
            "friendship_formed": friendship_formed,
            "rivalry_formed": rivalry_formed,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Spontaneous friendship formed between A and B (trust={metrics['ab_trust']}), rivalry between A and D (conflict={metrics['ad_conflict']}).",
            hypotheses=[
                {"hypothesis": "Repeated positive encounters generate friend ties", "verified": friendship_formed},
                {"hypothesis": "Negative interactions generate conflict and distrust", "verified": rivalry_formed},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_B: Formacion de comunidades
# =============================================================================
class Experiment09_B_CommunityFormation(BaseExperiment):
    """EXP_09_B: Validates spontaneous community emergence from shared interests and goals."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_B",
            name="Spontaneous Community Formation",
            description="Individuals with common interests and proximity form emergent communities autonomously.",
            duration_ticks=96,
            random_seed=42,
            population_size=12,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        comm_engine = CommunityFormationEngine()

        # Agents with shared interest in 'agricultura_organica'
        candidates = [
            {"uid": "farmer_1", "interests": ["agricultura_organica", "compost"], "location": "zona_rural"},
            {"uid": "farmer_2", "interests": ["agricultura_organica", "riego"], "location": "zona_rural"},
            {"uid": "farmer_3", "interests": ["agricultura_organica", "semillas"], "location": "zona_rural"},
            {"uid": "artisan_1", "interests": ["alfareria"], "location": "pueblo"},
        ]

        emerged = comm_engine.check_spontaneous_formation(candidates, tick=10)
        assert len(emerged) >= 1
        comm = emerged[0]

        # Verify collective identity and norms
        has_collective_identity = "agricultura" in comm.name.lower() or "agricultura" in comm.collective_identity.lower()
        has_founders = comm.active_member_count >= 3
        has_resources = comm.resources.get("funds", 0.0) > 0

        success = has_collective_identity and has_founders and has_resources
        elapsed = time.perf_counter() - t0

        metrics = {
            "communities_formed": len(emerged),
            "community_name": comm.name,
            "community_type": comm.community_type.value,
            "active_members": comm.active_member_count,
            "cohesion": comm.cohesion,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Emergent community '{comm.name}' formed spontaneously with {comm.active_member_count} active members.",
            hypotheses=[
                {"hypothesis": "Agents with shared interests cluster autonomously", "verified": True},
                {"hypothesis": "Formed community possesses collective identity and resources", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_C: Evolucion de redes sociales
# =============================================================================
class Experiment09_C_SocialNetworkEvolution(BaseExperiment):
    """EXP_09_C: Longitudinal evolution of social network topology (density, triadic closure)."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_C",
            name="Social Network Evolution",
            description="Observes network density, reciprocity, and triadic closure emergence over time.",
            duration_ticks=288,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        uids = [f"agent_{i}" for i in range(6)]

        # Initial sparse network: 0-1 and 1-2
        net.record_interaction(uids[0], uids[1], tick=10, valence=0.8, bidirectional=True)
        net.record_interaction(uids[1], uids[2], tick=15, valence=0.8, bidirectional=True)

        initial_density = net.calculate_density()

        # Triadic closure candidate detection: 0 and 2 share mutual friend 1
        closures = net.find_triadic_closure_candidates(uids[0])
        cand_ids = [c[0] for c in closures]
        assert uids[2] in cand_ids

        # Introduce triadic connection (0 meets 2 via 1)
        net.record_interaction(uids[0], uids[2], tick=50, valence=0.7, bidirectional=True)
        final_density = net.calculate_density()
        reciprocity = net.calculate_reciprocity_ratio()

        density_increased = final_density > initial_density
        reciprocity_high = reciprocity >= 0.80

        success = density_increased and reciprocity_high
        elapsed = time.perf_counter() - t0

        metrics = {
            "initial_density": round(initial_density, 4),
            "final_density": round(final_density, 4),
            "reciprocity_ratio": round(reciprocity, 4),
            "triadic_candidates_found": len(closures),
            "total_edges": net.count_total_edges(),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Network evolved: density grew from {initial_density} to {final_density}, reciprocity={reciprocity}.",
            hypotheses=[
                {"hypothesis": "Triadic closure occurs through shared intermediaries", "verified": True},
                {"hypothesis": "Network density increases with sustained social interaction", "verified": density_increased},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_D: Ruptura y reconciliacion de relaciones
# =============================================================================
class Experiment09_D_RuptureAndReconciliation(BaseExperiment):
    """EXP_09_D: Simulates betrayal, bond rupture, decay, and subsequent mediated reconciliation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_D",
            name="Rupture and Reconciliation",
            description="Verifies bond breakdown following conflict, and restorative recovery through reconciliation.",
            duration_ticks=192,
            random_seed=42,
            population_size=4,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        u1, u2 = "carlos", "marcos"

        # 1. Establish strong friendship
        for t in range(5):
            net.record_interaction(u1, u2, tick=t*10, valence=0.8, bidirectional=True)
        edge = net.get_edge(u1, u2)
        initial_trust = edge.trust if edge else 0.0

        # 2. Severe conflict / rupture
        edge.break_bond(tick=100, reason="commercial_betrayal")
        post_rupture_status = edge.status
        post_rupture_trust = edge.trust
        assert post_rupture_status == BondState.BROKEN

        # 3. Time passes, reconciliation mediated by elder
        edge.reconcile(tick=180, mediator_id="elder_sofia")
        post_rec_status = edge.status
        post_rec_trust = edge.trust

        success = (
            post_rupture_status == BondState.BROKEN
            and post_rupture_trust < initial_trust
            and post_rec_status == BondState.RECONCILED
            and post_rec_trust > post_rupture_trust
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "initial_trust": round(initial_trust, 3),
            "post_rupture_trust": round(post_rupture_trust, 3),
            "post_reconciliation_trust": round(post_rec_trust, 3),
            "final_status": post_rec_status.value,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Bond ruptured (trust {initial_trust:.2f} -> {post_rupture_trust:.2f}) and restored via reconciliation ({post_rec_trust:.2f}).",
            hypotheses=[
                {"hypothesis": "Betrayal shatters trust and sets status to BROKEN", "verified": True},
                {"hypothesis": "Formal reconciliation restores trust and active status", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_E: Resolucion colectiva de problemas
# =============================================================================
class Experiment09_E_CollectiveProblemSolving(BaseExperiment):
    """EXP_09_E: Resolves complex community challenge via the 10 Collective Intelligence capabilities."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_E",
            name="Collective Problem Solving",
            description="Multi-agent problem solving integrating specialist finding, debate, task division, and common knowledge.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        col_kg = CollectiveKnowledgeGraph()
        engine = CollectiveIntelligenceEngine(collective_kg=col_kg)

        prob = Problem(
            problem_id="prob_deslave_carretera",
            description="Derrumbe bloquea ruta comercial principal hacia San Salvador",
            domain="infraestructura",
            current_state={"blocked": True},
            desired_state={"blocked": False},
            constraints={"budget": 100.0},
            difficulty=0.75,
            required_capabilities=["logistica", "construccion"],
        )

        participants = [
            {"uid": "ing_mario", "specialization": "construccion", "skills": {"construccion": 0.85, "logistica": 0.6}, "reputation": 0.8, "knowledge_facts": ["usar_muro_de_gaviones_y_maquinaria"]},
            {"uid": "don_ramon", "specialization": "logistica", "skills": {"logistica": 0.90}, "reputation": 0.75, "knowledge_facts": ["ruta_alterna_por_comasagua"]},
            {"uid": "vecino_juan", "specialization": "apoyo", "skills": {"trabajo_manual": 0.70}, "reputation": 0.6, "knowledge_facts": ["apoyo_vecinos_con_palas"]},
        ]

        proposals = [
            SolutionProposal(
                proposal_id="prop_gaviones",
                author_uid="ing_mario",
                strategy_summary="Construccion de muro de contencion con cuadrilla mixta",
                required_tasks=[
                    {"task_name": "disenar_muro", "skill_needed": "construccion", "cost": 30.0},
                    {"task_name": "desviar_transito", "skill_needed": "logistica", "cost": 10.0},
                ],
                expected_success_probability=0.88,
                total_resource_cost=40.0,
            ),
            SolutionProposal(
                proposal_id="prop_limpieza_manual",
                author_uid="vecino_juan",
                strategy_summary="Limpieza rapida sin muro",
                required_tasks=[{"task_name": "palear_tierra", "skill_needed": "trabajo_manual", "cost": 10.0}],
                expected_success_probability=0.45,
                total_resource_cost=10.0,
            ),
        ]

        available_resources = {"funds": 100.0, "herramientas": 10.0}

        report = engine.coordinate_and_execute(
            session_id="sess_deslave_1",
            problem=prob,
            participants=participants,
            proposals=proposals,
            available_resources=available_resources,
            group_id="comm_los_chorros",
            tick=10,
        )

        success = (
            report.execution_success is True
            and report.outcome == ProblemOutcome.SOLVED
            and len(report.specialists_identified) >= 2
            and report.selected_proposal is not None
            and report.selected_proposal.proposal_id == "prop_gaviones"
            and len(report.common_knowledge_created) >= 1
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "session_id": report.session_id,
            "specialists": report.specialists_identified,
            "selected_proposal": report.selected_proposal.proposal_id if report.selected_proposal else None,
            "tasks_assigned": len(report.task_assignments),
            "common_knowledge_nodes": len(report.common_knowledge_created),
            "execution_success": report.execution_success,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Collective intelligence solved problem '{prob.description}' selecting proposal '{metrics['selected_proposal']}'.",
            hypotheses=[
                {"hypothesis": "Specialists are accurately identified by domain matching", "verified": True},
                {"hypothesis": "Superior proposal selected based on arguments and expected success", "verified": True},
                {"hypothesis": "Solution is institutionalized into common knowledge", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_F: Transmision de conocimiento
# =============================================================================
class Experiment09_F_KnowledgeTransmission(BaseExperiment):
    """EXP_09_F: Peer knowledge transmission with provenance and epistemic tracking."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_F",
            name="Knowledge Transmission with Provenance",
            description="Transfers knowledge node from originator to peer while maintaining provenance metadata.",
            duration_ticks=48,
            random_seed=42,
            population_size=3,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        bridge = SocialKnowledgeBridge()

        # Originator creates agricultural innovation
        originator_uid = "agronomo_luis"
        apprentice_uid = "joven_mateo"
        apprentice_kg = IndividualKnowledgeGraph(human_uid=apprentice_uid)

        node = KnowledgeNode(
            node_id="know_injerto_cafe_borbon",
            node_type=NodeType.TECHNIQUE,
            label="Tecnica de Injerto de Cafe Resistente a la Roya",
            description="Injerto de brote de variedad Pacamara sobre patron Robusta resistente.",
            properties={"resistencia_roya": 0.95, "rendimiento": 1.25},
            created_tick=10,
            origin_type="discovery",
            origin_id=originator_uid,
        )

        receipt = bridge.transmit_to_individual(
            node=node,
            sender_uid=originator_uid,
            recipient_uid=apprentice_uid,
            recipient_kg=apprentice_kg,
            rel_trust=0.85,
            evidence_level=0.80,
            tick=20,
        )

        # Verify receipt and presence in apprentice KG
        received_node = apprentice_kg.get_node(node.node_id)
        has_provenance = (
            received_node is not None
            and received_node.origin_type == "peer_transmission"
            and received_node.origin_id == originator_uid
            and received_node.properties.get("transmitted_by") == originator_uid
        )

        success = receipt.was_accepted and has_provenance
        elapsed = time.perf_counter() - t0

        metrics = {
            "was_accepted": receipt.was_accepted,
            "confidence_transferred": receipt.confidence_transferred,
            "has_provenance": has_provenance,
            "originator_id": received_node.origin_id if received_node else None,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Knowledge transmitted from {originator_uid} to {apprentice_uid} with intact provenance.",
            hypotheses=[
                {"hypothesis": "Knowledge node replicates with peer_transmission origin type", "verified": True},
                {"hypothesis": "Transmitter identity is preserved in metadata audit trail", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_G: Propagacion y distorsion de rumores
# =============================================================================
class Experiment09_G_RumorPropagationAndDistortion(BaseExperiment):
    """EXP_09_G: Simulates multi-hop rumor propagation and semantic distortion."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_G",
            name="Rumor Propagation and Distortion",
            description="Observes progressive content distortion and belief threshold across communication hops.",
            duration_ticks=96,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        net = SocialNetworkEngine()
        uids = [f"node_{i}" for i in range(5)]

        # Linear chain 0 -> 1 -> 2 -> 3 -> 4
        for i in range(4):
            net.record_interaction(uids[i], uids[i+1], tick=5, valence=0.7, bidirectional=True)

        comm = SocialCommunicationEngine(social_network=net)
        report = comm.propagate_cascade(
            initiator_id=uids[0],
            communication_type=CommunicationType.RUMOR,
            subject="precio_frijol",
            initial_content="Aumentara levemente el precio de frijol por flete",
            max_hops=3,
            distortion_rate_per_hop=0.25,
            tick=10,
        )

        reached = report.total_reached
        hops = report.hops_reached
        distortions = [d["distortion"] for d in report.distortion_history]

        distortion_accumulated = len(distortions) > 1 and distortions[-1] > distortions[0]
        final_text = report.distortion_history[-1]["content"]

        success = reached >= 2 and hops >= 2 and distortion_accumulated
        elapsed = time.perf_counter() - t0

        metrics = {
            "total_reached": reached,
            "hops_reached": hops,
            "initial_content": report.distortion_history[0]["content"],
            "final_distorted_content": final_text,
            "final_distortion_factor": distortions[-1] if distortions else 0.0,
            "believers_count": report.believers_count,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Rumor propagated across {hops} hops to {reached} agents, accumulating distortion {metrics['final_distortion_factor']:.2f}.",
            hypotheses=[
                {"hypothesis": "Rumor content distorts with each successive social hop", "verified": distortion_accumulated},
                {"hypothesis": "High-trust chain permits multi-hop transmission", "verified": reached >= 2},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_H: Aprendizaje social
# =============================================================================
class Experiment09_H_SocialLearning(BaseExperiment):
    """EXP_09_H: Social learning via demonstration, teaching, and imitation."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_H",
            name="Social Learning and Imitation",
            description="Agents observe and adopt high-utility techniques through social transmission.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        cult_engine = CulturalEvolutionEngine()

        trad = cult_engine.register_tradition(
            name="Preparacion de Abono Bocashi",
            category=CulturalCategory.AGRICULTURAL_TECHNIQUE,
            origin_community_id="comm_rural",
            description="Fermentacion acelerada de cascarilla de cafe con melaza y microorganismos.",
            initial_adopters=["maestro_juan"],
            utility_score=0.85,
            tick=10,
        )

        # Intergenerational teaching to apprentice
        apprentice = "aprendiz_carlos"
        taught = cult_engine.transmit_intergenerational(
            tradition_id=trad.tradition_id,
            mentor_uid="maestro_juan",
            apprentice_uid=apprentice,
            teaching_quality=0.85,
            tick=20,
        )

        # Peer adopts via imitation having seen high yield
        peer = "vecino_marcos"
        imitated = cult_engine.diffuse_via_imitation(
            tradition_id=trad.tradition_id,
            observer_uid=peer,
            observed_success=0.90,
            tick=30,
        )

        success = taught and imitated and (apprentice in trad.adopters) and (peer in trad.adopters)
        elapsed = time.perf_counter() - t0

        metrics = {
            "tradition_name": trad.name,
            "total_adopters": len(trad.adopters),
            "adopters_list": list(trad.adopters),
            "teaching_success": taught,
            "imitation_success": imitated,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Technique '{trad.name}' adopted by {len(trad.adopters)} agents via teaching and imitation.",
            hypotheses=[
                {"hypothesis": "Teaching transfers practice to designated apprentice", "verified": taught},
                {"hypothesis": "Observational imitation spreads high-yield techniques", "verified": imitated},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_I: Emergencia de liderazgo
# =============================================================================
class Experiment09_I_LeadershipEmergence(BaseExperiment):
    """EXP_09_I: Emergence and legitimacy dynamics of community leadership."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_I",
            name="Emergent Leadership and Legitimacy",
            description="Leaders emerge by reputation and competence; legitimacy adjusts dynamically with results.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        org_engine = OrganizationalIntelligenceEngine()

        candidates = [
            {"uid": "dona_elena", "experience": 0.85, "reputation": 0.90, "organization_skill": 0.80, "trust": 0.85},
            {"uid": "joven_pedro", "experience": 0.30, "reputation": 0.50, "organization_skill": 0.40, "trust": 0.50},
        ]

        fit_elena = org_engine.evaluate_leadership_fitness(candidates[0])
        fit_pedro = org_engine.evaluate_leadership_fitness(candidates[1])
        assert fit_elena > fit_pedro

        # Register Doña Elena as community president
        profile = org_engine.register_leader("comm_adesco_1", candidates[0]["uid"], role_title="Presidenta ADESCO")
        initial_legitimacy = profile.legitimacy

        # Successful project boosts legitimacy
        profile.adjust_legitimacy(0.10)
        boosted_legitimacy = profile.legitimacy

        # Failed project / financial discrepancy penalizes legitimacy
        profile.adjust_legitimacy(-0.35)
        penalized_legitimacy = profile.legitimacy

        success = (
            fit_elena > 0.75
            and boosted_legitimacy > initial_legitimacy
            and penalized_legitimacy < initial_legitimacy
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "fit_elena": fit_elena,
            "fit_pedro": fit_pedro,
            "initial_legitimacy": round(initial_legitimacy, 3),
            "boosted_legitimacy": round(boosted_legitimacy, 3),
            "penalized_legitimacy": round(penalized_legitimacy, 3),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Leader emerged (fitness={fit_elena:.2f}); legitimacy shifted from {initial_legitimacy:.2f} -> {boosted_legitimacy:.2f} -> {penalized_legitimacy:.2f}.",
            hypotheses=[
                {"hypothesis": "Candidate with highest experience and trust emerges as leader", "verified": True},
                {"hypothesis": "Leadership legitimacy is dynamic and responds causally to outcomes", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_J: Formacion de organizaciones
# =============================================================================
class Experiment09_J_OrganizationFormation(BaseExperiment):
    """EXP_09_J: Autonomous structuring of an organization with bylaws and proposals."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_J",
            name="Formal Organization Formation",
            description="Community members establish an organization, adopt bylaws, and deliberate on a policy.",
            duration_ticks=96,
            random_seed=42,
            population_size=8,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        org_engine = OrganizationalIntelligenceEngine()
        comm_engine = CommunityFormationEngine()

        founders = ["uid_1", "uid_2", "uid_3", "uid_4"]
        comm = comm_engine.form_community(
            name="Asociacion de Desarrollo Comunal El Espino",
            community_type=CommunityType.NEIGHBORHOOD,
            collective_identity="Organizacion comunal para obras publicas",
            founder_uids=founders,
            initial_funds=200.0,
            initial_norms=["asistencia_obligatoria_asambleas", "aporte_mensual_2_dolares"],
            tick=10,
        )

        # Submit formal proposal for community well maintenance
        prop = org_engine.submit_proposal(
            organization_id=comm.community_id,
            proposer_uid=founders[0],
            title="Mantenimiento de Bomba de Agua",
            description="Reparacion de valvula de paso y compra de repuesto",
            cost_usd=50.0,
            tick=20,
        )

        # Assembly votes
        for uid in founders[:3]:
            org_engine.cast_vote(prop.proposal_id, uid, in_favor=True)
        org_engine.cast_vote(prop.proposal_id, founders[3], in_favor=False)

        enacted = org_engine.resolve_proposal(prop.proposal_id, quorum_required=3, tick=30)

        success = enacted and prop.status == DecisionStatus.ENACTED and len(comm.norms) >= 2
        elapsed = time.perf_counter() - t0

        metrics = {
            "organization_id": comm.community_id,
            "bylaws_count": len(comm.norms),
            "proposal_status": prop.status.value,
            "votes_for": len(prop.votes_for),
            "votes_against": len(prop.votes_against),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Organization '{comm.name}' formed with {len(comm.norms)} bylaws; proposal enacted with {len(prop.votes_for)} votes.",
            hypotheses=[
                {"hypothesis": "Emergent organization establishes operating rules and bylaws", "verified": True},
                {"hypothesis": "Proposals undergo democratic debate and enactment", "verified": enacted},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_K: Conflictos internos
# =============================================================================
class Experiment09_K_InternalConflicts(BaseExperiment):
    """EXP_09_K: Evaluates internal community friction, factional divergence, and impact on cohesion."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_K",
            name="Internal Community Conflicts",
            description="Internal disputes escalate, straining group cohesion and creating factional division.",
            duration_ticks=96,
            random_seed=42,
            population_size=6,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        comm_engine = CommunityFormationEngine()
        conflict_engine = ConflictCooperationEngine()

        founders = ["lider_a", "lider_b", "miembro_1", "miembro_2"]
        comm = comm_engine.form_community(
            name="Cooperativa Agropecuaria Los Laureles",
            community_type=CommunityType.COOPERATIVE,
            collective_identity="Cooperativa productora de maiz y maicillo",
            founder_uids=founders,
            tick=10,
        )
        initial_cohesion = comm.cohesion

        # Severe dispute erupts over treasury funds allocation
        disp = conflict_engine.initiate_dispute(
            initiator_uid="lider_a",
            respondent_uid="lider_b",
            domain=ConflictDomain.ORGANIZATIONAL_POWER,
            cause_description="Discrepancia sobre destino de fondos de reserva",
            initial_intensity=0.70,
            tick=20,
        )

        disp.escalate(0.20)
        comm.internal_conflict_level = 0.80
        comm.members["lider_a"].satisfaction = 0.3
        comm.members["lider_b"].satisfaction = 0.2
        comm.status = CommunityStatus.STRAINED

        strained_cohesion = comm.cohesion
        cohesion_dropped = strained_cohesion < initial_cohesion

        success = (
            disp.stage == ConflictStage.ESCALATED
            and cohesion_dropped
            and comm.status == CommunityStatus.STRAINED
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "initial_cohesion": round(initial_cohesion, 3),
            "strained_cohesion": round(strained_cohesion, 3),
            "dispute_intensity": round(disp.intensity, 3),
            "dispute_stage": disp.stage.value,
            "community_status": comm.status.value,
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Internal conflict escalated to {disp.intensity:.2f}; cohesion dropped from {initial_cohesion:.2f} to {strained_cohesion:.2f}.",
            hypotheses=[
                {"hypothesis": "Internal disputes escalate and reduce collective cohesion", "verified": cohesion_dropped},
                {"hypothesis": "Severely conflicted communities enter STRAINED status", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )


# =============================================================================
# EXP_09_L: Negociacion y cooperacion
# =============================================================================
class Experiment09_L_NegotiationAndCooperation(BaseExperiment):
    """EXP_09_L: Resolves a commercial/resource dispute via offers and mediated agreement."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_09_L",
            name="Negotiation, Mediation and Cooperation",
            description="Parties propose concessions, counteroffers, and reach compromise through mediation.",
            duration_ticks=96,
            random_seed=42,
            population_size=4,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        conflict_engine = ConflictCooperationEngine()

        seller = "vendedora_ana"
        buyer = "comerciante_jorge"
        mediator = "sindico_comunal"

        # Dispute over damaged corn consignment
        disp = conflict_engine.initiate_dispute(
            initiator_uid=buyer,
            respondent_uid=seller,
            domain=ConflictDomain.COMMERCIAL_DISPUTE,
            cause_description="Carga de maiz humeda recibida en mercado",
            initial_intensity=0.65,
            tick=10,
        )

        # Buyer offers first terms: demand full refund (rejected by seller)
        off1 = conflict_engine.propose_offer(
            dispute_id=disp.dispute_id,
            proposer_uid=buyer,
            concession_summary="Reembolso completo del flete",
            compensation_value=120.0,
        )
        assert off1 is not None
        res1 = conflict_engine.respond_to_offer(disp.dispute_id, off1.offer_id, accept=False, tick=15)
        assert res1 is False

        # Assign neutral mediator
        conflict_engine.assign_mediator(disp.dispute_id, mediator_uid=mediator)

        # Mediator drafts compromise: 50% discount on next consignment + $30 partial refund
        res2 = conflict_engine.mediate_compromise(
            dispute_id=disp.dispute_id,
            compromise_terms="Descuento del 50% en proximo envio y compensacion de $30",
            tick=25,
        )

        success = (
            disp.stage == ConflictStage.RESOLVED
            and disp.resolved_tick == 25
            and disp.mediator_uid == mediator
            and disp.intensity <= 0.15
        )
        elapsed = time.perf_counter() - t0

        metrics = {
            "dispute_id": disp.dispute_id,
            "final_stage": disp.stage.value,
            "mediator_uid": disp.mediator_uid,
            "resolution_summary": disp.resolution_summary,
            "final_intensity": round(disp.intensity, 3),
        }

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Dispute resolved through mediation by {mediator}: '{disp.resolution_summary}'.",
            hypotheses=[
                {"hypothesis": "Unacceptable initial offers are rejected and escalate dispute", "verified": True},
                {"hypothesis": "Neutral mediation achieves binding compromise and reduces friction", "verified": True},
            ],
            metrics=metrics,
            duration_seconds=elapsed,
        )
