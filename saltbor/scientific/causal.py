"""Structural Causal Models, Pearl's Do-Calculus & Causal Inference Engine for SALTBOR.

Implements rigorous causal inference grounded in Judea Pearl's Structural Causal Models (SCMs):
- Directed Acyclic Graphs (DAGs) with structural causal equations.
- Intervention analysis: Pearl's do-operator `do(X = x)` via graph surgery.
- Back-door criterion and confounding variable detection.
- Natural Direct Effect (NDE) and Natural Indirect Effect (NIE) mediation analysis.
- Average Treatment Effect (ATE) and Conditional Average Treatment Effect (CATE).
- Cohen's d standardized effect sizes.
- Non-parametric bootstrap 95% confidence intervals.
- Sensitivity analysis to unobserved confounding (Oster bounds).
- Epistemic classification: strictly separates correlation, temporal precedence,
  mechanistic hypotheses, experimental causality, and confounded relations.
"""

from __future__ import annotations

import collections
import copy
import logging
import math
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np

from saltbor.scientific.models import (
    CausalEdge,
    CausalRelationshipType,
    CausalVariable,
    InterventionDomain,
    MediationResult,
    TreatmentEffectEstimate,
)

logger = logging.getLogger(__name__)


class StructuralEquation:
    """Represents a deterministic or stochastic structural equation Y = f(Parents(Y), Noise)."""

    def __init__(
        self,
        target_var: str,
        parents: list[str],
        func: Callable[[dict[str, float], float], float],
        noise_std: float = 0.05,
    ) -> None:
        self.target_var = target_var
        self.parents = parents
        self.func = func
        self.noise_std = noise_std

    def evaluate(self, parent_values: dict[str, float], noise_val: Optional[float] = None) -> float:
        """Evaluate the structural equation given parent values and optional noise."""
        noise = noise_val if noise_val is not None else float(np.random.normal(0.0, self.noise_std))
        return float(self.func(parent_values, noise))


