"""Unit tests for CompactExperimentDatabase and progressive disclosure levels."""

import pytest
from saltbor.domain.experiment_database import CompactExperimentDatabase
from saltbor.domain.models import (
    CompactExperimentRecord,
    ExperimentDefinitionRecord,
    ExperimentEvidenceRecord,
    ExperimentExecutionRecord,
    ExperimentResultRecord,
    ExperimentTraceabilityRecord,
)


def test_compact_database_progressive_disclosure():
    db = CompactExperimentDatabase(db_path=":memory:")
    rec = CompactExperimentRecord(
        experiment_id="EXP_TEST_DISCLOSURE",
        name="Disclosure Test",
        definition=ExperimentDefinitionRecord(
            experiment_id="EXP_TEST_DISCLOSURE",
            research_question="Does progressive disclosure work cleanly?",
            hypotheses=[{"hypothesis": "Level 1 is summary, Level 3 is technical", "confirmed": True}],
            domain="test",
            parameters={"p1": 10},
            initial_conditions={},
            population_selection={},
            geographic_scope="El Salvador",
            random_seeds=[42],
        ),
        execution=ExperimentExecutionRecord(
            run_id="run_1",
            execution_time_iso="2026-11-14T12:00:00Z",
            simulation_version="1.13.0",
            configuration_version="default",
            resource_consumption_sec=0.02,
            execution_status="SUCCESS",
        ),
        results=ExperimentResultRecord(
            key_indicators={"accuracy": 0.98},
            statistical_summaries={},
            comparisons={},
            confidence_intervals_95={"accuracy": (0.95, 1.0)},
            significant_events=[],
            unexpected_outcomes=[],
            limitations=["Unit test only"],
        ),
        evidence=ExperimentEvidenceRecord(
            data_references=["local_memory"],
            provenance="Unit test framework",
            relevant_logs=[],
            test_references=["tests/test_domain/test_compact_experiment_db.py"],
            methodology="In-memory assertions",
        ),
        traceability=ExperimentTraceabilityRecord(
            source_file_paths=["saltbor/domain/experiment_database.py"],
            relevant_classes=["CompactExperimentDatabase"],
            relevant_functions=["get_summary_level"],
            git_commit="HEAD",
            graphify_references=["CompactExperimentDatabase"],
            test_identifiers=["test_compact_database_progressive_disclosure"],
            implementation_status="TESTED",
        ),
    )
    db.save_experiment(rec)

    # 1. Summary Level
    lvl1 = db.get_summary_level("EXP_TEST_DISCLOSURE")
    assert lvl1["level"] == "SUMMARY"
    assert "research_question" in lvl1
    assert "key_indicators" in lvl1
    assert "source_file_paths" not in lvl1

    # 2. Evidence Level
    lvl2 = db.get_evidence_level("EXP_TEST_DISCLOSURE")
    assert lvl2["level"] == "EVIDENCE"
    assert "confidence_intervals_95" in lvl2
    assert "data_provenance" in lvl2

    # 3. Technical Level
    lvl3 = db.get_technical_level("EXP_TEST_DISCLOSURE")
    assert lvl3["level"] == "TECHNICAL"
    assert "source_files" in lvl3
    assert "git_commit" in lvl3

    # On-demand source code retrieval
    sources = db.fetch_source_code_on_demand("EXP_TEST_DISCLOSURE")
    assert len(sources) == 1
    assert "class CompactExperimentDatabase" in list(sources.values())[0]
