from __future__ import annotations

import numpy as np
import pandas as pd


def compute_v_reset(df_set: pd.DataFrame) -> pd.DataFrame:
    """
    V_reset per cycle: AV value at max(|AI|) for that cycle.
    Expects columns: cycle_number, AV, AI
    Returns: cycle_number, V_reset
    """
    if df_set.empty:
        return pd.DataFrame(columns=["cycle_number", "V_reset"])

    # idx of max abs(AI) per cycle
    idx = df_set.groupby("cycle_number")["AI"].apply(lambda s: s.abs().idxmax())
    out = df_set.loc[idx, ["cycle_number", "AV"]].rename(columns={"AV": "V_reset"}).reset_index(drop=True)
    return out


def compute_i_reset_max(df_set: pd.DataFrame) -> pd.DataFrame:
    """
    I_reset_max per cycle: max(|AI|) for that cycle.
    Expects columns: cycle_number, AI
    Returns: cycle_number, I_reset_max
    """
    if df_set.empty:
        return pd.DataFrame(columns=["cycle_number", "I_reset_max"])

    out = (
        df_set.groupby("cycle_number")["AI"]
        .apply(lambda s: s.abs().max())
        .reset_index(name="I_reset_max")
    )
    return out


def build_cdf_table(
    classic_df: pd.DataFrame,
    raw_by_set: dict[str, pd.DataFrame],
    v_forming_global: float | None,
) -> pd.DataFrame:
    """
    Produces table used by CDF plot:
    classic_df columns: source_file, cycle_number, VSET, R_LRS, R_HRS
    adds: V_reset, I_reset_max, V_forming
    """
    parts_v = []
    parts_i = []

    for s, df_set in raw_by_set.items():
        v = compute_v_reset(df_set)
        v["source_file"] = s
        parts_v.append(v)

        i = compute_i_reset_max(df_set)
        i["source_file"] = s
        parts_i.append(i)

    vreset_df = pd.concat(parts_v, ignore_index=True) if parts_v else pd.DataFrame(columns=["cycle_number", "V_reset", "source_file"])
    ireset_df = pd.concat(parts_i, ignore_index=True) if parts_i else pd.DataFrame(columns=["cycle_number", "I_reset_max", "source_file"])

    out = (
        classic_df
        .merge(vreset_df, on=["source_file", "cycle_number"], how="left")
        .merge(ireset_df, on=["source_file", "cycle_number"], how="left")
    )
    out["V_forming"] = v_forming_global
    return out


def build_box_table(
    classic_df: pd.DataFrame,
    raw_by_set: dict[str, pd.DataFrame],
    v_forming_global: float | None,
) -> pd.DataFrame:
    """
    Same underlying merged table as CDF; keeping it separate lets you rename columns differently later if needed.
    """
    return build_cdf_table(classic_df, raw_by_set, v_forming_global)


def build_endurance_table(raw_by_set: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Produces per-cycle endurance table for all sets.
    Output includes:
      source_file, cycle_number, V_set, V_reset, I_LRS, I_HRS, R_LRS, R_HRS, I_reset_max, Memory_window
    Expects per-set raw df columns: cycle_number, AV, AI, VSET, ILRS, IHRS (and Time is fine too)
    """
    all_sets = []

    for s, df_set in raw_by_set.items():
        if df_set.empty:
            continue

        # classic per-cycle summary
        classic = (
            df_set.groupby("cycle_number")
            .agg(
                V_set=("VSET", "max"),
                I_LRS=("ILRS", "last"),
                I_HRS=("IHRS", "last"),
                R_LRS=("ILRS", "max"),
                R_HRS=("IHRS", "max"),
                I_reset_max=("AI", lambda x: x.abs().max()),
            )
            .reset_index()
        )

        vreset = compute_v_reset(df_set)
        cycle_df = classic.merge(vreset, on="cycle_number", how="left")

        # Derived
        cycle_df["Memory_window"] = cycle_df["R_HRS"] / cycle_df["R_LRS"]
        cycle_df["source_file"] = s

        all_sets.append(cycle_df)

    return pd.concat(all_sets, ignore_index=True) if all_sets else pd.DataFrame()


def build_scatter_table(end_df: pd.DataFrame) -> pd.DataFrame:
    """
    Table for device-level correlation scatter plots.
    Ensures R_HRS and R_LRS are available (computed from V_set and currents).
    """
    if end_df.empty:
        return pd.DataFrame()

    df = end_df[["source_file", "cycle_number", "V_set", "V_reset", "I_HRS", "I_LRS", "I_reset_max"]].copy()

    # avoid division by zero
    df["R_HRS"] = df["V_set"] / df["I_HRS"].abs().replace(0, np.nan)
    df["R_LRS"] = df["V_set"] / df["I_LRS"].abs().replace(0, np.nan)

    return df
