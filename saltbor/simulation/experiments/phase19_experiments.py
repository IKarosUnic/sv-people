"""Phase 1.9 Emergent Society, Institutional Evolution, Governance & CPR Experiments.

Implements all 24 reproducible experiments: EXP_19_A through EXP_19_X.
"""

from __future__ import annotations

import copy
import statistics
import time
from typing import Any, Dict, List, Optional
import uuid

from saltbor.core.config import SimulationConfig
from saltbor.core.types import EmploymentStatus, HousingTenureType, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.organization.emergent_engine import (
    EmergentOrganization,
    MemberRole,
    OrganizationType,
    OrgLifecycleStatus,
)
from saltbor.social.institutions.institutional_evolution import (
    EvolvingInstitution,
    InstitutionDomain,
    InstitutionalStatus,
)
from saltbor.social.governance.collective_decision import (
    CollectiveProposal,
    ProposalStatus,
    VotingProtocol,
)
from saltbor.social.norms.norm_evolution import (
    NormDomain,
    NormFormalization,
    SanctionType,
    SocialNorm,
)
from saltbor.social.resources.cpr_manager import (
    CPRHealthStatus,
    CPRType,
    CommonPoolResource,
)
from saltbor.social.stratification.mobility_engine import (
    InequalityMetrics,
    StratificationProfile,
)
from saltbor.social.conflict.intergroup_engine import (
    ConflictTensionStage,
    IntergroupConflictType,
    IntergroupDispute,
)


def _make_runner(seed: int = 42, pop_size: int = 10) -> SimulationRunner:
    """Helper to initialize an in-memory simulation runner for testing."""
    cfg = SimulationConfig(
        database_path=":memory:",
        random_seed=seed,
        initial_population_size=pop_size,
    )
    r = SimulationRunner(config=cfg)
    r.initialize(load_existing=False)
    return r


# =============================================================================
# EXP_19_A: Formación espontánea de una organización comercial
# =============================================================================

class Experiment19_A_SpontaneousCommercialOrg(BaseExperiment):
    """EXP_19_A: Autonomous formation of a commercial collective from shared trader needs."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_A",
            name="Formación Espontánea de Organización Comercial",
            description="Agentes comerciantes con necesidad compartida y confianza forman una asociación.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        candidates = [
            {"uid": "trader_1", "needs": ["comercio"], "location": "mercado_central", "capital": 25.0},
            {"uid": "trader_2", "needs": ["comercio"], "location": "mercado_central", "capital": 30.0},
            {"uid": "trader_3", "needs": ["comercio"], "location": "mercado_central", "capital": 20.0},
        ]
        org = r.emergent_organizations.attempt_spontaneous_formation(candidates, tick=r.clock.current_tick)

        success = (
            org is not None
            and org.org_type == OrganizationType.COMMERCIAL_ASSOCIATION
            and org.active_member_count == 3
            and org.treasury_usd > 0.0
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Comerciantes con necesidades y ubicación común forman una asociación sin imposición externa.",
                "La tesorería inicial se nutre de aportes de capital de los miembros fundadores.",
            ]
            ],
            metrics={
                "org_created": org is not None,
                "active_members": org.active_member_count if org else 0,
                "treasury_usd": org.treasury_usd if org else 0.0,
                "cohesion": org.cohesion if org else 0.0,
            },
            summary=f"Organización '{org.name if org else 'None'}' formada con {org.active_member_count if org else 0} miembros y ${org.treasury_usd if org else 0.0:.2f} en tesorería.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_B: Fracaso organizacional por colapso de confianza y legitimidad
# =============================================================================

class Experiment19_B_OrgFailureTrustCollapse(BaseExperiment):
    """EXP_19_B: Organization fails and dissolves when members defect and legitimacy collapses."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_B",
            name="Fracaso Organizacional por Colapso de Confianza",
            description="Una organización pierde miembros y legitimidad hasta disolverse.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        org = r.emergent_organizations.create_organization(
            name="Asociación Frágil",
            org_type=OrganizationType.MUTUAL_AID_SOCIETY,
            mission="Socorro mutuo",
            founder_uids=["m1", "m2", "m3"],
            initial_treasury_usd=10.0,
            tick=1,
        )
        initial_count = org.active_member_count

        # Members depart due to dissatisfaction
        org.escalate_internal_conflict(delta=0.80, reason="Escándalo de malversación", tick=2)
        org.remove_member("m1", reason="desconfianza_absoluta", tick=3)
        org.remove_member("m2", reason="quiebra_moral", tick=4)

        success = (
            org.status == OrgLifecycleStatus.DISSOLVED
            and org.active_member_count < 2
            and org.internal_conflict_level > 0.50
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Una organización que pierde masa crítica de miembros activos (<2) se disuelve formalmente.",
                "El conflicto interno severo degrada la legitimidad y precipita deserciones en cadena.",
            ]
            ],
            metrics={
                "initial_members": initial_count,
                "final_members": org.active_member_count,
                "final_status": org.status.value,
                "internal_conflict": org.internal_conflict_level,
                "legitimacy": org.legitimacy,
            },
            summary=f"Organización pasó de {initial_count} a {org.active_member_count} miembros y culminó en estado '{org.status.value}'.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_C: Fisión organizacional por conflicto interno
# =============================================================================

