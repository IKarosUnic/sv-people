"""SQLite database connection and transaction management for Saltbor persistence."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional, Sequence

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages a single SQLite connection with WAL mode and transaction support.

    Usage::

        db = DatabaseManager(Path("simulation.db"))
        db.connect()
        with db.transaction():
            db.execute("INSERT INTO ...", (...))
        db.close()

    Also works as a context manager::

        with DatabaseManager(Path("simulation.db")) as db:
            db.execute("SELECT 1")
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path: Path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the SQLite connection and enable WAL mode."""
        if self._conn is not None:
            logger.warning("DatabaseManager.connect() called while already connected.")
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
        # Enable WAL for better concurrent read performance.
        self._conn.execute("PRAGMA journal_mode=WAL")
        # Enforce foreign-key constraints.
        self._conn.execute("PRAGMA foreign_keys=ON")
        logger.info("Connected to database: %s", self.db_path)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed: %s", self.db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Return the underlying :class:`sqlite3.Connection`.

        Raises:
            RuntimeError: If the connection has not been opened.
        """
        if self._conn is None:
            raise RuntimeError(
                "Database not connected. Call connect() first."
            )
        return self._conn

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def execute(
        self,
        sql: str,
        params: Sequence[Any] | dict[str, Any] = (),
    ) -> sqlite3.Cursor:
        """Execute a single SQL statement and return the cursor.

        Parameters:
            sql: The SQL string (may contain ``?`` or ``:name`` placeholders).
            params: Positional or named bind parameters.
        """
        conn = self.get_connection()
        return conn.execute(sql, params)

    def executemany(
        self,
        sql: str,
        params_list: Sequence[Sequence[Any] | dict[str, Any]],
    ) -> sqlite3.Cursor:
        """Execute a SQL statement against every parameter set.

        Parameters:
            sql: The SQL string with placeholders.
            params_list: An iterable of bind-parameter sequences/dicts.
        """
        conn = self.get_connection()
        return conn.executemany(sql, params_list)

    # ------------------------------------------------------------------
    # Transaction management
    # ------------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for an atomic transaction.

        Commits on clean exit; rolls back on exception.
        Handles nested transactions safely.
        """
        conn = self.get_connection()
        if conn.in_transaction:
            yield conn
            return
        with conn:
            yield conn

    # ------------------------------------------------------------------
    # Context-manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> DatabaseManager:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        self.close()
