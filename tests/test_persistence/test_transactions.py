"""Comprehensive tests for DatabaseManager transaction semantics and nesting.

Validates the nesting depth counter (_txn_depth), single-commit coalescing,
atomic rollbacks across inner/outer blocks, and repository integration.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.repositories import HumanRepository


def test_transaction_depth_tracking(temp_db: DatabaseManager) -> None:
    """_txn_depth correctly tracks nesting depth and unwinds to 0 on exit."""
    assert temp_db._txn_depth == 0

    with temp_db.transaction():
        assert temp_db._txn_depth == 1
        with temp_db.transaction():
            assert temp_db._txn_depth == 2
            with temp_db.transaction():
                assert temp_db._txn_depth == 3
            assert temp_db._txn_depth == 2
        assert temp_db._txn_depth == 1

    assert temp_db._txn_depth == 0


def test_transaction_depth_resets_on_exception(temp_db: DatabaseManager) -> None:
    """_txn_depth resets to 0 even if an exception occurs deep inside nesting."""
    assert temp_db._txn_depth == 0

    with pytest.raises(RuntimeError, match="deep explosion"):
        with temp_db.transaction():
            assert temp_db._txn_depth == 1
            with temp_db.transaction():
                assert temp_db._txn_depth == 2
                with temp_db.transaction():
                    assert temp_db._txn_depth == 3
                    raise RuntimeError("deep explosion")

    assert temp_db._txn_depth == 0


def test_single_transaction_commit_and_rollback(temp_db: DatabaseManager) -> None:
    """Single-level transactions commit on success and rollback on error."""
    temp_db.execute("CREATE TABLE test_items (id INTEGER PRIMARY KEY, name TEXT)")

    # 1. Successful transaction commits
    with temp_db.transaction():
        temp_db.execute("INSERT INTO test_items (id, name) VALUES (?, ?)", (1, "Alpha"))

    row = temp_db.execute("SELECT name FROM test_items WHERE id = 1").fetchone()
    assert row is not None and row["name"] == "Alpha"

    # 2. Failing transaction rolls back
    with pytest.raises(ValueError, match="fail"):
        with temp_db.transaction():
            temp_db.execute("INSERT INTO test_items (id, name) VALUES (?, ?)", (2, "Beta"))
            raise ValueError("fail")

    assert temp_db.execute("SELECT COUNT(*) FROM test_items WHERE id = 2").fetchone()[0] == 0
    assert temp_db._txn_depth == 0


def test_nested_transaction_commits_atomically(temp_db: DatabaseManager) -> None:
    """Nested transaction blocks issue exactly ONE BEGIN IMMEDIATE and ONE COMMIT."""
    temp_db.execute("CREATE TABLE test_counts (val INT)")

    recorded_statements: list[str] = []
    conn = temp_db.get_connection()
    conn.set_trace_callback(recorded_statements.append)

    try:
        with temp_db.transaction():
            temp_db.execute("INSERT INTO test_counts VALUES (10)")
            with temp_db.transaction():
                temp_db.execute("INSERT INTO test_counts VALUES (20)")
            with temp_db.transaction():
                temp_db.execute("INSERT INTO test_counts VALUES (30)")
    finally:
        conn.set_trace_callback(None)

    # Filter control statements
    control_stmts = [
        s.strip().upper()
        for s in recorded_statements
        if any(keyword in s.upper() for keyword in ("BEGIN", "COMMIT", "ROLLBACK"))
    ]

    assert control_stmts == ["BEGIN IMMEDIATE", "COMMIT"]

    rows = [r[0] for r in temp_db.execute("SELECT val FROM test_counts ORDER BY val").fetchall()]
    assert rows == [10, 20, 30]
    assert temp_db._txn_depth == 0


def test_nested_transaction_outer_rollback_aborts_inner_writes(temp_db: DatabaseManager) -> None:
    """Inner block clean exit does NOT commit early; outer failure rolls back inner writes.

    This directly validates the a615da5 bug fix where an outer block before
    first DML had in_transaction == False, causing inner blocks to commit on their own.
    """
    temp_db.execute("CREATE TABLE test_log (msg TEXT)")

    with pytest.raises(RuntimeError, match="outer crash after inner completed"):
        with temp_db.transaction():
            # Outer block performs NO DML before entering inner block
            with temp_db.transaction():
                temp_db.execute("INSERT INTO test_log VALUES ('inner written successfully')")
            # Inner block exited cleanly, but outer block fails afterwards
            temp_db.execute("INSERT INTO test_log VALUES ('outer partial')")
            raise RuntimeError("outer crash after inner completed")

    # Both inner and outer writes must have been completely rolled back
    count = temp_db.execute("SELECT COUNT(*) FROM test_log").fetchone()[0]
    assert count == 0
    assert temp_db._txn_depth == 0


def test_nested_transaction_inner_exception_aborts_all(temp_db: DatabaseManager) -> None:
    """An exception inside an inner transaction aborts outer and inner writes."""
    temp_db.execute("CREATE TABLE test_records (id INT, label TEXT)")

    with pytest.raises(ZeroDivisionError):
        with temp_db.transaction():
            temp_db.execute("INSERT INTO test_records VALUES (1, 'initial')")
            with temp_db.transaction():
                temp_db.execute("INSERT INTO test_records VALUES (2, 'doomed')")
                _ = 1 / 0

    count = temp_db.execute("SELECT COUNT(*) FROM test_records").fetchone()[0]
    assert count == 0
    assert temp_db._txn_depth == 0


def test_transaction_reusability_after_rollback(temp_db: DatabaseManager) -> None:
    """Connection and transaction manager remain fully operational after rollbacks."""
    temp_db.execute("CREATE TABLE test_resilience (step TEXT)")

    # 1. Rollback
    with pytest.raises(RuntimeError):
        with temp_db.transaction():
            with temp_db.transaction():
                temp_db.execute("INSERT INTO test_resilience VALUES ('should rollback')")
            raise RuntimeError("abort")

    # 2. Subsequent transaction succeeds cleanly
    with temp_db.transaction():
        temp_db.execute("INSERT INTO test_resilience VALUES ('clean commit')")

    rows = [r[0] for r in temp_db.execute("SELECT step FROM test_resilience").fetchall()]
    assert rows == ["clean commit"]
    assert temp_db._txn_depth == 0


def test_transaction_external_already_open(temp_db: DatabaseManager) -> None:
    """If connection was already in a transaction, db.transaction() does not issue BEGIN/COMMIT."""
    temp_db.execute("CREATE TABLE test_external (val INT)")
    conn = temp_db.get_connection()

    # Manually open a transaction outside DatabaseManager.transaction
    conn.execute("BEGIN IMMEDIATE")
    assert conn.in_transaction

    with temp_db.transaction() as yield_conn:
        assert yield_conn is conn
        temp_db.execute("INSERT INTO test_external VALUES (999)")

    # Should still be in external transaction because already_open was True
    assert conn.in_transaction
    conn.commit()

    count = temp_db.execute("SELECT COUNT(*) FROM test_external WHERE val = 999").fetchone()[0]
    assert count == 1
    assert temp_db._txn_depth == 0


def test_repository_nested_transaction_atomicity(temp_db: DatabaseManager, population_20) -> None:
    """Simulates checkpointing: wrapping multiple repo.save() calls in an outer transaction.

    Each repo.save() invokes with self.db.transaction(): internally. If the batch
    fails mid-way, all saved humans are rolled back atomically.
    """
    h_repo = HumanRepository(temp_db)
    assert h_repo.count() == 0

    # 1. Simulated failure mid-checkpoint
    with pytest.raises(RuntimeError, match="checkpoint failure mid-batch"):
        with temp_db.transaction():
            # Save first 5 humans
            for human in population_20[:5]:
                h_repo.save(human)
            # Simulated failure before checkpoint metadata is written
            raise RuntimeError("checkpoint failure mid-batch")

    # No humans should have leaked into the database
    assert h_repo.count() == 0
    assert temp_db._txn_depth == 0

    # 2. Successful batch checkpoint commits all 20 humans in one transaction
    recorded: list[str] = []
    conn = temp_db.get_connection()
    conn.set_trace_callback(recorded.append)

    try:
        with temp_db.transaction():
            for human in population_20:
                h_repo.save(human)
    finally:
        conn.set_trace_callback(None)

    commits = [s for s in recorded if s.strip().upper() == "COMMIT"]
    # Only 1 COMMIT occurred for all 20 human saves, rather than 20 separate commits!
    assert len(commits) == 1
    assert h_repo.count() == 20
    assert temp_db._txn_depth == 0
