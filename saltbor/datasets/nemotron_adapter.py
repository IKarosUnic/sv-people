"""Dataset adapter for NVIDIA Nemotron Personas El Salvador.

Dataset source: https://huggingface.co/datasets/nvidia/Nemotron-Personas-El-Salvador

Handles dataset discovery, safe downloading, schema normalization, and provenance.
Provides graceful fallback to mock data when network or HuggingFace libraries
are unavailable.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from saltbor.core.types import DataSource, Gender

logger = logging.getLogger(__name__)


class NemotronAdapter:
    """Adapter for downloading and normalizing NVIDIA Nemotron Personas dataset."""

    DATASET_ID = "nvidia/Nemotron-Personas-El-Salvador"

    def __init__(self) -> None:
        self._is_available: bool = False
        self._raw_dataset: Any = None
        self._license_info: str = "NVIDIA Open Model License / Creative Commons (verify upon load)"

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def license_info(self) -> str:
        return self._license_info

    def try_load(self) -> bool:
        """Attempt to load the dataset using datasets or huggingface_hub.

        Returns True if successful, False if unavailable (triggers fallback).
        """
        try:
            from datasets import load_dataset  # type: ignore[import-untyped]

            logger.info("Attempting to load %s via huggingface datasets...", self.DATASET_ID)
            ds = load_dataset(self.DATASET_ID, split="train")
            self._raw_dataset = ds
            self._is_available = True
            logger.info("Successfully loaded %d records from %s", len(ds), self.DATASET_ID)
            return True
        except ImportError:
            logger.info(
                "huggingface 'datasets' library is not installed. Using local mock adapter."
            )
            self._is_available = False
            return False
        except Exception as ex:
            logger.warning(
                "Could not download %s (%s). Using local mock adapter.",
                self.DATASET_ID,
                ex,
            )
            self._is_available = False
            return False

    def get_profiles(self, n: int = 20) -> list[dict[str, Any]]:
        """Extract and normalize demographic profiles from the dataset.

        Returns empty list if dataset is not loaded.
        """
        if not self._is_available or self._raw_dataset is None:
            return []

        profiles: list[dict[str, Any]] = []
        for i, row in enumerate(self._raw_dataset):
            if i >= n:
                break

            # Normalize schema fields
            gender_val = Gender.MALE
            raw_gender = str(row.get("gender", "")).lower()
            if "fem" in raw_gender or "mujer" in raw_gender:
                gender_val = Gender.FEMALE
            elif "non" in raw_gender:
                gender_val = Gender.NON_BINARY

            profile = {
                "serial": i + 1,
                "given_name": row.get("given_name") or row.get("name", f"Persona_{i+1}"),
                "family_name": row.get("family_name", "El Salvador"),
                "nickname": row.get("nickname"),
                "age": int(row.get("age", 30)),
                "gender": gender_val,
                "occupation": str(row.get("occupation", "Trabajador")),
                "education_level": str(row.get("education", "Secundaria")),
                "income_level": float(row.get("income_percentile", 0.5)),
                "data_source": DataSource.NEMOTRON_DATASET,
            }
            profiles.append(profile)

        return profiles
