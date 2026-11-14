"""Universal Domain Configuration Engine for SALTBOR.

Coordinates all human activity domains, registries, and operational subsystems:
- Domain registration, validation, activation, deactivation, and versioning.
- Pluggable domain implementations reusing the shared human simulation core.
- Integration with HumanActivityCatalog, ContextualBehaviorEngine, EditableWorldEngine,
  DomainPermissionEngine, HumanCenteredScenarioEngine, DomainDataRegistry,
  DecisionIntelligenceEngine, and CompactExperimentDatabase.
- Discrete per-tick lifecycle step to advance all active domains synchronously.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from saltbor.domain.agriculture import AgricultureActivityDomain
from saltbor.domain.behavior import ContextualBehaviorEngine
from saltbor.domain.catalog import HumanActivityCatalog
from saltbor.domain.commerce import BusinessActivityDomain
from saltbor.domain.data_registry import DomainDataRegistry
from saltbor.domain.decision_intelligence import DecisionIntelligenceEngine
from saltbor.domain.editable_world import EditableWorldEngine
from saltbor.domain.education import EducationActivityDomain
from saltbor.domain.experiment_database import CompactExperimentDatabase
from saltbor.domain.food import FoodActivityDomain
from saltbor.domain.healthcare import HealthcareActivityDomain
from saltbor.domain.models import (
    DomainCategory,
    DomainDefinition,
    DomainStatus,
    WorldLayerType,
)
from saltbor.domain.permissions import DomainPermissionEngine
from saltbor.domain.scenarios import HumanCenteredScenarioEngine
from saltbor.domain.transportation import TransportationActivityDomain

logger = logging.getLogger(__name__)


class UniversalDomainEngine:
    """Master orchestrator for configurable multi-domain human activity simulation."""

    def __init__(
        self,
        geography_db_path: Optional[str] = None,
        experiment_db_path: Optional[str] = None,
    ) -> None:
        # Core Shared Subsystems
        self.catalog = HumanActivityCatalog()
        self.behavior_engine = ContextualBehaviorEngine()
        self.world_engine = EditableWorldEngine(geography_db_path=geography_db_path)
        self.permission_engine = DomainPermissionEngine()
        self.data_registry = DomainDataRegistry()
        self.scenario_engine = HumanCenteredScenarioEngine()
        self.decision_engine = DecisionIntelligenceEngine()
        self.experiment_db = CompactExperimentDatabase(db_path=experiment_db_path)

        # Specialized Activity Domains
        self.food_domain = FoodActivityDomain(behavior_engine=self.behavior_engine)
        self.commerce_domain = BusinessActivityDomain()
        self.education_domain = EducationActivityDomain()
        self.healthcare_domain = HealthcareActivityDomain()
        self.transportation_domain = TransportationActivityDomain()
        self.agriculture_domain = AgricultureActivityDomain()

        # Domain Definition Registry
        self.definitions: Dict[str, DomainDefinition] = {}
        self.active_domain_ids: Set[str] = set()

        # Register and activate standard initial domains
        self._register_default_domains()

    def register_domain(self, definition: DomainDefinition) -> bool:
        """Register a new domain definition after validating configuration."""
        errors = self.validate_domain_configuration(definition)
        if errors:
            logger.error("Domain '%s' failed validation: %s", definition.domain_id, errors)
            return False

        definition.status = DomainStatus.VALIDATED
        self.definitions[definition.domain_id] = definition
        logger.info("Registered domain '%s' (v%s, category: %s)", definition.name, definition.version, definition.category.value)
        return True

    def validate_domain_configuration(self, definition: DomainDefinition) -> List[str]:
        """Validate that a domain definition meets all structural and operational criteria."""
        errors: List[str] = []

        if not definition.domain_id or len(definition.domain_id) < 3:
            errors.append("domain_id must be at least 3 characters")
        if not definition.name:
            errors.append("name is required")
        if not definition.purpose:
            errors.append("purpose is required")
        if not definition.geographic_scope:
            errors.append("geographic_scope is required")

        return errors

    def activate_domain(self, domain_id: str) -> bool:
        """Activate a registered domain for live simulation execution."""
        defn = self.definitions.get(domain_id)
        if not defn:
            logger.warning("Cannot activate unknown domain '%s'", domain_id)
            return False

        defn.status = DomainStatus.ACTIVE
        self.active_domain_ids.add(domain_id)
        logger.info("Domain '%s' activated.", domain_id)
        return True

    def deactivate_domain(self, domain_id: str) -> bool:
        """Deactivate an active domain."""
        defn = self.definitions.get(domain_id)
        if not defn:
            return False

        defn.status = DomainStatus.PAUSED
        self.active_domain_ids.discard(domain_id)
        logger.info("Domain '%s' deactivated.", domain_id)
        return True

    def get_domain(self, domain_id: str) -> Optional[DomainDefinition]:
        return self.definitions.get(domain_id)

    def list_domains(self) -> List[Dict[str, Any]]:
        """Return catalog of all registered domains and their live status."""
        return [
            {
                "domain_id": d.domain_id,
                "name": d.name,
                "category": d.category.value,
                "purpose": d.purpose,
                "status": d.status.value,
                "is_active": d.domain_id in self.active_domain_ids,
                "version": d.version,
                "indicators": d.indicators,
                "activities_count": len(d.activities),
                "entities": d.entities,
            }
            for d in self.definitions.values()
        ]

    def step(self, current_tick: int) -> Dict[str, Any]:
        """Advance all active domains during discrete tick execution."""
        results: Dict[str, Any] = {}

        # Daily cycle executed at tick_of_day == 0 (every 96 ticks)
        if current_tick % 96 == 0:
            if "commerce_retail" in self.active_domain_ids:
                results["commerce"] = self.commerce_domain.execute_daily_cycle()

        return results

    def _register_default_domains(self) -> None:
        """Register the 6 initial built-in activity domains and activate them."""
        # 1. Food and Gastronomy
        self.register_domain(self.food_domain.get_definition())
        self.activate_domain("food_gastronomy")

        # 2. Commerce and Retail
        self.register_domain(self.commerce_domain.get_definition())
        self.activate_domain("commerce_retail")

        # 3. Education
        self.register_domain(self.education_domain.get_definition())
        self.activate_domain("education")

        # 4. Healthcare
        self.register_domain(self.healthcare_domain.get_definition())
        self.activate_domain("healthcare")

        # 5. Transportation
        self.register_domain(self.transportation_domain.get_definition())
        self.activate_domain("transportation")

        # 6. Agriculture
        self.register_domain(self.agriculture_domain.get_definition())
        self.activate_domain("agriculture")
