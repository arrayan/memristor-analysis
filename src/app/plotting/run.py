from __future__ import annotations
from pathlib import Path

from .config import load_config
from .pipeline import load_all

from .fig_characteristic import build_characteristic_figs
from .fig_cdf import build_cdf_figs
from .fig_boxplots import build_boxplots_figs
from .fig_endurance import build_endurance_figs
from .fig_correlation import build_correlation_scatter_figs
from .fig_correlation_stack import build_stack_level_correlation_figs
from .fig_boxplots_stack import build_stack_level_boxplots
from .fig_cdf_stack import build_stack_level_cdf_figs
from .fig_correlation_matrix import build_correlation_matrix_figs
from .fig_correlation_matrix_stack import build_stack_level_correlation_matrix_figs


def _write(fig, out_path) -> None:
    fig.write_html(out_path)
    print("Wrote:", out_path)


def _write_json(fig, out_path) -> None:
    out_path.write_text(fig.to_json(), encoding="utf-8")
    print("Wrote:", out_path)


def main(mode: str = "device") -> None:
    cfg = load_config()
    data = load_all(cfg)

    stack_id = getattr(data, "stack_id", None)
    if stack_id is None:
        if data.sets:
            sample_path = Path(next(iter(data.sets)))
            stack_id = (
                sample_path.stem.split("_")[0]
                if "_" in sample_path.stem
                else sample_path.stem
            )
            print(f"Info: Inferred stack_id from sets: {stack_id}")
        else:
            stack_id = "Unknown"
            print("Warning: No sets found, using Unknown as stack_id")

    devices = []
    if data.sets and stack_id != "Unknown":
        device_set = set()
        for s in data.sets:
            path = Path(s)
            stem = path.stem
            if stem.startswith(f"{stack_id}_"):
                remainder = stem[len(stack_id) + 1 :]
                if "_" in remainder:
                    device = remainder.split("_")[0]
                else:
                    device = remainder
                if device:
                    device_set.add(device)
        devices = sorted(device_set)

    if not devices:
        print(f"Warning: No devices found for stack {stack_id}")

    # Characteristic (set + reset)
    def write_characteristic_figs():
        char_dir = cfg.output_dir / "characteristic_plots"
        char_dir.mkdir(parents=True, exist_ok=True)

        char_figs = build_characteristic_figs(
            data.raw_characteristic,
            data.sets,
            raw_by_reset=data.raw_reset,  # pass reset data for current plot
        )
        for fig in char_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, char_dir / f"{pid}.html")
            _write_json(fig, char_dir / f"{pid}.json")

    write_characteristic_figs()

    # CDF
    def write_cdf_figs():
        cdf_dir = cfg.output_dir / "cdfs"
        cdf_dir.mkdir(parents=True, exist_ok=True)

        cdf_figs = build_cdf_figs(data.cdf_table, data.sets)
        for fig in cdf_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, cdf_dir / f"{pid}.html")
            _write_json(fig, cdf_dir / f"{pid}.json")

    write_cdf_figs()

    # CDF stack level
    def write_stack_level_cdf_figs():
        stack_cdf_dir = cfg.output_dir / "cdfs_stack_level"
        stack_cdf_dir.mkdir(parents=True, exist_ok=True)

        stack_cdf_figs = build_stack_level_cdf_figs(
            cdf_table=data.cdf_table,
            stack_id=stack_id,
            devices=devices,
        )
        for fig in stack_cdf_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, stack_cdf_dir / f"{pid}.html")
            _write_json(fig, stack_cdf_dir / f"{pid}.json")

    write_stack_level_cdf_figs()

    # Boxplots
    def write_boxplot_figs():
        boxplot_dir = cfg.output_dir / "boxplots"
        boxplot_dir.mkdir(parents=True, exist_ok=True)

        figs = build_boxplots_figs(data.box_table, data.sets)
        for fig in figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, boxplot_dir / f"{pid}.html")
            _write_json(fig, boxplot_dir / f"{pid}.json")

    write_boxplot_figs()

    # Stack level boxplots
    def write_stack_level_boxplots():
        stack_dir = cfg.output_dir / "boxplots_stack_level"
        stack_dir.mkdir(parents=True, exist_ok=True)

        stack_figs = build_stack_level_boxplots(
            box_table=data.box_table,
            stack_id=stack_id,
            devices=devices,
        )
        for fig in stack_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, stack_dir / f"{pid}.html")
            _write_json(fig, stack_dir / f"{pid}.json")

    write_stack_level_boxplots()

    # Endurance performance vs cycle
    def write_endurance_figs():
        end_dir = cfg.output_dir / "endurance_performance"
        end_dir.mkdir(parents=True, exist_ok=True)

        end_figs = build_endurance_figs(data.end_df, data.sets)
        for fig in end_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, end_dir / f"{pid}.html")
            _write_json(fig, end_dir / f"{pid}.json")

    write_endurance_figs()

    # Correlation scatter
    def write_correlation_scatter_figs():
        # Device-Level
        char_dir = cfg.output_dir / "correlation_plots"
        char_dir.mkdir(parents=True, exist_ok=True)

        correlation_figs = build_correlation_scatter_figs(data.scatter_df, data.sets)
        for fig in correlation_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, char_dir / f"{pid}.html")
            _write_json(fig, char_dir / f"{pid}.json")

        # Stack-Level
        stack_corr_dir = cfg.output_dir / "correlation_plots_stack_level"
        stack_corr_dir.mkdir(parents=True, exist_ok=True)

        stack_corr_figs = build_stack_level_correlation_figs(
            scatter_df=data.scatter_df,
            stack_id=stack_id,
            devices=devices,
        )
        for fig in stack_corr_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, stack_corr_dir / f"{pid}.html")
            _write_json(fig, stack_corr_dir / f"{pid}.json")

    write_correlation_scatter_figs()

    # Correlation matrix
    def write_correlation_matrix_figs():
        # Device-Level
        matrix_dir = cfg.output_dir / "correlation_matrices"
        matrix_dir.mkdir(parents=True, exist_ok=True)

        matrix_figs = build_correlation_matrix_figs(
            scatter_df=data.scatter_df,
            sets=data.sets,
            devices=devices,
        )
        for fig in matrix_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, matrix_dir / f"{pid}.html")
            _write_json(fig, matrix_dir / f"{pid}.json")

        # Stack-Level
        stack_matrix_dir = cfg.output_dir / "correlation_matrices_stack_level"
        stack_matrix_dir.mkdir(parents=True, exist_ok=True)

        stack_matrix_figs = build_stack_level_correlation_matrix_figs(
            scatter_df=data.scatter_df,
            stack_id=stack_id,
            devices=devices,
        )
        for fig in stack_matrix_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, stack_matrix_dir / f"{pid}.html")
            _write_json(fig, stack_matrix_dir / f"{pid}.json")

    write_correlation_matrix_figs()


if __name__ == "__main__":
    main()