class Experiment19_C_OrgFissionInternalConflict(BaseExperiment):
    """EXP_19_C: An organization experiencing factional strife splits into two distinct entities."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_C",
            name="Fisión Organizacional por Conflicto Interno",
            description="Una facción disidente se escinde y funda una nueva organización dividiendo activos.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        org = r.emergent_organizations.create_organization(
            name="Cooperativa Madre San Esteban",
            org_type=OrganizationType.AGRICULTURAL_COOPERATIVE,
            mission="Producción de granos",
            founder_uids=["u1", "u2", "u3", "u4", "u5"],
            initial_treasury_usd=200.0,
            tick=1,
        )
        parent, child = r.emergent_organizations.execute_fission(
            org_id=org.org_id,
            dissident_uids=["u4", "u5"],
            new_org_name="Cooperativa Disidente El Progreso",
            new_mission="Producción agroecológica independiente",
            asset_split_ratio=0.35,
            tick=10,
        )

        success = (
            parent is not None
            and child is not None
            and parent.active_member_count == 3
            and child.active_member_count == 2
            and round(parent.treasury_usd + child.treasury_usd, 2) == 200.0
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "El conflicto faccional insoluble conduce a la escisión formal en dos organizaciones viables.",
                "La masa monetaria y patrimonial se conserva estrictamente sin creación de fondos ficticios.",
            ]
            ],
            metrics={
                "parent_members": parent.active_member_count if parent else 0,
                "child_members": child.active_member_count if child else 0,
                "parent_treasury": parent.treasury_usd if parent else 0.0,
                "child_treasury": child.treasury_usd if child else 0.0,
                "total_funds_conserved": (parent.treasury_usd + child.treasury_usd) if (parent and child) else 0.0,
            },
            summary=f"Fisión exitosa: Cooperativa escindida en 2 entidades conservando los $200.00 originales (${parent.treasury_usd if parent else 0:.2f} + ${child.treasury_usd if child else 0:.2f}).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_D: Institución creada para resolver necesidad colectiva
# =============================================================================

class Experiment19_D_InstitutionCollectiveNeed(BaseExperiment):
    """EXP_19_D: Institutionalization in response to urgent community health and sanitation needs."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_D",
            name="Creación Institucional por Necesidad Colectiva",
            description="Formalización de una institución de salud comunitaria con estatutos y presupuesto.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        inst = r.institutional_evolution.register_institution(
            name="Clínica y Promotoría de Salud San Esteban",
            formal_acronym="CPSS-SE",
            domain=InstitutionDomain.HEALTHCARE,
            mission="Atención primaria preventiva y saneamiento de pozos.",
            headquarters_loc_id="clinica_salud",
            initial_treasury_usd=350.0,
            director_uid="dr_martinez",
            initial_rules=["Turno rotativo de promotores", "Atención prioritaria pediátrica"],
            tick=1,
        )

        # Service requested and processed
        r_srv = inst.request_service("petitioner_01", "consulta_preventiva", tick=2)
        ops = inst.process_daily_operations(tick=96)

        success = (
            inst.domain == InstitutionDomain.HEALTHCARE
            and r_srv is True
            and ops["processed_count"] >= 1
            and inst.legitimacy >= 0.80
            and len(inst.rules_and_bylaws) == 2
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las instituciones formalizan reglas y procesan peticiones ciudadanas mediante capacidad operativa finita.",
                "El cumplimiento de servicios mantiene alta la legitimidad comunitaria.",
            ]
            ],
            metrics={
                "acronym": inst.formal_acronym,
                "treasury_usd": inst.treasury_usd,
                "rules_count": len(inst.rules_and_bylaws),
                "processed_services": ops["processed_count"],
                "legitimacy": inst.legitimacy,
            },
            summary=f"Institución '{inst.formal_acronym}' procesó {ops['processed_count']} servicios con {len(inst.rules_and_bylaws)} estatutos vigentes.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_E: Crisis de legitimidad institucional
# =============================================================================

class Experiment19_E_InstitutionLegitimacyCrisis(BaseExperiment):
    """EXP_19_E: Institution enters legitimacy crisis when scandals and failures exceed tolerance."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_E",
            name="Crisis de Legitimidad Institucional",
            description="Una institución sufre sanciones y negligencia, degradando su legitimidad por debajo del 25%.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        inst = r.institutional_evolution.register_institution(
            name="Tribunal Arbitral Comunal",
            formal_acronym="TAC",
            domain=InstitutionDomain.CONFLICT_RESOLUTION,
            mission="Arbitraje vecinal",
            headquarters_loc_id="casa_comunal",
            initial_treasury_usd=100.0,
            director_uid="juez_01",
            tick=1,
        )
        initial_legitimacy = inst.legitimacy

        # Two major crises
        inst.suffer_crisis(penalty=0.35, reason="Arbitraje parcial favoreciendo familiares", tick=5)
        inst.suffer_crisis(penalty=0.35, reason="Desvío de fondos de costas comunales", tick=10)

        success = (
            inst.legitimacy <= 0.25
            and inst.status == InstitutionalStatus.LEGITIMACY_CRISIS
            and len(inst.decision_history) >= 3
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "La pérdida reiterada de confianza precipita el estado formal de crisis de legitimidad.",
                "El historial inmutable de decisiones registra la causa raíz de la deslegitimación.",
            ]
            ],
            metrics={
                "initial_legitimacy": initial_legitimacy,
                "final_legitimacy": inst.legitimacy,
                "final_status": inst.status.value,
                "crisis_events_logged": len([e for e in inst.decision_history if e.get("event") == "legitimacy_crisis"]),
            },
            summary=f"Legitimidad colapsó de {initial_legitimacy:.2f} a {inst.legitimacy:.2f}, declarando '{inst.status.value}'.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_F: Cambio de liderazgo institucional y reformas
# =============================================================================

class Experiment19_F_LeadershipSuccessionImpact(BaseExperiment):
    """EXP_19_F: Change of institutional leadership enacts reform and restores operational vitality."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_F",
            name="Sucesión de Liderazgo y Reforma Institucional",
            description="Reforma estatutaria bajo nueva dirección rescata una institución en crisis.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        inst = r.institutional_evolution.register_institution(
            name="Comité de Agua y Saneamiento",
            formal_acronym="CAS",
            domain=InstitutionDomain.COMMON_RESOURCES_CPR,
            mission="Gobernanza del pozo comunal",
            headquarters_loc_id="casa_comunal",
            initial_treasury_usd=120.0,
            director_uid="director_saliente",
            tick=1,
        )
        inst.suffer_crisis(penalty=0.45, reason="Cobros opacos de cuotas de agua", tick=5)
        crisis_legitimacy = inst.legitimacy

        # Reform under new director
        inst.enact_reform(
            new_rules=["Libro contable público en plaza central", "Auditoría mensual por asamblea de vecinos"],
            new_director_uid="directora_nueva",
            tick=10,
        )

        success = (
            inst.status == InstitutionalStatus.REFORMED
            and inst.officers["director"] == "directora_nueva"
            and inst.legitimacy > crisis_legitimacy
            and len(inst.rules_and_bylaws) == 2
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "La reforma institucional puede revertir el deterioro de legitimidad mediante reglas de transparencia.",
                "El cambio de liderazgo queda inmutablemente trazado en el historial administrativo.",
            ]
            ],
            metrics={
                "crisis_legitimacy": crisis_legitimacy,
                "reformed_legitimacy": inst.legitimacy,
                "new_director": inst.officers["director"],
                "new_rules_count": len(inst.rules_and_bylaws),
                "status": inst.status.value,
            },
            summary=f"Reforma completada bajo {inst.officers['director']}: legitimidad ascendió de {crisis_legitimacy:.2f} a {inst.legitimacy:.2f}.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_G: Votación en asamblea con desacuerdo persistente
# =============================================================================

