"""Social Norms and Rule Evolution Engine for SALTBOR Phase 1.9.

Models how social norms emerge, diffuse, adapt, enforce, and decay:
- Explicit and implicit norms (turn-taking, fair bargaining, fiado, faenas, water rights).
- Graduated sanctions (reputation degradation, fines, exclusion).
- Compliance dynamics based on legitimacy, trust, and peer monitoring.
- Norm decay (desuetudo) and extinction.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Set
import uuid

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class NormDomain(str, enum.Enum):
    """Domains of community norms."""

    RESOURCE_SHARING = "resource_sharing"       # E.g., water turns, pasture grazing
    COMMERCIAL_PRACTICE = "commercial_practice" # E.g., fiado, honest measures, pricing
    CIVIC_COOPERATION = "civic_cooperation"     # E.g., ADESCO faenas, clean-up workdays
    NEIGHBORHOOD_CONVIVENCIA = "convivencia"   # E.g., noise, dispute resolution, boundary respect
    FAMILY_SOLIDARITY = "family_solidarity"     # E.g., elder support, mutual emergency aid
    GOVERNANCE_HONOR = "governance_honor"       # E.g., respecting assembly decisions, quorum


class NormFormalization(str, enum.Enum):
    """Level of institutional codification."""

    IMPLICIT_CUSTOM = "implicit_custom"         # Unwritten cultural habit
    COMMUNITY_AGREEMENT = "community_agreement" # Explicitly agreed at neighborhood meeting
    FORMAL_BYLAW = "formal_bylaw"               # Formally enacted in ADESCO or municipal statute


class SanctionType(str, enum.Enum):
    """Graduated sanctions for norm non-compliance (Elinor Ostrom design principle)."""

    VERBAL_WARNING = "verbal_warning"
    REPUTATION_LOSS = "reputation_loss"
    ECONOMIC_FINE = "economic_fine"
    TEMPORARY_SUSPENSION = "temporary_suspension"
    SOCIAL_OSTRACISM = "social_ostracism"
    COMMUNITY_EXCLUSION = "community_exclusion"


@dataclasses.dataclass
class SocialNorm:
    """A community norm with dynamic compliance, enforcement, and vitality."""

    norm_id: str
    title: str
    description: str
    domain: NormDomain
    formalization: NormFormalization = NormFormalization.COMMUNITY_AGREEMENT
    origin_community_id: str = "comunidad_general"
    created_tick: int = 0

    # Core Parameters
    legitimacy: float = 0.80           # [0.0, 1.0] Community belief in fairness
    enforcement_rigor: float = 0.60    # [0.0, 1.0] Probability that violation is sanctioned
    default_sanction: SanctionType = SanctionType.REPUTATION_LOSS
    fine_amount_usd: float = 2.0

    # Dynamic Tracking
    adherence_rate: float = 0.85       # [0.0, 1.0] Observed compliance ratio
    total_compliances: int = 0
    total_violations: int = 0
    total_sanctions_applied: int = 0
    last_evaluated_tick: int = 0
    is_active: bool = True
    dormant_ticks: int = 0             # Ticks with zero enforcement/practice

    # History
    history_log: list[str] = dataclasses.field(default_factory=list)

    def record_compliance(self, human_uid: str, tick: int) -> None:
        """Record an act of norm compliance."""
        self.total_compliances += 1
        self.dormant_ticks = 0
        self.last_evaluated_tick = tick
        total = self.total_compliances + self.total_violations
        self.adherence_rate = round(self.total_compliances / max(1, total), 3)

    def record_violation(
        self,
        violator_uid: str,
        tick: int,
        sanction_applied: Optional[SanctionType] = None,
    ) -> dict[str, Any]:
        """Record an act of norm violation and evaluate sanction."""
        self.total_violations += 1
        self.dormant_ticks = 0
        self.last_evaluated_tick = tick
        total = self.total_compliances + self.total_violations
        self.adherence_rate = round(self.total_compliances / max(1, total), 3)

        sanction_record: dict[str, Any] = {
            "violator_uid": violator_uid,
            "norm_id": self.norm_id,
            "tick": tick,
            "sanction": None,
            "fine_usd": 0.0,
        }

        if sanction_applied is not None:
            self.total_sanctions_applied += 1
            sanction_record["sanction"] = sanction_applied.value
            if sanction_applied == SanctionType.ECONOMIC_FINE:
                sanction_record["fine_usd"] = self.fine_amount_usd
            self.history_log.append(
                f"Tick {tick}: Violation by {violator_uid} penalized with {sanction_applied.value}"
            )
        else:
            # Unsanctioned violation slowly erodes norm legitimacy and adherence
            self.legitimacy = max(0.10, self.legitimacy - 0.02)
            self.history_log.append(f"Tick {tick}: Unsanctioned violation by {violator_uid}")

        return sanction_record

    def decay_vitality(self, ticks_elapsed: int = 24) -> None:
        """Gradual decay (desuetudo) if norm is not practiced or enforced."""
        self.dormant_ticks += ticks_elapsed
        if self.dormant_ticks > 192:  # 2 simulated days with no activity
            self.legitimacy = max(0.05, self.legitimacy - 0.03)
            self.enforcement_rigor = max(0.05, self.enforcement_rigor - 0.02)
        if self.legitimacy <= 0.15 and self.dormant_ticks >= 384:
            self.is_active = False
            self.history_log.append("Norm collapsed into desuetudo (extinction)")


class SocialNormEvolutionEngine:
    """Manages the lifecycle, transmission, enforcement, and evolution of social norms."""

    def __init__(self) -> None:
        self._norms: dict[str, SocialNorm] = {}
        self._norm_adherence_by_human: dict[tuple[str, str], float] = {} # (human_uid, norm_id) -> compliance tendency

    def get_norm(self, norm_id: str) -> Optional[SocialNorm]:
        return self._norms.get(norm_id)

    def get_all_norms(self, active_only: bool = True) -> list[SocialNorm]:
        if not active_only:
            return list(self._norms.values())
        return [n for n in self._norms.values() if n.is_active]

    def register_norm(
        self,
        title: str,
        description: str,
        domain: NormDomain,
        formalization: NormFormalization = NormFormalization.COMMUNITY_AGREEMENT,
        origin_community_id: str = "comunidad_general",
        default_sanction: SanctionType = SanctionType.REPUTATION_LOSS,
        fine_usd: float = 2.0,
        legitimacy: float = 0.85,
        enforcement_rigor: float = 0.65,
        tick: int = 0,
    ) -> SocialNorm:
        """Introduce or formalize a new social norm."""
        norm_id = f"norm_{domain.value[:4]}_{uuid.uuid4().hex[:6]}"
        norm = SocialNorm(
            norm_id=norm_id,
            title=title,
            description=description,
            domain=domain,
            formalization=formalization,
            origin_community_id=origin_community_id,
            default_sanction=default_sanction,
            fine_amount_usd=fine_usd,
            legitimacy=legitimacy,
            enforcement_rigor=enforcement_rigor,
            created_tick=tick,
        )
        norm.history_log.append(f"Tick {tick}: Norm enacted ({formalization.value})")
        self._norms[norm_id] = norm
        return norm

    def evaluate_individual_compliance(
        self,
        human_uid: str,
        norm_id: str,
        temptation_benefit: float,
        personal_integrity: float = 0.5,
    ) -> tuple[bool, Optional[SanctionType]]:
        """Determine whether an individual complies with a norm or violates it.

        Compliance depends on personal integrity, norm legitimacy, perceived enforcement,
        and temptation to free-ride.
        """
        norm = self._norms.get(norm_id)
        if not norm or not norm.is_active:
            return True, None

        compliance_propensity = (personal_integrity * 0.40) + (norm.legitimacy * 0.35) + (norm.enforcement_rigor * 0.25)
        # Violation occurs if temptation exceeds compliance propensity
        complies = compliance_propensity >= temptation_benefit

        sanction: Optional[SanctionType] = None
        if not complies:
            # Check if enforcement occurs
            if norm.enforcement_rigor >= 0.30:
                sanction = norm.default_sanction

        return complies, sanction

    def step(self, current_tick: Tick) -> None:
        """Periodic evolution and decay check for norms."""
        if current_tick % 96 == 0:  # Daily maintenance
            for norm in list(self._norms.values()):
                if norm.is_active:
                    norm.decay_vitality(ticks_elapsed=96)
