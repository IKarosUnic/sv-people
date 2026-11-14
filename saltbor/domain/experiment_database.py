"""Compact Experiment Database and Knowledge Management Engine for SALTBOR.

Directly addresses the architectural problem of duplicate procedural source code
appearing inside experimental records.

Enforces strict separation of:
A. EXPERIMENT DEFINITION (Question, hypotheses, domain, parameters, initial conditions, seeds)
B. EXPERIMENT EXECUTION (Run ID, timestamp, simulation version, runtime, status)
C. RESULTS (Key indicators, bootstrap 95% CIs, statistical summaries, events, limitations)
D. EVIDENCE (Data references, provenance, logs, test references, methodology)
E. IMPLEMENTATION TRACEABILITY (File paths, classes, functions, git commit, graphify node, test ID)

Provides 3-level progressive disclosure:
1. SUMMARY: Research question, status, findings, key limitations.
2. EVIDENCE: Empirical indicators, 95% CIs, distributions, data provenance.
3. TECHNICAL: Source file paths, class/function references, test suites, git commit.

Does NOT duplicate entire Python source files into database records.
Enables on-demand retrieval of source code directly from the codebase.
Includes safe migration for historical records.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from saltbor.domain.models import (
    CompactExperimentRecord,
    ExperimentDefinitionRecord,
    ExperimentEvidenceRecord,
    ExperimentExecutionRecord,
    ExperimentResultRecord,
    ExperimentTraceabilityRecord,
)

logger = logging.getLogger(__name__)


class CompactExperimentDatabase:
    """Stores compact, highly structured experimental records with full traceability and progressive disclosure."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or ":memory:"
        self.in_memory_records: Dict[str, CompactExperimentRecord] = {}
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        """Create structured compact experiment tables in SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compact_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    research_question TEXT NOT NULL,
                    execution_status TEXT NOT NULL,
                    validation_tier TEXT NOT NULL,
                    definition_json TEXT NOT NULL,
                    execution_json TEXT NOT NULL,
                    results_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    traceability_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_exp_domain ON compact_experiments(domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_exp_status ON compact_experiments(execution_status)")
            conn.commit()
            conn.close()
        except Exception as ex:
            logger.debug("SQLite initialization fallback (in-memory mode): %s", ex)

    def save_experiment(self, record: CompactExperimentRecord) -> None:
        """Save a structured experiment record to memory and SQLite without embedding source code."""
        self.in_memory_records[record.experiment_id] = record

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = time.time()
            cursor.execute(
                """
                INSERT OR REPLACE INTO compact_experiments (
                    experiment_id, name, domain, research_question, execution_status,
                    validation_tier, definition_json, execution_json, results_json,
                    evidence_json, traceability_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.experiment_id,
                    record.name,
                    record.definition.domain,
                    record.definition.research_question,
                    record.execution.execution_status,
                    record.traceability.implementation_status,
                    json.dumps(dataclasses.asdict(record.definition)),
                    json.dumps(dataclasses.asdict(record.execution)),
                    json.dumps(dataclasses.asdict(record.results)),
                    json.dumps(dataclasses.asdict(record.evidence)),
                    json.dumps(dataclasses.asdict(record.traceability)),
                    now,
                    now,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as ex:
            logger.debug("SQLite save fallback: %s", ex)

    def get_experiment(self, experiment_id: str) -> Optional[CompactExperimentRecord]:
        """Retrieve full structured compact experiment record."""
        if experiment_id in self.in_memory_records:
            return self.in_memory_records[experiment_id]

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM compact_experiments WHERE experiment_id = ?", (experiment_id,)).fetchone()
            conn.close()
            if row:
                return CompactExperimentRecord(
                    experiment_id=row["experiment_id"],
                    name=row["name"],
                    definition=ExperimentDefinitionRecord(**json.loads(row["definition_json"])),
                    execution=ExperimentExecutionRecord(**json.loads(row["execution_json"])),
                    results=ExperimentResultRecord(**json.loads(row["results_json"])),
                    evidence=ExperimentEvidenceRecord(**json.loads(row["evidence_json"])),
                    traceability=ExperimentTraceabilityRecord(**json.loads(row["traceability_json"])),
                )
        except Exception as ex:
            logger.debug("SQLite get fallback: %s", ex)
        return None

    # =========================================================================
    # 3 Information Levels (Progressive Disclosure)
    # =========================================================================

    def get_summary_level(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Level 1: SUMMARY - Research question, status, main findings, and limitations."""
        exp = self.get_experiment(experiment_id)
        if not exp:
            return None
        return {
            "level": "SUMMARY",
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "domain": exp.definition.domain,
            "research_question": exp.definition.research_question,
            "execution_status": exp.execution.execution_status,
            "hypotheses_summary": exp.definition.hypotheses,
            "key_indicators": exp.results.key_indicators,
            "limitations": exp.results.limitations,
        }

    def get_evidence_level(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Level 2: EVIDENCE - Empirical indicators, 95% CIs, data references, methodology."""
        exp = self.get_experiment(experiment_id)
        if not exp:
            return None
        return {
            "level": "EVIDENCE",
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "indicators": exp.results.key_indicators,
            "statistical_summaries": exp.results.statistical_summaries,
            "confidence_intervals_95": exp.results.confidence_intervals_95,
            "significant_events": exp.results.significant_events,
            "data_provenance": exp.evidence.provenance,
            "data_references": exp.evidence.data_references,
            "methodology": exp.evidence.methodology,
        }

    def get_technical_level(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Level 3: TECHNICAL - Source references, classes, functions, git commit, graphify, tests."""
        exp = self.get_experiment(experiment_id)
        if not exp:
            return None
        return {
            "level": "TECHNICAL",
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "execution_metadata": dataclasses.asdict(exp.execution),
            "traceability": dataclasses.asdict(exp.traceability),
            "source_files": exp.traceability.source_file_paths,
            "relevant_classes": exp.traceability.relevant_classes,
            "relevant_functions": exp.traceability.relevant_functions,
            "git_commit": exp.traceability.git_commit,
            "graphify_nodes": exp.traceability.graphify_references,
            "test_identifiers": exp.traceability.test_identifiers,
            "logs": exp.evidence.relevant_logs,
        }

    def fetch_source_code_on_demand(self, experiment_id: str) -> Dict[str, str]:
        """Retrieve full source code on demand directly from the actual codebase."""
        exp = self.get_experiment(experiment_id)
        if not exp:
            return {}

        sources = {}
        for path_str in exp.traceability.source_file_paths:
            p = Path(path_str)
            if p.exists() and p.is_file():
                try:
                    sources[path_str] = p.read_text(encoding="utf-8")
                except Exception as ex:
                    sources[path_str] = f"Error reading source file: {ex}"
            else:
                sources[path_str] = "File path not found in local workspace."
        return sources

    def list_all_experiments(self) -> List[Dict[str, Any]]:
        """Return catalog of all stored experiments with their status."""
        # Query SQLite if available
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT experiment_id, name, domain, research_question, execution_status, validation_tier FROM compact_experiments").fetchall()
            conn.close()
            if rows:
                return [dict(r) for r in rows]
        except Exception:
            pass

        return [
            {
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "domain": exp.definition.domain,
                "research_question": exp.definition.research_question,
                "execution_status": exp.execution.execution_status,
                "validation_tier": exp.traceability.implementation_status,
            }
            for exp in self.in_memory_records.values()
        ]

    def migrate_legacy_experiment_results(self, legacy_dir: str = "experiments/results") -> int:
        """Safely import historical experiment JSON files into the compact database without deleting data."""
        p_dir = Path(legacy_dir)
        if not p_dir.exists():
            return 0

        migrated_count = 0
        for json_path in p_dir.rglob("*.json"):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                exp_id = data.get("experiment_id") or json_path.stem.upper()
                name = data.get("name") or exp_id
                if self.get_experiment(exp_id):
                    continue  # Already recorded

                rec = CompactExperimentRecord(
                    experiment_id=exp_id,
                    name=name,
                    definition=ExperimentDefinitionRecord(
                        experiment_id=exp_id,
                        research_question=data.get("summary") or "Historical simulation experiment",
                        hypotheses=data.get("hypotheses", []),
                        domain="historical_migration",
                        parameters={},
                        initial_conditions={},
                        population_selection={"source": "legacy_results"},
                        geographic_scope="El Salvador",
                        random_seeds=[42],
                    ),
                    execution=ExperimentExecutionRecord(
                        run_id=f"migrated_{exp_id}",
                        execution_time_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        simulation_version="1.12.0",
                        configuration_version="legacy",
                        resource_consumption_sec=float(data.get("duration_seconds", 0.05)),
                        execution_status="SUCCESS" if data.get("success", True) else "FAILED",
                    ),
                    results=ExperimentResultRecord(
                        key_indicators={k: float(v) for k, v in data.get("metrics", {}).items() if isinstance(v, (int, float))},
                        statistical_summaries={},
                        comparisons={},
                        confidence_intervals_95={},
                        significant_events=[],
                        unexpected_outcomes=[],
                        limitations=["Migrated from legacy unstructured experiment output."],
                    ),
                    evidence=ExperimentEvidenceRecord(
                        data_references=[str(json_path)],
                        provenance="Migrated from experiments/results/",
                        relevant_logs=[],
                        test_references=[],
                        methodology="Historical behavioral run",
                    ),
                    traceability=ExperimentTraceabilityRecord(
                        source_file_paths=["saltbor/experiments/experiments.py"],
                        relevant_classes=["BaseExperiment"],
                        relevant_functions=["run"],
                        git_commit="migrated",
                        graphify_references=["BaseExperiment"],
                        test_identifiers=["tests/test_experiments/"],
                        implementation_status="HISTORICALLY_VALIDATED",
                    ),
                )
                self.save_experiment(rec)
                migrated_count += 1
            except Exception as ex:
                logger.debug("Skipping unparseable legacy file %s: %s", json_path, ex)

        logger.info("Migrated %d legacy experiment records into CompactExperimentDatabase.", migrated_count)
        return migrated_count
