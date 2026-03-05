from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    db_file: Path
    output_dir: Path

    # File name patterns
    endurance_set_like: str = "%endurance_set%"
    electroforming_like: str = "%electroforming%"
    leakage_set_like: str = "%leakage%"
    endurance_reset_like: str = "%endurance_reset%"

    # Output HTML files
    characteristic_html: str = "characteristic_plots.html"
    cdf_html: str = "endurance_cdf.html"
    boxplots_html: str = "endurance_boxplots.html"
    endurance_html: str = "endurance_performance.html"
    correlation_html: str = "device_correlation_scatter.html"


def load_config() -> Config:
    # DB path from environment variable (portable across machines)
    db = Path(__file__).parent.parent.parent.parent / "output.duckdb"
    if not db:
        raise RuntimeError(
            "MEMRISTOR_DB is not set.\n"
            "Set it like:\n"
            "  export MEMRISTOR_DB='/path/to/memristor_data.duckdb'\n"
        )

    db_file = Path(db).expanduser().resolve()
    if not db_file.exists():
        raise FileNotFoundError(f"DuckDB file not found: {db_file}")

    # Output directory defaults to project_root/output (project_root = parent of plotting/)
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "temp" / "device"
    output_dir.mkdir(parents=True, exist_ok=True)

    return Config(db_file=db_file, output_dir=output_dir)
