"""Tests for population generation, differentiation, and physical states."""

from saltbor.core.config import SimulationConfig
from saltbor.population.factory import PopulationFactory
from saltbor.population.human import SyntheticHuman


def test_population_diversity_and_completeness(population_20: list[SyntheticHuman]):
    assert len(population_20) == 20

    # Ensure uniqueness of UIDs and Serials
    uids = {h.uid for h in population_20}
    serials = {h.identity.serial for h in population_20}
    assert len(uids) == 20
    assert len(serials) == 20

    # Check diverse occupations
    occupations = {h.demographics.occupation for h in population_20}
    assert len(occupations) >= 15

    # Check age range >= 18
    for h in population_20:
        assert h.demographics.age >= 18

    # Check personality traits have meaningful spread (not uniform copies)
    openness_values = [h.personality.get_trait("openness") for h in population_20]
    assert max(openness_values) - min(openness_values) > 0.25
