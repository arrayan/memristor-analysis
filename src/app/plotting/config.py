from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from ..core import Mode


@dataclass(frozen=True)
class Config:
    db_file: Path
    output_dir: Path
    mode: Mode

    # File name patterns
    endurance_set_like: str = "%endurance_set%"
    electroforming_like: str = "%electroforming%"


def load_config() -> Config:
    """
    Loads configuration.
    Determines mode from environment variable 'MEMRISTOR_MODE'
    (set by the ImportWorker) to decide the output directory.
    """
    # 1. Resolve Database Path
    # You can keep your logic or use an environment variable for flexibility
    db = Path(__file__).parent.parent.parent.parent / "output.duckdb"
    db_file = db.expanduser().resolve()

    if not db_file.exists():
        # Fallback to current directory for development
        db_file = Path("output.duckdb").resolve()
        if not db_file.exists():
            raise FileNotFoundError(f"DuckDB file not found at {db_file}")

    # 2. Determine Mode
    # We use an environment variable so the GUI can communicate the mode
    # to the plotting script without changing function signatures.
    mode = os.environ.get("MEMRISTOR_MODE", "Device Level")

    # 3. Resolve Output Directory
    # project_root = parent of plotting/
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "temp" / mode

    output_dir.mkdir(parents=True, exist_ok=True)

    return Config(db_file=db_file, output_dir=output_dir, mode=mode)
