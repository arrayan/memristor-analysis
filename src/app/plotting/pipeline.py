from __future__ import annotations

from dataclasses import dataclass

import duckdb
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
    resets: list[str]
    stack_id: str
    devices: list[str]

    # raw
    raw_characteristic: dict[str, pd.DataFrame]  # cycle_number, Time, AV, AI, NORM_COND
    raw_endurance: dict[
        str, pd.DataFrame
    ]  # cycle_number, Time, AV, AI, VSET, ILRS, IHRS
    raw_reset: dict[str, pd.DataFrame]  # cycle_number, Time, AV, AI

    # derived
    forming_v: float | None  # global forming voltage
    forming_v_by_device: dict[str, float]  # per-device forming voltage
    leakage_i_by_device: dict[str, float]  # per-device leakage current (pristine)
    v_read: float  # read voltage from leakage file
    first_v_reset: dict[str, float]  # per-device 1st V_reset

    classic: pd.DataFrame
    cdf_table: pd.DataFrame
    box_table: pd.DataFrame
    end_df: pd.DataFrame
    scatter_df: pd.DataFrame


def load_all(cfg: Config) -> LoadedData:
    # 1. Safety check for the cycles table (Catalog Error prevention)
    # Prevents a bug encountered during initial build testing
    # 1. Check if the 'cycles' table exists
    with duckdb.connect(str(cfg.db_file)) as check_conn:
        table_exists = check_conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = 'cycles'"
        ).fetchone()[0]

    # 2. If the file exists but is empty, raise a helpful error
    if table_exists == 0:
        raise RuntimeError(
            f"The database at {cfg.db_file} contains no data.\n\n"
            "Please check if your Excel files follow the required naming convention "
            "and contain the necessary 'cycles' sheets."
        )

    with DuckDBSession(cfg.db_file) as conn:
        repo = MemristorRepository(conn)

        sets = repo.list_endurance_sets(cfg.endurance_set_like)
        resets = repo.list_endurance_resets(cfg.endurance_reset_like)

        stack_id = repo.get_stack_id() or "Unknown"
        devices = repo.list_devices()

        # raw for characteristic plot (set files)
        raw_characteristic = {s: repo.load_cycles_for_set(s) for s in sets}

        # raw for endurance metrics (set files)
        raw_endurance = {s: repo.load_endurance_cycles_for_set(s) for s in sets}

        # raw reset files — used for V_reset and I_reset_max
        raw_reset = {s: repo.load_endurance_cycles_for_reset(s) for s in resets}

        forming_v = repo.load_forming_voltage_global(cfg.electroforming_like)
        forming_v_by_device = repo.load_forming_voltage_per_device(
            devices, cfg.electroforming_like
        )
        leakage_i_by_device = repo.load_leakage_current_per_device(
            devices, cfg.leakage_like
        )
        first_v_reset = repo.load_first_v_reset(cfg.endurance_reset_like)
        v_read = repo.load_v_read(cfg.leakage_like)

        classic = repo.load_classic_cycle_params_for_sets(sets, v_read=v_read)

        # transforms (no DB needed)
        cdf_table = build_cdf_table(
            classic,
            raw_reset,
            forming_v_by_device,
            leakage_i_by_device,
            stack_id=stack_id,
        )
        box_table = build_box_table(
            classic,
            raw_reset,
            forming_v_by_device,
            leakage_i_by_device,
            stack_id=stack_id,
        )
        end_df = build_endurance_table(raw_endurance, raw_reset, v_read=v_read)
        scatter_df = build_scatter_table(end_df)

        return LoadedData(
            sets=sets,
            resets=resets,
            stack_id=stack_id,
            devices=devices,
            raw_characteristic=raw_characteristic,
            raw_endurance=raw_endurance,
            raw_reset=raw_reset,
            forming_v=forming_v,
            forming_v_by_device=forming_v_by_device,
            leakage_i_by_device=leakage_i_by_device,
            first_v_reset=first_v_reset,
            v_read=v_read,
            classic=classic,
            cdf_table=cdf_table,
            box_table=box_table,
            end_df=end_df,
            scatter_df=scatter_df,
        )