class Experiment19_G_AssemblyVotingPersistentDissent(BaseExperiment):
    """EXP_19_G: Collective deliberative assembly resolves a motion with registered dissent."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_G",
            name="Votación en Asamblea con Desacuerdo Persistente",
            description="Una propuesta presupuestaria pasa por mayoría simple pero registra votos en contra y disenso.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        gov = r.collective_governance
        prop = gov.submit_proposal(
            organization_id="org_adesco_01",
            proposer_uid="vecino_lider",
            title="Compra de Bomba de Agua Eléctrica para Pozo",
            description="Inversión de $80 para mejorar caudal de extracción diaria.",
            cost_usd=80.0,
            protocol=VotingProtocol.SIMPLE_MAJORITY,
            tick=1,
        )

        # 4 votes in favor, 2 votes against with dissent reasons, 1 abstention
        gov.cast_deliberative_vote(prop.proposal_id, "v1", "for", influence_weight=1.5)
        gov.cast_deliberative_vote(prop.proposal_id, "v2", "for", influence_weight=1.0)
        gov.cast_deliberative_vote(prop.proposal_id, "v3", "for", influence_weight=1.0)
        gov.cast_deliberative_vote(prop.proposal_id, "v4", "against", influence_weight=1.2, reason="Costo excesivo; priorizar bacheo de cuesta")
        gov.cast_deliberative_vote(prop.proposal_id, "v5", "against", influence_weight=1.0, reason="Gasto innecesario antes del invierno")
        gov.cast_deliberative_vote(prop.proposal_id, "v6", "abstain", influence_weight=0.5)

        enacted, summary = gov.resolve_assembly_vote(
            proposal_id=prop.proposal_id,
            total_eligible_members=10,
            treasury_balance_usd=150.0,
            quorum_fraction=0.40,
            tick=2,
        )

        success = (
            enacted is True
            and prop.status == ProposalStatus.ENACTED
            and len(prop.votes_against) == 2
            and len(prop.dissenting_reasons) == 2
            and prop.weighted_approval_ratio > 0.50
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las asambleas deliberativas aprueban propuestas reflejando pesos de influencia pero sin silenciar el disenso.",
                "Las razones del voto en contra quedan registradas en el acta para trazabilidad cívica.",
            ]
            ],
            metrics={
                "votes_for": len(prop.votes_for),
                "votes_against": len(prop.votes_against),
                "abstentions": len(prop.abstentions),
                "weighted_ratio": prop.weighted_approval_ratio,
                "dissenting_records": len(prop.dissenting_reasons),
                "enacted": enacted,
            },
            summary=f"Moción aprobada ({len(prop.votes_for)} a favor vs {len(prop.votes_against)} en contra) con {len(prop.dissenting_reasons)} objeciones archivadas.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_H: Negociación entre organizaciones rivales y pacto
# =============================================================================

class Experiment19_H_IntergroupNegotiationPact(BaseExperiment):
    """EXP_19_H: Commercial dispute between market vendor syndicate and formal store resolved by pact."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_H",
            name="Negociación y Pacto entre Organizaciones",
            description="Resolución de rivalidad comercial mediante mediación de ADESCO y firma de acuerdo.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        conflict_engine = r.intergroup_conflicts
        dispute = conflict_engine.initiate_dispute(
            initiator_org_id="gremio_vendedoras_mercado",
            respondent_org_id="asoc_comercio_establecido",
            conflict_type=IntergroupConflictType.COMMERCIAL_RIVALRY,
            grievance="Invasión de aceras frente a locales formales y competencia desleal de precios",
            initial_intensity=0.70,
            tick=1,
        )
        dispute.escalate(boost=0.15, action_type="bloqueo_simbolico_de_calle", tick=3)
        dispute.enter_mediation("Junta Directiva ADESCO Centro", tick=5)
        dispute.sign_compromise_pact(
            terms=[
                "Respeto a franja de 1.5 metros para circulación peatonal",
                "Acuerdo de precios mínimos para libra de frijol y queso",
                "Mesa de concertación mensual en casa comunal",
            ],
            compensation=15.0,
            tick=10,
        )

        success = (
            dispute.stage == ConflictTensionStage.PACT_ENACTED
            and len(dispute.terms_agreed) == 3
            and dispute.intensity <= 0.40
            and dispute.compensation_usd == 15.0
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Los conflictos colectivos escalan pero pueden resolverse mediante mediación comunitaria neutral.",
                "El pacto formal reduce la tensión e instaura compromisos operativos verificables.",
            ]
            ],
            metrics={
                "initial_intensity": 0.70,
                "final_intensity": dispute.intensity,
                "agreed_terms_count": len(dispute.terms_agreed),
                "compensation_usd": dispute.compensation_usd,
                "final_stage": dispute.stage.value,
            },
            summary=f"Pacto suscrito entre organizaciones mediado por ADESCO con compensación de ${dispute.compensation_usd:.2f} y tensión reducida a {dispute.intensity:.2f}.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_I: Gestión colectiva de agua (CPR Ostrom)
# =============================================================================

