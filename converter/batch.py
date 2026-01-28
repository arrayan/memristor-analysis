import multiprocessing

import polars as pl
import glob
import os
import time
from pathlib import Path
import concurrent.futures
from typing import Optional
from .models import ProcessingResult
from .file_processor import ExcelFileProcessor
from .writer import DuckDBWriter


class BatchConverter:
    """batch conversion of excel files to DuckDB"""

    def __init__(self, db_path: str | Path, max_workers: Optional[int] = None):
        self.db_path = Path(db_path)
        self.max_workers = max_workers
        self.file_processor = ExcelFileProcessor()
        self.db_writer = DuckDBWriter(self.db_path)

    def convert(
        self,
        input_pattern: str | list[str | Path],
        exclude_sheets: Optional[list[str]] = None,
    ) -> Path:
        """
        Convert Excel files to DuckDB database.
        Args:
            input_pattern: Glob pattern or list of file paths
            exclude_sheets: Sheet names to exclude;
        Returns:
            Path to the created database
        """
        files = self._resolve_files(input_pattern)

        if not files:
            raise ValueError(f"No Excel files found matching: {input_pattern}")

        print("=" * 67)
        print(f"BATCH PROCESSING: {len(files)} Excel files")
        print("=" * 67)

        total_start = time.time()

        # Process all files
        results = self._process_files(files, exclude_sheets)

        # Combine and write results
        print(f"\nCombining data from {len(files)} files...")
        self._write_results(results)

        total_elapsed = time.time() - total_start
        self._print_summary(len(files), total_elapsed, results)

        return self.db_path

    def _resolve_files(self, input_pattern: str | list[str | Path]) -> list[Path]:
        """Resolve input pattern to list of file paths."""
        if isinstance(input_pattern, str):
            files = [Path(f) for f in glob.glob(input_pattern, recursive=True)]
        else:
            files = [Path(p) for p in input_pattern]

        # Filter out temp files
        return [f for f in files if not f.name.startswith("~$")]

    def _process_files(
        self,
        files: list[Path],
        exclude_sheets: Optional[list[str]],
    ) -> list[ProcessingResult]:
        """Process all files sequentially."""
        exclude_sheets = exclude_sheets or []
        max_workers = self.max_workers or max(1, os.cpu_count() - 1) #1 core left free for safety just in case GUI takes up memory
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = []
            for i, file_path in enumerate(files, 1):
                result = self.file_processor.process(file_path, exclude_sheets)
                results.append(result)

                status = (
                    f"{result.row_count:,} rows"
                    if result.row_count > 0
                    else "metadata only"
                )
                print(
                    f"[{i}/{len(files)}] {file_path.name}: {status} ({result.elapsed:.2f}s)"
                )

            return results





    def _write_results(self, results: list[ProcessingResult]):
        """Combine and write all results to database."""
        # Combine cycles
        all_cycles = [r.cycles_df for r in results if r.cycles_df is not None]
        if all_cycles:
            combined_cycles = pl.concat(all_cycles, how="diagonal")
            row_count = self.db_writer.write_cycles(combined_cycles)
            print(f"Created 'cycles' table with {row_count:,} rows")

        # Combine metadata tables
        all_metadata: dict[str, list[pl.DataFrame]] = {}
        for result in results:
            for table_name, df in result.metadata_dfs.items():
                if table_name not in all_metadata:
                    all_metadata[table_name] = []
                all_metadata[table_name].append(df)

        for table_name, dfs in all_metadata.items():
            combined = pl.concat(dfs, how="diagonal")
            row_count = self.db_writer.write_metadata_table(table_name, combined)
            print(f"Created '{table_name}' table with {row_count:,} rows")

        # Create views
        # self.db_writer.create_views()

    def _print_summary(
        self,
        file_count: int,
        elapsed: float,
        results: list[ProcessingResult],
    ):
        """Processing summary including warnings"""
        all_warnings = []
        for r in results:
            all_warnings.extend(r.warnings)

        print(f"\n{'=' * 67}")
        print("BATCH PROCESSING COMPLETE")
        print(f"{'=' * 67}")
        print(f"Files processed: {file_count}")
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Average time per file: {elapsed / file_count:.2f} seconds")
        print(f"Database saved to: {self.db_path.absolute()}")

        if all_warnings:
            print(f"\nWarnings ({len(all_warnings)}):")
            for w in all_warnings[:10]:
                print(f"  - {w}")
            if len(all_warnings) > 10:
                print(f"  ... and {len(all_warnings) - 10} more")
