import duckdb
import polars as pl
from pathlib import Path

"""Writes DataFrames to DuckDB database."""


class DuckDBWriter:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def write_cycles(self, df: pl.DataFrame) -> int:
        """Write cycles DataFrame to database."""
        conn = duckdb.connect(str(self.db_path))
        conn.register("cycles_view", df)
        conn.execute("DROP TABLE IF EXISTS cycles")
        conn.execute("CREATE TABLE cycles AS SELECT * FROM cycles_view")
        conn.unregister("cycles_view")

        row_count = conn.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
        conn.close()

        return row_count

    def write_metadata_table(self, table_name: str, df: pl.DataFrame) -> int:
        """Write a metadata table to database."""
        conn = duckdb.connect(str(self.db_path))
        conn.register("meta_view", df)
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM meta_view")
        conn.unregister("meta_view")

        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        conn.close()

        return row_count
