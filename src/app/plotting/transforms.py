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
    if df_reset.empty:
        return pd.DataFrame(columns=["cycle_number", "V_reset"])

    # Use pre-computed VRESET column if available
    if "VRESET" in df_reset.columns:
        out = (
            df_reset[df_reset["VRESET"].notna()][["cycle_number", "VRESET"]]
            .drop_duplicates("cycle_number")
            .rename(columns={"VRESET": "V_reset"})
            .reset_index(drop=True)
        )
        return out

    # Fallback: compute from raw AV at max |AI|
    idx = df_reset.groupby("cycle_number")["AI"].apply(lambda s: s.abs().idxmax())
    out = (
        df_reset.loc[idx, ["cycle_number", "AV"]]
        .rename(columns={"AV": "V_reset"})
        .reset_index(drop=True)
    )
    return out


def compute_i_reset_max(df_reset: pd.DataFrame) -> pd.DataFrame:
    if df_reset.empty:
        return pd.DataFrame(columns=["cycle_number", "I_reset_max"])

    # Use pre-computed IRESET column if available
    if "IRESET" in df_reset.columns:
        out = (
            df_reset[df_reset["IRESET"].notna()][["cycle_number", "IRESET"]]
            .drop_duplicates("cycle_number")
            .rename(columns={"IRESET": "I_reset_max"})
            .reset_index(drop=True)
        )
        return out

    # Fallback: compute max |AI| per cycle
    out = (
        df_reset.groupby("cycle_number")["AI"]
        .apply(lambda s: s.abs().max())
        .reset_index(name="I_reset_max")
    )
    return out


def _assign_reset_by_position(
    classic: pd.DataFrame,
    vreset: pd.DataFrame,
    ireset: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign V_reset and I_reset_max by row position rather than cycle_number.
    This handles cases where reset files restart cycle numbering from 1
    instead of continuing from where the set file left off.
    """
    classic = classic.reset_index(drop=True)
    if not vreset.empty:
        classic["V_reset"] = vreset["V_reset"].reindex(classic.index).values
    else:
        classic["V_reset"] = np.nan
    if not ireset.empty:
        classic["I_reset_max"] = ireset["I_reset_max"].reindex(classic.index).values
    else:
        classic["I_reset_max"] = np.nan
    return classic


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
    """
    # Build per-set_key positional reset values
    vreset_parts = []
    ireset_parts = []

    for s, df_reset in raw_by_reset.items():
        set_key = s.replace("endurance_reset", "endurance_set")

        vreset = compute_v_reset(df_reset).reset_index(drop=True)
        ireset = compute_i_reset_max(df_reset).reset_index(drop=True)

        # Get the classic rows for this set, sorted by cycle_number
        classic_set = (
            classic_df[classic_df["source_file"] == set_key]
            .sort_values("cycle_number")
            .reset_index(drop=True)
        )

        if classic_set.empty:
            continue

        # Assign by position
        classic_set = _assign_reset_by_position(classic_set, vreset, ireset)
        vreset_parts.append(classic_set[["source_file", "cycle_number", "V_reset"]])
        ireset_parts.append(classic_set[["source_file", "cycle_number", "I_reset_max"]])

    if vreset_parts:
        vreset_df = pd.concat(vreset_parts, ignore_index=True)
        ireset_df = pd.concat(ireset_parts, ignore_index=True)
        out = classic_df.merge(
            vreset_df, on=["source_file", "cycle_number"], how="left"
        )
        out = out.merge(ireset_df, on=["source_file", "cycle_number"], how="left")
    else:
        out = classic_df.copy()
        out["V_reset"] = np.nan
        out["I_reset_max"] = np.nan

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
            .sort_values("cycle_number")
            .reset_index(drop=True)
        )

        MIN_CURRENT = 1e-10  # below 0.1 nA is treated as unmeasured
        i_lrs = classic["I_LRS"].abs()
        i_hrs = classic["I_HRS"].abs()
        classic["R_LRS"] = 0.2 / i_lrs.where(i_lrs > MIN_CURRENT)
        classic["R_HRS"] = 0.2 / i_hrs.where(i_hrs > MIN_CURRENT)
        classic["Memory_window"] = classic["R_HRS"] / classic["R_LRS"]

        reset_key = s.replace("endurance_set", "endurance_reset")
        df_reset = raw_by_reset.get(reset_key, pd.DataFrame())

        vreset = compute_v_reset(df_reset).reset_index(drop=True)
        ireset = compute_i_reset_max(df_reset).reset_index(drop=True)

        # Use positional assignment instead of cycle_number merge
        cycle_df = _assign_reset_by_position(classic, vreset, ireset)
        cycle_df["source_file"] = s

        all_sets.append(cycle_df)

    return pd.concat(all_sets, ignore_index=True) if all_sets else pd.DataFrame()


def build_scatter_table(end_df: pd.DataFrame) -> pd.DataFrame:
    """
    Table for device-level correlation scatter plots.
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
