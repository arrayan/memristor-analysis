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

    def load_first_v_reset(
        self, endurance_reset_like: str = "%endurance_reset%"
    ) -> dict[str, float]:
        """
        1st V_reset per device = AV at max(|AI|) in the very first cycle
        (MIN cycle_number) of each device's endurance_reset file.

        source_file pattern: {stack}_{device}_{nr}_endurance_reset
        Device is extracted as the second underscore-delimited token.

        Returns: dict mapping device (e.g. "D12") -> first_v_reset value
        """
        df = self.conn.execute(
            """
            WITH first_cycles AS (
                SELECT source_file,
                       MIN(cycle_number) AS first_cn
                FROM cycles
                WHERE source_file LIKE ?
                GROUP BY source_file
            ),
            ranked AS (
                SELECT c.source_file,
                       c.AV,
                       ROW_NUMBER() OVER (
                           PARTITION BY c.source_file
                           ORDER BY ABS(c.AI) DESC
                       ) AS rn
                FROM cycles c
                JOIN first_cycles fc
                  ON c.source_file = fc.source_file
                 AND c.cycle_number = fc.first_cn
            )
            SELECT source_file,
                   AV AS first_v_reset
            FROM ranked
            WHERE rn = 1
            """,
            [endurance_reset_like],
        ).df()

        if df.empty:
            return {}

        result = {}
        for _, row in df.iterrows():
            # extract device: {stack}_{device}_{nr}_endurance_reset -> token[1]
            parts = str(row["source_file"]).split("_")
            if len(parts) >= 2:
                device = parts[1]
                val = row["first_v_reset"]
                if not pd.isna(val):
                    result[device] = float(val)
        return result

    def load_cycles_for_reset_set(self, source_file: str) -> pd.DataFrame:
        """Raw reset sweep data for butterfly plot: cycle_number, AV, AI."""
        return self.conn.execute(
            """
            SELECT cycle_number, Time, AV, AI
            FROM cycles
            WHERE source_file = ?
            ORDER BY cycle_number, Time
            """,
            [source_file],
        ).df()

    def list_reset_sets(self, endurance_reset_like: str = "%endurance_reset%") -> list[str]:
        rows = self.conn.execute(
            """
            SELECT DISTINCT source_file
            FROM cycles
            WHERE source_file LIKE ?
            ORDER BY source_file
            """,
            [endurance_reset_like],
        ).fetchall()
        return [r[0] for r in rows]

    def load_forming_voltage_global(
        self, electroforming_like: str = "%Electroforming%"
    ) -> float | None:
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
            return pd.DataFrame(
                columns=["source_file", "cycle_number", "VSET", "R_LRS", "R_HRS"]
            )

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

    def list_leakage_sets(self, pattern: str = "%leakage%") -> list[str]:
        rows = self.conn.execute(
            """
            SELECT DISTINCT source_file
            FROM cycles
            WHERE source_file LIKE ?
            ORDER BY source_file
            """,
            [pattern],
        ).fetchall()
        return [r[0] for r in rows]

    def load_leakage_for_set(self, source_file: str) -> pd.DataFrame:
        return self.conn.execute(
            """
            SELECT cycle_number, Time, AV, AI
            FROM cycles
            WHERE source_file = ?
            ORDER BY cycle_number, Time
            """,
            [source_file],
        ).df()