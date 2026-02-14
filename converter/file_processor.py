import fastexcel
import polars as pl
import time
from pathlib import Path
from typing import Optional
from .models import ProcessingResult
from .metadata import MetadataExtractor
from .sheets import SheetProcessor


class ExcelFileProcessor:
    """Processes a single Excel file into DataFrames."""

    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
        self.sheet_processor = SheetProcessor()

    def process(
        self,
        file_path: Path,
        exclude_sheets: Optional[list[str]] = None,
    ) -> ProcessingResult:
        """Process an Excel file and return all data."""
        file_path = Path(file_path)
        exclude_sheets = exclude_sheets or []
        metadata = self.metadata_extractor.extract(file_path)
        result = ProcessingResult(file_id=metadata.source_id)
        start_time = time.time()

        try:
            excel_file = fastexcel.read_excel(file_path)
            sheet_names = excel_file.sheet_names

            run_sheets = [
                s
                for s in sheet_names
                if s.startswith("Run") and s not in exclude_sheets
            ]
            other_sheets = [
                s
                for s in sheet_names
                if not s.startswith("Run") and s not in exclude_sheets
            ]

            # Process all run sheets
            all_cycles = []
            for sheet_name in run_sheets:
                df, warning = self.sheet_processor.process_run_sheet(
                    excel_file, sheet_name, metadata
                )
                if warning:
                    result.warnings.append(warning)
                if df is not None:
                    all_cycles.append(df)

            if all_cycles:  # diagonal concatenation
                result.cycles_df = pl.concat(all_cycles, how="diagonal_relaxed")

            # Process metadata sheets
            for sheet_name in other_sheets:
                df, table_name, warning = self.sheet_processor.process_metadata_sheet(
                    excel_file, sheet_name, metadata.source_id
                )
                if warning:
                    result.warnings.append(warning)
                if df is not None:
                    result.metadata_dfs[table_name] = df

        except Exception as e:
            result.warnings.append(f"Fatal error: {e}")
        result.elapsed = time.time() - start_time
        return result
