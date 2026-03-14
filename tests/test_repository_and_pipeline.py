"""
Integration and edge case tests:
1. repository.py — DuckDB integration tests
2. transforms.py — edge cases (zero current, negative current)
3. pipeline.py — smoke test with in-memory DuckDB
"""

from __future__ import annotations

import pandas as pd
import pytest
import duckdb

from app.plotting.repository import MemristorRepository
from app.plotting.transforms import (
    build_endurance_table,
    compute_i_lrs_from_reset,
    _device_from_source,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def conn():
    """In-memory DuckDB connection with a minimal cycles table."""
    c = duckdb.connect(":memory:")
    c.execute("""
        CREATE TABLE cycles (
            source_file VARCHAR,
            cycle_number INTEGER,
            Time DOUBLE,
            AV DOUBLE,
            AI DOUBLE,
            VSET DOUBLE,
            ILRS DOUBLE,
            IHRS DOUBLE,
            NORM_COND DOUBLE,
            VFORM DOUBLE
        )
    """)
    return c


@pytest.fixture
def repo(conn):
    return MemristorRepository(conn)


def _insert_rows(conn, rows: list[dict]):
    """Helper to insert rows into cycles table."""
    for row in rows:
        conn.execute(
            """
            INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                row.get("source_file"),
                row.get("cycle_number", 1),
                row.get("Time", 0.0),
                row.get("AV", 0.0),
                row.get("AI", 0.0),
                row.get("VSET", 0.0),
                row.get("ILRS", 0.0),
                row.get("IHRS", 0.0),
                row.get("NORM_COND", 0.0),
                row.get("VFORM", None),
            ],
        )


# ── Repository: load_classic_cycle_params_for_sets ──────────────────────────


class TestLoadClassicCycleParams:
    def test_r_lrs_is_0_2_divided_by_ilrs(self, conn, repo):
        """R_LRS must be 0.2 / ILRS, not ILRS itself."""
        _insert_rows(
            conn,
            [
                {
                    "source_file": "H25098_A10_03_endurance_set",
                    "cycle_number": 1,
                    "ILRS": 1e-3,
                    "IHRS": 1e-6,
                },
            ],
        )
        result = repo.load_classic_cycle_params_for_sets(
            ["H25098_A10_03_endurance_set"]
        )
        assert result["R_LRS"].iloc[0] == pytest.approx(0.2 / 1e-3)

    def test_r_hrs_is_0_2_divided_by_ihrs(self, conn, repo):
        """R_HRS must be 0.2 / IHRS, not IHRS itself."""
        _insert_rows(
            conn,
            [
                {
                    "source_file": "H25098_A10_03_endurance_set",
                    "cycle_number": 1,
                    "ILRS": 1e-3,
                    "IHRS": 1e-6,
                },
            ],
        )
        result = repo.load_classic_cycle_params_for_sets(
            ["H25098_A10_03_endurance_set"]
        )
        assert result["R_HRS"].iloc[0] == pytest.approx(0.2 / 1e-6)

    def test_zero_ilrs_gives_null_r_lrs(self, conn, repo):
        """NULLIF prevents division by zero — R_LRS should be NULL/NaN."""
        _insert_rows(
            conn,
            [
                {
                    "source_file": "H25098_A10_03_endurance_set",
                    "cycle_number": 1,
                    "ILRS": 0.0,
                    "IHRS": 1e-6,
                },
            ],
        )
        result = repo.load_classic_cycle_params_for_sets(
            ["H25098_A10_03_endurance_set"]
        )
        assert pd.isna(result["R_LRS"].iloc[0])

    def test_empty_sets_returns_empty_df(self, conn, repo):
        result = repo.load_classic_cycle_params_for_sets([])
        assert result.empty

    def test_multiple_cycles_aggregated_correctly(self, conn, repo):
        _insert_rows(
            conn,
            [
                {
                    "source_file": "H25098_A10_03_endurance_set",
                    "cycle_number": 1,
                    "ILRS": 1e-3,
                    "IHRS": 1e-6,
                },
                {
                    "source_file": "H25098_A10_03_endurance_set",
                    "cycle_number": 2,
                    "ILRS": 2e-3,
                    "IHRS": 2e-6,
                },
            ],
        )
        result = repo.load_classic_cycle_params_for_sets(
            ["H25098_A10_03_endurance_set"]
        )
        assert len(result) == 2
        assert result[result["cycle_number"] == 2]["R_LRS"].iloc[0] == pytest.approx(
            0.2 / 2e-3
        )


# ── Repository: load_forming_voltage_per_device ──────────────────────────────


class TestLoadFormingVoltagePerDevice:
    def test_returns_max_vform_per_device(self, conn, repo):
        _insert_rows(
            conn,
            [
                {"source_file": "H25098_A10_01_Electroforming", "VFORM": 2.5},
                {"source_file": "H25098_A10_01_Electroforming", "VFORM": 3.0},
                {"source_file": "H25098_B12_01_Electroforming", "VFORM": 2.0},
            ],
        )
        result = repo.load_forming_voltage_per_device(["A10", "B12"])
        assert result["A10"] == pytest.approx(3.0)
        assert result["B12"] == pytest.approx(2.0)

    def test_missing_device_not_in_result(self, conn, repo):
        _insert_rows(
            conn,
            [
                {"source_file": "H25098_A10_01_Electroforming", "VFORM": 2.5},
            ],
        )
        result = repo.load_forming_voltage_per_device(["A10", "B12"])
        assert "A10" in result
        assert "B12" not in result

    def test_empty_devices_returns_empty_dict(self, conn, repo):
        result = repo.load_forming_voltage_per_device([])
        assert result == {}


# ── Repository: load_leakage_current_per_device ──────────────────────────────


class TestLoadLeakageCurrentPerDevice:
    def test_returns_max_abs_ai_per_device(self, conn, repo):
        _insert_rows(
            conn,
            [
                {"source_file": "H25098_A10_00_leakage", "AI": -1e-10},
                {"source_file": "H25098_A10_00_leakage", "AI": -5e-10},
                {"source_file": "H25098_B12_00_leakage", "AI": -2e-10},
            ],
        )
        result = repo.load_leakage_current_per_device(["A10", "B12"])
        assert result["A10"] == pytest.approx(5e-10)
        assert result["B12"] == pytest.approx(2e-10)

    def test_missing_device_not_in_result(self, conn, repo):
        _insert_rows(
            conn,
            [
                {"source_file": "H25098_A10_00_leakage", "AI": -1e-10},
            ],
        )
        result = repo.load_leakage_current_per_device(["A10", "B12"])
        assert "A10" in result
        assert "B12" not in result


# ── Repository: list_endurance_resets ────────────────────────────────────────


class TestListEnduranceResets:
    def test_matches_endurance_reset_pattern(self, conn, repo):
        _insert_rows(
            conn,
            [
                {"source_file": "H25098_A10_03_endurance_reset"},
                {"source_file": "H25098_A10_03_endurance_set"},  # should NOT match
                {"source_file": "H25098_B12_03_endurance_reset"},
            ],
        )
        result = repo.list_endurance_resets("%endurance_reset%")
        assert "H25098_A10_03_endurance_reset" in result
        assert "H25098_B12_03_endurance_reset" in result
        assert "H25098_A10_03_endurance_set" not in result


# ── Transforms: compute_i_lrs_from_reset ────────────────────────────────────


class TestComputeILrsFromReset:
    def test_returns_last_ireset_per_cycle(self):
        df_reset = pd.DataFrame(
            {
                "cycle_number": [1, 1, 2, 2],
                "IRESET": [1e-4, 2e-4, 3e-4, 4e-4],
                "AI": [0.0, 0.0, 0.0, 0.0],
            }
        )
        result = compute_i_lrs_from_reset(df_reset)
        assert result[result["cycle_number"] == 1]["I_LRS"].iloc[0] == pytest.approx(
            2e-4
        )
        assert result[result["cycle_number"] == 2]["I_LRS"].iloc[0] == pytest.approx(
            4e-4
        )

    def test_abs_value_of_negative_ireset(self):
        df_reset = pd.DataFrame(
            {
                "cycle_number": [1],
                "IRESET": [-1e-4],
                "AI": [0.0],
            }
        )
        result = compute_i_lrs_from_reset(df_reset)
        assert result["I_LRS"].iloc[0] == pytest.approx(1e-4)
        assert result["I_LRS"].iloc[0] > 0

    def test_empty_df_returns_empty(self):
        result = compute_i_lrs_from_reset(pd.DataFrame())
        assert result.empty
        assert "I_LRS" in result.columns

    def test_all_zero_ireset_returns_empty(self):
        df_reset = pd.DataFrame(
            {
                "cycle_number": [1, 2],
                "IRESET": [0.0, 0.0],
                "AI": [1e-4, 2e-4],
            }
        )
        result = compute_i_lrs_from_reset(df_reset)
        assert result.empty

    def test_fallback_to_ai_when_no_ireset_column(self):
        df_reset = pd.DataFrame(
            {
                "cycle_number": [1, 1],
                "AI": [-1e-4, -2e-4],
            }
        )
        result = compute_i_lrs_from_reset(df_reset)
        assert result["I_LRS"].iloc[0] == pytest.approx(2e-4)

    def test_nan_ireset_values_excluded(self):
        df_reset = pd.DataFrame(
            {
                "cycle_number": [1, 2],
                "IRESET": [float("nan"), 3e-4],
                "AI": [0.0, 0.0],
            }
        )
        result = compute_i_lrs_from_reset(df_reset)
        assert len(result) == 1
        assert result["I_LRS"].iloc[0] == pytest.approx(3e-4)


# ── Transforms: edge cases ───────────────────────────────────────────────────


class TestBuildEnduranceTableEdgeCases:
    def _make_set(self, i_hrs=1e-6):
        return pd.DataFrame(
            {
                "cycle_number": [1],
                "Time": [0.0],
                "AV": [-0.5],
                "AI": [-1e-4],
                "VSET": [1.5],
                "ILRS": [0.0],  # ignored — I_LRS now comes from reset
                "IHRS": [i_hrs],
            }
        )

    def _make_reset(self, ireset=1e-3, vreset=0.8):
        return pd.DataFrame(
            {
                "cycle_number": [1],
                "Time": [0.0],
                "AV": [vreset],
                "AI": [-ireset],
                "VRESET": [vreset],
                "IRESET": [ireset],
            }
        )

    def test_zero_ireset_gives_nan_r_lrs(self):
        """Zero IRESET in reset file should produce NaN R_LRS."""
        df_set = self._make_set()
        df_reset = self._make_reset(ireset=0.0)
        result = build_endurance_table(
            {"H25098_A10_03_endurance_set": df_set},
            {"H25098_A10_03_endurance_reset": df_reset},
        )
        assert pd.isna(result["R_LRS"].iloc[0])

    def test_negative_ireset_gives_positive_resistance(self):
        """Negative IRESET should still yield positive R_LRS."""
        df_set = self._make_set()
        df_reset = self._make_reset(ireset=-1e-3)
        result = build_endurance_table(
            {"H25098_A10_03_endurance_set": df_set},
            {"H25098_A10_03_endurance_reset": df_reset},
        )
        assert result["R_LRS"].iloc[0] == pytest.approx(0.2 / 1e-3)
        assert result["R_LRS"].iloc[0] > 0

    def test_memory_window_always_positive(self):
        """Memory window must be positive."""
        df_set = self._make_set(i_hrs=1e-6)
        df_reset = self._make_reset(ireset=1e-3)
        result = build_endurance_table(
            {"H25098_A10_03_endurance_set": df_set},
            {"H25098_A10_03_endurance_reset": df_reset},
        )
        assert result["Memory_window"].iloc[0] > 0

    def test_missing_reset_file_gives_nan_r_lrs(self):
        """No reset file means I_LRS is NaN, so R_LRS should also be NaN."""
        df_set = self._make_set()
        result = build_endurance_table(
            {"H25098_A10_03_endurance_set": df_set},
            {},
        )
        assert pd.isna(result["R_LRS"].iloc[0])


# ── Transforms: _device_from_source ─────────────────────────────────────────


class TestDeviceFromSource:
    def test_extracts_device_from_standard_filename(self):
        assert _device_from_source("H25098_A10_03_endurance_set") == "A10"

    def test_extracts_device_from_b12(self):
        assert _device_from_source("H25098_B12_04_endurance_reset") == "B12"

    def test_returns_none_for_no_underscore(self):
        assert _device_from_source("nodashes") is None


# ── Pipeline: smoke test ─────────────────────────────────────────────────────


class TestPipelineSmokeTest:
    def test_load_all_returns_loaded_data_with_all_fields(self, tmp_path):
        """End-to-end smoke test with a minimal in-memory DuckDB written to disk."""
        import duckdb
        from app.plotting.config import Config
        from app.plotting.pipeline import load_all, LoadedData

        # Create a minimal DuckDB file
        db_path = tmp_path / "test.duckdb"
        c = duckdb.connect(str(db_path))
        c.execute("""
            CREATE TABLE cycles (
                source_file VARCHAR,
                cycle_number INTEGER,
                Time DOUBLE,
                AV DOUBLE,
                AI DOUBLE,
                VSET DOUBLE,
                ILRS DOUBLE,
                IHRS DOUBLE,
                NORM_COND DOUBLE,
                VFORM DOUBLE,
                VRESET DOUBLE,
                IRESET DOUBLE
            )
        """)
        # Insert minimal set and reset rows
        for i in range(1, 4):
            c.execute(
                "INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    "H25098_A10_03_endurance_set",
                    i,
                    float(i),
                    -0.5,
                    -1e-4,
                    1.5,
                    1e-3,
                    1e-6,
                    1e-4,
                    None,
                    None,
                    None,
                ],
            )
            c.execute(
                "INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    "H25098_A10_03_endurance_reset",
                    i,
                    float(i),
                    0.8,
                    -5e-4,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    None,
                    0.8,
                    5e-4,
                ],
            )
            c.execute(
                "INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    "H25098_A10_01_Electroforming",
                    i,
                    float(i),
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    2.5,
                    None,
                    None,
                ],
            )
            c.execute(
                "INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    "H25098_A10_00_leakage",
                    i,
                    float(i),
                    0.0,
                    -1e-10,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    None,
                    None,
                    None,
                ],
            )
        c.close()

        cfg = Config(
            db_file=db_path,
            output_dir=tmp_path / "output",
            mode="device",
        )

        data = load_all(cfg)

        assert isinstance(data, LoadedData)
        assert len(data.sets) == 1
        assert len(data.resets) == 1
        assert not data.end_df.empty
        assert not data.cdf_table.empty
        assert not data.box_table.empty
        assert not data.scatter_df.empty
        assert "R_LRS" in data.end_df.columns
        assert "R_HRS" in data.end_df.columns
        assert "V_reset" in data.end_df.columns
        assert "I_reset_max" in data.end_df.columns
        assert "Memory_window" in data.end_df.columns
        assert data.forming_v_by_device.get("A10") == pytest.approx(2.5)
        assert data.leakage_i_by_device.get("A10") == pytest.approx(1e-10)
