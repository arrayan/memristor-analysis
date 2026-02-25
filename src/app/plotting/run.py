from __future__ import annotations

from .config import load_config
from .pipeline import load_all

from .fig_characteristic import build_characteristic_figs
from .fig_cdf import build_cdf_figs
from .fig_boxplots import build_boxplots_figs
from .fig_endurance import build_endurance_figs
from .fig_correlation import build_correlation_scatter_figs


def _write(fig, out_path) -> None:
    fig.write_html(out_path)
    print("Wrote:", out_path)


# generating a JSON for Export
def _write_json(fig, out_path) -> None:
    out_path.write_text(fig.to_json(), encoding="utf-8")
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
            # Save as AI.html and NORM_COND.html as well as JSON for export
            _write(fig, char_dir / f"{pid}.html")
            _write_json(fig, char_dir / f"{pid}.json")

    write_characteristic_figs()

    #  CDF
    def write_cdf_figs():
        # Create the directory
        cdf_dir = cfg.output_dir / "cdfs"
        cdf_dir.mkdir(parents=True, exist_ok=True)

        # Generate and Save
        cdf_figs = build_cdf_figs(data.cdf_table, data.sets)
        for fig in cdf_figs:
            pid = fig.layout.meta.get("param_id")
            # Using your existing _write function
            _write(fig, cdf_dir / f"{pid}.html")
            _write_json(fig, cdf_dir / f"{pid}.json")

    write_cdf_figs()

    # Boxplots
    def write_boxplot_figs():
        # Create the directory
        boxplot_dir = cfg.output_dir / "boxplots"
        boxplot_dir.mkdir(parents=True, exist_ok=True)

        # Generate and Save
        figs = build_boxplots_figs(data.box_table, data.sets)
        for fig in figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, boxplot_dir / f"{pid}.html")
            _write_json(fig, boxplot_dir / f"{pid}.json")

    write_boxplot_figs()

    #  Endurance performance vs cycle
    def write_endurance_figs():
        #  Endurance Performance (Nested)
        end_dir = cfg.output_dir / "endurance_performance"
        end_dir.mkdir(parents=True, exist_ok=True)

        # Generate and Save
        end_figs = build_endurance_figs(data.end_df, data.sets)
        for fig in end_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, end_dir / f"{pid}.html")
            _write_json(fig, end_dir / f"{pid}.json")

    write_endurance_figs()

    #  Correlation scatter
    def write_correlation_scatter_figs():
        #  Correlation plots
        char_dir = cfg.output_dir / "correlation_plots"
        char_dir.mkdir(parents=True, exist_ok=True)

        # Generate and Save
        correlation_figs = build_correlation_scatter_figs(data.scatter_df, data.sets)
        for fig in correlation_figs:
            pid = fig.layout.meta.get("param_id")
            _write(fig, char_dir / f"{pid}.html")
            _write_json(fig, char_dir / f"{pid}.json")

    write_correlation_scatter_figs()


if __name__ == "__main__":
    main()
