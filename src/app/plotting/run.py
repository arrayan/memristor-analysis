from __future__ import annotations

from .config import load_config
from .pipeline import load_all

from .fig_characteristic import build_characteristic_fig
from .fig_cdf import build_cdf_fig
from .fig_boxplots import build_boxplots_fig
from .fig_endurance import build_endurance_fig
from .fig_correlation import build_correlation_scatter_fig


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

    #  Boxplots
    fig = build_boxplots_fig(data.box_table, data.sets)
    _write(fig, cfg.output_dir / cfg.boxplots_html)

    #  Endurance performance vs cycle
    fig = build_endurance_fig(data.end_df, data.sets)
    _write(fig, cfg.output_dir / cfg.endurance_html)

    #  Correlation scatter
    fig = build_correlation_scatter_fig(data.scatter_df, data.sets)
    _write(fig, cfg.output_dir / cfg.correlation_html)


if __name__ == "__main__":
    main()
