"""
Tests verifying the corrections from Eszter's review email:

- R_LRS = 0.2 / I_LRS  (not raw current)
- R_HRS = 0.2 / I_HRS  (not raw current)
- Memory_window = R_HRS / R_LRS  (dimensionless, no units)
- V_reset extracted from RESET file, not SET file
- I_reset_max extracted from RESET file, not SET file
- V_forming mapped per device from forming file
- I_leakage_pristine mapped per device from leakage file
- Characteristic plot includes both set and reset traces
- Conductance axis label is G/G₀
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.plotting.transforms import (
    compute_v_reset,
    compute_i_reset_max,
    build_cdf_table,
    build_box_table,
    build_endurance_table,
)
from app.plotting.fig_characteristic import build_characteristic_figs


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_set_df(cycle_number=1, vset=1.5, ilrs=1e-3, ihrs=1e-6) -> pd.DataFrame:
    """Minimal endurance SET dataframe."""
    return pd.DataFrame(
        {
            "cycle_number": [cycle_number, cycle_number],
            "Time": [0.0, 1.0],
            "AV": [-0.5, -1.0],
            "AI": [-1e-4, -2e-4],
            "VSET": [vset, vset],
            "ILRS": [ilrs, ilrs],
            "IHRS": [ihrs, ihrs],
        }
    )


def _make_reset_df(cycle_number=1, v_at_max_i=-0.8, max_i=-5e-4) -> pd.DataFrame:
    """Minimal endurance RESET dataframe with a clear max |AI| point."""
    return pd.DataFrame(
        {
            "cycle_number": [cycle_number, cycle_number],
            "Time": [0.0, 1.0],
            "AV": [-0.3, v_at_max_i],
            "AI": [-1e-5, max_i],
        }
    )


def _make_classic_df(source_file="H25098_A10_03_endurance_set") -> pd.DataFrame:
    """Minimal classic table as returned by load_classic_cycle_params_for_sets."""
    return pd.DataFrame(
        {
            "source_file": [source_file, source_file],
            "cycle_number": [1, 2],
            "VSET": [1.5, 1.5],
            "I_LRS": [1e-3, 1e-3],
            "I_HRS": [1e-6, 1e-6],
            "R_LRS": [0.2 / 1e-3, 0.2 / 1e-3],
            "R_HRS": [0.2 / 1e-6, 0.2 / 1e-6],
        }
    )


# ── compute_v_reset ─────────────────────────────────────────────────────────


class TestComputeVReset:
    def test_returns_av_at_max_abs_ai(self):
        df = _make_reset_df(v_at_max_i=-0.8, max_i=-5e-4)
        result = compute_v_reset(df)
        assert len(result) == 1
        assert result["V_reset"].iloc[0] == pytest.approx(-0.8)

    def test_empty_input_returns_empty(self):
        result = compute_v_reset(pd.DataFrame(columns=["cycle_number", "AV", "AI"]))
        assert result.empty

    def test_multiple_cycles(self):
        df = pd.DataFrame(
            {
                "cycle_number": [1, 1, 2, 2],
                "AV": [-0.3, -0.8, -0.4, -0.9],
                "AI": [-1e-5, -5e-4, -2e-5, -6e-4],
            }
        )
        result = compute_v_reset(df)
        assert len(result) == 2
        assert result[result["cycle_number"] == 1]["V_reset"].iloc[0] == pytest.approx(
            -0.8
        )
        assert result[result["cycle_number"] == 2]["V_reset"].iloc[0] == pytest.approx(
            -0.9
        )

    def test_uses_abs_ai_not_signed(self):
        """Positive AI values should also be considered (abs comparison)."""
        df = pd.DataFrame(
            {
                "cycle_number": [1, 1],
                "AV": [-0.3, -0.8],
                "AI": [5e-4, 1e-5],  # positive but first is larger in abs
            }
        )
        result = compute_v_reset(df)
        assert result["V_reset"].iloc[0] == pytest.approx(-0.3)


# ── compute_i_reset_max ──────────────────────────────────────────────────────


class TestComputeIResetMax:
    def test_returns_max_abs_ai(self):
        df = _make_reset_df(max_i=-5e-4)
        result = compute_i_reset_max(df)
        assert result["I_reset_max"].iloc[0] == pytest.approx(5e-4)

    def test_empty_input_returns_empty(self):
        result = compute_i_reset_max(pd.DataFrame(columns=["cycle_number", "AI"]))
        assert result.empty

    def test_multiple_cycles(self):
        df = pd.DataFrame(
            {
                "cycle_number": [1, 1, 2, 2],
                "AI": [-1e-4, -5e-4, -2e-4, -3e-4],
            }
        )
        result = compute_i_reset_max(df)
        assert result[result["cycle_number"] == 1]["I_reset_max"].iloc[
            0
        ] == pytest.approx(5e-4)
        assert result[result["cycle_number"] == 2]["I_reset_max"].iloc[
            0
        ] == pytest.approx(3e-4)


# ── build_endurance_table ────────────────────────────────────────────────────


class TestBuildEnduranceTable:
    def setup_method(self):
        self.set_key = "H25098_A10_03_endurance_set"
        self.reset_key = "H25098_A10_03_endurance_reset"
        self.df_set = _make_set_df(ilrs=1e-3, ihrs=1e-6)
        self.df_reset = _make_reset_df(v_at_max_i=-0.8, max_i=-5e-4)

    def test_r_lrs_is_resistance_not_current(self):
        """R_LRS must be 0.2 / I_LRS, not I_LRS itself."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {self.reset_key: self.df_reset},
        )
        expected = 0.2 / 1e-3
        assert result["R_LRS"].iloc[0] == pytest.approx(expected)

    def test_r_hrs_is_resistance_not_current(self):
        """R_HRS must be 0.2 / I_HRS, not I_HRS itself."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {self.reset_key: self.df_reset},
        )
        expected = 0.2 / 1e-6
        assert result["R_HRS"].iloc[0] == pytest.approx(expected)

    def test_memory_window_is_dimensionless_ratio(self):
        """Memory_window = R_HRS / R_LRS = I_LRS / I_HRS (dimensionless)."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {self.reset_key: self.df_reset},
        )
        expected = (0.2 / 1e-6) / (0.2 / 1e-3)  # = I_LRS / I_HRS = 1e3
        assert result["Memory_window"].iloc[0] == pytest.approx(expected)

    def test_memory_window_equals_current_ratio(self):
        """Memory_window = I_LRS / I_HRS (alternative form)."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {self.reset_key: self.df_reset},
        )
        assert result["Memory_window"].iloc[0] == pytest.approx(1e-3 / 1e-6)

    def test_v_reset_from_reset_file_not_set_file(self):
        """V_reset must come from reset file. Set file has AV of -0.5/-1.0,
        reset file has max |AI| at AV=-0.8. Result must be -0.8."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {self.reset_key: self.df_reset},
        )
        assert "V_reset" in result.columns
        assert result["V_reset"].iloc[0] == pytest.approx(-0.8)

    def test_i_reset_max_from_reset_file_not_set_file(self):
        """I_reset_max must come from reset file (max |AI| = 5e-4),
        not set file where AI values are different."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {self.reset_key: self.df_reset},
        )
        assert result["I_reset_max"].iloc[0] == pytest.approx(5e-4)

    def test_missing_reset_file_gives_nan_not_error(self):
        """If no matching reset file, V_reset and I_reset_max should be NaN."""
        result = build_endurance_table(
            {self.set_key: self.df_set},
            {},  # no reset files
        )
        assert result["V_reset"].isna().all()
        assert result["I_reset_max"].isna().all()

    def test_empty_set_returns_empty(self):
        result = build_endurance_table({}, {})
        assert result.empty


# ── build_cdf_table / build_box_table ───────────────────────────────────────


class TestBuildCdfTable:
    def setup_method(self):
        self.source_file = "H25098_A10_03_endurance_set"
        self.classic = _make_classic_df(self.source_file)
        self.reset_key = "H25098_A10_03_endurance_reset"
        self.df_reset = _make_reset_df(v_at_max_i=-0.8, max_i=-5e-4)

    def test_v_forming_scalar_applied_globally(self):
        result = build_cdf_table(
            self.classic, {self.reset_key: self.df_reset}, v_forming=2.5
        )
        assert (result["V_forming"] == 2.5).all()

    def test_v_forming_per_device_dict(self):
        result = build_cdf_table(
            self.classic,
            {self.reset_key: self.df_reset},
            v_forming={"A10": 2.5, "B12": 3.0},
        )
        assert (result["V_forming"] == 2.5).all()

    def test_v_forming_per_device_no_match_gives_nan(self):
        result = build_cdf_table(
            self.classic,
            {self.reset_key: self.df_reset},
            v_forming={"B12": 3.0},  # A10 not in dict
        )
        assert result["V_forming"].isna().all()

    def test_i_leakage_pristine_per_device(self):
        result = build_cdf_table(
            self.classic,
            {self.reset_key: self.df_reset},
            v_forming={"A10": 2.5},
            leakage_i={"A10": 1e-10},
        )
        assert "I_leakage_pristine" in result.columns
        assert np.allclose(result["I_leakage_pristine"].dropna(), 1e-10)

    def test_i_leakage_pristine_none_skips_column(self):
        result = build_cdf_table(
            self.classic,
            {self.reset_key: self.df_reset},
            v_forming={"A10": 2.5},
            leakage_i=None,
        )
        assert "I_leakage_pristine" not in result.columns

    def test_box_table_matches_cdf_table(self):
        cdf = build_cdf_table(
            self.classic,
            {self.reset_key: self.df_reset},
            v_forming={"A10": 2.5},
            leakage_i={"A10": 1e-10},
        )

        box = build_box_table(
            self.classic,
            {self.reset_key: self.df_reset},
            v_forming={"A10": 2.5},
            leakage_i={"A10": 1e-10},
        )
        pd.testing.assert_frame_equal(cdf, box)


# ── fig_characteristic ───────────────────────────────────────────────────────


class TestBuildCharacteristicFigs:
    def setup_method(self):
        self.set_key = "H25098_A10_03_endurance_set"
        self.reset_key = "H25098_A10_03_endurance_reset"

        self.raw_set = {
            self.set_key: pd.DataFrame(
                {
                    "cycle_number": [1, 1],
                    "AV": [-0.5, -1.0],
                    "AI": [-1e-4, -2e-4],
                    "NORM_COND": [1e-4, 2e-4],
                }
            )
        }
        self.raw_reset = {
            self.reset_key: pd.DataFrame(
                {
                    "cycle_number": [1, 1],
                    "AV": [0.3, 0.8],
                    "AI": [1e-4, 5e-4],
                }
            )
        }

    def test_returns_three_figures(self):
        figs = build_characteristic_figs(self.raw_set, [self.set_key])
        assert len(figs) == 3

    def test_current_fig_has_reset_traces_when_provided(self):
        figs = build_characteristic_figs(
            self.raw_set, [self.set_key], raw_by_reset=self.raw_reset
        )
        current_fig = next(f for f in figs if f.layout.meta.get("param_id") == "AI")
        trace_names = [t.name for t in current_fig.data]
        assert any("reset" in name for name in trace_names), (
            "Expected reset traces in current plot but found: " + str(trace_names)
        )

    def test_current_fig_has_set_traces(self):
        figs = build_characteristic_figs(
            self.raw_set, [self.set_key], raw_by_reset=self.raw_reset
        )
        current_fig = next(f for f in figs if f.layout.meta.get("param_id") == "AI")
        trace_names = [t.name for t in current_fig.data]
        assert any("set" in name for name in trace_names)

    def test_conductance_fig_yaxis_label_is_g_over_g0(self):
        figs = build_characteristic_figs(self.raw_set, [self.set_key])
        cond_fig = next(f for f in figs if f.layout.meta.get("param_id") == "NORM_COND")
        assert (
            "G₀" in cond_fig.layout.yaxis.title.text
            or "G/G" in cond_fig.layout.yaxis.title.text
        )

    def test_no_reset_data_still_produces_three_figs(self):
        figs = build_characteristic_figs(self.raw_set, [self.set_key])
        assert len(figs) == 3

    def test_param_ids_are_correct(self):
        figs = build_characteristic_figs(self.raw_set, [self.set_key])
        param_ids = {f.layout.meta.get("param_id") for f in figs}
        assert param_ids == {"AI", "NORM_COND", "butterfly_curve"}
