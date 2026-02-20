from __future__ import annotations

from plotting.config import load_config
from plotting.pipeline import load_all

from plotting.fig_characteristic import build_characteristic_figs
from plotting.fig_cdf import build_cdf_figs
from plotting.fig_boxplots import build_boxplots_figs
from plotting.fig_endurance import build_endurance_fig
from plotting.fig_correlation import build_correlation_scatter_fig


def _write(fig, out_path) -> None:
    fig.write_html(out_path)
    print("Wrote:", out_path)


def main() -> None:
    cfg = load_config()
    data = load_all(cfg)

    #  Characteristic
    def write_characteristic_figs():
        # Create the directory for characteristic plots
        char_dir = cfg.output_dir / "characteristic_plots"
        char_dir.mkdir(parents=True, exist_ok=True)

        # Generate and Save
        char_figs = build_characteristic_figs(data.raw_characteristic, data.sets)
        for fig in char_figs:
            pid = fig.layout.meta.get("param_id")
            # Save as AI.html and NORM_COND.html
            _write(fig, char_dir / f"{pid}.html")

    write_characteristic_figs()

    #  CDF
    # Create the directory
    cdf_dir = cfg.output_dir / "cdfs"
    cdf_dir.mkdir(parents=True, exist_ok=True)

    # Generate and Save
    cdf_figs = build_cdf_figs(data.cdf_table, data.sets)
    for fig in cdf_figs:
        pid = fig.layout.meta.get("param_id")
        # Using your existing _write function
        _write(fig, cdf_dir / f"{pid}.html")

    # Boxplots
    # 1. Define and create the output directory
    boxplot_dir = cfg.output_dir / "boxplots"
    boxplot_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generate the figures
    figs = build_boxplots_figs(data.box_table, data.sets)

    # 3. Save each figure to its own file in the new directory
    for fig in figs:
        # Extract the parameter name we stored in meta (e.g., "VSET", "R_LRS")
        param_id = fig.layout.meta.get("param_id", "plot")

        # Define the final path: cfg.output_dir / boxplots / VSET.html
        target_path = boxplot_dir / f"{param_id}.html"

        # Write the file
        _write(fig, target_path)

    #  Endurance performance vs cycle
    fig = build_endurance_fig(data.end_df, data.sets)
    _write(fig, cfg.output_dir / cfg.endurance_html)

    #  Correlation scatter
    fig = build_correlation_scatter_fig(data.scatter_df, data.sets)
    _write(fig, cfg.output_dir / cfg.correlation_html)


if __name__ == "__main__":
    main()