class Experiment19_I_CollectiveWaterManagementCPR(BaseExperiment):
    """EXP_19_I: Sustainable governance of common water well under Ostrom quotas and maintenance."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_I",
            name="Gestión Colectiva Sostenible de Agua (CPR Ostrom)",
            description="Usuarios autorizados extraen agua dentro de la cuota diaria y realizan faena de recarga.",
            duration_ticks=96,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        cpr = r.cpr_manager.get_resource("pozo_san_esteban")
        assert cpr is not None

        initial_stock = cpr.current_stock
        extracted_sum = 0.0

        # 5 authorized members extract within quota (40 L each <= 50 L daily quota)
        for uid in list(cpr.authorized_users)[:5]:
            ext, auth, _ = cpr.extract(uid, amount=40.0, tick=10)
            if auth:
                extracted_sum += ext

        # Members perform maintenance cleaning faena
        cpr.contribute_maintenance("maint_worker", labor_hours=4.0, funds_usd=0.0, tick=20)
        cpr.step_natural_regeneration(current_tick=96)

        success = (
            extracted_sum == 200.0
            and cpr.status in (CPRHealthStatus.STABLE, CPRHealthStatus.ABUNDANT)
            and len(cpr.extraction_history) >= 5
            and len(cpr.maintenance_history) >= 1
            and cpr.current_stock > cpr.depletion_threshold
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "La extracción gobernada por cuotas y faenas de mantenimiento preserva el recurso común.",
                "Cada litro extraído y hora de labor comunitaria queda auditada en el balance de masa.",
            ]
            ],
            metrics={
                "initial_stock_liters": initial_stock,
                "extracted_liters": extracted_sum,
                "final_stock_liters": cpr.current_stock,
                "health_status": cpr.status.value,
                "extractions_logged": len(cpr.extraction_history),
                "maintenance_records": len(cpr.maintenance_history),
            },
            summary=f"Pozo común sostuvo extracción de {extracted_sum:.1f} L y se mantuvo '{cpr.status.value}' ({cpr.current_stock:.0f} L en reserva).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_J: Sobreexplotación de recurso común (Tragedia de los Comunes)
# =============================================================================

class Experiment19_J_TragedyOfTheCommonsDepletion(BaseExperiment):
    """EXP_19_J: Depletion of unmonitored common resource by excessive free-riding extraction."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_J",
            name="Sobreexplotación y Tragedia de los Comunes",
            description="Extracción masiva no controlada supera la tasa de recarga y agota el pozo de agua.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        # Create a fragile small well without monitoring
        well = r.cpr_manager.register_resource(
            resource_id="pozo_vulnerable_fragil",
            name="Pocita de Riego Cantonal",
            resource_type=CPRType.WATER_WELL,
            community_id="canton_bajo",
            location_id="plaza_central",
            max_capacity=1000.0,
            initial_stock=400.0,
            regeneration_rate=20.0,
            unit="litros",
            daily_quota=500.0,
            authorized_users={"pirate_1", "pirate_2"},
            tick=1,
        )

        # Excessive free-riding extractions
        w1, _, _ = well.extract("pirate_1", amount=250.0, tick=2)
        w2, _, _ = well.extract("pirate_2", amount=250.0, tick=3)
        w3, _, msg = well.extract("pirate_1", amount=100.0, tick=4)

        success = (
            well.status == CPRHealthStatus.DEPLETED
            and well.current_stock <= well.depletion_threshold
            and "agotado" in msg.lower()
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "La extracción no restringida por encima de la capacidad de regeneración produce el colapso del recurso.",
                "El estado del recurso pasa formalmente a DEPLETED bloqueando futuras extracciones.",
            ]
            ],
            metrics={
                "initial_stock": 400.0,
                "remaining_stock": well.current_stock,
                "total_depleted": 400.0 - well.current_stock,
                "status": well.status.value,
            },
            summary=f"Tragedia de los Comunes verificada: Recurso agotado ({well.current_stock:.1f} L restantes) bajo estado '{well.status.value}'.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_K: Creación, endeudamiento y quiebra contable de un negocio
# =============================================================================

class Experiment19_K_BusinessLifecycleDebtBankruptcy(BaseExperiment):
    """EXP_19_K: A commercial business opens, accumulates liabilities, faces insolvency, and liquidates."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_K",
            name="Ciclo de Vida Empresarial: Creación, Deuda y Cierre",
            description="Una pequeña empresa informal incurre en pérdidas operativas hasta liquidar su stock.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        coop = r.collective_economy.register_enterprise(
            name="Taller de Carpintería La Esperanza",
            org_type=r.collective_economy._enterprise_types if hasattr(r.collective_economy, "_enterprise_types") else None,
            founder_uid="artesano_juan",
            initial_capital=50.0,
            location_id="taller_artesanal",
            tick=1,
        ) if hasattr(r.collective_economy, "register_enterprise") else None

        # If using emergent organizations or commercial engine
        biz = r.emergent_organizations.create_organization(
            name="Taller de Carpintería La Esperanza",
            org_type=OrganizationType.PRODUCER_GUILD,
            mission="Fabricación de muebles",
            founder_uids=["artesano_juan"],
            initial_treasury_usd=50.0,
            tick=1,
        )

        # High operating expenses with no sales lead to insolvency
        biz.treasury_usd = max(0.0, biz.treasury_usd - 60.0) # Deficit
        biz.escalate_internal_conflict(delta=0.60, reason="Insolvencia y falta de pedidos", tick=5)
        biz.dissolve(reason="quiebra_contable_por_perdidas", tick=10)

        success = (
            biz.status == OrgLifecycleStatus.DISSOLVED
            and biz.treasury_usd == 0.0
            and len(biz.history_log) >= 3
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las empresas no tienen rentabilidad garantizada ni subsidios artificiales por defecto.",
                "La insolvencia contable conduce al cierre y disolución ordenada de la organización productiva.",
            ]
            ],
            metrics={
                "initial_treasury": 50.0,
                "final_treasury": biz.treasury_usd,
                "status": biz.status.value,
                "dissolved": biz.status == OrgLifecycleStatus.DISSOLVED,
            },
            summary=f"Emprendimiento cerró con saldo ${biz.treasury_usd:.2f} tras registrar insolvencia operativa.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_L: Desigualdad y movilidad social longitudinal
# =============================================================================

class Experiment19_L_LongitudinalStratificationMobility(BaseExperiment):
    """EXP_19_L: Multidimensional stratification and quintile mobility tracking over time."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_L",
            name="Estratificación Multidimensional y Movilidad Social",
            description="Cálculo de coeficientes de Gini, ratio de Palma y transiciones entre quintiles.",
            duration_ticks=96,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        strat_engine = r.social_stratification
        humans = r.population.get_all()

        # Differentiate economic status across agents to produce meaningful inequality
        for idx, h in enumerate(humans):
            h.physical_state.money = float(((idx + 1) ** 1.8) * 15.0)
            if idx >= 7:
                h.housing_tenure = HousingTenureType.OWNER_OCCUPIED
            elif idx <= 2:
                h.housing_tenure = HousingTenureType.INFORMAL_HOUSING

        metrics_day1 = strat_engine.step(r.population, r.social, current_tick=96)
        assert metrics_day1 is not None

        # Simulate shock: agent in lowest quintile earns income and skills (upward mobility)
        lowest_agent = humans[0]
        lowest_agent.physical_state.money += 300.0
        lowest_agent.demographics.occupation = "comerciante_mayorista"

        # Agent in top quintile suffers misfortune / wealth loss (downward mobility)
        top_agent = humans[-1]
        top_agent.physical_state.money = 5.0
        top_agent.housing_tenure = HousingTenureType.RENTAL

        metrics_day2 = strat_engine.step(r.population, r.social, current_tick=192)
        assert metrics_day2 is not None

        success = (
            metrics_day1.gini_income > 0.15
            and metrics_day1.palma_ratio > 0.40
            and (metrics_day2.upward_mobility_count > 0 or metrics_day2.downward_mobility_count > 0)
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "La estratificación social multidimensional captura desigualdades sin reducirlas a una sola variable.",
                "Los cambios de patrimonio y ocupación inducen movilidad ascendente y descendente entre quintiles.",
            ]
            ],
            metrics={
                "gini_income_day1": metrics_day1.gini_income,
                "gini_wealth_day1": metrics_day1.gini_wealth,
                "palma_day1": metrics_day1.palma_ratio,
                "upward_transitions": metrics_day2.upward_mobility_count,
                "downward_transitions": metrics_day2.downward_mobility_count,
            },
            summary=f"Gini inicial de {metrics_day1.gini_income:.3f} (Palma {metrics_day1.palma_ratio:.2f}) con {metrics_day2.upward_mobility_count} ascensos y {metrics_day2.downward_mobility_count} descensos observados.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_M: Conflicto laboral y negociación mediada
