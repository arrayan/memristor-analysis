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


'''
    ##Not needed. Disable pre demonstration. Stricly for testing!
    def create_views(self):
        conn = duckdb.connect(str(self.db_path))
        conn.execute("""
            CREATE OR REPLACE VIEW cycle_summary AS
            SELECT 
                source_file,
                cycle_number,
                COUNT(*) as measurement_count,
                MIN(Time) as start_time,
                MAX(Time) as end_time,
                AVG(I) as avg_current,
                MAX(ABS(I)) as max_abs_current,
                MIN(AV) as min_voltage,
                MAX(AV) as max_voltage
            FROM cycles
            GROUP BY source_file, cycle_number
            ORDER BY source_file, cycle_number
        """)

        conn.execute("""
            CREATE OR REPLACE VIEW file_summary AS
            SELECT 
                source_file,
                COUNT(DISTINCT cycle_number) as num_cycles,
                COUNT(*) as total_measurements,
                MIN(cycle_number) as first_cycle,
                MAX(cycle_number) as last_cycle
            FROM cycles
            GROUP BY source_file
            ORDER BY source_file
        """)
        conn.close()
'''
