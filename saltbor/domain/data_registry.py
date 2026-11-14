"""Domain Data and Evidence Registry for SALTBOR.

Maintains provenance, legal licenses, spatial/temporal resolution, and epistemic validation
tiers across all empirical, reference, simulated, and hypothetical datasets:

Epistemic Validation Tiers:
1. OBSERVED_REAL: Verified empirical records (BCR, DIGESTYC/ONEC, CNR, Geofabrik OSM).
2. IMPORTED_REFERENCE: External multilateral benchmark datasets (World Bank, FAO, WHO, UNESCO).
3. USER_PROVIDED: Specific local parameters or files configured by users.
4. SIMULATED: Emergent outputs computed by SALTBOR runtime.
5. HYPOTHETICAL: Explicit scenario assumptions for what-if exploration.
6. MODEL_RECOMMENDATION: Outputs synthesized by decision intelligence algorithms.

Strict Directive: Never silently mix simulated information with verified real-world records.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional

from saltbor.domain.models import DataProvenanceTier, DatasetMetadata

logger = logging.getLogger(__name__)


class DomainDataRegistry:
    """Central registry and verification validator for datasets and simulation inputs."""

    def __init__(self) -> None:
        self.datasets: Dict[str, DatasetMetadata] = {}
        self._seed_salvadoran_and_reference_datasets()

    def register_dataset(self, metadata: DatasetMetadata) -> None:
        """Register a dataset with its complete provenance schema."""
        self.datasets[metadata.dataset_id] = metadata

    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        return self.datasets.get(dataset_id)

    def list_datasets(
        self,
        tier: Optional[DataProvenanceTier] = None,
        geographic_coverage: Optional[str] = None,
    ) -> List[DatasetMetadata]:
        """Filter datasets by epistemic tier or geographic scope."""
        results = list(self.datasets.values())
        if tier is not None:
            results = [d for d in results if d.tier == tier]
        if geographic_coverage is not None:
            results = [d for d in results if geographic_coverage.lower() in d.geographic_coverage.lower()]
        return results

    def verify_no_contamination(self, dataset_ids: List[str], expected_tier: DataProvenanceTier) -> bool:
        """Verify that a set of datasets only contains the expected epistemic tier."""
        for did in dataset_ids:
            ds = self.get_dataset(did)
            if not ds:
                return False
            if ds.tier != expected_tier:
                logger.error(
                    "Epistemic contamination detected: Dataset '%s' is %s, expected %s",
                    did,
                    ds.tier.value,
                    expected_tier.value,
                )
                return False
        return True

    def _seed_salvadoran_and_reference_datasets(self) -> None:
        """Register official Salvadoran and international reference datasets."""

        # 1. OpenStreetMap El Salvador
        self.register_dataset(
            DatasetMetadata(
                dataset_id="osm_el_salvador_2026",
                name="OpenStreetMap El Salvador Cartography",
                source="Geofabrik OpenStreetMap Extracts",
                license="ODbL-1.0",
                collection_date="2026-11-13",
                geographic_coverage="El Salvador (14 departments)",
                temporal_coverage="2026",
                resolution="Metric geometry (EPSG:4326)",
                methodology="Collaborative open-source geographic mapping with satellite verification",
                verification_status="VERIFIED_REAL",
                confidence_score=0.95,
                limitations=[
                    "Informal roads in rural hillsides may lack turn restriction tags.",
                    "Attribution required under Open Database License.",
                ],
                tier=DataProvenanceTier.OBSERVED_REAL,
                attributes={"feature_count": 151227, "format": "SQLite/SpatiaLite"},
            )
        )

        # 2. Banco Central de Reserva (BCR) Basic Food Basket
        self.register_dataset(
            DatasetMetadata(
                dataset_id="bcr_canasta_basica_2026",
                name="Costo de la Canasta Básica Alimentaria (CBA)",
                source="Banco Central de Reserva de El Salvador (BCR) & ONEC",
                license="Open Government Data El Salvador",
                collection_date="2026-10-31",
                geographic_coverage="El Salvador (Urbano y Rural)",
                temporal_coverage="Monthly 2020-2026",
                resolution="National & Urban/Rural disaggregation",
                methodology="Statistical price survey of essential food items per household per day",
                verification_status="VERIFIED_REAL",
                confidence_score=0.98,
                limitations=[
                    "Represents standard nutritional minimum, not actual individual spending preferences.",
                ],
                tier=DataProvenanceTier.OBSERVED_REAL,
                attributes={"urban_monthly_cost_usd": 257.40, "rural_monthly_cost_usd": 189.20},
            )
        )

        # 3. DIGESTYC / ONEC Encuesta de Hogares de Propósitos Múltiples (EHPM)
        self.register_dataset(
            DatasetMetadata(
                dataset_id="digestyc_ehpm_2026",
                name="Encuesta de Hogares de Propósitos Múltiples (EHPM)",
                source="Oficina Nacional de Estadística y Censos (ONEC / DIGESTYC)",
                license="Public Sector Statistical Release",
                collection_date="2026-06-30",
                geographic_coverage="14 Departments of El Salvador",
                temporal_coverage="Annual 2024-2026",
                resolution="Departmental & Household sample",
                methodology="Stratified probabilistic household sampling across urban and rural segments",
                verification_status="VERIFIED_REAL",
                confidence_score=0.96,
                limitations=[
                    "Informal sector income subject to self-reporting recall bias.",
                ],
                tier=DataProvenanceTier.OBSERVED_REAL,
                attributes={"sample_households": 21000, "sample_individuals": 78000},
            )
        )

        # 4. FAO Food and Agriculture Benchmarks
        self.register_dataset(
            DatasetMetadata(
                dataset_id="fao_corredor_seco_yields",
                name="FAO Central America Dry Corridor Crop Yield Benchmarks",
                source="Food and Agriculture Organization (FAO)",
                license="CC-BY-3.0-IGO",
                collection_date="2025-12-15",
                geographic_coverage="Central American Dry Corridor (El Salvador, Guatemala, Honduras)",
                temporal_coverage="2015-2025",
                resolution="Agro-ecological zones",
                methodology="Agronomic surveys and satellite drought index (ASIS) correlation",
                verification_status="CORROBORATED_REFERENCE",
                confidence_score=0.90,
                limitations=[
                    "Averaged over broad ecological zones; local microclimates may vary.",
                ],
                tier=DataProvenanceTier.IMPORTED_REFERENCE,
                attributes={"maize_drought_yield_loss_range": [0.40, 0.65]},
            )
        )

        # 5. World Bank Educational Indicators
        self.register_dataset(
            DatasetMetadata(
                dataset_id="worldbank_education_indicators_slv",
                name="World Bank El Salvador Education Statistics",
                source="World Bank Group Development Indicators",
                license="CC-BY-4.0",
                collection_date="2025-09-01",
                geographic_coverage="El Salvador",
                temporal_coverage="2010-2025",
                resolution="National level aggregates",
                methodology="Harmonized national accounts and administrative reporting",
                verification_status="CORROBORATED_REFERENCE",
                confidence_score=0.92,
                limitations=["Lacks municipal granular breakdowns."],
                tier=DataProvenanceTier.IMPORTED_REFERENCE,
            )
        )

        # 6. Simulated Baseline Model Run
        self.register_dataset(
            DatasetMetadata(
                dataset_id="saltbor_simulated_baseline_run_42",
                name="SALTBOR Simulated Baseline Trajectory (Seed 42)",
                source="SALTBOR Simulation Core Engine",
                license="Internal Computational Artifact",
                collection_date="2026-11-14",
                geographic_coverage="San Salvador Centro (Simulated Agents)",
                temporal_coverage="Simulated 96 ticks",
                resolution="15-minute discrete ticks / Individual human agents",
                methodology="Multi-agent emergent simulation with bounded-rational cognitive appraisal",
                verification_status="SIMULATED_NOT_REAL",
                confidence_score=0.85,
                limitations=[
                    "Synthetic agent decisions approximate human behavior; not empirical observations.",
                ],
                tier=DataProvenanceTier.SIMULATED,
            )
        )
