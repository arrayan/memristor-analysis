from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import duckdb


@dataclass(frozen=True)
class DuckDBClient:
    db_file: Path

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_file))


class DuckDBSession:
    """
    Context manager for DuckDB connections.
    Usage:
        with DuckDBSession(db_file) as conn:
            ...
    """

    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.conn: duckdb.DuckDBPyConnection | None = None

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        self.conn = duckdb.connect(str(self.db_file))
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
