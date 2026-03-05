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

    def list_endurance_resets(
        self, endurance_reset_like: str = "%endurance reset%"
    ) -> list[str]:
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

    def load_endurance_cycles_for_set(self, source_file: str) -> pd.DataFrame:
        """
        Raw data from endurance set files:
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

    def load_endurance_cycles_for_reset(self, source_file: str) -> pd.DataFrame:
        """
        Raw data from endurance reset files:
        cycle_number, Time, AV, AI
        Used for V_reset and I_reset_max.
        """
        return self.conn.execute(
            """
            SELECT cycle_number, Time, AV, AI
            FROM cycles
            WHERE source_file = ?
            ORDER BY cycle_number, Time
            """,
            [source_file],
        ).df()

    def load_cycles_for_set(self, source_file: str) -> pd.DataFrame:
        return self.conn.execute(
            """
            SELECT cycle_number, Time, AV, AI, NORM_COND
            FROM cycles
            WHERE source_file = ?
            ORDER BY cycle_number, Time
            """,
            [source_file],
        ).df()

    def load_forming_voltage_per_device(
        self,
        devices: list[str],
        electroforming_like: str = "%Electroforming%",
    ) -> dict[str, float]:
        """
        Per-device forming voltage: MAX(VFORM) from each device's forming file.
        Returns {device: V_forming}.
        """
        result = {}
        for device in devices:
            df = self.conn.execute(
                """
                SELECT MAX(VFORM) AS vf
                FROM cycles
                WHERE source_file LIKE ?
                  AND source_file LIKE ?
                """,
                [electroforming_like, f"%{device}%"],
            ).df()
            if not df.empty:
                val = df["vf"].iloc[0]
                if not pd.isna(val):
                    result[device] = float(val)
        return result

    def load_leakage_current_per_device(
        self,
        devices: list[str],
        leakage_like: str = "%Leakage%",
    ) -> dict[str, float]:
        """
        Per-device leakage current: MAX(|AI|) from each device's leakage file.
        Returns {device: I_leakage_pristine}.
        """
        result = {}
        for device in devices:
            df = self.conn.execute(
                """
                SELECT MAX(ABS(AI)) AS il
                FROM cycles
                WHERE source_file LIKE ?
                  AND source_file LIKE ?
                """,
                [leakage_like, f"%{device}%"],
            ).df()
            if not df.empty:
                val = df["il"].iloc[0]
                if not pd.isna(val):
                    result[device] = float(val)
        return result

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
        return None if pd.isna(val) else float(val)

    def load_classic_cycle_params_for_sets(self, sets: list[str]) -> pd.DataFrame:
        """
        Per (source_file, cycle_number) classic params used by CDF/boxplots.
        R_LRS = 0.2 / I_LRS, R_HRS = 0.2 / I_HRS as per spec.
        """
        if not sets:
            return pd.DataFrame(
                columns=["source_file", "cycle_number", "VSET", "R_LRS", "R_HRS"]
            )

        return self.conn.execute(
            """
            SELECT source_file,
                   cycle_number,
                   MAX(VSET)                              AS VSET,
                   MAX(ILRS)                              AS I_LRS,
                   MAX(IHRS)                              AS I_HRS,
                   0.2 / NULLIF(MAX(ILRS), 0)            AS R_LRS,
                   0.2 / NULLIF(MAX(IHRS), 0)            AS R_HRS
            FROM cycles
            WHERE source_file IN (SELECT * FROM UNNEST(?))
            GROUP BY source_file, cycle_number
            ORDER BY source_file, cycle_number
            """,
            [sets],
        ).df()
