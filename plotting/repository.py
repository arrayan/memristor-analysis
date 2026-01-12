from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
import duckdb


@dataclass(frozen=True)
class MemristorRepository:
    """
    Data access layer: SQL -> pandas DataFrames.
    No plotting, no transforms (groupby/apply/merge) beyond what SQL returns.
    """
    conn: duckdb.DuckDBPyConnection

    def list_endurance_sets(self, endurance_like: str = "%endurance set%") -> list[str]:
        rows = self.conn.execute(
            """
            SELECT DISTINCT source_file
            FROM cycles
            WHERE source_file LIKE ?
            ORDER BY source_file
            """,
            [endurance_like],
        ).fetchall()
        return [r[0] for r in rows]
    
    def load_endurance_cycles_for_set(self, source_file: str) -> pd.DataFrame:
        """
        Raw data needed for endurance/end_df/scatter:
        cycle_number, Time, AV, AI, VSET, ILRS, IHRS
        """
        return self.conn.execute(
            """
            SELECT cycle_number, Time, AV, AI, VSET, ILRS, IHRS
            FROM cycles
            WHERE source_file = ?
            ORDER BY cycle_number, Time
            """,
            [source_file],
        ).df()

    def load_cycles_for_set(self, source_file: str) -> pd.DataFrame:
        # NOTE: include Time because your original query orders by Time
        return self.conn.execute(
            """
            SELECT cycle_number, Time, AV, AI, NORM_COND
            FROM cycles
            WHERE source_file = ?
            ORDER BY cycle_number, Time
            """,
            [source_file],
        ).df()

    def load_forming_voltage_global(self, electroforming_like: str = "%Electroforming%") -> float | None:
        df = self.conn.execute(
            """
            SELECT MAX(VFORM) AS V_forming_global
            FROM cycles
            WHERE source_file LIKE ?
            """,
            [electroforming_like],
        ).df()

        if df.empty:
            return None

        val = df["V_forming_global"].iloc[0]
        # DuckDB returns None for all-null MAX; handle that too
        return None if pd.isna(val) else float(val)

    def load_classic_cycle_params_for_sets(self, sets: list[str]) -> pd.DataFrame:
        """
        Per (source_file, cycle_number) classic params used by CDF/boxplots.
        """
        if not sets:
            return pd.DataFrame(columns=["source_file", "cycle_number", "VSET", "R_LRS", "R_HRS"])

        return self.conn.execute(
            """
            SELECT source_file,
                   cycle_number,
                   MAX(VSET) AS VSET,
                   MAX(ILRS) AS R_LRS,
                   MAX(IHRS) AS R_HRS
            FROM cycles
            WHERE source_file IN (SELECT * FROM UNNEST(?))
            GROUP BY source_file, cycle_number
            ORDER BY source_file, cycle_number
            """,
            [sets],
        ).df()
