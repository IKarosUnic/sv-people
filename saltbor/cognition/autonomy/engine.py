"""Autonomy engine — intrinsic goal generation, prioritization, and self-direction.

Allows synthetic humans to formulate their own goals driven by physical needs,
financial circumstances, skill deficits, social relationships, and emotional motivations,
rather than executing fixed developer scripts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import GoalID, HumanID, LocationID, NeedType, SkillID, Tick


@dataclass
class Goal:
    """An autonomous objective formulated by an individual."""

    goal_id: GoalID = field(default_factory=uuid.uuid4)
    description: str = ""
    priority: float = 0.5            # 0.0 to 1.0
    need_type: Optional[NeedType] = None
    category: str = "general"        # 'biological', 'financial', 'skill', 'social', 'reconciliation', 'recreation'
    progress: float = 0.0            # 0.0 (started) to 1.0 (completed)
    deadline_tick: Optional[Tick] = None
    status: str = "active"           # 'active', 'completed', 'abandoned', 'procrastinated', 'modified'
    plan_steps: list[str] = field(default_factory=list)
    plan_actions: list[Any] = field(default_factory=list)
    current_step_index: int = 0
    feasibility: float = 0.8
    target_human_id: Optional[HumanID] = None
    target_location_id: Optional[LocationID] = None
    target_skill_id: Optional[SkillID] = None
    consecutive_failures: int = 0
    procrastination_count: int = 0
    created_tick: Tick = 0
    reasoning: str = ""
    # Phase 0.7 Open-Ended Autonomous Goal Hierarchy & Diversity Extensions
    parent_goal_id: Optional[GoalID] = None
    subgoal_ids: list[GoalID] = field(default_factory=list)
    time_horizon: str = "medium_term"  # 'short_term', 'medium_term', 'long_term'
    driver: str = "biological"         # One of the 11 Phase 0.7 motivation drivers
    competing_conflicts: list[GoalID] = field(default_factory=list)

    def set_action_plan(self, actions: list[Any]) -> None:
        """Assign formal GOAP/HTN action sequence."""
        self.plan_actions = list(actions)
        self.plan_steps = [getattr(a, "name", str(a)) for a in actions]
        self.current_step_index = 0

    def replan(self, new_actions: list[Any], reason: str = "") -> None:
        """Dynamically replace plan sequence upon failed precondition."""
        self.set_action_plan(new_actions)
        self.status = "modified"
        self.consecutive_failures = 0
        if reason:
            self.reasoning += f" [Replanned: {reason}]"

    def advance(self, delta: float) -> None:
        """Advance progress and update current step."""
        self.progress = min(1.0, self.progress + delta)
        if self.plan_steps:
            # Advance through step indices as progress increases
            step_target = int(self.progress * len(self.plan_steps))
            self.current_step_index = min(len(self.plan_steps) - 1, step_target)
        if self.progress >= 1.0:
            self.status = "completed"

    def procrastinate(self) -> None:
        """Temporarily suspend active pursuit due to fatigue, hesitation, or low urgency."""
        self.status = "procrastinated"
        self.procrastination_count += 1
        self.priority = max(0.1, self.priority * 0.85)

    def resume(self) -> None:
        """Re-activate a procrastinated goal."""
        self.status = "active"

    def modify(self, new_description: str, new_plan_steps: Optional[list[str]] = None) -> None:
        """Adapt the objective after encountering obstacles."""
        self.description = new_description
        if new_plan_steps is not None:
            self.plan_steps = new_plan_steps
            self.current_step_index = 0
        self.status = "modified"
        self.consecutive_failures = 0

    def abandon(self, reason: str = "") -> None:
        """Abandon objective when no longer feasible or relevant."""
        self.status = "abandoned"
        if reason:
            self.reasoning += f" [Abandoned: {reason}]"


class AutonomyEngine:
    """Self-direction, intrinsic motivation, and goal lifecycle management."""

    def __init__(self) -> None:
        self._goals: dict[GoalID, Goal] = {}
        self.completed_goals_history: list[Goal] = []

    @property
    def goals(self) -> list[Goal]:
        """Return list of all goals across all states."""
        return list(self._goals.values())

    def get_active_goals(self) -> list[Goal]:
        """Return all active (and modified) goals sorted by priority (descending)."""
        active = [g for g in self._goals.values() if g.status in ("active", "modified")]
        return sorted(active, key=lambda g: g.priority, reverse=True)

    def current_primary_goal(self) -> Optional[Goal]:
        """Return highest-priority active goal."""
        active = self.get_active_goals()
        return active[0] if active else None

    def add_goal(self, goal: Goal) -> None:
        """Register a new autonomous goal."""
        self._goals[goal.goal_id] = goal

    def get_goal(self, goal_id: GoalID) -> Optional[Goal]:
        return self._goals.get(goal_id)

    def complete_goal(self, goal_id: GoalID) -> None:
        if goal_id in self._goals:
            self._goals[goal_id].status = "completed"
            self._goals[goal_id].progress = 1.0
            self.completed_goals_history.append(self._goals[goal_id])

    def abandon_goal(self, goal_id: GoalID, reason: str = "") -> None:
        if goal_id in self._goals:
            self._goals[goal_id].abandon(reason)

    def generate_goals_from_needs(
        self,
        needs: dict[NeedType, float],
        personality: PersonalityEngine,
        current_tick: Tick,
        money: Optional[float] = None,
        skills: Optional[list[Any]] = None,
        emotions: Optional[EmotionalEngine] = None,
    ) -> list[Goal]:
        """Formulate personal goals to address urgent deficits or pursue aspirations."""
        new_goals: list[Goal] = []
        active_goals = self.get_active_goals()
        existing_categories = {g.category for g in active_goals}
        existing_needs = {g.need_type for g in active_goals if g.need_type}

        # 1. Biological survival needs (Hunger & Rest)
        hunger = needs.get(NeedType.HUNGER, 0.0)
        if hunger > 0.50 and NeedType.HUNGER not in existing_needs:
            urgency = min(1.0, 0.4 + hunger * 0.6)
            goal = Goal(
                description="Obtain and eat food",
                priority=urgency,
                need_type=NeedType.HUNGER,
                category="biological",
                plan_steps=["find_food_source", "consume_meal", "satiate_hunger"],
                deadline_tick=current_tick + 32,
                created_tick=current_tick,
                reasoning=f"High biological hunger ({hunger:.2f})",
            )
            self.add_goal(goal)
            new_goals.append(goal)

        energy_deficit = needs.get(NeedType.REST, 0.0)
        if energy_deficit > 0.55 and NeedType.REST not in existing_needs:
            urgency = min(1.0, 0.4 + energy_deficit * 0.6)
            goal = Goal(
                description="Find rest or go home to sleep",
                priority=urgency,
                need_type=NeedType.REST,
                category="biological",
                plan_steps=["seek_resting_spot", "sleep_or_rest", "recover_energy"],
                deadline_tick=current_tick + 48,
                created_tick=current_tick,
                reasoning=f"Acute fatigue deficit ({energy_deficit:.2f})",
            )
            self.add_goal(goal)
            new_goals.append(goal)

        # 2. Financial / Economic circumstances
        if money is not None and money < 40.0 and "financial" not in existing_categories:
            conscientiousness = personality.get_trait("conscientiousness")
            urgency = min(0.90, 0.50 + (1.0 - (money / 40.0)) * 0.35 + conscientiousness * 0.15)
            goal = Goal(
                description="Improve financial circumstances through productive work",
                priority=urgency,
                need_type=NeedType.SAFETY,
                category="financial",
                plan_steps=["go_to_workplace", "complete_shift", "earn_wages"],
                deadline_tick=current_tick + 96,
                created_tick=current_tick,
                reasoning=f"Low funds (${money:.2f}) threaten economic security",
            )
            self.add_goal(goal)
            new_goals.append(goal)

        # 3. Social / Relationship development
        extraversion = personality.get_trait("extraversion")
        social_deficit = needs.get(NeedType.SOCIAL, 0.0)
        loneliness = emotions.get_emotion("loneliness") if emotions else 0.0
        effective_social_need = max(social_deficit, loneliness)

        if effective_social_need > 0.55 and NeedType.SOCIAL not in existing_needs and "social" not in existing_categories:
            social_priority = min(0.9, 0.3 + (effective_social_need * 0.4) + (extraversion * 0.3))
            goal = Goal(
                description="Connect or converse with friends/neighbors",
                priority=social_priority,
                need_type=NeedType.SOCIAL,
                category="social",
                plan_steps=["visit_plaza_or_comedor", "find_companion", "socialize_and_converse"],
                deadline_tick=current_tick + 64,
                created_tick=current_tick,
                reasoning=f"Social deficit ({effective_social_need:.2f}) and loneliness",
            )
            self.add_goal(goal)
            new_goals.append(goal)

        # 4. Self-improvement & Skill Acquisition
        openness = personality.get_trait("openness")
        persistence = personality.get_trait("persistence")
        curiosity = emotions.get_emotion("curiosity") if emotions else 0.0
        achievement_deficit = needs.get(NeedType.ACHIEVEMENT, 0.0)

        if (achievement_deficit > 0.60 or curiosity > 0.40) and "skill" not in existing_categories:
            # Check if there is a low-level skill to improve
            target_skill_name = "practical trade craft"
            target_skill_id = "skill_technical"
            if skills:
                # Find skill with lowest proficiency
                lowest_skill = min(skills, key=lambda s: getattr(s, "level", 0.5))
                if getattr(lowest_skill, "level", 0.5) < 0.65:
                    target_skill_name = getattr(lowest_skill, "name", "skill")
                    target_skill_id = getattr(lowest_skill, "skill_id", "skill_technical")

            ach_priority = min(0.85, 0.25 + (openness * 0.3) + (persistence * 0.25) + (curiosity * 0.2))
            goal = Goal(
                description=f"Improve personal competency in {target_skill_name}",
                priority=ach_priority,
                need_type=NeedType.ACHIEVEMENT,
                category="skill",
                target_skill_id=target_skill_id,
                plan_steps=["travel_to_learning_center", "study_technique", "practice_and_master"],
                deadline_tick=current_tick + 144,
                created_tick=current_tick,
                reasoning=f"Self-improvement drive: desire to master {target_skill_name}",
            )
            self.add_goal(goal)
            new_goals.append(goal)

        return new_goals

    # -------------------------------------------------------------------------
    # Phase 0.7 Open-Ended Autonomous Goal Generation & Subgoal Decomposition
    # -------------------------------------------------------------------------

    def spawn_subgoals(
        self,
        parent_goal: Goal,
        current_tick: Tick,
    ) -> list[Goal]:
        """Decompose a high-level goal into hierarchical operational subgoals (Section 4)."""
        subgoals: list[Goal] = []
        p_desc = parent_goal.description.lower()

        if "economic" in p_desc or "financial" in p_desc or "household" in p_desc:
            specs = [
                ("Identify household expenses and reduce waste", "short_term", 0.75, "economic"),
                ("Seek supplemental day labor or commercial work", "short_term", 0.70, "economic"),
                ("Learn a trade skill to increase earning capacity", "medium_term", 0.65, "skill"),
                ("Investigate local commercial opportunities or arbitrage", "medium_term", 0.60, "opportunity"),
                ("Accumulate buffer savings of coin or staple goods", "long_term", 0.55, "economic"),
                ("Request short-term assistance or mutual aid from kin", "short_term", 0.50, "social"),
            ]
        elif "craft" in p_desc or "skill" in p_desc or "competency" in p_desc:
            specs = [
                ("Consult local artisan or study manuals at workshop", "short_term", 0.70, "skill"),
                ("Gather raw materials for hands-on practice", "short_term", 0.65, "economic"),
                ("Execute deliberate repetitive practice trials", "medium_term", 0.60, "skill"),
                ("Solicit expert feedback on produced work", "medium_term", 0.55, "social"),
            ]
        elif "explore" in p_desc or "curiosity" in p_desc or "discover" in p_desc:
            specs = [
                ("Pack provisions and check physical condition", "short_term", 0.65, "biological"),
                ("Travel to boundary quadrant or unvisited site", "medium_term", 0.60, "curiosity"),
                ("Survey physical environment and record observations", "medium_term", 0.55, "curiosity"),
                ("Inquire with nearby inhabitants about local lore", "short_term", 0.50, "social"),
            ]
        else:
            specs = [
                (f"Prepare preliminary resources for {parent_goal.description}", "short_term", parent_goal.priority * 0.9, parent_goal.driver),
                (f"Execute core activity for {parent_goal.description}", "medium_term", parent_goal.priority * 0.85, parent_goal.driver),
                (f"Consolidate results of {parent_goal.description}", "long_term", parent_goal.priority * 0.8, parent_goal.driver),
            ]

        for desc, horizon, prio, driver in specs:
            sg = Goal(
                description=desc,
                priority=prio,
                category=parent_goal.category,
                parent_goal_id=parent_goal.goal_id,
                time_horizon=horizon,
                driver=driver,
                deadline_tick=current_tick + (48 if horizon == "short_term" else (144 if horizon == "medium_term" else 384)),
                created_tick=current_tick,
                reasoning=f"Operational subgoal derived from parent: '{parent_goal.description}'",
            )
            self.add_goal(sg)
            parent_goal.subgoal_ids.append(sg.goal_id)
            subgoals.append(sg)

        return subgoals

    def generate_open_ended_goals(
        self,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        current_tick: Tick,
        context: Optional[dict[str, Any]] = None,
    ) -> list[Goal]:
        """Formulate goals derived from the 11 Phase 0.7 cognitive motivation drivers:
        1. Biological needs
        2. Psychological needs (autonomy, belonging, tranquility)
        3. Family responsibilities
        4. Economic situations
        5. Social relationships
        6. Curiosity
        7. Personal interests (craftsmanship, scholarship, farming, quiet life)
        8. Previous experiences
        9. Detected problems
        10. Observed opportunities
        11. Newly acquired knowledge
        """
        context = context or {}
        new_goals: list[Goal] = []
        active_descs = {g.description for g in self.get_active_goals()}

        openness = personality.get_trait("openness")
        conscientiousness = personality.get_trait("conscientiousness")
        extraversion = personality.get_trait("extraversion")
        agreeableness = personality.get_trait("agreeableness")
        neuroticism = personality.get_trait("neuroticism")

        curiosity_val = emotions.get_emotion("curiosity")
        loneliness_val = emotions.get_emotion("loneliness")

        # Driver 3: Family Responsibilities
        family_dependents = context.get("family_dependents_count", 0)
        pantry_rations = context.get("household_food_rations", 10.0)
        if family_dependents > 0 and pantry_rations < 8.0:
            desc = "Provision sustenance and secure supplies for household family"
            if desc not in active_descs:
                prio = min(0.95, 0.60 + (conscientiousness * 0.25) + (agreeableness * 0.15))
                g = Goal(
                    description=desc,
                    priority=prio,
                    category="family",
                    time_horizon="short_term",
                    driver="family",
                    deadline_tick=current_tick + 64,
                    created_tick=current_tick,
                    reasoning="Kin responsibilities: pantry rations dangerously low for dependents",
                )
                self.add_goal(g)
                new_goals.append(g)

        # Driver 6: Curiosity (Exploration of unknown places or phenomena)
        unvisited_loci = context.get("unvisited_locations", [])
        if (curiosity_val > 0.45 or openness > 0.65) and unvisited_loci:
            target_loc = unvisited_loci[0]
            desc = f"Explore unfamiliar area at {target_loc}"
            if desc not in active_descs:
                prio = min(0.80, 0.35 + (openness * 0.30) + (curiosity_val * 0.25) - (neuroticism * 0.15))
                g = Goal(
                    description=desc,
                    priority=prio,
                    category="exploration",
                    time_horizon="medium_term",
                    driver="curiosity",
                    deadline_tick=current_tick + 120,
                    created_tick=current_tick,
                    reasoning="Epistemic curiosity: desire to explore unvisited territory",
                )
                self.add_goal(g)
                new_goals.append(g)

        # Driver 7: Personal Interests & Diverse Aspirations (Not all seek wealth!)
        vocation_pref = context.get("vocation_preference", "scholarship" if openness > 0.6 else "artisanry")
        if openness > 0.55 and "scholarship" in vocation_pref:
            desc = "Read historical treatises and study natural philosophy"
            if desc not in active_descs:
                g = Goal(
                    description=desc,
                    priority=0.60 + (openness * 0.2),
                    category="scholarship",
                    time_horizon="long_term",
                    driver="personal_interest",
                    deadline_tick=current_tick + 240,
                    created_tick=current_tick,
                    reasoning="Scholarly inclination: personal passion for intellectual inquiry",
                )
                self.add_goal(g)
                new_goals.append(g)
        elif agreeableness > 0.70 and extraversion < 0.40:
            # Tranquil agrarian / quiet craft preference
            desc = "Maintain peaceful home garden and tend quiet daily chores"
            if desc not in active_descs:
                g = Goal(
                    description=desc,
                    priority=0.55 + (agreeableness * 0.2),
                    category="tranquility",
                    time_horizon="medium_term",
                    driver="psychological",
                    deadline_tick=current_tick + 144,
                    created_tick=current_tick,
                    reasoning="Desire for tranquility and modest, peaceful domestic life",
                )
                self.add_goal(g)
                new_goals.append(g)

        # Driver 9: Detected Problems
        detected_crises = context.get("detected_problems", [])
        for prob_desc in detected_crises:
            desc = f"Resolve crisis: {prob_desc}"
            if desc not in active_descs:
                g = Goal(
                    description=desc,
                    priority=0.85,
                    category="problem_solving",
                    time_horizon="short_term",
                    driver="detected_problem",
                    deadline_tick=current_tick + 48,
                    created_tick=current_tick,
                    reasoning="Urgent response required for detected community or personal problem",
                )
                self.add_goal(g)
                new_goals.append(g)

        # Driver 10: Observed Opportunities
        observed_opps = context.get("observed_opportunities", [])
        for opp in observed_opps:
            desc = f"Seize economic opportunity: {opp}"
            if desc not in active_descs:
                prio = 0.50 + (conscientiousness * 0.2) + (extraversion * 0.15)
                g = Goal(
                    description=desc,
                    priority=prio,
                    category="opportunity",
                    time_horizon="medium_term",
                    driver="opportunity",
                    deadline_tick=current_tick + 96,
                    created_tick=current_tick,
                    reasoning="Observed high-yield opportunity in the settlement",
                )
                self.add_goal(g)
                new_goals.append(g)

        # Driver 11: Newly Acquired Knowledge
        new_knowledge_items = context.get("new_knowledge_items", [])
        for k_item in new_knowledge_items:
            desc = f"Practice and experiment with newly learned concept: {k_item}"
            if desc not in active_descs:
                g = Goal(
                    description=desc,
                    priority=0.65,
                    category="practice",
                    time_horizon="short_term",
                    driver="newly_acquired_knowledge",
                    deadline_tick=current_tick + 80,
                    created_tick=current_tick,
                    reasoning="Validate and consolidate recently acquired knowledge in practical use",
                )
                self.add_goal(g)
                new_goals.append(g)

        return new_goals

    def resolve_competing_goals(
        self,
        current_tick: Tick,
    ) -> list[str]:
        """Detect conflicts between competing active goals and dynamically adjust priorities."""
        notifications: list[str] = []
        active = self.get_active_goals()

        for i, g1 in enumerate(active):
            for g2 in active[i + 1 :]:
                # Conflict 1: Biological rest vs intense work
                if g1.category == "biological" and g2.category in ("financial", "economic"):
                    if "sleep" in g1.description.lower() or "rest" in g1.description.lower():
                        g1.competing_conflicts.append(g2.goal_id)
                        g2.competing_conflicts.append(g1.goal_id)
                        # Biological survival takes precedence over long shifts
                        if g1.priority >= 0.70:
                            g2.priority = max(0.20, g2.priority * 0.75)
                            notifications.append(f"Deprioritized '{g2.description}' in favor of urgent biological rest")

                # Conflict 2: Exploration / long journey vs family emergency
                if g1.category == "family" and g2.category in ("exploration", "trade_caravan"):
                    g1.competing_conflicts.append(g2.goal_id)
                    g2.competing_conflicts.append(g1.goal_id)
                    if g1.priority >= 0.65:
                        g2.procrastinate()
                        notifications.append(f"Postponed '{g2.description}' to address domestic family responsibilities")

        return notifications

    def evaluate_and_adapt_goals(
        self,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        current_tick: Tick,
    ) -> list[str]:
        """Execute goal evaluation step in the lifecycle.

        Individuals may procrastinate when overwhelmed or low-persistence,
        modify unfeasible goals, or abandon goals after repeated failures.
        """
        notifications: list[str] = []
        persistence = personality.get_trait("persistence")
        frustration = emotions.get_emotion("frustration")
        anxiety = emotions.get_emotion("anxiety")

        for goal in list(self._goals.values()):
            if goal.status not in ("active", "modified", "procrastinated"):
                continue

            # Check missed deadline
            if goal.deadline_tick and current_tick > goal.deadline_tick:
                # If persistence is high, adapt/extend the deadline rather than giving up immediately
                if persistence > 0.70 and goal.progress >= 0.4:
                    goal.deadline_tick = current_tick + 48
                    goal.modify(f"{goal.description} (resumed with renewed effort)")
                    notifications.append(f"Extended deadline for {goal.description}")
                else:
                    goal.abandon("Missed deadline without sufficient progress")
                    notifications.append(f"Abandoned goal due to deadline: {goal.description}")
                continue

            # Check consecutive failures / obstacles
            if goal.consecutive_failures >= 2:
                if persistence < 0.45 or frustration > 0.60:
                    # Give up or abandon
                    goal.abandon("Repeated setbacks and mounting frustration")
                    notifications.append(f"Abandoned goal due to repeated obstacles: {goal.description}")
                elif persistence > 0.50:
                    # Adapt strategy / modify goal
                    goal.modify(f"{goal.description} (adapted strategy)")
                    notifications.append(f"Adapted plan for {goal.description}")

            # Check procrastination tendency (low persistence + high anxiety/fatigue)
            if goal.status == "active" and (frustration > 0.55 or anxiety > 0.65) and persistence < 0.50:
                if goal.category not in ("biological",):  # Cannot procrastinate on starving
                    goal.procrastinate()
                    notifications.append(f"Procrastinated on {goal.description}")

            # Resume procrastinated goal if mood has recovered
            if goal.status == "procrastinated" and anxiety < 0.35 and frustration < 0.35:
                goal.resume()
                notifications.append(f"Resumed pursuit of {goal.description}")

        return notifications

    def cleanup_completed_or_stale(self, current_tick: Tick) -> None:
        """Prune long-past completed goals or abandoned deadlocks."""
        for g in list(self._goals.values()):
            if g.status == "active" and g.deadline_tick and current_tick > g.deadline_tick:
                g.status = "abandoned"
