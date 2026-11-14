"""Decision engine — context-aware, utility-driven action selection.

Integrates physiological needs, emotional states, personality traits,
memories, active goals, and environmental constraints into actionable decisions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from saltbor.cognition.autonomy.engine import Goal
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import ActivityType, HumanID, LocationID, NeedType


@dataclass
class ActionOption:
    """A candidate action evaluated by the decision engine."""

    action_type: ActivityType
    target_location_id: Optional[LocationID] = None
    expected_utility: float = 0.0
    reasoning: str = ""


@dataclass
class DecisionTrace:
    """Audit and explanation record for an individual's decision."""

    chosen_action: ActivityType
    target_location_id: Optional[LocationID]
    expected_utility: float
    reasoning: str
    dominant_factors: list[str]
    alternatives: list[dict[str, Any]]


@dataclass
class DecisionContext:
    """The situational context upon which a decision is made."""

    current_location_id: Optional[LocationID]
    available_activities: list[ActivityType]
    current_needs: dict[NeedType, float]
    current_energy: float
    current_hunger: float
    current_money: float
    is_daytime: bool
    hour_int: int
    active_goals: list[Goal] = field(default_factory=list)
    nearby_humans: list[HumanID] = field(default_factory=list)
    home_location_id: Optional[LocationID] = None
    work_location_id: Optional[LocationID] = None

    # Phase 1.4 Civilization Integration Context Signals
    has_active_dispute: bool = False
    has_remittance_pending: bool = False
    has_pending_loan: bool = False
    has_cuchubal_turn: bool = False
    is_community_assembly_active: bool = False
    is_festival_active: bool = False
    is_mentor: bool = False
    is_apprentice: bool = False
    active_curiosity_anomaly: Optional[str] = None
    active_dispute_target: Optional[HumanID] = None

    # Phase 1.5 Everyday Life, Labor & Housing Context Signals
    is_unemployed: bool = False
    is_homeless: bool = False
    has_unpaid_rent: bool = False
    has_social_invitation: bool = False
    invitation_activity: Optional[ActivityType] = None
    invitation_location_id: Optional[LocationID] = None
    invitation_offered_treat: bool = False
    personal_preferences: dict[str, Any] = field(default_factory=dict)

    # Phase 1.7 bounded psychological modulation.  Small, explicit weights;
    # a strong goal or a critical need must still be able to win.
    psychological: dict[str, Any] = field(default_factory=dict)

    # Phase 1.8 Diurnal daily life schedule & transportation signals
    diurnal_phase: Optional[str] = None
    suggested_daily_activity: Optional[ActivityType] = None
    suggested_daily_location: Optional[LocationID] = None
    is_road_blocked_ahead: bool = False


