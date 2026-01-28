"""
Example queries and analysis utilities for the memristor DuckDB database.
"""

import duckdb
import polars as pl
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).parent / "memristor_data.duckdb"


def get_connection(
    db_path: Optional[Path] = None, read_only: bool = True
) -> duckdb.DuckDBPyConnection:
    """Get a connection to the DuckDB database."""
    path = db_path or DB_PATH
    return duckdb.connect(str(path), read_only=read_only)


def query(sql: str, db_path: Optional[Path] = None) -> pl.DataFrame:
    """Run a SQL query and return a Polars DataFrame."""
    conn = get_connection(db_path)
    result = conn.execute(sql).pl()
    conn.close()
    return result


def list_tables(db_path: Optional[Path] = None) -> list[str]:
    """List all tables in the database."""
    conn = get_connection(db_path)
    tables = conn.execute("SHOW TABLES").fetchall()
    conn.close()
    return [t[0] for t in tables]


def describe_table(table_name: str, db_path: Optional[Path] = None) -> pl.DataFrame:
    """Get schema information for a table."""
    return query(f"DESCRIBE {table_name}", db_path)


def list_source_files(db_path: Optional[Path] = None) -> pl.DataFrame:
    """List all source files in a batch-processed database."""
    return query("SELECT * FROM file_summary", db_path)


# Example analysis functions


def get_cycle_data(
    cycle_number: int, source_file: Optional[str] = None, db_path: Optional[Path] = None
) -> pl.DataFrame:
    """Get all data for a specific cycle."""
    if source_file:
        where = f"WHERE cycle_number = {cycle_number} AND source_file = '{source_file}'"
    else:
        where = f"WHERE cycle_number = {cycle_number}"
    return query(f"SELECT * FROM cycles {where} ORDER BY Time", db_path)


def get_iv_curve(
    cycle_number: int, source_file: Optional[str] = None, db_path: Optional[Path] = None
) -> pl.DataFrame:
    """Get voltage-current data for plotting IV curves."""
    if source_file:
        where = f"WHERE cycle_number = {cycle_number} AND source_file = '{source_file}'"
    else:
        where = f"WHERE cycle_number = {cycle_number}"
    return query(
        f"""
        SELECT AV as voltage, I as current, Time, source_file
        FROM cycles 
        {where}
        ORDER BY Time
    """,
        db_path,
    )


def get_all_cycle_summary(db_path: Optional[Path] = None) -> pl.DataFrame:
    """Get summary statistics for all cycles."""
    return query(
        "SELECT * FROM cycle_summary ORDER BY source_file, cycle_number", db_path
    )


def get_resistance_states(
    source_file: Optional[str] = None, db_path: Optional[Path] = None
) -> pl.DataFrame:
    """Extract high and low resistance state values per cycle."""
    filter_clause = f"AND source_file = '{source_file}'" if source_file else ""

    return query(
        f"""
        SELECT 
            source_file,
            cycle_number,
            MAX(ILRS) as low_resistance_current,
            MAX(IHRS) as high_resistance_current,
            MAX(VSET) as set_voltage,
            CASE WHEN MAX(IHRS) > 0 THEN MAX(ILRS) / MAX(IHRS) ELSE NULL END as resistance_ratio
        FROM cycles
        WHERE (ILRS IS NOT NULL OR IHRS IS NOT NULL) {filter_clause}
        GROUP BY source_file, cycle_number
        ORDER BY source_file, cycle_number
    """,
        db_path,
    )


def get_endurance_trend(
    source_file: Optional[str] = None, db_path: Optional[Path] = None
) -> pl.DataFrame:
    """Analyze how device characteristics change over cycles (endurance)."""
    where = f"WHERE source_file = '{source_file}'" if source_file else ""

    return query(
        f"""
        SELECT 
            source_file,
            cycle_number,
            AVG(I) as avg_current,
            MAX(IMAX) as max_current,
            MAX(VSET) as set_voltage,
            MAX(ILRS) as lrs_current,
            MAX(IHRS) as hrs_current
        FROM cycles
        {where}
        GROUP BY source_file, cycle_number
        ORDER BY source_file, cycle_number
    """,
        db_path,
    )


def compare_files(db_path: Optional[Path] = None) -> pl.DataFrame:
    """Compare statistics across different source files (batch mode)."""
    return query(
        """
        SELECT 
            source_file,
            COUNT(DISTINCT cycle_number) as num_cycles,
            COUNT(*) as total_measurements,
            AVG(I) as overall_avg_current,
            MAX(ABS(I)) as max_abs_current,
            AVG(CASE WHEN ILRS IS NOT NULL THEN ILRS END) as avg_lrs_current,
            AVG(CASE WHEN IHRS IS NOT NULL THEN IHRS END) as avg_hrs_current
        FROM cycles
        GROUP BY source_file
        ORDER BY source_file
    """,
        db_path,
    )


if __name__ == "__main__":
    print("=== Memristor Analysis Database ===\n")

    print("Tables available:")
    for table in list_tables():
        print(f"  - {table}")

    print("\n--- Cycles Table Schema ---")
    print(describe_table("cycles").to_pandas())

    # Check if file_summary view exists (batch mode)
    tables = list_tables()
    if "file_summary" in tables:
        print("\n--- Source Files (Batch Mode) ---")
        print(list_source_files())

    print("\n--- Sample Cycle Summary ---")
    print(get_all_cycle_summary().head(10))

    print("\n--- Resistance States ---")
    print(get_resistance_states().head(10))

    print("\n--- Endurance Trend ---")
    print(get_endurance_trend().head(10))

    print("\n--- Sample IV Curve Data (Cycle 200) ---")
    iv_data = get_iv_curve(200)
    print(iv_data.head(10))

    # Show file comparison if batch mode
    if "file_summary" in tables:
        print("\n--- File Comparison ---")
        print(compare_files())