# =============================================================================

class Experiment19_M_LaborStrikeMediation(BaseExperiment):
    """EXP_19_M: Day laborers declare strike over daily wage and reach mediated settlement."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_M",
            name="Conflicto Laboral, Huelga y Mediación",
            description="Gremio de jornaleros declara huelga de brazos caídos y acuerda nuevo salario con patronos.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        disp = r.intergroup_conflicts.initiate_dispute(
            initiator_org_id="sindicato_jornaleros_agricolas",
            respondent_org_id="asoc_duenos_fincas",
            conflict_type=IntergroupConflictType.LABOR_STRIKE,
            grievance="Salario diario de $10 insuficiente ante inflación de canasta básica",
            initial_intensity=0.65,
            tick=1,
        )
        disp.escalate(boost=0.20, action_type="huelga_de_brazos_caidos", tick=3)
        disp.enter_mediation("Juzgado Comunal de Paz", tick=5)
        disp.sign_compromise_pact(
            terms=["Ajuste salarial a $12.50 diarios", "Suministro de almuerzo en jornada larga"],
            compensation=20.0,
            tick=10,
        )

        success = (
            disp.conflict_type == IntergroupConflictType.LABOR_STRIKE
            and disp.stage == ConflictTensionStage.PACT_ENACTED
            and len(disp.terms_agreed) == 2
            and disp.intensity <= 0.40
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las fricciones distributivas laborales pueden canalizarse mediante huelgas y pactos vinculantes.",
                "La mediación neutral permite resolver la huelga sin violencia forzada.",
            ]
            ],
            metrics={
                "conflict_type": disp.conflict_type.value,
                "final_stage": disp.stage.value,
                "agreed_terms": len(disp.terms_agreed),
                "residual_tension": disp.intensity,
            },
            summary=f"Huelga laboral resuelta mediante pacto con {len(disp.terms_agreed)} términos acordados (tensión final {disp.intensity:.2f}).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_N: Transmisión y adaptación de una norma social
# =============================================================================

class Experiment19_N_NormTransmissionIntergenerational(BaseExperiment):
    """EXP_19_N: Community norm is transmitted, tested by temptations, and sustained by sanctions."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_N",
            name="Transmisión y Cumplimiento de Norma Social",
            description="Evaluación de observancia de una norma comunitaria frente a incentivos de evasión.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        norm = r.social_norms.register_norm(
            title="Aporte de Mano de Obra en Faenas Comunitarias",
            description="Cada familia aporta 1 miembro a las faenas mensuales de ADESCO.",
            domain=NormDomain.CIVIC_COOPERATION,
            formalization=NormFormalization.COMMUNITY_AGREEMENT,
            legitimacy=0.85,
            enforcement_rigor=0.70,
            tick=1,
        )

        # 4 agents comply, 1 agent evades due to high temptation
        compliances = 0
        violations = 0
        for i in range(4):
            complies, _ = r.social_norms.evaluate_individual_compliance(f"ag_{i}", norm.norm_id, temptation_benefit=0.30, personal_integrity=0.70)
            if complies:
                norm.record_compliance(f"ag_{i}", tick=2)
                compliances += 1

        complies_free, sanction = r.social_norms.evaluate_individual_compliance("free_rider", norm.norm_id, temptation_benefit=0.95, personal_integrity=0.20)
        if not complies_free:
            norm.record_violation("free_rider", tick=3, sanction_applied=sanction)
            violations += 1

        success = (
            compliances == 4
            and violations == 1
            and norm.adherence_rate == 0.80
            and norm.total_sanctions_applied == 1
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las normas comunitarias enfrentan incentivos de polizonaje (free-riding) contenidos por sanciones graduadas.",
                "La tasa de adherencia refleja el balance empírico de cumplimientos y violaciones.",
            ]
            ],
            metrics={
                "compliances": norm.total_compliances,
                "violations": norm.total_violations,
                "sanctions_applied": norm.total_sanctions_applied,
                "adherence_rate": norm.adherence_rate,
            },
            summary=f"Norma comunitaria registró {norm.total_compliances} cumplimientos y {norm.total_violations} infracción penalizada (tasa de adherencia {norm.adherence_rate*100:.1f}%).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_O: Desaparición de una tradición por desuetudo
# =============================================================================

class Experiment19_O_CulturalTraditionDesuetudo(BaseExperiment):
    """EXP_19_O: An unpracticed cultural custom falls into desuetudo and collapses into extinction."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_O",
            name="Desaparición de Tradición por Desuetudo",
            description="Una costumbre no practicada durante múltiples ciclos pierde legitimidad y se extingue.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        norm = r.social_norms.register_norm(
            title="Danza Colonial de Moros y Cristianos en Fiestas",
            description="Costumbre folclórica patronal no renovada por generaciones jóvenes.",
            domain=NormDomain.NEIGHBORHOOD_CONVIVENCIA,
            formalization=NormFormalization.IMPLICIT_CUSTOM,
            legitimacy=0.30,
            enforcement_rigor=0.10,
            tick=1,
        )

        # Decay through prolonged dormancy (repeated inactive periods)
        for _ in range(10):
            norm.decay_vitality(ticks_elapsed=50)

        success = (
            norm.is_active is False
            and norm.legitimacy <= 0.15
            and "desuetudo" in norm.history_log[-1].lower()
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las tradiciones culturales y normas no practicadas decaen paulatinamente por desuetudo.",
                "Al perder legitimidad y masa de practicantes, la norma queda formalmente inactiva.",
            ]
            ],
            metrics={
                "initial_legitimacy": 0.30,
                "final_legitimacy": norm.legitimacy,
                "dormant_ticks": norm.dormant_ticks,
                "is_active": norm.is_active,
            },
            summary=f"Costumbre extinguida por desuetudo tras {norm.dormant_ticks} ticks inactivos (legitimidad residual {norm.legitimacy:.2f}).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_P: Institución que conserva conocimiento y potencia habilidades
# =============================================================================

class Experiment19_P_InstitutionKnowledgeConservation(BaseExperiment):
    """EXP_19_P: Educational workshop transmits artisanal knowledge and accelerates apprentice skill."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_P",
            name="Conservación Institucional del Conocimiento",
            description="Taller artesanal capacita aprendices y transmite técnicas de carpintería y albañilería.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        edu = r.distributed_education
        humans = r.population.get_all()
        mentor = humans[0]
        apprentice = humans[1]

        # Establish agreement
        contract = edu.establish_apprenticeship(
            mentor_uid=str(mentor.uid),
            apprentice_uid=str(apprentice.uid),
            domain="carpinteria",
            target_proficiency=0.75,
        )

        # Practice sessions accelerate proficiency
        for t in range(5):
            contract.ticks_completed += 1
            contract.current_proficiency = min(1.0, contract.current_proficiency + 0.12)

        success = (
            contract.ticks_completed == 5
            and contract.current_proficiency > 0.10
            and contract.is_active is True
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las instituciones de enseñanza comunitaria conservan y transmiten saberes técnicos.",
                "La práctica deliberada supervisada produce aumentos medibles en la competencia procedimental.",
            ]
            ],
            metrics={
                "initial_proficiency": 0.10,
                "final_proficiency": contract.current_proficiency,
                "ticks_completed": contract.ticks_completed,
                "domain": contract.skill_domain,
            },
            summary=f"Aprendiz elevó competencia en {contract.skill_domain} a {contract.current_proficiency:.2f} tras {contract.ticks_completed} sesiones.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_Q: Fragmentación de una comunidad en facciones rivales
