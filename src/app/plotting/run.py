from __future__ import annotations

from plotting.config import load_config
from plotting.pipeline import load_all

from plotting.fig_characteristic import build_characteristic_fig
from plotting.fig_cdf import build_cdf_fig
from plotting.fig_boxplots import build_boxplots_fig
from plotting.fig_endurance import build_endurance_fig
from plotting.fig_correlation import build_correlation_scatter_fig


def _write(fig, out_path) -> None:
    fig.write_html(out_path)
    print("Wrote:", out_path)


def main() -> None:
    cfg = load_config()
    data = load_all(cfg)

    #  Characteristic
    fig = build_characteristic_fig(data.raw_characteristic, data.sets)
    _write(fig, cfg.output_dir / cfg.characteristic_html)

    #  CDF
    fig = build_cdf_fig(data.cdf_table, data.sets)
    _write(fig, cfg.output_dir / cfg.cdf_html)

    
    # 1. Define and create the output directory
    boxplot_dir = cfg.output_dir / "boxplots"
    boxplot_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generate the figures
    figs = build_boxplots_fig(data.box_table, data.sets)

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
