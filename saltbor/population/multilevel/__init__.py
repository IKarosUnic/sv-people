"""Multi-level Population Architecture and LOD Scaling module."""

from __future__ import annotations

from typing import Optional

from saltbor.population.multilevel.aggregation import PopulationAggregator
from saltbor.population.multilevel.models import (
    CohortGroup,
    CommunityAggregate,
    LODLevel,
    PersistentIndividualRecord,
    PopulationTier,
    RegionalAggregate,
)
from saltbor.population.multilevel.population_manager import MultilevelPopulationManager

_manager_instance: Optional[MultilevelPopulationManager] = None


def get_multilevel_manager() -> MultilevelPopulationManager:
    """Return the global MultilevelPopulationManager singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MultilevelPopulationManager()
        # Seed initial persistent population from simulation runner if available
        from saltbor.simulation.benchmarks.million_benchmark import MillionAgentBenchmark
        records = MillionAgentBenchmark.generate_synthetic_population(count=10000)
        _manager_instance.register_batch(records)

        # Register central community
        comm = CommunityAggregate(
            community_id="comunidad_centro",
            district_id="distrito_san_salvador",
            name="San Salvador Centro Histórico",
            center_lat=13.6978,
            center_lon=-89.1915,
            total_population=6000,
        )
        _manager_instance.register_community(comm)

        # Hydrate initial active agents
        for i in range(20):
            _manager_instance.promote_to_active(f"agent_{i:07d}", LODLevel.LOD_0_INDIVIDUAL)

    return _manager_instance


__all__ = [
    "CohortGroup",
    "CommunityAggregate",
    "LODLevel",
    "MultilevelPopulationManager",
    "PersistentIndividualRecord",
    "PopulationAggregator",
    "PopulationTier",
    "RegionalAggregate",
    "get_multilevel_manager",
]