class DecisionEngine:
    """Multi-attribute utility decision engine with bounded rationality and cognitive traceability."""

    def __init__(self) -> None:
        self.last_decision_trace: Optional[DecisionTrace] = None
        self.decision_history: list[DecisionTrace] = []

    def get_last_trace(self) -> Optional[DecisionTrace]:
        """Return the most recent explanatory decision trace."""
        return self.last_decision_trace

    def evaluate_options(
        self,
        context: DecisionContext,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        memory: Optional[MemoryEngine] = None,
    ) -> list[ActionOption]:
        """Compute utility score and explanatory reasoning for candidate actions."""
        options: list[ActionOption] = []

        # Trait values
        conscientiousness = personality.get_trait("conscientiousness")
        extraversion = personality.get_trait("extraversion")
        agreeableness = personality.get_trait("agreeableness")
        openness = personality.get_trait("openness")
        neuroticism = personality.get_trait("neuroticism")
        risk_tolerance = personality.get_trait("risk_tolerance")
        patience = personality.get_trait("patience")

        # Emotional weights & states
        weights = emotions.get_decision_weights() if hasattr(emotions, "get_decision_weights") else {}
        mood = emotions.get_mood() if hasattr(emotions, "get_mood") else 0.0
        frustration = emotions.get_emotion("frustration") if hasattr(emotions, "get_emotion") else 0.0
        loneliness = emotions.get_emotion("loneliness") if hasattr(emotions, "get_emotion") else 0.0
        anxiety = emotions.get_emotion("anxiety") if hasattr(emotions, "get_emotion") else 0.0
        fear = emotions.get_emotion("fear") if hasattr(emotions, "get_emotion") else 0.0
        curiosity = emotions.get_emotion("curiosity") if hasattr(emotions, "get_emotion") else 0.0

        # Needs
        hunger = context.current_hunger
        exhaustion = 1.0 - context.current_energy
        social_need = context.current_needs.get(NeedType.SOCIAL, 0.0)

        # Active Goals Influence
        active_goal_categories = {g.category for g in context.active_goals if getattr(g, "status", "active") in ("active", "modified")}
        primary_goal = context.active_goals[0] if context.active_goals else None

        # -------------------------------------------------------------------
        # 1. SLEEP (High utility when exhausted, late at night, or at home)
        # -------------------------------------------------------------------
        sleep_util = exhaustion * 1.5
        if not context.is_daytime:
            sleep_util += 0.4
        if exhaustion > 0.8:
            sleep_util += 1.0  # Acute physical fatigue override
        if anxiety > 0.5:
            sleep_util += 0.2  # Safety withdrawal in home sanctuary

        options.append(
            ActionOption(
                action_type=ActivityType.SLEEP,
                target_location_id=context.home_location_id,
                expected_utility=sleep_util,
                reasoning=f"Exhaustion level is {exhaustion:.2f}; nighttime sleep required.",
            )
        )

        # -------------------------------------------------------------------
        # 2. REST (Short respite)
        # -------------------------------------------------------------------
        rest_util = exhaustion * 0.9 + (frustration * 0.3) + (anxiety * 0.85) + (fear * 0.60)
        options.append(
            ActionOption(
                action_type=ActivityType.REST,
                target_location_id=context.current_location_id,
                expected_utility=rest_util,
                reasoning=f"Taking a short break to recover breath (fatigue={exhaustion:.2f}).",
            )
        )

        # -------------------------------------------------------------------
        # 3. EAT / COOK (Driven by hunger)
        # -------------------------------------------------------------------
        if hunger > 0.3:
            eat_util = hunger * 2.0
            # If money is low, prefer cooking at home over dining out
            if context.current_money < 10.0 and context.home_location_id:
                options.append(
                    ActionOption(
                        action_type=ActivityType.COOK,
                        target_location_id=context.home_location_id,
                        expected_utility=eat_util + 0.3,
                        reasoning=f"Hungry ({hunger:.2f}), low funds (${context.current_money:.2f}); cooking at home.",
                    )
                )
            else:
                target = "comedor_dona_maria" if (context.hour_int >= 6 and context.hour_int <= 20) else context.home_location_id
                options.append(
                    ActionOption(
                        action_type=ActivityType.EAT,
                        target_location_id=target,
                        expected_utility=eat_util,
                        reasoning=f"Hunger ({hunger:.2f}) requires having a meal.",
                    )
                )

        # -------------------------------------------------------------------
        # 4. WORK (Driven by daylight, daytime shift hours, conscientiousness, financial goals)
        # -------------------------------------------------------------------
        if context.is_daytime and (7 <= context.hour_int <= 17) and context.work_location_id:
            work_util = 0.5 + (conscientiousness * 0.5)
            if anxiety > 0.4:
                work_util -= (anxiety * 0.45 + fear * 0.40)
            if context.current_money < 30.0:
                work_util += 0.4  # Economic survival motivation
            if "financial" in active_goal_categories:
                work_util += 0.45  # Direct autonomous goal pursuit
            if exhaustion > 0.7:
                work_util -= 0.6  # Too tired to work safely
            options.append(
                ActionOption(
                    action_type=ActivityType.WORK,
                    target_location_id=context.work_location_id,
                    expected_utility=work_util,
                    reasoning=f"Work shift during productive hours (conscientiousness={conscientiousness:.2f}).",
                )
            )

        # -------------------------------------------------------------------
        # 5. SOCIALIZE (Driven by social need, loneliness, extraversion, plaza/market)
        # -------------------------------------------------------------------
        effective_social_drive = max(social_need, loneliness)
        social_util = (effective_social_drive * 0.8) + (extraversion * 0.5) + (mood * 0.2)
        if anxiety > 0.4:
            social_util -= anxiety * 0.35  # Fear / social withdrawal
        if "social" in active_goal_categories or (primary_goal and primary_goal.category in ("social", "reconciliation")):
            social_util += 0.4
        
        nearby_count = len(context.nearby_humans)
        if 0 < nearby_count <= 12:
            social_util += 0.25  # Pleasant company
        elif nearby_count > 25:
            social_util -= 0.15  # Avoid extreme overcrowding / noise

        # Distribute socializing destinations to prevent single-node gridlock
        social_nodes = ["plaza_central", "plaza_libertad", "parque_cuscatlan", "mercado_central", "casa_comunal"]
        if context.current_location_id in social_nodes and nearby_count >= 1:
            social_target = context.current_location_id
        else:
            # Deterministically disperse across town using agent's current coordinates/hour
            loc_hash = abs(hash(str(context.current_location_id) + str(context.hour_int))) % len(social_nodes)
            social_target = social_nodes[loc_hash]

        options.append(
            ActionOption(
                action_type=ActivityType.SOCIALIZE,
                target_location_id=social_target,
                expected_utility=social_util,
                reasoning=f"Connecting with neighbors (social need={effective_social_drive:.2f}, extraversion={extraversion:.2f}).",
            )
        )

        # -------------------------------------------------------------------
        # 6. STUDY / LEARN (Driven by openness, curiosity, school hours, skill goals)
        # -------------------------------------------------------------------
        if context.is_daytime and (8 <= context.hour_int <= 16):
            study_util = (openness * 0.6) + (conscientiousness * 0.3) + (curiosity * 0.75)
            if anxiety > 0.4:
                study_util -= anxiety * 0.35  # Anxiety impairs focus
            if "skill" in active_goal_categories or (primary_goal and primary_goal.category == "skill"):
                study_util += 0.55  # Pursuing autonomous skill development goal
            options.append(
                ActionOption(
                    action_type=ActivityType.STUDY,
                    target_location_id="escuela_comunal",
                    expected_utility=study_util,
                    reasoning=f"Engaging in study and learning (openness={openness:.2f}, curiosity={curiosity:.2f}).",
                )
            )

        # -------------------------------------------------------------------
        # 7. SHOP (Market commerce and supplies)
        # -------------------------------------------------------------------
        if context.is_daytime and (8 <= context.hour_int <= 17) and context.current_money >= 15.0:
            shop_util = 0.35 + (0.05 * min(5.0, context.current_money / 20.0))
            options.append(
                ActionOption(
                    action_type=ActivityType.SHOP,
                    target_location_id="mercado_municipal",
                    expected_utility=shop_util,
                    reasoning="Visiting the municipal market for supplies and trade.",
                )
            )

        # -------------------------------------------------------------------
        # 8. EXERCISE / RELAX (Park/nature outdoors)
        # -------------------------------------------------------------------
        if context.is_daytime and exhaustion < 0.5:
            exercise_util = 0.3 + (openness * 0.3) - (neuroticism * 0.1) + (curiosity * 0.2)
            options.append(
                ActionOption(
                    action_type=ActivityType.EXERCISE,
                    target_location_id="parque_la_ceiba",
                    expected_utility=exercise_util,
                    reasoning="Exercising in the open air at Parque La Ceiba.",
                )
            )

        options.append(
            ActionOption(
                action_type=ActivityType.RELAX,
                target_location_id=context.current_location_id or "plaza_central",
                expected_utility=0.25 + (1.0 - conscientiousness) * 0.2,
                reasoning="Taking quiet personal leisure time.",
            )
        )

        # -------------------------------------------------------------------
        # Phase 1.4 Civilization Integration Opportunities
        # -------------------------------------------------------------------
        # 9. COMMUNITY_MEETING / ADESCO Assembly
        if context.is_daytime and (context.is_community_assembly_active or "community" in active_goal_categories or (conscientiousness > 0.65 and agreeableness > 0.65)):
            comm_util = 0.35 + (agreeableness * 0.35) + (conscientiousness * 0.20) - (exhaustion * 0.3)
            options.append(
                ActionOption(
                    action_type=ActivityType.COMMUNITY_MEETING,
                    target_location_id="plaza_central",
                    expected_utility=comm_util,
                    reasoning=f"Attending community assembly / ADESCO meeting (agreeableness={agreeableness:.2f}).",
                )
            )

        # 10. LITIGATE / SEEK_MEDIATION (Triggered by active dispute or intense conflict)
        if context.has_active_dispute or frustration > 0.60:
            if agreeableness >= 0.50:
                med_util = 0.45 + (agreeableness * 0.35) + (patience * 0.25)
                options.append(
                    ActionOption(
                        action_type=ActivityType.SEEK_MEDIATION,
                        target_location_id="alcaldia_comunal",
                        expected_utility=med_util,
                        reasoning="Seeking peaceful communal mediation for dispute.",
                    )
                )
            else:
                lit_util = 0.40 + (frustration * 0.40) + ((1.0 - agreeableness) * 0.30) - (fear * 0.20)
                options.append(
                    ActionOption(
                        action_type=ActivityType.LITIGATE,
                        target_location_id="tribunal_de_paz",
                        expected_utility=lit_util,
                        reasoning="Filing formal judicial lawsuit before the tribunal.",
                    )
                )

        # 11. COMMERCE_SELL / COMMERCE_BUY (Market and Pulpería informal commerce)
        if context.is_daytime and (8 <= context.hour_int <= 17):
            if "commerce" in active_goal_categories or (context.work_location_id and "mercado" in context.work_location_id):
                sell_util = 0.45 + (conscientiousness * 0.35) + (extraversion * 0.20)
                options.append(
                    ActionOption(
                        action_type=ActivityType.COMMERCE_SELL,
                        target_location_id=context.work_location_id or "mercado_municipal",
                        expected_utility=sell_util,
                        reasoning="Selling goods and groceries at market stall or corner store.",
                    )
                )
            if hunger > 0.25 and context.current_money >= 3.0:
                buy_util = 0.40 + (hunger * 0.60)
                target_store = "tienda_san_pedro" if context.current_money < 30.0 else "mercado_central"
                options.append(
                    ActionOption(
                        action_type=ActivityType.COMMERCE_BUY,
                        target_location_id=target_store,
                        expected_utility=buy_util,
                        reasoning=f"Buying daily staples and household provisions at {target_store}.",
                    )
                )

        # 12. RECEIVE_REMITTANCE (When a family transfer from abroad has arrived)
        if context.has_remittance_pending and context.is_daytime:
            rem_util = 0.80 + ((1.0 - min(1.0, context.current_money / 50.0)) * 0.35)
            options.append(
                ActionOption(
                    action_type=ActivityType.RECEIVE_REMITTANCE,
                    target_location_id="agencia_remesas",
                    expected_utility=rem_util,
                    reasoning="Collecting monthly family remittance from relatives abroad.",
                )
            )

        # 13. SEEK_CREDIT / REPAY_DEBT
        if context.has_pending_loan and context.current_money >= 10.0:
            repay_util = 0.40 + (conscientiousness * 0.45)
            options.append(
                ActionOption(
                    action_type=ActivityType.REPAY_DEBT,
                    target_location_id="caja_de_credito",
                    expected_utility=repay_util,
                    reasoning="Repaying credit installment or settling fiado balance.",
                )
            )
        elif context.current_money < 15.0 and ("financial" in active_goal_categories or conscientiousness > 0.60):
            credit_util = 0.35 + ((1.0 - min(1.0, context.current_money / 20.0)) * 0.35)
            options.append(
                ActionOption(
                    action_type=ActivityType.SEEK_CREDIT,
                    target_location_id="caja_de_credito",
                    expected_utility=credit_util,
                    reasoning="Applying for micro-credit or emergency grocery credit.",
                )
            )

        # 14. TEACH_APPRENTICE / LEARN_TRADE (Mentorship & Distributed Education)
        if context.is_daytime and (8 <= context.hour_int <= 16):
            if context.is_mentor:
                teach_util = 0.45 + (agreeableness * 0.35) + (conscientiousness * 0.25)
                options.append(
                    ActionOption(
                        action_type=ActivityType.TEACH_APPRENTICE,
                        target_location_id=context.work_location_id or "taller_artesanal",
                        expected_utility=teach_util,
                        reasoning="Instructing apprentice in craft techniques at workshop.",
                    )
                )
            elif context.is_apprentice or "skill" in active_goal_categories:
                learn_util = 0.50 + (openness * 0.35) + (curiosity * 0.30)
                options.append(
                    ActionOption(
                        action_type=ActivityType.LEARN_TRADE,
                        target_location_id="taller_artesanal",
                        expected_utility=learn_util,
                        reasoning="Practicing trade skills under master supervision.",
                    )
                )

        # 15. CONDUCT_EXPERIMENT (Scientific inquiry)
        if context.is_daytime and (curiosity > 0.50 or openness > 0.70 or context.active_curiosity_anomaly is not None):
            exp_util = 0.40 + (curiosity * 0.45) + (openness * 0.30)
            options.append(
                ActionOption(
                    action_type=ActivityType.CONDUCT_EXPERIMENT,
                    target_location_id="laboratorio_agricola",
                    expected_utility=exp_util,
                    reasoning=f"Conducting empirical test on hypothesis (curiosity={curiosity:.2f}).",
                )
            )

        # 16. ATTEND_CELEBRATION / COOPERATE
        if context.is_festival_active and exhaustion < 0.6:
            fest_util = 0.50 + (extraversion * 0.40) + (mood * 0.20)
            options.append(
                ActionOption(
                    action_type=ActivityType.ATTEND_CELEBRATION,
                    target_location_id="plaza_central",
                    expected_utility=fest_util,
                    reasoning="Participating in community patron saint festival.",
                )
            )

        # -------------------------------------------------------------------
        # Phase 1.5 Everyday Life, Commercial, Labor, Housing & Leisure Options
        # -------------------------------------------------------------------

        # 17. Commercial Browsing, Window Shopping & Price Comparison
        if context.is_daytime and (7 <= context.hour_int <= 19):
            # Window shopping: admire goods without entering or spending
            if curiosity > 0.35 or openness > 0.45 or context.current_money < 20.0:
                win_util = 0.28 + (curiosity * 0.30) + (openness * 0.15)
                options.append(
                    ActionOption(
                        action_type=ActivityType.WINDOW_SHOPPING,
                        target_location_id="mercado_central",
                        expected_utility=win_util,
                        reasoning="Observing goods and window shopping without spending money.",
                    )
                )

            # Browsing store: inspect goods inside store out of curiosity
            if curiosity > 0.45:
                browse_util = 0.30 + (curiosity * 0.35) + (openness * 0.20)
                options.append(
                    ActionOption(
                        action_type=ActivityType.BROWSE_STORE,
                        target_location_id="tienda_san_pedro",
                        expected_utility=browse_util,
                        reasoning="Browsing corner store shelves to see new items and check inventory.",
                    )
                )

            # Price comparison: smart consumer market survey
            if conscientiousness > 0.45:
                comp_util = 0.29 + (conscientiousness * 0.35)
                options.append(
                    ActionOption(
                        action_type=ActivityType.COMPARE_PRICES,
                        target_location_id="mercado_central",
                        expected_utility=comp_util,
                        reasoning="Surveying prices across market vendors to budget carefully.",
                    )
                )

        # 18. DINE_OUT (Eating prepared food at pupusería or comedor)
        if (7 <= context.hour_int <= 21) and hunger > 0.25:
            dining_pref = context.personal_preferences.get("dining_out_affinity", 0.5)
            if context.current_money >= 3.50 or context.invitation_offered_treat:
                dine_util = 0.35 + (hunger * 0.50) + (extraversion * 0.20) + (dining_pref * 0.25)
                options.append(
                    ActionOption(
                        action_type=ActivityType.DINE_OUT,
                        target_location_id="comedor_dona_maria",
                        expected_utility=dine_util,
                        reasoning="Dine out for hot pupusas and social chatter at comedor.",
                    )
                )

        # 19. Leisure: VISIT_PARK, SEEK_ENTERTAINMENT, SPORT, HOBBY
        if context.is_daytime and exhaustion < 0.70:
            park_pref = context.personal_preferences.get("park_walking_preference", 0.6)
            park_util = 0.32 + (park_pref * 0.25) + (openness * 0.20) + (anxiety * 0.25)
            options.append(
                ActionOption(
                    action_type=ActivityType.VISIT_PARK,
                    target_location_id="parque_la_ceiba",
                    expected_utility=park_util,
                    reasoning="Visiting park under ceiba trees for fresh air and stress relief.",
                )
            )

            # Hobby
            hobby_util = 0.28 + (openness * 0.35) + (conscientiousness * 0.20)
            options.append(
                ActionOption(
                    action_type=ActivityType.PARTICIPATE_IN_HOBBY,
                    target_location_id=context.home_location_id or "casa_comunal",
                    expected_utility=hobby_util,
                    reasoning="Practicing craft hobby or personal reading.",
                )
            )

            # Sport
            if 14 <= context.hour_int <= 18 and exhaustion < 0.50:
                sport_pref = context.personal_preferences.get("sports_affinity", 0.4)
                sport_util = 0.30 + (sport_pref * 0.35) + (extraversion * 0.25)
                options.append(
                    ActionOption(
                        action_type=ActivityType.PLAY_SPORT,
                        target_location_id="parque_la_ceiba",
                        expected_utility=sport_util,
                        reasoning="Joining pickup soccer game with community youth.",
                    )
                )

        # 20. Social Visits (VISIT_FRIEND / VISIT_RELATIVE)
        if social_need > 0.30 and exhaustion < 0.65:
            social_visit_util = 0.35 + (social_need * 0.40) + (agreeableness * 0.25)
            options.append(
                ActionOption(
                    action_type=ActivityType.VISIT_FRIEND,
                    target_location_id="casa_comunal",
                    expected_utility=social_visit_util,
                    reasoning="Visiting friend or relative for coffee and neighborly solidarity.",
                )
            )

        # 21. Dynamic Labor Market: SEARCH_EMPLOYMENT
        if context.is_unemployed and context.is_daytime and (7 <= context.hour_int <= 16):
            job_search_util = 0.65 + ((1.0 - min(1.0, context.current_money / 25.0)) * 0.35) + (conscientiousness * 0.25)
            options.append(
                ActionOption(
                    action_type=ActivityType.SEARCH_EMPLOYMENT,
                    target_location_id="taller_artesanal",
                    expected_utility=job_search_util,
                    reasoning="Searching for employment opportunities and asking workshops for openings.",
                )
            )

        # 22. Housing & Homelessness: SEEK_HOUSING / SEEK_SHELTER
        if context.is_homeless:
            shelter_util = 0.75 + (exhaustion * 0.40) + (hunger * 0.25)
            options.append(
                ActionOption(
                    action_type=ActivityType.SEEK_SHELTER,
                    target_location_id="casa_comunal",
                    expected_utility=shelter_util,
                    reasoning="Unhoused; seeking communal shelter bed and assistance.",
                )
            )
            if context.current_money >= 12.0:
                rent_search_util = 0.70 + (conscientiousness * 0.30)
                options.append(
                    ActionOption(
                        action_type=ActivityType.SEEK_HOUSING,
                        target_location_id="plaza_central",
                        expected_utility=rent_search_util,
                        reasoning="Has accumulated savings; searching for affordable rental room.",
                    )
                )

        # 23. Assistance: REQUEST_ASSISTANCE / OFFER_ASSISTANCE
        if context.current_money < 3.0 and (hunger > 0.50 or context.has_unpaid_rent):
            req_util = 0.55 + (hunger * 0.35)
            options.append(
                ActionOption(
                    action_type=ActivityType.REQUEST_ASSISTANCE,
                    target_location_id="casa_comunal",
                    expected_utility=req_util,
                    reasoning="Experiencing economic hardship; requesting emergency community aid.",
                )
            )
        elif context.current_money > 60.0 and agreeableness > 0.65:
            offer_util = 0.30 + (agreeableness * 0.35)
            options.append(
                ActionOption(
                    action_type=ActivityType.OFFER_ASSISTANCE,
                    target_location_id="casa_comunal",
                    expected_utility=offer_util,
                    reasoning="Financially comfortable; offering mutual support to neighbors.",
                )
            )

        # 24. Pending Social Invitation
        if context.has_social_invitation and context.invitation_activity:
            inv_util = 0.55 + (extraversion * 0.25) + (agreeableness * 0.20)
            if context.invitation_offered_treat:
                inv_util += 0.15
            options.append(
                ActionOption(
                    action_type=context.invitation_activity,
                    target_location_id=context.invitation_location_id or "comedor_dona_maria",
                    expected_utility=inv_util,
                    reasoning="Joining friend who extended a personal invitation.",
                )
            )

        # -------------------------------------------------------------------
        # 7b. Psychological Load Modulation (Phase 1.7)
        #
        # Bounded rationality under stress: the agent does not lose the ability
        # to reason, it changes which options look worth doing.  The modifiers
        # are produced by RegulationEngine and are individually grounded.
        # -------------------------------------------------------------------
        psych = context.psychological or {}
        if psych:
            load = float(psych.get("psychological_load", 0.0))
            rest_w = float(psych.get("rest_weight", 0.0))
            social_w = float(psych.get("social_weight", 0.0))
            work_w = float(psych.get("work_weight", 0.0))
            avoidance = float(psych.get("avoidance", 0.0))
            risk_perception = float(psych.get("risk_perception", 0.0))
            crisis_severity = float(psych.get("crisis_severity", 0.0))
            crisis_kind = str(psych.get("crisis_kind", ""))
            for opt in options:
                act = opt.action_type
                delta = 0.0
                if act in (ActivityType.REST, ActivityType.SLEEP):
                    delta += 0.24 * rest_w + 0.08 * avoidance
                elif act in (ActivityType.SOCIALIZE, ActivityType.ATTEND_CELEBRATION, ActivityType.COMMUNITY_MEETING):
                    delta += 0.22 * social_w - 0.10 * avoidance
                    if crisis_kind == "withdrawal":
                        delta -= 0.16 * crisis_severity
                elif act in (
                    ActivityType.WORK, ActivityType.STUDY, ActivityType.LEARN_TRADE,
                    ActivityType.SEARCH_EMPLOYMENT, ActivityType.APPLY_FOR_JOB,
                    ActivityType.TEACH_APPRENTICE, ActivityType.BUSINESS_CREATE,
                ):
                    delta += 0.20 * work_w - 0.10 * load
                elif act in (
                    ActivityType.COMMERCE_BUY, ActivityType.PURCHASE_GOODS,
                    ActivityType.SEEK_CREDIT, ActivityType.REPAY_DEBT,
                ):
                    delta -= 0.10 * (1.0 - risk_perception) * crisis_severity
                elif act in (
                    ActivityType.TRAVEL, ActivityType.EXERCISE, ActivityType.EXPLORE_LOCATION,
                ):
                    delta -= 0.06 * risk_perception * load
                elif act in (ActivityType.EAT, ActivityType.COOK):
                    delta += 0.06 * float(psych.get("avoidance", 0.0))
                elif act in (ActivityType.SEEK_MEDICAL_CARE, ActivityType.REST_RECOVER):
                    delta += 0.10 * float(psych.get("help_seeking", 0.0))

                if abs(delta) > 0.005:
                    opt.expected_utility += delta
                    opt.reasoning += f" [Psych: load={load:.2f}, delta={delta:+.2f}]"

        # -------------------------------------------------------------------
        # 8. Emotional Associations Modulation (Location Aversion & Place Affinity)
        # -------------------------------------------------------------------
        if memory and hasattr(memory, "get_location_association"):
            for opt in options:
                if opt.target_location_id:
                    loc_assoc = memory.get_location_association(opt.target_location_id)
                    val = loc_assoc.get("valence", 0.0)
                    if val < -0.15:
                        # Negative memories at location produce avoidance
                        aversion_penalty = abs(val) * 0.40
                        opt.expected_utility = max(0.01, opt.expected_utility - aversion_penalty)
                        opt.reasoning += f" [Avoidance: unpleasant memories at {opt.target_location_id}]"
                    elif val > 0.25:
                        # Positive memories at location encourage revisit
                        affinity_bonus = val * 0.25
                        opt.expected_utility += affinity_bonus
                        opt.reasoning += f" [Affinity: positive memories at {opt.target_location_id}]"

        # Phase 1.8: Diurnal routine alignment and daily life intentionality
        if context.suggested_daily_activity:
            matched = False
            for opt in options:
                if opt.action_type == context.suggested_daily_activity:
                    matched = True
                    opt.expected_utility += 0.35
                    opt.reasoning += f" [Rutina diaria: {context.diurnal_phase or 'horario'}]"
            if not matched:
                options.append(
                    ActionOption(
                        action_type=context.suggested_daily_activity,
                        target_location_id=context.suggested_daily_location or context.current_location_id,
                        expected_utility=0.45,
                        reasoning=f"Iniciativa de rutina diaria: {context.diurnal_phase or 'cotidiana'}",
                    )
                )

        return options

    def decide(
        self,
        context: DecisionContext,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        memory: Optional[MemoryEngine] = None,
        rng: Optional[Any] = None,
        exploration_noise: float = 0.10,
        brain: Optional[Any] = None,
    ) -> ActionOption:
        """Select an action using softmax utility evaluation with bounded rationality, brain deliberation, and record trace."""
        options = self.evaluate_options(context, personality, emotions, memory)
        if not options:
            fallback = ActionOption(
                action_type=ActivityType.REST,
                target_location_id=context.current_location_id,
                expected_utility=0.1,
                reasoning="Default fallback action.",
            )
            return fallback

        # Optional modulation by CognitiveBrainArchitecture (subsystems: frontal, parietal, cerebellar, limbic)
        brain_outcome = None
        if brain is not None and hasattr(brain, "deliberate"):
            try:
                candidate_acts = [
                    {"action_name": opt.action_type.value, "target_location": opt.target_location_id}
                    for opt in options
                ]
                brain_outcome = brain.deliberate(
                    current_location_id=context.current_location_id,
                    available_candidate_actions=candidate_acts,
                )
                if brain_outcome:
                    for opt in options:
                        if opt.action_type.value == brain_outcome.action_name:
                            opt.expected_utility += 0.15 * (1.0 - min(1.0, brain_outcome.spatial_travel_cost / 1000.0))
                            opt.reasoning += f" [Brain deliberation: {brain_outcome.action_name}]"
            except Exception:
                brain_outcome = None

        # Bounded rationality noise modulated by personality:
        # High conscientiousness & high patience -> lower deliberation noise
        # High impulsiveness -> higher noise
        modifiers = personality.get_behavioral_modifier() if hasattr(personality, "get_behavioral_modifier") else {}
        impulsiveness = modifiers.get("impulsiveness", 0.5)
        determination = modifiers.get("determination", 0.5)
        effective_noise = max(0.02, exploration_noise * (0.6 + impulsiveness * 0.8 - determination * 0.3))

        utilities = []
        for opt in options:
            noise = (
                rng.normal(0.0, effective_noise)
                if rng is not None and hasattr(rng, "normal")
                else random.gauss(0.0, effective_noise)
            )
            utilities.append(opt.expected_utility + noise)

        best_idx = int(np.argmax(utilities)) if hasattr(np, "argmax") else max(range(len(utilities)), key=lambda i: utilities[i])
        chosen = options[best_idx]

        # Record decision trace
        dominant_factors: list[str] = []
        if context.current_hunger > 0.5:
            dominant_factors.append(f"Hunger ({context.current_hunger:.2f})")
        if context.current_energy < 0.3:
            dominant_factors.append(f"Exhaustion ({1.0 - context.current_energy:.2f})")
        if hasattr(emotions, "get_mood") and emotions.get_mood() < -0.3:
            dominant_factors.append(f"Low Mood ({emotions.get_mood():.2f})")
        if context.active_goals:
            dominant_factors.append(f"Goal: {context.active_goals[0].description}")
        if brain_outcome:
            dominant_factors.append(f"Brain Deliberation ({brain_outcome.action_name})")
        if context.psychological:
            dominant_factors.append(
                f"Psychological load ({float(context.psychological.get('psychological_load', 0.0)):.2f})"
            )
            if context.psychological.get("crisis_severity", 0) > 0:
                dominant_factors.append(
                    f"Crisis: {context.psychological.get('crisis_kind', 'unknown')}"
                )

        trace = DecisionTrace(
            chosen_action=chosen.action_type,
            target_location_id=chosen.target_location_id,
            expected_utility=chosen.expected_utility,
            reasoning=chosen.reasoning,
            dominant_factors=dominant_factors,
            alternatives=[
                {
                    "action": opt.action_type.value,
                    "location": opt.target_location_id,
                    "utility": round(opt.expected_utility, 3),
                }
                for opt in options
            ],
        )
        self.last_decision_trace = trace
        self.decision_history.append(trace)
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)

        return chosen

    def decide_formal(
        self,
        internal_state: Any,
        beliefs: Any,
        info: Any,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        active_goal_categories: Optional[set[str]] = None,
        rng: Optional[Any] = None,
    ) -> tuple[ActionOption, Any]:
        """Execute decision using the formal MAUT architecture (Section 2.1)."""
        from saltbor.cognition.decision.formal_decision import (
            FormalDecisionArchitecture,
        )

        arch = FormalDecisionArchitecture(rng=rng)
        traits_dict = {
            t: personality.get_trait(t)
            for t in [
                "conscientiousness", "extraversion", "openness", "neuroticism",
                "risk_tolerance", "patience", "persistence"
            ]
        }
        emots_dict = {
            e: emotions.get_emotion(e) if hasattr(emotions, "get_emotion") else 0.0
            for e in ["anxiety", "fear", "loneliness", "curiosity", "frustration"]
        }
        mood = emotions.get_mood() if hasattr(emotions, "get_mood") else 0.0
        prefs = arch.derive_preference_weights(traits_dict, emots_dict, mood)

        # Build candidate consequences
        candidates = []
        for act in info.available_activities:
            # Determine appropriate target location
            target = info.current_location_id
            if act == ActivityType.SLEEP:
                target = info.home_location_id
            elif act == ActivityType.WORK:
                target = info.work_location_id
            elif act == ActivityType.STUDY:
                target = "escuela_comunal"
            elif act == ActivityType.SHOP:
                target = "mercado_municipal"
            elif act == ActivityType.EAT:
                target = "comedor_dona_maria"

            conseq = arch.evaluate_candidate(
                act=act,
                target_loc=target,
                internal=internal_state,
                beliefs=beliefs,
                info=info,
                prefs=prefs,
                active_goal_categories=active_goal_categories or set(),
            )
            candidates.append(conseq)

        chosen_conseq, structured_trace = arch.select_action(candidates)
        opt = ActionOption(
            action_type=chosen_conseq.action_type,
            target_location_id=chosen_conseq.target_location_id,
            expected_utility=chosen_conseq.total_expected_utility,
            reasoning=chosen_conseq.reasoning,
        )
        return opt, structured_trace