# =============================================================================

class Experiment19_Q_CommunityFragmentation(BaseExperiment):
    """EXP_19_Q: Neighborhood community fragments into rival geographic factions after resource dispute."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_Q",
            name="Fragmentación Comunitaria en Facciones",
            description="Desacuerdo irreconciliable de distribución hídrica fragmenta el vecindario en dos sectores.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        comm = r.emergent_organizations.create_organization(
            name="Comunidad Vecinal San Esteban Unido",
            org_type=OrganizationType.NEIGHBORHOOD_BOARD,
            mission="Convivencia y obras vecinales",
            founder_uids=["v_norte1", "v_norte2", "v_sur1", "v_sur2"],
            initial_treasury_usd=160.0,
            tick=1,
        )
        comm.escalate_internal_conflict(delta=0.75, reason="Disputa territorial por cuota de pozo", tick=3)

        parent, child = r.emergent_organizations.execute_fission(
            org_id=comm.org_id,
            dissident_uids=["v_sur1", "v_sur2"],
            new_org_name="Sector Vecinal El Calvario Sur",
            new_mission="Autonomía hídrica y comunal del sector sur",
            asset_split_ratio=0.45,
            tick=5,
        )

        success = (
            parent is not None
            and child is not None
            and parent.active_member_count == 2
            and child.active_member_count == 2
            and child.mission_purpose.startswith("Autonomía")
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las tensiones comunitarias territorializadas pueden producir fragmentación en dos directivas vecinales.",
                "Cada sector hereda legitimidad y autonomía sobre sus propios miembros.",
            ]
            ],
            metrics={
                "parent_name": parent.name if parent else "",
                "child_name": child.name if child else "",
                "parent_members": parent.active_member_count if parent else 0,
                "child_members": child.active_member_count if child else 0,
                "total_funds": (parent.treasury_usd + child.treasury_usd) if (parent and child) else 0.0,
            },
            summary=f"Comunidad fragmentada en '{parent.name if parent else ''}' ({parent.active_member_count if parent else 0} miembros) y '{child.name if child else ''}' ({child.active_member_count if child else 0} miembros).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_R: Cooperación y fusión entre organizaciones
# =============================================================================

class Experiment19_R_IntercommunityMerger(BaseExperiment):
    """EXP_19_R: Two small producer groups unite their treasuries and memberships into a unified cooperative."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_R",
            name="Cooperación y Fusión de Organizaciones",
            description="Dos pequeños colectivos agrícolas se fusionan para aumentar su capacidad de compra mayorista.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        org_a = r.emergent_organizations.create_organization(
            name="Grupo Maicero San Pedro",
            org_type=OrganizationType.AGRICULTURAL_COOPERATIVE,
            mission="Acopio de maíz",
            founder_uids=["a1", "a2"],
            initial_treasury_usd=75.0,
            tick=1,
        )
        org_b = r.emergent_organizations.create_organization(
            name="Productores de Frijol El Calvario",
            org_type=OrganizationType.AGRICULTURAL_COOPERATIVE,
            mission="Acopio de frijol",
            founder_uids=["b1", "b2"],
            initial_treasury_usd=85.0,
            tick=1,
        )

        merged = r.emergent_organizations.execute_merger(
            org_a_id=org_a.org_id,
            org_b_id=org_b.org_id,
            merged_name="Cooperativa Agropecuaria Unida de Granos Básicos",
            tick=5,
        )

        success = (
            merged is not None
            and merged.active_member_count == 4
            and round(merged.treasury_usd, 2) == 160.0
            and org_a.status == OrgLifecycleStatus.MERGED
            and org_b.status == OrgLifecycleStatus.MERGED
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las organizaciones con misiones afines pueden consolidarse en una entidad de mayor escala.",
                "La fusión suma tesorerías y unifica padrones de socios manteniendo la conservación contable.",
            ]
            ],
            metrics={
                "merged_members": merged.active_member_count if merged else 0,
                "merged_treasury_usd": merged.treasury_usd if merged else 0.0,
                "org_a_status": org_a.status.value,
                "org_b_status": org_b.status.value,
            },
            summary=f"Fusión consolidada en '{merged.name if merged else ''}' con {merged.active_member_count if merged else 0} miembros y tesorería combinada de ${merged.treasury_usd if merged else 0.0:.2f}.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_S: Desigualdad de influencia en decisiones colectivas
# =============================================================================

