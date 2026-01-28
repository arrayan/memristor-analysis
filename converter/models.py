import polars as pl
from dataclasses import dataclass
from dataclasses import field
from typing import Optional


@dataclass
class FileMetadata:
    """Metadata extracted from file path for stack-level analysis and imports"""

    source_id: str
    stack_id: Optional[str] = None
    device_id: Optional[str] = None
    device_row: Optional[str] = None
    device_col: Optional[int] = None
    measurement_type: Optional[str] = None
    file_path: str = ""


@dataclass
class ProcessingResult:
    """Result of processing a single Excel file."""

    file_id: str
    cycles_df: Optional[pl.DataFrame] = None
    metadata_dfs: dict[str, pl.DataFrame] = field(default_factory=dict)
    elapsed: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.cycles_df) if self.cycles_df is not None else 0

    @property
    def has_data(self) -> bool:
        return self.cycles_df is not None or len(self.metadata_dfs) > 0
