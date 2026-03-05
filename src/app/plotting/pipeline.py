from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from .config import Config
from .db import DuckDBSession
from .repository import MemristorRepository
from .transforms import (
    build_cdf_table,
    build_box_table,
    build_endurance_table,
    build_scatter_table,
)


@dataclass(frozen=True)
class LoadedData:
    sets: list[str]

    # raw
    raw_characteristic: dict[str, pd.DataFrame]
    raw_endurance: dict[str, pd.DataFrame]
    raw_reset: dict[str, pd.DataFrame] | None
    raw_leakage: dict[str, pd.DataFrame] | None

    # derived
    forming_v: float | None
    first_v_reset: dict[str, float]
    classic: pd.DataFrame
    cdf_table: pd.DataFrame
    box_table: pd.DataFrame
    end_df: pd.DataFrame
    scatter_df: pd.DataFrame
    leakage_df: pd.DataFrame | None


def load_all(cfg: Config) -> LoadedData:
    with DuckDBSession(cfg.db_file) as conn:
        repo = MemristorRepository(conn)

        sets = repo.list_endurance_sets(cfg.endurance_set_like)

        # load leakage sets
        leakage_sets = repo.list_leakage_sets(cfg.leakage_set_like)

        # raw for characteristic plot
        raw_characteristic = {s: repo.load_cycles_for_set(s) for s in sets}

        # raw for endurance metrics
        raw_endurance = {s: repo.load_endurance_cycles_for_set(s) for s in sets}

        # raw for reset (butterfly plot)
        reset_sets = repo.list_reset_sets(cfg.endurance_reset_like)
        raw_reset = (
            {s: repo.load_cycles_for_reset_set(s) for s in reset_sets}
            if reset_sets
            else None
        )

        # raw for leakage
        raw_leakage = (
            {s: repo.load_leakage_for_set(s) for s in leakage_sets}
            if leakage_sets
            else None
        )

        forming_v = repo.load_forming_voltage_global(cfg.electroforming_like)
        first_v_reset = repo.load_first_v_reset(cfg.endurance_reset_like)
        classic = repo.load_classic_cycle_params_for_sets(sets)

    # transforms (no DB needed)
    cdf_table = build_cdf_table(classic, raw_characteristic, forming_v)
    box_table = build_box_table(classic, raw_characteristic, forming_v)
    end_df = build_endurance_table(raw_endurance)
    scatter_df = build_scatter_table(end_df)

    # combine leakage
    leakage_df = _combine_leakage_data(raw_leakage) if raw_leakage else None

    return LoadedData(
        sets=sets,
        raw_characteristic=raw_characteristic,
        raw_endurance=raw_endurance,
        raw_reset=raw_reset,
        raw_leakage=raw_leakage,
        forming_v=forming_v,
        first_v_reset=first_v_reset,
        classic=classic,
        cdf_table=cdf_table,
        box_table=box_table,
        end_df=end_df,
        scatter_df=scatter_df,
        leakage_df=leakage_df,
    )


def _combine_leakage_data(raw_leakage: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dfs = []
    for name, df in raw_leakage.items():
        df_copy = df.copy()
        df_copy["source_file"] = name
        dfs.append(df_copy)
    return pd.concat(dfs, ignore_index=True)