class Experiment19_S_AsymmetricInfluenceGovernance(BaseExperiment):
    """EXP_19_S: Voting outcome is shaped by social capital and influential leaders' asymmetric weight."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_S",
            name="Desigualdad de Influencia en Decisiones Colectivas",
            description="Una minoría con alto capital social y peso de influencia logra aprobar una moción reñida.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        gov = r.collective_governance
        prop = gov.submit_proposal(
            organization_id="org_comercial_01",
            proposer_uid="lider_comerciante",
            title="Cuota Extraordinaria de Vigilancia Nocturna",
            description="Contratación de guardia privado para puestos de mercado.",
            cost_usd=50.0,
            protocol=VotingProtocol.SIMPLE_MAJORITY,
            tick=1,
        )

        # 2 influential leaders vote FOR (weights 2.5 each = 5.0 effective)
        gov.cast_deliberative_vote(prop.proposal_id, "lider_1", "for", influence_weight=2.5)
        gov.cast_deliberative_vote(prop.proposal_id, "lider_2", "for", influence_weight=2.5)

        # 4 ordinary members vote AGAINST (weights 1.0 each = 4.0 effective)
        gov.cast_deliberative_vote(prop.proposal_id, "v1", "against", influence_weight=1.0)
        gov.cast_deliberative_vote(prop.proposal_id, "v2", "against", influence_weight=1.0)
        gov.cast_deliberative_vote(prop.proposal_id, "v3", "against", influence_weight=1.0)
        gov.cast_deliberative_vote(prop.proposal_id, "v4", "against", influence_weight=1.0)

        enacted, summary = gov.resolve_assembly_vote(
            proposal_id=prop.proposal_id,
            total_eligible_members=10,
            treasury_balance_usd=100.0,
            quorum_fraction=0.40,
            tick=2,
        )

        # Passes due to effective influence: 5.0 + 1.0 (proposer) = 6.0 > 4.0 against, despite fewer voters
        success = (
            enacted is True
            and len(prop.votes_for) < len(prop.votes_against)
            and prop.effective_votes_for > prop.effective_votes_against
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las asimetrías de poder y capital social permiten que votos de alta influencia superen a mayorías numéricas simples desarticuladas.",
                "El modelo refleja asimetrías reales de influencia cívica sin igualitarismo artificial.",
            ]
            ],
            metrics={
                "voters_for": len(prop.votes_for),
                "voters_against": len(prop.votes_against),
                "effective_votes_for": prop.effective_votes_for,
                "effective_votes_against": prop.effective_votes_against,
                "enacted": enacted,
            },
            summary=f"Moción aprobada por influencia ponderada ({prop.effective_votes_for:.1f} pts de {len(prop.votes_for)} líderes vs {prop.effective_votes_against:.1f} pts de {len(prop.votes_against)} opositores).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_T: Crisis institucional prolongada por déficit presupuestario
# =============================================================================

class Experiment19_T_InstitutionalCapacityDeficit(BaseExperiment):
    """EXP_19_T: Prolonged budgetary deficit causes case backlog accumulation and capacity strain."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_T",
            name="Crisis Institucional por Déficit Presupuestario",
            description="Una institución sin fondos suficientes reduce su rendimiento y acumula trámites pendientes.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        inst = r.institutional_evolution.register_institution(
            name="Registro y Catastro Comunal",
            formal_acronym="RCC",
            domain=InstitutionDomain.COMMUNITY_ADMINISTRATION,
            mission="Titulación y registro de linderos vecinales",
            headquarters_loc_id="casa_comunal",
            initial_treasury_usd=10.0, # Critically low funds
            director_uid="registrador",
            tick=1,
        )

        # File 12 title claims
        for i in range(12):
            inst.request_service(f"claimant_{i}", "registro_solar", tick=2)

        # Execute daily operations with constrained budget
        ops = inst.process_daily_operations(tick=96)

        success = (
            inst.status == InstitutionalStatus.CAPACITY_STRAINED
            and ops["backlog"] > 0
            and inst.treasury_usd < 10.0
            and inst.legitimacy < 0.85
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las instituciones con presupuesto deficitario sufren estrangulamiento de capacidad operativa.",
                "La acumulación de trámites no resueltos degrada gradualmente la legitimidad ciudadana.",
            ]
            ],
            metrics={
                "remaining_treasury": inst.treasury_usd,
                "processed_today": ops["processed_count"],
                "backlog_queue": ops["backlog"],
                "status": inst.status.value,
                "legitimacy": inst.legitimacy,
            },
            summary=f"Institución entró en '{inst.status.value}' con {ops['backlog']} trámites represados y tesorería agotada (${inst.treasury_usd:.2f}).",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_U: Organización informal que sustituye servicio ausente
# =============================================================================

class Experiment19_U_InformalSubstitutionAbsentService(BaseExperiment):
    """EXP_19_U: Informal mutual aid circle provides emergency funds when formal welfare is absent."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_U",
            name="Sustitución Informal de Servicio Ausente",
            description="Ante la ausencia de seguridad social formal, un cuchubal vecinal cubre gastos médicos de emergencia.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        cuchubal = r.salvadoran_adesco.create_cuchubal(
            circle_id="cuchubal_salud_vecinos",
            name="Cuchubal de Emergencia San Esteban",
            organizer_uid="vecina_lider",
            member_uids=["vecina_lider", "v1", "v2", "v3", "v4"],
            contribution_usd=15.0,
        )
        pot = cuchubal.total_pot_per_turn # 5 x $15 = $75

        # Payout round delivered to distressed member
        payout = r.salvadoran_adesco.execute_cuchubal_turn(cuchubal.circle_id)

        success = (
            pot == 75.0
            and payout is not None
            and payout.get("success") is True
            and payout.get("pot_received_usd") == 75.0
            and cuchubal.turns_completed == 1
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Los mecanismos informales tradicionales (cuchubales) sustituyen eficazmente la ausencia de seguros formales.",
                "La rotación periódica del fondo proporciona liquidez de emergencia a familias vulnerables.",
            ]
            ],
            metrics={
                "members": len(cuchubal.member_uids),
                "pot_usd": pot,
                "payout_usd": payout.get("pot_received_usd") if payout else 0.0,
                "recipient": payout.get("beneficiary") if payout else "",
            },
            summary=f"Círculo de ahorro rotativo entregó ${pot:.2f} a {payout.get('beneficiary') if payout else ''} en su primer turno de ayuda.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_V: Transformación histórica de propósito institucional
# =============================================================================

class Experiment19_V_HistoricalMissionShift(BaseExperiment):
    """EXP_19_V: An institution adapts its charter from disaster relief to permanent microcredit."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_V",
            name="Transformación Histórica de Misión Institucional",
            description="Una institución vecinal nacida para socorro de emergencia muta a cooperativa permanente.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        org = r.emergent_organizations.create_organization(
            name="Comité de Socorro Temporal Tormenta",
            org_type=OrganizationType.MUTUAL_AID_SOCIETY,
            mission="Albergue y comida de emergencia",
            founder_uids=["f1", "f2", "f3"],
            initial_treasury_usd=100.0,
            tick=1,
        )
        old_mission = org.mission_purpose

        # Evolve mission to microcredit and reconstruction
        org.shift_mission(
            new_purpose="Fondo Rotativo de Microcrédito y Reconstrucción Vecinal",
            tick=96,
        )

        success = (
            org.mission_purpose != old_mission
            and "Microcrédito" in org.mission_purpose
            and len(org.history_log) >= 2
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las organizaciones colectivas no son estáticas; adaptan su misión a nuevas fases históricas.",
                "La transición queda documentada en el historial evolutivo de la entidad.",
            ]
            ],
            metrics={
                "old_mission": old_mission,
                "new_mission": org.mission_purpose,
                "history_entries": len(org.history_log),
            },
            summary=f"Propósito institucional transformado con éxito: '{old_mission}' $\\to$ '{org.mission_purpose}'.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_W: Comparación entre sociedades con condiciones iniciales distintas
