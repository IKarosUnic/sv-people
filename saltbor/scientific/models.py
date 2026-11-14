"""Scientific Experimentation and Causal Inference Models for SALTBOR Phase 1.12.

Provides domain contracts, enums, and dataclasses for:
- Controlled, observational, longitudinal, comparative, and counterfactual experiments.
- Structural Causal Models (SCMs), causal DAGs, do-calculus interventions.
- Treatment effects (ATE, CATE), mediation analysis, bootstrap confidence intervals.
- Parameter sensitivity sweeps and elementary effects.
- Multi-tier causal event traceability.
- Stratified population sampling.
- Scientific validation tiers and external comparator matrices.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import math
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4


class ExperimentType(str, Enum):
    """Categorization of scientific experiments."""
    CONTROLLED = "controlled"
    OBSERVATIONAL = "observational"
    LONGITUDINAL = "longitudinal"
    COMPARATIVE = "comparative"
    COUNTERFACTUAL = "counterfactual"
    ABLATION = "ablation"


class InterventionDomain(str, Enum):
    """Domain of intervention or treatment applied to the simulation."""
    ENVIRONMENTAL = "environmental"
    ECONOMIC = "economic"
    SOCIAL = "social"
    INSTITUTIONAL = "institutional"
    DEMOGRAPHIC = "demographic"
    CULTURAL = "cultural"


class CausalRelationshipType(str, Enum):
    """Epistemic classification of variable relationships."""
    CORRELATION = "correlation"                         # Mere statistical co-occurrence
    TEMPORAL_ASSOCIATION = "temporal_association"       # Precedes in time, but unverified mechanism
    MECHANISTIC_HYPOTHESIS = "mechanistic_hypothesis"   # Plausible structural theory, unverified
    EXPERIMENTALLY_SUPPORTED = "experimentally_supported"# Supported by do-calculus intervention
    UNCERTAIN_CONFOUNDED = "uncertain_confounded"       # Apparent relationship confounded by third variable


class EvidenceValidationTier(str, Enum):
    """Formal tier of scientific evidence validity."""
    IMPLEMENTED = "IMPLEMENTED"                         # Code exists and runs
    TESTED = "TESTED"                                   # Unit and integration tests pass
    EXPERIMENTALLY_EVALUATED = "EXPERIMENTALLY_EVALUATED"# Tested via multi-seed experimental protocol
    EMPIRICALLY_CALIBRATED = "EMPIRICALLY_CALIBRATED"   # Calibrated against external observed ranges
    EXTERNALLY_VALIDATED = "EXTERNALLY_VALIDATED"       # Statistically validated against empirical datasets


class SensitivityClass(str, Enum):
    """Classification of parameter sensitivity behavior."""
    ROBUST = "robust"                                   # Output stable across variations
    FRAGILE = "fragile"                                 # Output sharply sensitive to minor shifts
    NON_LINEAR = "non_linear"                           # Discontinuous or exponential response
    INTERACTIVE = "interactive"                         # Strongly dependent on other parameters
    UNCERTAIN = "uncertain"                             # Insufficient evidence to classify


class CausalTraceTier(str, Enum):
    """9-tier causal event hierarchy for deep retrospective tracing."""
    TIER_1_INITIAL_CONDITIONS = "tier_1_initial_conditions"
    TIER_2_ENVIRONMENTAL_CHANGE = "tier_2_environmental_change"
    TIER_3_HUMAN_DECISION = "tier_3_human_decision"
    TIER_4_SOCIAL_INTERACTION = "tier_4_social_interaction"
    TIER_5_ECONOMIC_TRANSACTION = "tier_5_economic_transaction"
    TIER_6_INSTITUTIONAL_DECISION = "tier_6_institutional_decision"
    TIER_7_PRIMARY_CONSEQUENCE = "tier_7_primary_consequence"
    TIER_8_SECONDARY_CONSEQUENCE = "tier_8_secondary_consequence"
    TIER_9_HISTORICAL_OUTCOME = "tier_9_historical_outcome"


class CausalLinkQuality(str, Enum):
    """Epistemic status of a link between two simulation events."""
    DIRECT_CAUSE = "direct_cause"                       # Necessary and sufficient in model state
    CONTRIBUTING_FACTOR = "contributing_factor"         # Modulates probability or magnitude
    INDIRECT_EFFECT = "indirect_effect"                 # Transmitted through intermediate causal mediators
    COINCIDENTAL_CO_OCCURRENCE = "coincidental"         # Simultaneous without causal connection


@dataclasses.dataclass
class CausalVariable:
    """A variable in a Structural Causal Model (SCM)."""
    name: str
    domain: InterventionDomain
    is_observable: bool = True
    description: str = ""
    unit: str = ""
    baseline_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_treatment: bool = False
    is_outcome: bool = False
    is_confounder: bool = False
    is_mediator: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class CausalEdge:
    """A directed edge in a Structural Causal Model DAG."""
    source: str
    target: str
    relation_type: CausalRelationshipType
    weight: float = 1.0                                 # Estimated path strength
    confidence: float = 0.5                             # [0.0, 1.0] confidence
    mechanism: str = ""                                 # Narrative or formulaic mechanism
    is_confounded: bool = False
    confounder_names: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TreatmentEffectEstimate:
    """Statistical outcome of causal treatment effect estimation."""
    treatment_var: str
    outcome_var: str
    ate: float                                          # Average Treatment Effect: E[Y|do(X=1)] - E[Y|do(X=0)]
    cate: dict[str, float] = dataclasses.field(default_factory=dict) # Conditional ATE by stratum
    confidence_interval_95: tuple[float, float] = (0.0, 0.0) # Bootstrap 95% CI
    cohens_d: float = 0.0                               # Standardized effect size
    p_value: float = 1.0                                # Permutation or t-test p-value
    sample_size_treated: int = 0
    sample_size_control: int = 0
    is_statistically_significant: bool = False
    is_practically_significant: bool = False            # True if |d| > 0.2 and p < 0.05
    assumptions_violated: list[str] = dataclasses.field(default_factory=list)
    potential_confounders: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["confidence_interval_95"] = list(self.confidence_interval_95)
        return d


@dataclasses.dataclass
class MediationResult:
    """Decomposition of total effect into direct and indirect effects."""
    treatment_var: str
    mediator_var: str
    outcome_var: str
    total_effect: float                                 # TE = NDE + NIE
    natural_direct_effect: float                        # NDE (effect without mediator)
    natural_indirect_effect: float                      # NIE (effect transmitted through mediator)
    proportion_mediated: float                          # NIE / TE
    is_mediated: bool = False
    confidence_interval_nie: tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["confidence_interval_nie"] = list(self.confidence_interval_nie)
        return d


@dataclasses.dataclass
class StratifiedSampleSpec:
    """Specification for representative population and geographic sampling."""
    sample_size: int = 50
    departments: list[str] = dataclasses.field(default_factory=list) # Specific depts or all 14
    urban_rural_ratio: Optional[float] = None           # e.g. 0.62 urban / 0.38 rural
    wealth_quintiles: list[int] = dataclasses.field(default_factory=lambda: [1, 2, 3, 4, 5])
    age_cohorts: list[str] = dataclasses.field(default_factory=lambda: ["youth", "working_age", "elderly"])
    gender_balance: bool = True
    occupations: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ScientificExperimentProtocol:
    """Formal protocol definition for an experiment."""
    protocol_id: str
    name: str
    research_question: str
    hypotheses: list[str]
    experiment_type: ExperimentType
    domain: InterventionDomain
    independent_variables: list[str]
    dependent_variables: list[str]
    control_variables: list[str]
    treatment_definition: dict[str, Any]
    sampling_spec: StratifiedSampleSpec
    geographic_scope: str = "El Salvador"
    duration_ticks: int = 96
    random_seeds: list[int] = dataclasses.field(default_factory=lambda: [42, 101, 202, 303, 404])
    measurement_methodology: str = ""
    data_provenance: str = "SALTBOR Local Synthetic Engine"
    expected_limitations: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["sampling_spec"] = self.sampling_spec.to_dict()
        return d


@dataclasses.dataclass
class SingleRunResult:
    """Outcome of a single experiment run on a specific seed."""
    run_id: str
    seed: int
    duration_seconds: float
    success: bool
    metrics: dict[str, Any]
    hypotheses_confirmed: dict[str, bool]
    anomalies: list[str] = dataclasses.field(default_factory=list)
    event_counts: dict[str, int] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class MultiSeedExperimentResult:
    """Aggregated outcome of an experiment evaluated across multiple seeds."""
    protocol_id: str
    name: str
    experiment_type: ExperimentType
    domain: InterventionDomain
    seeds_evaluated: list[int]
    total_runs: int
    successful_runs: int
    failure_rate: float
    duration_seconds_total: float
    hypotheses_status: dict[str, dict[str, Any]]        # hypothesis -> {confirmed_count, rate, confirmed}
    summary_statistics: dict[str, dict[str, float]]     # metric -> {mean, median, std, var, ci_95_low, ci_95_high, min, max}
    outlier_runs: list[int]                             # Seeds identified as statistical outliers
    runs: list[SingleRunResult] = dataclasses.field(default_factory=list)
    causal_estimates: dict[str, TreatmentEffectEstimate] = dataclasses.field(default_factory=dict)
    limitations_noted: list[str] = dataclasses.field(default_factory=list)
    validation_tier: EvidenceValidationTier = EvidenceValidationTier.EXPERIMENTALLY_EVALUATED

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "experiment_type": self.experiment_type.value,
            "domain": self.domain.value,
            "seeds_evaluated": self.seeds_evaluated,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failure_rate": self.failure_rate,
            "duration_seconds_total": self.duration_seconds_total,
            "hypotheses_status": self.hypotheses_status,
            "summary_statistics": self.summary_statistics,
            "outlier_runs": self.outlier_runs,
            "runs": [r.to_dict() for r in self.runs],
            "causal_estimates": {k: v.to_dict() for k, v in self.causal_estimates.items()},
            "limitations_noted": self.limitations_noted,
            "validation_tier": self.validation_tier.value,
        }


@dataclasses.dataclass
class SensitivitySweepResult:
    """Result of systematic parameter sensitivity analysis."""
    parameter_name: str
    baseline_value: float
    tested_values: list[float]
    outcome_metrics: list[str]
    responses: dict[str, list[float]]                   # metric -> list of mean values per tested param
    elasticities: dict[str, float]                      # metric -> % delta metric / % delta parameter
    sensitivity_class: SensitivityClass
    is_monotonic: bool
    has_threshold_inflection: bool
    inflection_point: Optional[float] = None
    narrative_conclusion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_name": self.parameter_name,
            "baseline_value": self.baseline_value,
            "tested_values": self.tested_values,
            "outcome_metrics": self.outcome_metrics,
            "responses": self.responses,
            "elasticities": self.elasticities,
            "sensitivity_class": self.sensitivity_class.value,
            "is_monotonic": self.is_monotonic,
            "has_threshold_inflection": self.has_threshold_inflection,
            "inflection_point": self.inflection_point,
            "narrative_conclusion": self.narrative_conclusion,
        }


@dataclasses.dataclass
class CounterfactualTrajectoryComparison:
    """Comparative analysis of baseline history vs counterfactual history."""
    scenario_id: str
    scenario_name: str
    intervention_tick: int
    intervention_description: str
    altered_parameters: dict[str, Any]
    baseline_seed: int
    timesteps: list[int]                                # Ticks evaluated
    baseline_metrics: dict[str, list[float]]            # metric -> trajectory values
    counterfactual_metrics: dict[str, list[float]]      # metric -> trajectory values
    divergence_point_tick: int                          # Tick where trajectory diverged > 5%
    total_trajectory_divergence: dict[str, float]       # metric -> L2 or area divergence
    qualitative_divergence: str = ""
    confounding_factors: list[str] = dataclasses.field(default_factory=list)
    limitations: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class CausalTraceStep:
    """A single node/step in the 9-tier causal event trace."""
    step_id: str
    event_id: str
    tick: int
    tier: CausalTraceTier
    description: str
    entity_id: Optional[str] = None
    location_id: Optional[str] = None
    link_to_next: CausalLinkQuality = CausalLinkQuality.DIRECT_CAUSE
    contributing_factors: list[str] = dataclasses.field(default_factory=list)
    mechanism_explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "event_id": self.event_id,
            "tick": self.tick,
            "tier": self.tier.value,
            "description": self.description,
            "entity_id": self.entity_id,
            "location_id": self.location_id,
            "link_to_next": self.link_to_next.value,
            "contributing_factors": self.contributing_factors,
            "mechanism_explanation": self.mechanism_explanation,
        }


@dataclasses.dataclass
class MultiTierCausalTrace:
    """Complete multi-tier causal narrative and chain for a simulation event."""
    target_event_id: str
    target_description: str
    target_tick: int
    steps: list[CausalTraceStep] = dataclasses.field(default_factory=list)
    root_cause_summary: str = ""
    direct_causes_count: int = 0
    contributing_factors_count: int = 0
    coincidental_events_filtered: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_event_id": self.target_event_id,
            "target_description": self.target_description,
            "target_tick": self.target_tick,
            "steps": [s.to_dict() for s in self.steps],
            "root_cause_summary": self.root_cause_summary,
            "direct_causes_count": self.direct_causes_count,
            "contributing_factors_count": self.contributing_factors_count,
            "coincidental_events_filtered": self.coincidental_events_filtered,
        }
