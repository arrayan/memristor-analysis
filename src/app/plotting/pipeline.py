from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from plotting.config import Config
from plotting.db import DuckDBSession
from plotting.repository import MemristorRepository
from plotting.transforms import (
    build_cdf_table,
    build_box_table,
    build_endurance_table,
    build_scatter_table,
)


@dataclass(frozen=True)
class LoadedData:
    sets: list[str]

    # raw
    raw_characteristic: dict[str, pd.DataFrame]  # cycle_number, Time, AV, AI, NORM_COND
    raw_endurance: dict[
        str, pd.DataFrame
    ]  # cycle_number, Time, AV, AI, VSET, ILRS, IHRS

    # derived
    forming_v: float | None
    classic: pd.DataFrame
    cdf_table: pd.DataFrame
    box_table: pd.DataFrame
    end_df: pd.DataFrame
    scatter_df: pd.DataFrame


def load_all(cfg: Config) -> LoadedData:
    with DuckDBSession(cfg.db_file) as conn:
        repo = MemristorRepository(conn)

        sets = repo.list_endurance_sets(cfg.endurance_set_like)

        # raw for characteristic plot
        raw_characteristic = {s: repo.load_cycles_for_set(s) for s in sets}

        # raw for endurance metrics
        raw_endurance = {s: repo.load_endurance_cycles_for_set(s) for s in sets}

        forming_v = repo.load_forming_voltage_global(cfg.electroforming_like)
        classic = repo.load_classic_cycle_params_for_sets(sets)

    # transforms (no DB needed)
    cdf_table = build_cdf_table(classic, raw_characteristic, forming_v)
    box_table = build_box_table(classic, raw_characteristic, forming_v)
    end_df = build_endurance_table(raw_endurance)
    scatter_df = build_scatter_table(end_df)

    return LoadedData(
        sets=sets,
        raw_characteristic=raw_characteristic,
        raw_endurance=raw_endurance,
        forming_v=forming_v,
        classic=classic,
        cdf_table=cdf_table,
        box_table=box_table,
        end_df=end_df,
        scatter_df=scatter_df,
    )
