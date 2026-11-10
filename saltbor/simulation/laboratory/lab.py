"""Simulation Laboratory: central experimental orchestrator and laboratory environment."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from saltbor.core.config import SimulationConfig
from saltbor.simulation.analysis.cognitive_validator import CognitiveSystemValidator
from saltbor.simulation.analysis.individual_observability import IndividualObservability
from saltbor.simulation.analysis.population_analyzer import PopulationAnalyzer
from saltbor.simulation.experiments.base import BaseExperiment, ExperimentResult
from saltbor.simulation.experiments.experiments_a_d import (
    ExperimentA_Autonomy,
    ExperimentB_PersonalityEvolution,
    ExperimentC_MemoryAndLearning,
    ExperimentD_SocialRelationships,
)
from saltbor.simulation.experiments.experiments_e_h import (
    ExperimentE_EnvironmentalAdaptation,
    ExperimentF_ConflictingNeeds,
    ExperimentG_LongTermDevelopment,
    ExperimentH_Emergence,
)
from saltbor.simulation.experiments.phase04_experiments import (
    Experiment04_A_MultigenerationalPopulation,
    Experiment04_B_FamilyDevelopment,
    Experiment04_C_EconomicDynamics,
    Experiment04_D_ComplexPlanning,
    Experiment04_E_InformationPropagation,
    Experiment04_F_GroupFormation,
    Experiment04_G_ContinuousNavigation,
    Experiment04_H_LongTermSocialEvolution,
)
from saltbor.simulation.experiments.phase05_experiments import (
    Experiment05_A_CulturalEmergence,
    Experiment05_B_EconomicCredit,
    Experiment05_C_BusinessEcosystem,
    Experiment05_D_SocialNetworkEvolution,
    Experiment05_E_InstitutionalDevelopment,
    Experiment05_F_SocialLearning,
    Experiment05_G_GeographicAdaptation,
    Experiment05_H_IntegratedSocialCrisis,
    Experiment05_I_LongitudinalCivilization,
    Experiment05_J_EmergentBehaviorValidation,
)
from saltbor.simulation.experiments.phase06_experiments import (
    Experiment06_A_RegionalTradeArbitrage,
    Experiment06_B_StatutoryLegalAdjudication,
    Experiment06_C_PaymentInKind,
    Experiment06_D_RegionalShockAndRelief,
)
from saltbor.simulation.experiments.phase06_knowledge_experiments import (
    Experiment06_A_IndividualKnowledgeAcquisition,
    Experiment06_B_KnowledgeTransmission,
    Experiment06_C_IntergenerationalKnowledge,
    Experiment06_D_IndependentDiscovery,
    Experiment06_E_CompositionalReasoning,
    Experiment06_F_HypothesisAndExperimentation,
    Experiment06_G_ContradictoryKnowledge,
    Experiment06_H_CollectiveIntelligence,
    Experiment06_I_KnowledgeSpecialization,
    Experiment06_J_KnowledgeAndEconomicInnovation,
    Experiment06_K_OpenEndedCapability,
    Experiment06_L_KnowledgePersistence,
)
from saltbor.simulation.experiments.phase07_reasoning_experiments import (
    Experiment07_A_DeductiveReasoning,
    Experiment07_B_InductiveLearning,
    Experiment07_C_AbductiveReasoning,
    Experiment07_D_CausalReasoning,
    Experiment07_E_AnalogicalTransfer,
    Experiment07_F_CounterfactualReasoning,
    Experiment07_G_UnknownProblemSolving,
    Experiment07_H_Metacognition,
    Experiment07_I_CreativeCombination,
    Experiment07_J_AutonomousGoalGeneration,
    Experiment07_K_CollectiveIntelligence,
    Experiment07_L_IndependentDiscovery,
    Experiment07_M_FailureAdaptation,
    Experiment07_N_LongitudinalCognitiveDevelopment,
    Experiment07_O_Persistence,
)
from saltbor.simulation.experiments.salvadoran_experiments import (
    ExperimentSV_01_UrbanRuralDifferences,
    ExperimentSV_02_SeasonalClimateAgriculture,
    ExperimentSV_03_LocalMarketInformalCommerce,
    ExperimentSV_04_CulturalTransmissionGenerations,
    ExperimentSV_05_RegionalLanguageVariation,
    ExperimentSV_06_MigrationRemittances,
    ExperimentSV_07_PatronSaintFestivalEconomics,
    ExperimentSV_08_TransportAccessibility,
    ExperimentSV_09_CommunityCooperationDisruption,
    ExperimentSV_10_IndividualAdaptationEnvironments,
)
from saltbor.simulation.experiments.territorial_experiments import (
    Experiment08_A_TerritorialIntegrity,
    Experiment08_B_SpatialPrecision,
    Experiment08_C_RealPlaces,
    Experiment08_D_DuplicateDetection,
    Experiment08_E_IncrementalUpdate,
    Experiment08_F_Navigation,
    Experiment08_G_Obstacles,
    Experiment08_H_TerritorialEconomy,
    Experiment08_I_GeographicCognition,
    Experiment08_J_SocialTransmission,
    Experiment08_K_IncorrectInformation,
    Experiment08_L_EnvironmentalImpact,
    Experiment08_M_OfflineOperation,
    Experiment08_N_Persistence,
    Experiment08_O_UpdateAndRecovery,
    Experiment08_P_Scalability,
    Experiment08_Q_GlobalIntegration,
    Experiment08_R_TerritorialConsistency,
    Experiment08_S_SourceQuality,
    Experiment08_T_VersionComparison,
)
from saltbor.simulation.experiments.phase09_experiments import (
    Experiment09_A_FriendshipFormation,
    Experiment09_B_CommunityFormation,
    Experiment09_C_SocialNetworkEvolution,
    Experiment09_D_RuptureAndReconciliation,
    Experiment09_E_CollectiveProblemSolving,
    Experiment09_F_KnowledgeTransmission,
    Experiment09_G_RumorPropagationAndDistortion,
    Experiment09_H_SocialLearning,
    Experiment09_I_LeadershipEmergence,
    Experiment09_J_OrganizationFormation,
    Experiment09_K_InternalConflicts,
    Experiment09_L_NegotiationAndCooperation,
    Experiment09_M_ReputationAndTrust,
    Experiment09_N_EconomicCooperation,
    Experiment09_O_CulturalDevelopment,
    Experiment09_P_InstitutionalTransformation,
    Experiment09_Q_InnovationDiffusion,
    Experiment09_R_CollectiveIntelligenceUncertainty,
    Experiment09_S_CommunityFissionAndDissolution,
    Experiment09_T_LongitudinalSimulation,
    Experiment09_U_GeographyEconomySocietyIntegration,
    Experiment09_V_PersistenceAndRecovery,
    Experiment09_W_IncompleteInformation,
    Experiment09_X_NetworkScalability,
)
from saltbor.simulation.experiments.phase10_experiments_a_l import (
    Experiment10_A_MultigenerationalContinuity,
    Experiment10_B_DemographicTurnover,
    Experiment10_C_SettlementEvolution,
    Experiment10_D_TerritorialMigration,
    Experiment10_E_FamilyStructures,
    Experiment10_F_KnowledgeTransmission,
    Experiment10_G_CulturalTraditions,
    Experiment10_H_InnovationDiffusion,
    Experiment10_I_EconomicTransformation,
    Experiment10_J_SocialMobility,
    Experiment10_K_InstitutionalTransformation,
    Experiment10_L_InequalityEvolution,
)
from saltbor.simulation.experiments.phase10_experiments_m_x import (
    Experiment10_M_EnvironmentalCrisisResponse,
    Experiment10_N_EconomicResilience,
    Experiment10_O_CommunityFragmentation,
    Experiment10_P_CollectiveIdentityFormation,
    Experiment10_Q_InterSocietyRelations,
    Experiment10_R_KnowledgeLossAndRecovery,
    Experiment10_S_SettlementHistoricalTransformation,
    Experiment10_T_InstitutionalGenerationalContinuity,
    Experiment10_U_ResourceConditionedTech,
    Experiment10_V_HistoricalScenarioComparison,
    Experiment10_W_SocietyExtinctionOrTransformation,
    Experiment10_X_LongTermCivilizationEvolution,
)
from saltbor.simulation.experiments.phase11_experiments import (
    Experiment11_A_ArchitectureAudit,
    Experiment11_B_SeedReproducibility,
    Experiment11_C_IndividualGoalEmergence,
    Experiment11_D_SocialRelationshipEmergence,
    Experiment11_E_SpontaneousCommunityFormation,
    Experiment11_F_EconomicActivityEmergence,
    Experiment11_G_IntergenerationalCulturalTransmission,
    Experiment11_H_ScarcityAdaptation,
    Experiment11_I_LongitudinalDemographics,
    Experiment11_J_CollectiveProblemSolving,
    Experiment11_K_CognitiveArchitectureAblation,
    Experiment11_L_KnowledgeGraphAblation,
    Experiment11_M_ParameterSensitivity,
    Experiment11_N_LongHistoricalSimulation,
    Experiment11_O_SustainedPerformance,
    Experiment11_P_PersistenceAndRecovery,
    Experiment11_Q_SalvadoranGeographyValidation,
    Experiment11_R_ArchitecturalComparison,
    Experiment11_S_CausalTraceability,
    Experiment11_T_CivilizationIntegralTest,
)
from saltbor.simulation.experiments.phase111_experiments import (
    Experiment111_A_DynamicCulturalDrift,
    Experiment111_B_Communities20to100Agents,
    Experiment111_C_LongitudinalAutonomousEconomy,
    Experiment111_D_CollectiveResourceConflicts,
    Experiment111_E_AutonomousTechnologicalDiscovery,
    Experiment111_F_KnowledgeTransmissionMentorship,
    Experiment111_G_InnovationAndEconomicSpecialization,
    Experiment111_H_MultiSeedReproducibility,
    Experiment111_I_CrossEnginePerformanceAudit,
    Experiment111_J_LongitudinalCommunityTransformation,
)
from saltbor.simulation.experiments.phase12_experiments import (
    Experiment12_A_EnvironmentalDivergence,
    Experiment12_B_CulturalKnowledgeExtinction,
    Experiment12_C_GenerationalKnowledgeSeverance,
    Experiment12_D_CommunityFissionAndNewSettlement,
    Experiment12_E_FoodCrisisAndDistressMigration,
    Experiment12_F_FinancialLiquidityFreezeAndInKindSettlement,
    Experiment12_G_OpenCombinatorialDiscovery,
    Experiment12_H_TechnologicalFailureAndResourceLoss,
    Experiment12_I_ImperfectTransmissionAndKnowledgeMutation,
    Experiment12_J_TerritorialDecayAndAbandonment,
    Experiment12_K_CivilizationalRecoveryPostCrisis,
    Experiment12_L_LongitudinalCivilizationalDivergence,
)
from saltbor.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class SimulationLaboratory:
    """The central experimental workbench for Saltbor Phase 0.3 and Phase 0.4.

    Allows researchers to:
    - Launch, pause, step, accelerate, and reset simulations.
    - Run the entire suite of 8 Behavioral Experiments (A through H).
    - Perform population diversity diagnostics and anti-artificial behavior checks.
    - Validate cognitive system feedback loops.
    - Export standardized Markdown and JSON experiment reports.
    """

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()
        self.runner: Optional[SimulationRunner] = None
        self.experiment_registry: dict[str, type[BaseExperiment]] = {
            "EXP_A": ExperimentA_Autonomy,
            "EXP_B": ExperimentB_PersonalityEvolution,
            "EXP_C": ExperimentC_MemoryAndLearning,
            "EXP_D": ExperimentD_SocialRelationships,
            "EXP_E": ExperimentE_EnvironmentalAdaptation,
            "EXP_F": ExperimentF_ConflictingNeeds,
            "EXP_G": ExperimentG_LongTermDevelopment,
            "EXP_H": ExperimentH_Emergence,
            # Phase 0.4 experiments
            "EXP_04_A": Experiment04_A_MultigenerationalPopulation,
            "EXP_04_B": Experiment04_B_FamilyDevelopment,
            "EXP_04_C": Experiment04_C_EconomicDynamics,
            "EXP_04_D": Experiment04_D_ComplexPlanning,
            "EXP_04_E": Experiment04_E_InformationPropagation,
            "EXP_04_F": Experiment04_F_GroupFormation,
            "EXP_04_G": Experiment04_G_ContinuousNavigation,
            "EXP_04_H": Experiment04_H_LongTermSocialEvolution,
            # Phase 0.5 experiments
            "EXP_05_A": Experiment05_A_CulturalEmergence,
            "EXP_05_B": Experiment05_B_EconomicCredit,
            "EXP_05_C": Experiment05_C_BusinessEcosystem,
            "EXP_05_D": Experiment05_D_SocialNetworkEvolution,
            "EXP_05_E": Experiment05_E_InstitutionalDevelopment,
            "EXP_05_F": Experiment05_F_SocialLearning,
            "EXP_05_G": Experiment05_G_GeographicAdaptation,
            "EXP_05_H": Experiment05_H_IntegratedSocialCrisis,
            "EXP_05_I": Experiment05_I_LongitudinalCivilization,
            "EXP_05_J": Experiment05_J_EmergentBehaviorValidation,
            # Phase 0.6 Macro-Regional Experiments
            "EXP_06_REGIONAL_A": Experiment06_A_RegionalTradeArbitrage,
            "EXP_06_REGIONAL_B": Experiment06_B_StatutoryLegalAdjudication,
            "EXP_06_REGIONAL_C": Experiment06_C_PaymentInKind,
            "EXP_06_REGIONAL_D": Experiment06_D_RegionalShockAndRelief,
            # Phase 0.6 Knowledge Graph, Learning & Collective Intelligence Suite
            "EXP_06_A": Experiment06_A_IndividualKnowledgeAcquisition,
            "EXP_06_B": Experiment06_B_KnowledgeTransmission,
            "EXP_06_C": Experiment06_C_IntergenerationalKnowledge,
            "EXP_06_D": Experiment06_D_IndependentDiscovery,
            "EXP_06_E": Experiment06_E_CompositionalReasoning,
            "EXP_06_F": Experiment06_F_HypothesisAndExperimentation,
            "EXP_06_G": Experiment06_G_ContradictoryKnowledge,
            "EXP_06_H": Experiment06_H_CollectiveIntelligence,
            "EXP_06_I": Experiment06_I_KnowledgeSpecialization,
            "EXP_06_J": Experiment06_J_KnowledgeAndEconomicInnovation,
            "EXP_06_K": Experiment06_K_OpenEndedCapability,
            "EXP_06_L": Experiment06_L_KnowledgePersistence,
            # Phase 0.7 Advanced Reasoning, Problem Solving & Open-Ended Intelligence
            "EXP_07_A": Experiment07_A_DeductiveReasoning,
            "EXP_07_B": Experiment07_B_InductiveLearning,
            "EXP_07_C": Experiment07_C_AbductiveReasoning,
            "EXP_07_D": Experiment07_D_CausalReasoning,
            "EXP_07_E": Experiment07_E_AnalogicalTransfer,
            "EXP_07_F": Experiment07_F_CounterfactualReasoning,
            "EXP_07_G": Experiment07_G_UnknownProblemSolving,
            "EXP_07_H": Experiment07_H_Metacognition,
            "EXP_07_I": Experiment07_I_CreativeCombination,
            "EXP_07_J": Experiment07_J_AutonomousGoalGeneration,
            "EXP_07_K": Experiment07_K_CollectiveIntelligence,
            "EXP_07_L": Experiment07_L_IndependentDiscovery,
            "EXP_07_M": Experiment07_M_FailureAdaptation,
            "EXP_07_N": Experiment07_N_LongitudinalCognitiveDevelopment,
            "EXP_07_O": Experiment07_O_Persistence,
            # Section 19 Salvadoran Environment & Cultural Context Suite
            "EXP_SV_01": ExperimentSV_01_UrbanRuralDifferences,
            "EXP_SV_02": ExperimentSV_02_SeasonalClimateAgriculture,
            "EXP_SV_03": ExperimentSV_03_LocalMarketInformalCommerce,
            "EXP_SV_04": ExperimentSV_04_CulturalTransmissionGenerations,
            "EXP_SV_05": ExperimentSV_05_RegionalLanguageVariation,
            "EXP_SV_06": ExperimentSV_06_MigrationRemittances,
            "EXP_SV_07": ExperimentSV_07_PatronSaintFestivalEconomics,
            "EXP_SV_08": ExperimentSV_08_TransportAccessibility,
            "EXP_SV_09": ExperimentSV_09_CommunityCooperationDisruption,
            "EXP_SV_10": ExperimentSV_10_IndividualAdaptationEnvironments,
            # Phase 0.8 Real Geographic World & El Salvador Integration Suite
            "EXP_08_A": Experiment08_A_TerritorialIntegrity,
            "EXP_08_B": Experiment08_B_SpatialPrecision,
            "EXP_08_C": Experiment08_C_RealPlaces,
            "EXP_08_D": Experiment08_D_DuplicateDetection,
            "EXP_08_E": Experiment08_E_IncrementalUpdate,
            "EXP_08_F": Experiment08_F_Navigation,
            "EXP_08_G": Experiment08_G_Obstacles,
            "EXP_08_H": Experiment08_H_TerritorialEconomy,
            "EXP_08_I": Experiment08_I_GeographicCognition,
            "EXP_08_J": Experiment08_J_SocialTransmission,
            "EXP_08_K": Experiment08_K_IncorrectInformation,
            "EXP_08_L": Experiment08_L_EnvironmentalImpact,
            "EXP_08_M": Experiment08_M_OfflineOperation,
            "EXP_08_N": Experiment08_N_Persistence,
            "EXP_08_O": Experiment08_O_UpdateAndRecovery,
            "EXP_08_P": Experiment08_P_Scalability,
            "EXP_08_Q": Experiment08_Q_GlobalIntegration,
            "EXP_08_R": Experiment08_R_TerritorialConsistency,
            "EXP_08_S": Experiment08_S_SourceQuality,
            "EXP_08_T": Experiment08_T_VersionComparison,
            # Phase 0.9 Collective Intelligence, Social Networks & Emergent Communities
            "EXP_09_A": Experiment09_A_FriendshipFormation,
            "EXP_09_B": Experiment09_B_CommunityFormation,
            "EXP_09_C": Experiment09_C_SocialNetworkEvolution,
            "EXP_09_D": Experiment09_D_RuptureAndReconciliation,
            "EXP_09_E": Experiment09_E_CollectiveProblemSolving,
            "EXP_09_F": Experiment09_F_KnowledgeTransmission,
            "EXP_09_G": Experiment09_G_RumorPropagationAndDistortion,
            "EXP_09_H": Experiment09_H_SocialLearning,
            "EXP_09_I": Experiment09_I_LeadershipEmergence,
            "EXP_09_J": Experiment09_J_OrganizationFormation,
            "EXP_09_K": Experiment09_K_InternalConflicts,
            "EXP_09_L": Experiment09_L_NegotiationAndCooperation,
            "EXP_09_M": Experiment09_M_ReputationAndTrust,
            "EXP_09_N": Experiment09_N_EconomicCooperation,
            "EXP_09_O": Experiment09_O_CulturalDevelopment,
            "EXP_09_P": Experiment09_P_InstitutionalTransformation,
            "EXP_09_Q": Experiment09_Q_InnovationDiffusion,
            "EXP_09_R": Experiment09_R_CollectiveIntelligenceUncertainty,
            "EXP_09_S": Experiment09_S_CommunityFissionAndDissolution,
            "EXP_09_T": Experiment09_T_LongitudinalSimulation,
            "EXP_09_U": Experiment09_U_GeographyEconomySocietyIntegration,
            "EXP_09_V": Experiment09_V_PersistenceAndRecovery,
            "EXP_09_W": Experiment09_W_IncompleteInformation,
            "EXP_09_X": Experiment09_X_NetworkScalability,
            # Phase 1.0 Civilization Evolution & Historical Emergence Suite
            "EXP_10_A": Experiment10_A_MultigenerationalContinuity,
            "EXP_10_B": Experiment10_B_DemographicTurnover,
            "EXP_10_C": Experiment10_C_SettlementEvolution,
            "EXP_10_D": Experiment10_D_TerritorialMigration,
            "EXP_10_E": Experiment10_E_FamilyStructures,
            "EXP_10_F": Experiment10_F_KnowledgeTransmission,
            "EXP_10_G": Experiment10_G_CulturalTraditions,
            "EXP_10_H": Experiment10_H_InnovationDiffusion,
            "EXP_10_I": Experiment10_I_EconomicTransformation,
            "EXP_10_J": Experiment10_J_SocialMobility,
            "EXP_10_K": Experiment10_K_InstitutionalTransformation,
            "EXP_10_L": Experiment10_L_InequalityEvolution,
            "EXP_10_M": Experiment10_M_EnvironmentalCrisisResponse,
            "EXP_10_N": Experiment10_N_EconomicResilience,
            "EXP_10_O": Experiment10_O_CommunityFragmentation,
            "EXP_10_P": Experiment10_P_CollectiveIdentityFormation,
            "EXP_10_Q": Experiment10_Q_InterSocietyRelations,
            "EXP_10_R": Experiment10_R_KnowledgeLossAndRecovery,
            "EXP_10_S": Experiment10_S_SettlementHistoricalTransformation,
            "EXP_10_T": Experiment10_T_InstitutionalGenerationalContinuity,
            "EXP_10_U": Experiment10_U_ResourceConditionedTech,
            "EXP_10_V": Experiment10_V_HistoricalScenarioComparison,
            "EXP_10_W": Experiment10_W_SocietyExtinctionOrTransformation,
            "EXP_10_X": Experiment10_X_LongTermCivilizationEvolution,
            # Phase 1.1 Architecture Consolidation, Benchmarking & Emergence Suite
            "EXP_11_A": Experiment11_A_ArchitectureAudit,
            "EXP_11_B": Experiment11_B_SeedReproducibility,
            "EXP_11_C": Experiment11_C_IndividualGoalEmergence,
            "EXP_11_D": Experiment11_D_SocialRelationshipEmergence,
            "EXP_11_E": Experiment11_E_SpontaneousCommunityFormation,
            "EXP_11_F": Experiment11_F_EconomicActivityEmergence,
            "EXP_11_G": Experiment11_G_IntergenerationalCulturalTransmission,
            "EXP_11_H": Experiment11_H_ScarcityAdaptation,
            "EXP_11_I": Experiment11_I_LongitudinalDemographics,
            "EXP_11_J": Experiment11_J_CollectiveProblemSolving,
            "EXP_11_K": Experiment11_K_CognitiveArchitectureAblation,
            "EXP_11_L": Experiment11_L_KnowledgeGraphAblation,
            "EXP_11_M": Experiment11_M_ParameterSensitivity,
            "EXP_11_N": Experiment11_N_LongHistoricalSimulation,
            "EXP_11_O": Experiment11_O_SustainedPerformance,
            "EXP_11_P": Experiment11_P_PersistenceAndRecovery,
            "EXP_11_Q": Experiment11_Q_SalvadoranGeographyValidation,
            "EXP_11_R": Experiment11_R_ArchitecturalComparison,
            "EXP_11_S": Experiment11_S_CausalTraceability,
            "EXP_11_T": Experiment11_T_CivilizationIntegralTest,
            # Phase 1.1.1 Validation Extension Suite
            "EXP_111_A": Experiment111_A_DynamicCulturalDrift,
            "EXP_111_B": Experiment111_B_Communities20to100Agents,
            "EXP_111_C": Experiment111_C_LongitudinalAutonomousEconomy,
            "EXP_111_D": Experiment111_D_CollectiveResourceConflicts,
            "EXP_111_E": Experiment111_E_AutonomousTechnologicalDiscovery,
            "EXP_111_F": Experiment111_F_KnowledgeTransmissionMentorship,
            "EXP_111_G": Experiment111_G_InnovationAndEconomicSpecialization,
            "EXP_111_H": Experiment111_H_MultiSeedReproducibility,
            "EXP_111_I": Experiment111_I_CrossEnginePerformanceAudit,
            "EXP_111_J": Experiment111_J_LongitudinalCommunityTransformation,
            # Phase 1.2 Open-Ended Society & Longitudinal Civilizational Experiments
            "EXP_12_A": Experiment12_A_EnvironmentalDivergence,
            "EXP_12_B": Experiment12_B_CulturalKnowledgeExtinction,
            "EXP_12_C": Experiment12_C_GenerationalKnowledgeSeverance,
            "EXP_12_D": Experiment12_D_CommunityFissionAndNewSettlement,
            "EXP_12_E": Experiment12_E_FoodCrisisAndDistressMigration,
            "EXP_12_F": Experiment12_F_FinancialLiquidityFreezeAndInKindSettlement,
            "EXP_12_G": Experiment12_G_OpenCombinatorialDiscovery,
            "EXP_12_H": Experiment12_H_TechnologicalFailureAndResourceLoss,
            "EXP_12_I": Experiment12_I_ImperfectTransmissionAndKnowledgeMutation,
            "EXP_12_J": Experiment12_J_TerritorialDecayAndAbandonment,
            "EXP_12_K": Experiment12_K_CivilizationalRecoveryPostCrisis,
            "EXP_12_L": Experiment12_L_LongitudinalCivilizationalDivergence,
        }

    def start_simulation(self, seed: Optional[int] = None) -> SimulationRunner:
        """Initialize or reset the simulation runner."""
        if seed is not None:
            self.config.random_seed = seed
        self.runner = SimulationRunner(config=self.config)
        self.runner.initialize(load_existing=False)
        return self.runner

    def step(self) -> int:
        """Step the simulation by exactly 1 tick."""
        if self.runner is None:
            self.start_simulation()
        return self.runner.step()

    def advance_ticks(self, count: int) -> None:
        """Advance the simulation by an arbitrary count of ticks."""
        if self.runner is None:
            self.start_simulation()
        for _ in range(count):
            self.runner.step()

    def run_experiment(self, exp_key: str, **kwargs: Any) -> ExperimentResult:
        """Execute a single experiment by its key."""
        exp_cls = self.experiment_registry.get(exp_key.upper())
        if not exp_cls:
            raise ValueError(f"Unknown experiment '{exp_key}'. Available: {list(self.experiment_registry.keys())}")
        exp_instance = exp_cls()
        if "duration_ticks" in kwargs:
            exp_instance.config.duration_ticks = kwargs["duration_ticks"]
        return exp_instance.run()

    def run_all_experiments(self) -> dict[str, ExperimentResult]:
        """Execute all 8 behavioral experiments and collect results."""
        results: dict[str, ExperimentResult] = {}
        for key in sorted(self.experiment_registry.keys()):
            logger.info("Executing Behavioral Experiment %s...", key)
            results[key] = self.run_experiment(key)
        return results

    def inspect_individual(self, serial: int) -> dict[str, Any]:
        """Generate complete state dossier and structured decision explanation trace."""
        if self.runner is None:
            self.start_simulation()
        human = self.runner.population.get_by_serial(serial)
        if not human:
            raise ValueError(f"Human #{serial} not found in population.")
        return IndividualObservability.get_structured_dossier(human, self.runner.social)

    def explain_last_decision(self, serial: int) -> str:
        """Produce the human-readable explanation trace for an individual."""
        if self.runner is None:
            self.start_simulation()
        human = self.runner.population.get_by_serial(serial)
        if not human:
            raise ValueError(f"Human #{serial} not found in population.")
        return IndividualObservability.format_decision_trace_text(human)

    def analyze_population(self) -> dict[str, Any]:
        """Run complete population-wide behavioral analysis and anti-artificial tests."""
        if self.runner is None:
            self.start_simulation()
        pop = self.runner.population
        soc = self.runner.social

        pers_div = PopulationAnalyzer.analyze_personality_diversity(pop)
        emot_div = PopulationAnalyzer.analyze_emotional_diversity(pop)
        autonomy_div = PopulationAnalyzer.analyze_goals_and_autonomy(pop)
        social_conn = PopulationAnalyzer.analyze_social_connectivity(soc, pop)
        spatial_dist = PopulationAnalyzer.analyze_spatial_distribution(pop)
        anti_artificial = PopulationAnalyzer.analyze_anti_artificial_patterns(pop, soc)

        return {
            "population_size": pop.count,
            "personality_diversity": pers_div,
            "emotional_diversity": emot_div,
            "autonomy_and_goals": autonomy_div,
            "social_connectivity": social_conn,
            "spatial_distribution": spatial_dist,
            "anti_artificial_audit": anti_artificial,
        }

    def validate_cognitive_architecture(self) -> dict[str, Any]:
        """Verify the causal interactions between frontal, limbic, hippocampal, and motor subsystems."""
        return CognitiveSystemValidator.validate_causal_feedback_loop()

    def export_experiment_report(self, result: ExperimentResult, output_dir: Path) -> Path:
        """Save Markdown and JSON reports to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        md_file = output_dir / f"{result.experiment_id.lower()}_report.md"
        json_file = output_dir / f"{result.experiment_id.lower()}_data.json"

        md_file.write_text(result.report_markdown, encoding="utf-8")
        data = {
            "experiment_id": result.experiment_id,
            "name": result.name,
            "success": result.success,
            "summary": result.summary,
            "hypotheses": result.hypotheses,
            "metrics": result.metrics,
            "duration_seconds": result.duration_seconds,
        }
        json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return md_file