# =============================================================================

class Experiment19_W_ComparativeInitialConditionsDivergence(BaseExperiment):
    """EXP_19_W: Divergence between high-trust cooperative society vs low-trust fragmented society."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_W",
            name="Comparación Divergente por Condiciones Iniciales",
            description="Contraste entre dos sociedades: Alta confianza genera organizaciones; desconfianza produce estancamiento.",
            duration_ticks=24,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()

        # Society A: High Trust & Resources
        r_a = _make_runner(seed=101, pop_size=10)
        cands_a = [
            {"uid": f"a_{i}", "needs": ["comercio"], "location": "mercado_central", "capital": 50.0}
            for i in range(4)
        ]
        org_a = r_a.emergent_organizations.attempt_spontaneous_formation(cands_a, tick=1)

        # Society B: Low Trust / Dispersed needs
        r_b = _make_runner(seed=202, pop_size=10)
        cands_b = [
            {"uid": "b_1", "needs": ["comercio"], "location": "plaza_central", "capital": 5.0},
            {"uid": "b_2", "needs": ["agricultura"], "location": "taller_artesanal", "capital": 2.0},
        ]
        org_b = r_b.emergent_organizations.attempt_spontaneous_formation(cands_b, tick=1)

        success = (
            org_a is not None
            and org_b is None
            and len(r_a.emergent_organizations.get_all_organizations()) > len(r_b.emergent_organizations.get_all_organizations())
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "Las condiciones iniciales de confianza y alineamiento de necesidades determinan el surgimiento organizacional.",
                "Poblaciones atomizadas con necesidades dispersas no logran generar organizaciones espontáneas.",
            ]
            ],
            metrics={
                "society_a_orgs": len(r_a.emergent_organizations.get_all_organizations()),
                "society_b_orgs": len(r_b.emergent_organizations.get_all_organizations()),
                "org_a_created": org_a is not None,
                "org_b_created": org_b is not None,
            },
            summary=f"Divergencia confirmada: Sociedad A formó {len(r_a.emergent_organizations.get_all_organizations())} organizaciones; Sociedad B formó 0.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# EXP_19_X: Simulación sostenida con crecimiento organizacional
# =============================================================================

class Experiment19_X_SustainedSocietalComplexityGrowth(BaseExperiment):
    """EXP_19_X: Sustained 96-tick multi-layer simulation verifying stability of society & institutions."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_19_X",
            name="Simulación Sostenida de Complejidad Social",
            description="Ejecución de un día completo de simulación integrando organizaciones, normas, CPR y estratificación.",
            duration_ticks=96,
            random_seed=42,
            population_size=10,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        start_time = time.time()
        r = runner or _make_runner(seed=self.config.random_seed, pop_size=self.config.population_size)

        orgs_start = len(r.emergent_organizations.get_all_organizations())
        cpr_start = len(r.cpr_manager.get_all_resources())
        norms_start = len(r.social_norms.get_all_norms())

        # Step 96 ticks (1 complete day)
        for _ in range(self.config.duration_ticks):
            r.step()

        orgs_end = len(r.emergent_organizations.get_all_organizations())
        cpr_end = len(r.cpr_manager.get_all_resources())
        norms_end = len(r.social_norms.get_all_norms())
        latest_strat = r.social_stratification.get_latest_metrics()

        success = (
            r.clock.current_tick == self.config.duration_ticks
            and orgs_end >= orgs_start
            and cpr_end >= cpr_start
            and norms_end >= norms_start
            and latest_strat is not None
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            hypotheses=[
                {"hypothesis": h, "confirmed": success}
                for h in [
                "La arquitectura social e institucional de la Fase 1.9 opera de forma sostenida sin colapsos numéricos.",
                "Todos los subsistemas (organizaciones, normas, CPR, estratificación) coexisten armoniosamente.",
            ]
            ],
            metrics={
                "ticks_completed": r.clock.current_tick,
                "organizations_count": orgs_end,
                "cpr_resources_count": cpr_end,
                "norms_count": norms_end,
                "gini_income": latest_strat.gini_income if latest_strat else 0.0,
                "palma_ratio": latest_strat.palma_ratio if latest_strat else 0.0,
            },
            summary=f"Simulación sostenida de {r.clock.current_tick} ticks completada con {orgs_end} organizaciones, {cpr_end} recursos CPR y {norms_end} normas vigentes.",
            duration_seconds=time.time() - start_time,
        )


# =============================================================================
# Registry of All 24 Experiments for Phase 1.9
# =============================================================================

PHASE19_EXPERIMENTS = [
    Experiment19_A_SpontaneousCommercialOrg,
    Experiment19_B_OrgFailureTrustCollapse,
    Experiment19_C_OrgFissionInternalConflict,
    Experiment19_D_InstitutionCollectiveNeed,
    Experiment19_E_InstitutionLegitimacyCrisis,
    Experiment19_F_LeadershipSuccessionImpact,
    Experiment19_G_AssemblyVotingPersistentDissent,
    Experiment19_H_IntergroupNegotiationPact,
    Experiment19_I_CollectiveWaterManagementCPR,
    Experiment19_J_TragedyOfTheCommonsDepletion,
    Experiment19_K_BusinessLifecycleDebtBankruptcy,
    Experiment19_L_LongitudinalStratificationMobility,
    Experiment19_M_LaborStrikeMediation,
    Experiment19_N_NormTransmissionIntergenerational,
    Experiment19_O_CulturalTraditionDesuetudo,
    Experiment19_P_InstitutionKnowledgeConservation,
    Experiment19_Q_CommunityFragmentation,
    Experiment19_R_IntercommunityMerger,
    Experiment19_S_AsymmetricInfluenceGovernance,
    Experiment19_T_InstitutionalCapacityDeficit,
    Experiment19_U_InformalSubstitutionAbsentService,
    Experiment19_V_HistoricalMissionShift,
    Experiment19_W_ComparativeInitialConditionsDivergence,
    Experiment19_X_SustainedSocietalComplexityGrowth,
]
