from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path


def _device_from_source(source_file: str) -> str | None:
    """Extract device name from source_file stem (e.g. H25098_A10_03_endurance_set → A10)."""
    stem = Path(source_file).stem
    parts = stem.split("_")
    return parts[1] if len(parts) >= 2 else None


def _map_per_device(source_files: pd.Series, device_map: dict[str, float]) -> pd.Series:
    """Map a per-device dict onto a Series of source_file strings."""
    return source_files.map(lambda sf: device_map.get(_device_from_source(sf)))


def compute_v_reset(df_reset: pd.DataFrame) -> pd.DataFrame:
    """
    V_reset per cycle: AV value at max(|AI|) for that cycle.
    Must be called with RESET file data, not set file data.
    Expects columns: cycle_number, AV, AI
    Returns: cycle_number, V_reset
    """
    if df_reset.empty:
        return pd.DataFrame(columns=["cycle_number", "V_reset"])

    idx = df_reset.groupby("cycle_number")["AI"].apply(lambda s: s.abs().idxmax())
    out = (
        df_reset.loc[idx, ["cycle_number", "AV"]]
        .rename(columns={"AV": "V_reset"})
        .reset_index(drop=True)
    )
    return out


def compute_i_reset_max(df_reset: pd.DataFrame) -> pd.DataFrame:
    """
    I_reset_max per cycle: max(|AI|) for that cycle.
    Must be called with RESET file data, not set file data.
    Expects columns: cycle_number, AI
    Returns: cycle_number, I_reset_max
    """
    if df_reset.empty:
        return pd.DataFrame(columns=["cycle_number", "I_reset_max"])

    out = (
        df_reset.groupby("cycle_number")["AI"]
        .apply(lambda s: s.abs().max())
        .reset_index(name="I_reset_max")
    )
    return out


def build_cdf_table(
    classic_df: pd.DataFrame,
    raw_by_reset: dict[str, pd.DataFrame],
    v_forming: float | None | dict[str, float],
    leakage_i: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Produces table used by CDF plot.
    classic_df columns: source_file, cycle_number, VSET, R_LRS, R_HRS
    adds: V_reset, I_reset_max, V_forming, I_leakage_pristine

    raw_by_reset: dict of {source_file: df} from RESET files.
    v_forming: either a global scalar or a dict of {device: V_forming}.
    leakage_i: dict of {device: I_leakage_pristine} (optional).
    """
    parts_v = []
    parts_i = []

    for s, df_reset in raw_by_reset.items():
        # Map reset filename back to set filename so the merge on source_file matches classic_df
        set_key = s.replace("endurance_reset", "endurance_set")

        v = compute_v_reset(df_reset)
        v["source_file"] = set_key
        parts_v.append(v)

        i = compute_i_reset_max(df_reset)
        i["source_file"] = set_key
        parts_i.append(i)

    vreset_df = (
        pd.concat(parts_v, ignore_index=True)
        if parts_v
        else pd.DataFrame(columns=["cycle_number", "V_reset", "source_file"])
    )
    ireset_df = (
        pd.concat(parts_i, ignore_index=True)
        if parts_i
        else pd.DataFrame(columns=["cycle_number", "I_reset_max", "source_file"])
    )

    out = classic_df.merge(
        vreset_df, on=["source_file", "cycle_number"], how="left"
    ).merge(ireset_df, on=["source_file", "cycle_number"], how="left")

    # V_forming — per-device dict or global scalar
    if isinstance(v_forming, dict):
        out["V_forming"] = _map_per_device(out["source_file"], v_forming)
    else:
        out["V_forming"] = v_forming

    # I_leakage_pristine — per-device dict
    if leakage_i:
        out["I_leakage_pristine"] = _map_per_device(out["source_file"], leakage_i)

    return out


def build_box_table(
    classic_df: pd.DataFrame,
    raw_by_reset: dict[str, pd.DataFrame],
    v_forming: float | None | dict[str, float],
    leakage_i: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Same underlying merged table as CDF.
    raw_by_reset: dict of {source_file: df} from RESET files.
    v_forming: either a global scalar or a dict of {device: V_forming}.
    leakage_i: dict of {device: I_leakage_pristine} (optional).
    """
    return build_cdf_table(classic_df, raw_by_reset, v_forming, leakage_i)


def build_endurance_table(
    raw_by_set: dict[str, pd.DataFrame],
    raw_by_reset: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Produces per-cycle endurance table for all sets.
    Output includes:
      source_file, cycle_number, V_set, V_reset, I_LRS, I_HRS,
      R_LRS, R_HRS, I_reset_max, Memory_window
    """
    all_sets = []

    for s, df_set in raw_by_set.items():
        if df_set.empty:
            continue

        classic = (
            df_set.groupby("cycle_number")
            .agg(
                V_set=("VSET", "max"),
                I_LRS=("ILRS", "last"),
                I_HRS=("IHRS", "last"),
            )
            .reset_index()
        )

        classic["R_LRS"] = 0.2 / classic["I_LRS"].abs().replace(0, np.nan)
        classic["R_HRS"] = 0.2 / classic["I_HRS"].abs().replace(0, np.nan)
        classic["Memory_window"] = classic["R_HRS"] / classic["R_LRS"]

        reset_key = s.replace("endurance_set", "endurance_reset")
        df_reset = raw_by_reset.get(reset_key, pd.DataFrame())

        vreset = compute_v_reset(df_reset)
        ireset = compute_i_reset_max(df_reset)

        cycle_df = classic.merge(vreset, on="cycle_number", how="left")
        cycle_df = cycle_df.merge(ireset, on="cycle_number", how="left")
        cycle_df["source_file"] = s

        all_sets.append(cycle_df)

    return pd.concat(all_sets, ignore_index=True) if all_sets else pd.DataFrame()


def build_scatter_table(end_df: pd.DataFrame) -> pd.DataFrame:
    """
    Table for device-level correlation scatter plots.
    R_HRS and R_LRS are already correctly computed in build_endurance_table.
    """
    if end_df.empty:
        return pd.DataFrame()

    cols = [
        "source_file",
        "cycle_number",
        "V_set",
        "V_reset",
        "I_HRS",
        "I_LRS",
        "R_LRS",
        "R_HRS",
        "I_reset_max",
    ]
    return end_df[[c for c in cols if c in end_df.columns]].copy()
