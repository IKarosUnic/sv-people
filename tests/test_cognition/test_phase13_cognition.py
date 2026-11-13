"""Unit and Integration tests for SALTBOR Phase 1.3 Cognitive Engines."""

import numpy as np
import pytest

from saltbor.cognition.development.profile import (
    CognitiveCapability,
    CognitiveProfile,
)
from saltbor.cognition.development.meta_learning import (
    LearningStrategy,
    MetaLearningEngine,
)
from saltbor.cognition.development.plasticity import (
    CognitivePlasticityEngine,
    SkillDomainTransferMatrix,
)
from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.scientific_thinking import (
    ScientificThinkingEngine,
)
from saltbor.institutions.education import (
    DistributedEducationEngine,
    EducationalInstitutionType,
    EducationalRole,
)
from saltbor.cognition.problem_solving.collective import (
    CollectiveProblemSolvingEngine,
    Problem,
    ProblemOutcome,
    TeamMemberRole,
)
from saltbor.population.human import SyntheticHuman


def test_cognitive_profile_14_capabilities_and_budget():
    """Verify that CognitiveProfile maintains all 14 capabilities and enforces budget constraint."""
    profile = CognitiveProfile.create_default(human_uid="agent_test", age=30.0, rng=np.random.default_rng(42))
    assert len(profile.capabilities) == 14
    for cap in CognitiveCapability:
        lvl = profile.get_level(cap)
        assert 0.05 <= lvl <= 1.0

    # Total budget constraint
    total_levels = sum(m.current_level for m in profile.capabilities.values())
    assert total_levels <= profile.cognitive_budget_capacity + 0.01

    # Training one capability increases it and causes mild trade-offs on unpracticed ones
    initial_proc = profile.get_level(CognitiveCapability.PROCEDURAL_LEARNING)
    for t in range(30):
        profile.train_capability(CognitiveCapability.PROCEDURAL_LEARNING, effort_intensity=1.0, current_tick=t)
    profile.rest_and_recover()
    final_proc = profile.get_level(CognitiveCapability.PROCEDURAL_LEARNING)
    assert final_proc > initial_proc


def test_meta_learning_strategy_selection_and_switching():
    """Verify that MetaLearningEngine switches away from failing strategies."""
    meta = MetaLearningEngine(human_uid="meta_test")
    profile = CognitiveProfile.create_default("meta_test")

    # Initial preference
    initial_pref = meta.current_preferred_strategy

    # Simulate repeated failures on trial and error
    for t in range(5):
        meta.register_learning_outcome(
            strategy=LearningStrategy.TRIAL_AND_ERROR,
            task_domain="textiles",
            xp_gained=0.1,
            duration_ticks=2,
            was_successful=False,
            current_tick=t,
        )

    # Should detect need to seek help or switch
    assert meta.should_seek_help("textiles") is True

    # Register high success with deliberate practice
    for t in range(5):
        meta.register_learning_outcome(
            strategy=LearningStrategy.DELIBERATE_PRACTICE,
            task_domain="textiles",
            xp_gained=5.0,
            duration_ticks=2,
            was_successful=True,
            current_tick=10 + t,
        )

    best = meta.select_best_strategy("textiles", profile, mentor_available=False, peers_available=False)
    assert best == LearningStrategy.DELIBERATE_PRACTICE


def test_plasticity_and_divergence_metrics():
    """Verify practice curve diminishing returns and 14D divergence metric."""
    engine = CognitivePlasticityEngine()

    gain_early = engine.calculate_practice_gain(0.25, 4.0, 0.6, 0.6, 0.6)
    gain_late = engine.calculate_practice_gain(0.85, 4.0, 0.6, 0.6, 0.6)
    assert gain_early > gain_late * 2.0

    prof_a = CognitiveProfile.create_default("a", rng=np.random.default_rng(1))
    prof_b = CognitiveProfile.create_default("b", rng=np.random.default_rng(2))
    div = engine.compute_divergence_metric(prof_a, prof_b)
    assert "l2_distance" in div
    assert "l1_distance" in div
    assert div["l2_distance"] >= 0.0


def test_scientific_thinking_cycle():
    """Verify the 8-stage scientific thinking cycle."""
    engine = ScientificThinkingEngine(rng=np.random.default_rng(42))
    agent = SyntheticHuman.create(name="Investigador Juan", seed=42)

    session = engine.start_investigation(str(agent.uid), "Observacion anomala de suelo", tick=1)
    engine.formulate_question(session, "suelo", "humedad", tick=2)
    hyp = engine.generate_hypothesis(session, "mulch", "retiene_humedad", 0.4, tick=3)
    exp = engine.design_experiment(session, "mulch", 1.0, 0.0, trials=3, tick=4)

    engine.run_experimental_trials(session, true_causal_effect=1.5, noise_std=0.1, tick=5)
    outcome, final_belief = engine.evaluate_and_revise(session, true_causal_effect=1.5, cognitive_profile=agent.cognitive_profile, tick=6)

    assert len(session.cycle_history) >= 6
    assert outcome == "supported"
    assert final_belief.belief_type in (BeliefType.VERIFIED_KNOWLEDGE, BeliefType.PROVISIONAL_KNOWLEDGE)


def test_distributed_education_workshop_and_roles():
    """Verify that DistributedEducationEngine creates spontaneous workshops and assigns roles."""
    edu = DistributedEducationEngine(rng=np.random.default_rng(42))
    candidates = [
        {"uid": "maestro_1", "skill_level": 0.80, "prestige": 0.70, "money": 60.0, "age": 45},
        {"uid": "joven_1", "skill_level": 0.10, "prestige": 0.20, "money": 10.0, "age": 18},
        {"uid": "joven_2", "skill_level": 0.15, "prestige": 0.25, "money": 15.0, "age": 20},
    ]
    workshop = edu.check_spontaneous_institution_emergence(
        location_id="taller_barro",
        community_need_domain="pottery",
        candidates=candidates,
        collective_treasury=50.0,
        tick=1,
    )
    assert workshop is not None
    assert workshop.institution_type == EducationalInstitutionType.WORKSHOP
    assert edu.get_role("maestro_1") == EducationalRole.TEACHER
    assert edu.get_role("joven_1") == EducationalRole.APPRENTICE


def test_collective_problem_solving_groupthink_detection():
    """Verify that collective problem solving detects flawed proposals and groupthink."""
    solver = CollectiveProblemSolvingEngine()
    prob = Problem(
        problem_id="p1",
        description="Market liquidity deficit",
        domain="trade",
        current_state={"liquidity": 0.0},
        desired_state={"liquidity": 50.0},
        constraints={"max_cost": 20.0},
        difficulty=0.5,
        required_capabilities=["trade"],
    )
    team = [
        TeamMemberRole("c1", "coordination", "manage", trust_level=0.9),
        TeamMemberRole("s1", "trade", "execute", trust_level=0.95),
    ]

    report = solver.solve_collectively(prob, team, tick=1, inject_flawed_hypothesis_uid="s1")
    assert report.final_outcome == ProblemOutcome.FAILED
    assert "groupthink" in " ".join(report.shared_learnings).lower()
