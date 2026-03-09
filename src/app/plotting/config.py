from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from app.core.paths import DB_FILE, TEMP_DIR
from app.core.modes import Mode


@dataclass(frozen=True)
class Config:
    db_file: Path
    output_dir: Path
    mode: Mode

    # File name patterns
    endurance_set_like: str = "%endurance_set%"
    endurance_reset_like: str = "%endurance_reset%"
    electroforming_like: str = "%electroforming%"
    leakage_like: str = "%leakage%"

    # Output HTML files
    characteristic_html: str = "characteristic_plots.html"
    cdf_html: str = "endurance_cdf.html"
    boxplots_html: str = "endurance_boxplots.html"
    endurance_html: str = "endurance_performance.html"
    correlation_html: str = "device_correlation_scatter.html"


def load_config() -> Config:
    mode_str = os.environ.get("MEMRISTOR_MODE", Mode.DEVICE.value)
    mode = Mode(mode_str)

    # Point directly to AppData temp subfolder
    output_dir = TEMP_DIR / mode.value
    output_dir.mkdir(parents=True, exist_ok=True)

    return Config(
        db_file=DB_FILE,  # Absolute path to AppData
        output_dir=output_dir,
        mode=mode,
    )