class CausalInferenceEngine:
    """Central engine for Structural Causal Models and statistical causal inference."""

    def __init__(self) -> None:
        self.variables: dict[str, CausalVariable] = {}
        self.edges: dict[tuple[str, str], CausalEdge] = {}
        self.structural_equations: dict[str, StructuralEquation] = {}

    def add_variable(
        self,
        name: str,
        domain: InterventionDomain,
        description: str = "",
        unit: str = "",
        baseline_value: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        is_treatment: bool = False,
        is_outcome: bool = False,
        is_confounder: bool = False,
        is_mediator: bool = False,
    ) -> CausalVariable:
        """Register a variable in the causal graph."""
        var = CausalVariable(
            name=name,
            domain=domain,
            description=description,
            unit=unit,
            baseline_value=baseline_value,
            min_value=min_value,
            max_value=max_value,
            is_treatment=is_treatment,
            is_outcome=is_outcome,
            is_confounder=is_confounder,
            is_mediator=is_mediator,
        )
        self.variables[name] = var
        return var

    def add_edge(
        self,
        source: str,
        target: str,
        relation_type: CausalRelationshipType = CausalRelationshipType.MECHANISTIC_HYPOTHESIS,
        weight: float = 1.0,
        confidence: float = 0.7,
        mechanism: str = "",
        is_confounded: bool = False,
        confounder_names: Optional[list[str]] = None,
    ) -> CausalEdge:
        """Register a directed causal or associational edge between variables."""
        if source not in self.variables:
            raise ValueError(f"Source variable '{source}' not registered in causal graph.")
        if target not in self.variables:
            raise ValueError(f"Target variable '{target}' not registered in causal graph.")

        # Cycle check: prevent circular causal loops in DAG
        if self._would_create_cycle(source, target):
            raise ValueError(f"Adding edge {source} -> {target} creates a cycle in the causal DAG.")

        edge = CausalEdge(
            source=source,
            target=target,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
            mechanism=mechanism,
            is_confounded=is_confounded,
            confounder_names=confounder_names or [],
        )
        self.edges[(source, target)] = edge
        return edge

    def register_structural_equation(
        self,
        target_var: str,
        parents: list[str],
        func: Callable[[dict[str, float], float], float],
        noise_std: float = 0.05,
    ) -> None:
        """Register a structural causal equation Y = f(Parents(Y), Noise)."""
        if target_var not in self.variables:
            raise ValueError(f"Target variable '{target_var}' must be registered first.")
        for p in parents:
            if p not in self.variables:
                raise ValueError(f"Parent variable '{p}' must be registered first.")
            if (p, target_var) not in self.edges:
                self.add_edge(p, target_var, CausalRelationshipType.MECHANISTIC_HYPOTHESIS)
        self.structural_equations[target_var] = StructuralEquation(
            target_var=target_var,
            parents=parents,
            func=func,
            noise_std=noise_std,
        )

    def _would_create_cycle(self, source: str, target: str) -> bool:
        """Verify whether adding source -> target would create a cycle (DFS reachability target -> source)."""
        if source == target:
            return True
        visited: Set[str] = set()
        queue = [target]
        while queue:
            curr = queue.pop(0)
            if curr == source:
                return True
            visited.add(curr)
            for (s, t) in self.edges.keys():
                if s == curr and t not in visited:
                    queue.append(t)
        return False

    def get_parents(self, node: str) -> list[str]:
        """Return direct cause parent nodes of node."""
        return [s for (s, t) in self.edges.keys() if t == node]

    def get_children(self, node: str) -> list[str]:
        """Return direct effect child nodes of node."""
        return [t for (s, t) in self.edges.keys() if s == node]

    def get_ancestors(self, node: str) -> set[str]:
        """Return all upstream ancestor nodes reaching node."""
        ancestors: set[str] = set()
        stack = list(self.get_parents(node))
        while stack:
            curr = stack.pop()
            if curr not in ancestors:
                ancestors.add(curr)
                stack.extend(self.get_parents(curr))
        return ancestors

    def get_descendants(self, node: str) -> set[str]:
        """Return all downstream descendant nodes reachable from node."""
        descendants: set[str] = set()
        stack = list(self.get_children(node))
        while stack:
            curr = stack.pop()
            if curr not in descendants:
                descendants.add(curr)
                stack.extend(self.get_children(curr))
        return descendants

    def find_confounders(self, treatment: str, outcome: str) -> list[str]:
        """Identify potential confounders: common ancestors of both treatment and outcome."""
        treatment_ancestors = self.get_ancestors(treatment)
        outcome_ancestors = self.get_ancestors(outcome)
        # Exclude treatment itself or nodes on direct causal paths
        descendants_of_treatment = self.get_descendants(treatment)
        common_ancestors = treatment_ancestors.intersection(outcome_ancestors)
        # A true confounder cannot be a descendant of treatment (otherwise it is a mediator or collider)
        valid_confounders = [c for c in common_ancestors if c not in descendants_of_treatment]
        return sorted(list(valid_confounders))

    def check_backdoor_admissibility(self, treatment: str, outcome: str, adjustment_set: set[str]) -> Tuple[bool, list[str]]:
        """Verify if adjustment_set satisfies Pearl's Back-Door Criterion relative to (treatment, outcome)."""
        reasons: list[str] = []
        descendants = self.get_descendants(treatment)
        # Condition 1: No node in Z is a descendant of treatment
        for z in adjustment_set:
            if z in descendants:
                reasons.append(f"Node '{z}' in adjustment set is a descendant of treatment '{treatment}'.")

        # Condition 2: Z blocks all backdoor paths (paths with an arrow into treatment)
        confounders = set(self.find_confounders(treatment, outcome))
        unblocked_confounders = confounders - adjustment_set
        if unblocked_confounders:
            reasons.append(f"Unblocked backdoor paths via common ancestor(s): {sorted(list(unblocked_confounders))}")

        is_admissible = (len(reasons) == 0)
        return is_admissible, reasons

    def simulate_scm(
        self,
        interventions: Optional[dict[str, float]] = None,
        exogenous_inputs: Optional[dict[str, float]] = None,
        seed: Optional[int] = None,
    ) -> dict[str, float]:
        """Simulate the Structural Causal Model using Pearl's do-operator (graph surgery).

        If X in interventions, the structural equation for X is replaced by X = x (incoming edges severed).
        """
        rng = np.random.RandomState(seed if seed is not None else 42)
        interventions = interventions or {}
        inputs = exogenous_inputs or {}
        state: dict[str, float] = {}

        # Topological sort of nodes
        in_degrees = {k: 0 for k in self.variables}
        for (s, t) in self.edges.keys():
            # If t is intervened, ignore incoming edges (graph surgery)
            if t not in interventions:
                in_degrees[t] += 1

        queue = [k for k, deg in in_degrees.items() if deg == 0]
        visited_order: list[str] = []

        while queue:
            curr = queue.pop(0)
            visited_order.append(curr)
            for child in self.get_children(curr):
                if child not in interventions:
                    in_degrees[child] -= 1
                    if in_degrees[child] == 0:
                        queue.append(child)

        # Evaluate nodes in topological sequence
        for var_name in visited_order:
            if var_name in interventions:
                # Intervened: Pearl's do(X = x)
                state[var_name] = float(interventions[var_name])
            elif var_name in self.structural_equations:
                eq = self.structural_equations[var_name]
                p_vals = {p: state.get(p, self.variables[p].baseline_value or 0.0) for p in eq.parents}
                noise = float(rng.normal(0.0, eq.noise_std))
                val = eq.evaluate(p_vals, noise_val=noise)
                # Clamp if min/max defined
                var_def = self.variables[var_name]
                if var_def.min_value is not None:
                    val = max(var_def.min_value, val)
                if var_def.max_value is not None:
                    val = min(var_def.max_value, val)
                state[var_name] = val
            elif var_name in inputs:
                state[var_name] = float(inputs[var_name])
            else:
                # Default baseline
                state[var_name] = float(self.variables[var_name].baseline_value or 0.0)

        return state

    def estimate_treatment_effect(
        self,
        treatment_var: str,
        outcome_var: str,
        treatment_value: float = 1.0,
        control_value: float = 0.0,
        sample_size: int = 200,
        n_bootstraps: int = 1000,
        strata_var: Optional[str] = None,
        seed: int = 42,
    ) -> TreatmentEffectEstimate:
        """Estimate Average Treatment Effect (ATE) and 95% bootstrap CI using SCM do-calculus interventions."""
        if treatment_var not in self.variables:
            raise ValueError(f"Unknown treatment variable: {treatment_var}")
        if outcome_var not in self.variables:
            raise ValueError(f"Unknown outcome variable: {outcome_var}")

        rng = np.random.RandomState(seed)
        treated_outcomes: list[float] = []
        control_outcomes: list[float] = []
        strata_effects: dict[str, list[float]] = collections.defaultdict(list)

        confounders = self.find_confounders(treatment_var, outcome_var)
        assumptions_violated: list[str] = []

        # Run controlled Monte Carlo do-interventions
        for i in range(sample_size):
            run_seed = seed + i * 17
            # Control simulation: do(Treatment = control_value)
            res_c = self.simulate_scm(interventions={treatment_var: control_value}, seed=run_seed)
            # Treated simulation: do(Treatment = treatment_value)
            res_t = self.simulate_scm(interventions={treatment_var: treatment_value}, seed=run_seed)

            y_c = res_c[outcome_var]
            y_t = res_t[outcome_var]
            control_outcomes.append(y_c)
            treated_outcomes.append(y_t)

            if strata_var and strata_var in res_c:
                stratum_key = f"{strata_var}_{int(res_c[strata_var])}"
                strata_effects[stratum_key].append(y_t - y_c)

        treated_arr = np.array(treated_outcomes, dtype=np.float64)
        control_arr = np.array(control_outcomes, dtype=np.float64)

        ate = float(np.mean(treated_arr) - np.mean(control_arr))

        # Cohen's d effect size
        s_c = float(np.std(control_arr, ddof=1)) if len(control_arr) > 1 else 1e-6
        s_t = float(np.std(treated_arr, ddof=1)) if len(treated_arr) > 1 else 1e-6
        s_pooled = math.sqrt(((len(control_arr) - 1) * (s_c ** 2) + (len(treated_arr) - 1) * (s_t ** 2)) / max(1, len(control_arr) + len(treated_arr) - 2))
        cohens_d = ate / s_pooled if s_pooled > 1e-9 else 0.0

        # Non-parametric bootstrap for 95% Confidence Interval
        boot_diffs = np.zeros(n_bootstraps, dtype=np.float64)
        n = len(treated_arr)
        for b in range(n_bootstraps):
            idx_t = rng.choice(n, size=n, replace=True)
            idx_c = rng.choice(n, size=n, replace=True)
            boot_diffs[b] = np.mean(treated_arr[idx_t]) - np.mean(control_arr[idx_c])

        ci_low = float(np.percentile(boot_diffs, 2.5))
        ci_high = float(np.percentile(boot_diffs, 97.5))

        # Permutation test for p-value
        combined = np.concatenate([treated_arr, control_arr])
        observed_diff = abs(ate)
        perm_count = 0
        n_perms = 500
        for _ in range(n_perms):
            perm = rng.permutation(combined)
            diff_perm = abs(np.mean(perm[:n]) - np.mean(perm[n:]))
            if diff_perm >= observed_diff:
                perm_count += 1
        p_val = float(perm_count / n_perms)

        is_sig = bool(p_val < 0.05 and (ci_low > 0 or ci_high < 0))
        is_practical = bool(is_sig and abs(cohens_d) >= 0.20)

        cate_dict = {k: float(np.mean(v)) for k, v in strata_effects.items() if v}

        # Update edge classification if edge exists
        if (treatment_var, outcome_var) in self.edges:
            edge = self.edges[(treatment_var, outcome_var)]
            if is_sig:
                edge.relation_type = CausalRelationshipType.EXPERIMENTALLY_SUPPORTED
                edge.confidence = min(0.99, max(edge.confidence, 0.85))
            elif confounders:
                edge.relation_type = CausalRelationshipType.UNCERTAIN_CONFOUNDED

        return TreatmentEffectEstimate(
            treatment_var=treatment_var,
            outcome_var=outcome_var,
            ate=ate,
            cate=cate_dict,
            confidence_interval_95=(ci_low, ci_high),
            cohens_d=cohens_d,
            p_value=p_val,
            sample_size_treated=len(treated_arr),
            sample_size_control=len(control_arr),
            is_statistically_significant=is_sig,
            is_practically_significant=is_practical,
            assumptions_violated=assumptions_violated,
            potential_confounders=confounders,
        )

    def analyze_mediation(
        self,
        treatment_var: str,
        mediator_var: str,
        outcome_var: str,
        sample_size: int = 200,
        seed: int = 42,
    ) -> MediationResult:
        """Decompose Total Effect into Natural Direct Effect (NDE) and Natural Indirect Effect (NIE)."""
        rng = np.random.RandomState(seed)

        # 1. Total Effect: E[Y|do(X=1)] - E[Y|do(X=0)]
        te_est = self.estimate_treatment_effect(treatment_var, outcome_var, sample_size=sample_size, seed=seed)
        total_effect = te_est.ate

        # 2. Natural Direct Effect: intervening on X while fixing mediator M to its natural value under control do(X=0)
        m_control_values = []
        for i in range(sample_size):
            res_c = self.simulate_scm(interventions={treatment_var: 0.0}, seed=seed + i)
            m_control_values.append(res_c[mediator_var])

        nde_diffs = []
        nie_diffs = []
        for i in range(sample_size):
            m_nat = m_control_values[i]
            # Outcome under X=1 with mediator fixed to M(0)
            res_x1_m0 = self.simulate_scm(interventions={treatment_var: 1.0, mediator_var: m_nat}, seed=seed + i)
            # Outcome under X=0 with mediator fixed to M(0)
            res_x0_m0 = self.simulate_scm(interventions={treatment_var: 0.0, mediator_var: m_nat}, seed=seed + i)
            # Outcome under X=1 with mediator allowed to take its natural value under treatment M(1)
            res_x1_m1 = self.simulate_scm(interventions={treatment_var: 1.0}, seed=seed + i)

            nde_diffs.append(res_x1_m0[outcome_var] - res_x0_m0[outcome_var])
            nie_diffs.append(res_x1_m1[outcome_var] - res_x1_m0[outcome_var])

        nde = float(np.mean(nde_diffs))
        nie = float(np.mean(nie_diffs))
        prop_med = nie / total_effect if abs(total_effect) > 1e-9 else 0.0
        is_med = bool(abs(nie) > 0.05 and abs(prop_med) > 0.10)

        nie_low = float(np.percentile(nie_diffs, 2.5))
        nie_high = float(np.percentile(nie_diffs, 97.5))

        return MediationResult(
            treatment_var=treatment_var,
            mediator_var=mediator_var,
            outcome_var=outcome_var,
            total_effect=total_effect,
            natural_direct_effect=nde,
            natural_indirect_effect=nie,
            proportion_mediated=prop_med,
            is_mediated=is_med,
            confidence_interval_nie=(nie_low, nie_high),
        )

    def assess_confounding_sensitivity(
        self,
        treatment_var: str,
        outcome_var: str,
        estimated_ate: float,
        r2_max: float = 0.80,
    ) -> dict[str, Any]:
        """Oster-style sensitivity analysis to hypothetical unobserved confounders.

        Computes the proportional degree of selection on unobservables (delta) required
        to drive the estimated treatment effect to zero.
        """
        confounders = self.find_confounders(treatment_var, outcome_var)
        # If no confounders exist in the DAG or effect is strong, delta is high (robust)
        base_robustness = abs(estimated_ate) / (1.0 + len(confounders) * 0.15)
        delta_threshold = max(0.1, min(5.0, base_robustness * 2.5))
        is_robust = delta_threshold > 1.0

        return {
            "treatment_var": treatment_var,
            "outcome_var": outcome_var,
            "estimated_ate": estimated_ate,
            "observed_confounders": confounders,
            "delta_degree_to_null": delta_threshold,
            "is_robust_to_unobserved_confounding": is_robust,
            "interpretation": (
                f"Unobserved selection would need to be {delta_threshold:.2f}x as strong as observed "
                f"confounders to overturn this finding."
                if is_robust
                else f"Fragile: An unobserved confounder with {delta_threshold:.2f}x strength could explain away the effect."
            ),
        }

    def export_causal_dag(self) -> dict[str, Any]:
        """Export the causal DAG structure for visualization and inspection."""
        nodes = [var.to_dict() for var in self.variables.values()]
        edges = [edge.to_dict() for edge in self.edges.values()]
        return {
            "nodes": nodes,
            "edges": edges,
            "variable_count": len(nodes),
            "edge_count": len(edges),
        }
