"""
Excel to DuckDB converter for memristor analysis data.

Uses fastexcel (Rust-based Calamine) for efficient Excel parsing
and DuckDB for fast analytical queries.

Supports batch processing of multiple Excel files with parallel processing.
"""

import fastexcel
import duckdb
import polars as pl
from pathlib import Path
import time
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import glob
import re


def sanitize_table_name(name: str) -> str:
    """
    Sanitize a string to be a valid SQL table name.

    - Replaces spaces and hyphens with underscores
    - Removes special characters
    - Prepends 'tbl_' if name starts with a number
    - Converts to lowercase
    """
    # Convert to lowercase and replace common separators
    clean = name.lower().strip()
    clean = clean.replace(" ", "_").replace("-", "_")

    # Remove any character that's not alphanumeric or underscore
    clean = re.sub(r"[^a-z0-9_]", "", clean)

    # If starts with a number, prepend 'tbl_'
    if clean and clean[0].isdigit():
        clean = f"tbl_{clean}"

    # If empty after cleaning, use a default
    if not clean:
        clean = "unnamed_table"

    return clean


def convert_excel_to_duckdb(
    excel_path: str | Path,
    db_path: str | Path = "memristor_data.duckdb",
    exclude_sheets: Optional[list[str]] = None,
    file_id: Optional[str] = None,
    append: bool = False,
) -> Path:
    """
    Convert Excel file with multiple worksheets to DuckDB database.

    Each 'Run' sheet becomes a record in the 'cycles' table with all measurements.
    Settings and Calc sheets are stored separately.

    Args:
        excel_path: Path to the Excel file
        db_path: Path for the output DuckDB database
        exclude_sheets: Sheet names to exclude from processing
        file_id: Optional identifier for this file (used in batch mode to track source)
        append: If True, append to existing tables instead of replacing

    Returns:
        Path to the created DuckDB database
    """
    excel_path = Path(excel_path)
    db_path = Path(db_path)

    if exclude_sheets is None:
        exclude_sheets = []

    # Auto-generate file_id from filename if not provided
    if file_id is None:
        file_id = excel_path.stem  # filename without extension

    print(f"Reading Excel file: {excel_path}")
    start_time = time.time()

    # Open the Excel file with fastexcel
    excel_file = fastexcel.read_excel(excel_path)
    sheet_names = excel_file.sheet_names

    print(
        f"Found {len(sheet_names)} sheets: {sheet_names[:5]}{'...' if len(sheet_names) > 5 else ''}"
    )

    # Connect to DuckDB (creates file if doesn't exist)
    conn = duckdb.connect(str(db_path))

    # Separate run sheets from metadata sheets
    run_sheets = [
        s for s in sheet_names if s.startswith("Run") and s not in exclude_sheets
    ]
    metadata_sheets = [
        s for s in sheet_names if not s.startswith("Run") and s not in exclude_sheets
    ]

    print(
        f"Processing {len(run_sheets)} run sheets and {len(metadata_sheets)} metadata sheets"
    )

    # Process run sheets (cycle data)
    all_cycles = []
    for i, sheet_name in enumerate(run_sheets):
        try:
            # Extract cycle number from sheet name (e.g., "Run222" -> 222)
            cycle_num = int(sheet_name.replace("Run", ""))

            # Read sheet data using fastexcel
            df = excel_file.load_sheet_by_name(sheet_name).to_polars()

            # Add cycle identifier and file source columns
            df = df.with_columns(
                [
                    pl.lit(cycle_num).alias("cycle_number"),
                    pl.lit(file_id).alias("source_file"),
                ]
            )

            # Clean column names (remove any special characters)
            clean_cols = {
                col: col.strip().replace("#", "").replace(" ", "_")
                for col in df.columns
            }
            df = df.rename(clean_cols)

            # Handle NORM_COND column if present
            if "NORM_COND" in df.columns:
                df = df.with_columns(
                    pl.col("NORM_COND")
                    .str.strip_chars()
                    .str.replace_all(r"(?i)#REF", "")
                    .str.replace(",", ".")
                    .replace("", None)
                    .str.strip_chars()
                    .cast(pl.Float64, strict=False)
                    .alias("NORM_COND")
                )

            all_cycles.append(df)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(run_sheets)} run sheets...")

        except Exception as e:
            print(f"  Warning: Could not process sheet '{sheet_name}': {e}")

    # Combine all cycle data into one dataframe
    if all_cycles:
        print("Combining all cycle data...")
        combined_df = pl.concat(all_cycles, how="diagonal")

        # Convert to DuckDB table
        if append:
            # Append to existing table
            try:
                conn.execute("INSERT INTO cycles SELECT * FROM combined_df")
            except duckdb.CatalogException:
                # Table doesn't exist, create it
                conn.execute("CREATE TABLE cycles AS SELECT * FROM combined_df")
        else:
            conn.execute("DROP TABLE IF EXISTS cycles")
            conn.execute("CREATE TABLE cycles AS SELECT * FROM combined_df")

        row_count = conn.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
        print(f"Created 'cycles' table with {row_count:,} rows")

    # Process metadata sheets (Settings, Calc, etc.)
    for sheet_name in metadata_sheets:
        try:
            df = excel_file.load_sheet_by_name(sheet_name).to_polars()

            # Clean column names
            clean_cols = {
                col: col.strip().replace("#", "").replace(" ", "_")
                for col in df.columns
            }
            df = df.rename(clean_cols)

            # Add source file column
            df = df.with_columns(pl.lit(file_id).alias("source_file"))

            table_name = sanitize_table_name(sheet_name)

            if append:
                try:
                    conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
                except duckdb.CatalogException:
                    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            else:
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"Created '{table_name}' table with {row_count:,} rows")

        except Exception as e:
            print(f"  Warning: Could not process sheet '{sheet_name}': {e}")

    # Create views for analysis
    conn.execute("""
        CREATE OR REPLACE VIEW cycle_summary AS
        SELECT 
            source_file,
            cycle_number,
            COUNT(*) as measurement_count,
            MIN(Time) as start_time,
            MAX(Time) as end_time,
            AVG(I) as avg_current,
            MAX(ABS(I)) as max_abs_current,
            MIN(AV) as min_voltage,
            MAX(AV) as max_voltage
        FROM cycles
        GROUP BY source_file, cycle_number
        ORDER BY source_file, cycle_number
    """)
    print("Created 'cycle_summary' view")

    # Close connection
    conn.close()

    elapsed = time.time() - start_time
    print(f"\nConversion complete in {elapsed:.2f} seconds")
    print(f"Database saved to: {db_path.absolute()}")

    return db_path


def export_to_parquet(
    db_path: str | Path, output_dir: str | Path = "parquet_data"
) -> Path:
    """
    Export DuckDB tables to Parquet files for even faster analysis.

    Args:
        db_path: Path to the DuckDB database
        output_dir: Directory for output Parquet files

    Returns:
        Path to the output directory
    """
    db_path = Path(db_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    conn = duckdb.connect(str(db_path), read_only=True)

    # Get all tables
    tables = conn.execute("SHOW TABLES").fetchall()

    for (table_name,) in tables:
        output_file = output_dir / f"{table_name}.parquet"
        conn.execute(
            f"COPY {table_name} TO '{output_file}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        print(f"Exported {table_name} to {output_file}")

    conn.close()
    print(f"\nParquet files saved to: {output_dir.absolute()}")

    return output_dir


def _process_single_file(
    args: tuple,
) -> tuple[str, pl.DataFrame | None, dict[str, pl.DataFrame], float]:
    """
    Process a single Excel file and return DataFrames (for parallel processing).

    Args:
        args: Tuple of (excel_path, file_id, exclude_sheets)

    Returns:
        Tuple of (file_id, cycles_df, metadata_dfs_dict, elapsed_time)
    """
    excel_path, file_id, exclude_sheets = args
    excel_path = Path(excel_path)

    if file_id is None:
        file_id = excel_path.stem

    start_time = time.time()

    try:
        excel_file = fastexcel.read_excel(excel_path)
        sheet_names = excel_file.sheet_names

        run_sheets = [
            s for s in sheet_names if s.startswith("Run") and s not in exclude_sheets
        ]
        metadata_sheets = [
            s
            for s in sheet_names
            if not s.startswith("Run") and s not in exclude_sheets
        ]

        # Process run sheets
        all_cycles = []
        for sheet_name in run_sheets:
            try:
                cycle_num = int(sheet_name.replace("Run", ""))
                df = excel_file.load_sheet_by_name(sheet_name).to_polars()
                df = df.with_columns(
                    [
                        pl.lit(cycle_num).alias("cycle_number"),
                        pl.lit(file_id).alias("source_file"),
                    ]
                )
                clean_cols = {
                    col: col.strip().replace("#", "").replace(" ", "_")
                    for col in df.columns
                }
                df = df.rename(clean_cols)
                if "NORM_COND" in df.columns:
                    df = df.with_columns(
                        pl.col("NORM_COND")
                        .str.strip_chars()
                        .str.replace_all(r"(?i)#REF", "")
                        .str.replace(",", ".")
                        .replace("", None)
                        .str.strip_chars()
                        .cast(pl.Float64, strict=False)
                        .alias("NORM_COND")
                    )
                all_cycles.append(df)
            except Exception:
                pass

        cycles_df = pl.concat(all_cycles, how="diagonal") if all_cycles else None

        # Process metadata sheets
        metadata_dfs = {}
        for sheet_name in metadata_sheets:
            try:
                df = excel_file.load_sheet_by_name(sheet_name).to_polars()
                clean_cols = {
                    col: col.strip().replace("#", "").replace(" ", "_")
                    for col in df.columns
                }
                df = df.rename(clean_cols)
                if "NORM_COND" in df.columns:
                    df = df.with_columns(
                        pl.col("NORM_COND")
                        .str.strip_chars()
                        .str.replace_all(r"(?i)#REF", "")
                        .str.replace(",", ".")
                        .replace("", None)
                        .str.strip_chars()
                        .cast(pl.Float64, strict=False)
                        .alias("NORM_COND")
                    )
                df = df.with_columns(pl.lit(file_id).alias("source_file"))
                table_name = sanitize_table_name(sheet_name)
                metadata_dfs[table_name] = df
            except Exception:
                pass

        elapsed = time.time() - start_time
        return (file_id, cycles_df, metadata_dfs, elapsed)

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"Error processing {excel_path}: {e}")
        return (file_id, None, {}, elapsed)


def batch_convert_excel_to_duckdb(
    input_pattern: str | list[str | Path],
    db_path: str | Path = "memristor_data.duckdb",
    exclude_sheets: Optional[list[str]] = None,
    max_workers: Optional[int] = None,
    use_parallel: bool = True,
) -> Path:
    """
    Convert multiple Excel files to a single DuckDB database.

    Processes files in parallel for maximum performance.

    Args:
        input_pattern: Glob pattern (e.g., "excel_files/*.xlsx") or list of file paths
        db_path: Path for the output DuckDB database
        exclude_sheets: Sheet names to exclude from processing
        max_workers: Maximum number of parallel workers (default: CPU count)
        use_parallel: Whether to use parallel processing (default: True)

    Returns:
        Path to the created DuckDB database

    Examples:
        # Process all Excel files in a directory
        batch_convert_excel_to_duckdb("data/*.xlsx")

        # Process specific files
        batch_convert_excel_to_duckdb(["file1.xlsx", "file2.xlsx", "file3.xlsx"])

        # Process recursively
        batch_convert_excel_to_duckdb("data/**/*.xlsx")
    """
    db_path = Path(db_path)

    if exclude_sheets is None:
        exclude_sheets = []

    # Resolve file paths
    if isinstance(input_pattern, str):
        excel_files = list(glob.glob(input_pattern, recursive=True))
    else:
        excel_files = [str(p) for p in input_pattern]

    if not excel_files:
        raise ValueError(f"No Excel files found matching pattern: {input_pattern}")

    print("=" * 60)
    print(f"BATCH PROCESSING: {len(excel_files)} Excel files")
    print("=" * 60)

    total_start = time.time()

    # Prepare arguments for parallel processing
    args_list = [(f, None, exclude_sheets) for f in excel_files]

    all_cycles = []
    all_metadata: dict[str, list[pl.DataFrame]] = {}

    if use_parallel and len(excel_files) > 1:
        # Parallel processing
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), len(excel_files))

        print(f"Using {max_workers} parallel workers...\n")

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_process_single_file, args): args[0]
                for args in args_list
            }

            for i, future in enumerate(as_completed(futures), 1):
                file_path = futures[future]
                try:
                    file_id, cycles_df, metadata_dfs, elapsed = future.result()

                    if cycles_df is not None:
                        all_cycles.append(cycles_df)

                    for table_name, df in metadata_dfs.items():
                        if table_name not in all_metadata:
                            all_metadata[table_name] = []
                        all_metadata[table_name].append(df)

                    rows = len(cycles_df) if cycles_df is not None else 0
                    print(
                        f"[{i}/{len(excel_files)}] {Path(file_path).name}: {rows:,} rows ({elapsed:.2f}s)"
                    )

                except Exception as e:
                    print(
                        f"[{i}/{len(excel_files)}] {Path(file_path).name}: ERROR - {e}"
                    )
    else:
        # Sequential processing
        print("Processing sequentially...\n")

        for i, args in enumerate(args_list, 1):
            file_id, cycles_df, metadata_dfs, elapsed = _process_single_file(args)

            if cycles_df is not None:
                all_cycles.append(cycles_df)

            for table_name, df in metadata_dfs.items():
                if table_name not in all_metadata:
                    all_metadata[table_name] = []
                all_metadata[table_name].append(df)

            rows = len(cycles_df) if cycles_df is not None else 0
            print(
                f"[{i}/{len(excel_files)}] {Path(args[0]).name}: {rows:,} rows ({elapsed:.2f}s)"
            )

    # Combine all data and write to DuckDB
    print(f"\nCombining data from {len(excel_files)} files...")

    conn = duckdb.connect(str(db_path))

    # Write cycles table
    if all_cycles:
        combined_cycles = pl.concat(all_cycles, how="diagonal")
        conn.execute("DROP TABLE IF EXISTS cycles")
        conn.execute("CREATE TABLE cycles AS SELECT * FROM combined_cycles")
        total_rows = conn.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
        print(f"Created 'cycles' table with {total_rows:,} total rows")

    # Write metadata tables
    for table_name, dfs in all_metadata.items():
        combined_df = pl.concat(dfs, how="diagonal")
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM combined_df")
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"Created '{table_name}' table with {row_count:,} rows")

    # Create views
    conn.execute("""
        CREATE OR REPLACE VIEW cycle_summary AS
        SELECT 
            source_file,
            cycle_number,
            COUNT(*) as measurement_count,
            MIN(Time) as start_time,
            MAX(Time) as end_time,
            AVG(I) as avg_current,
            MAX(ABS(I)) as max_abs_current,
            MIN(AV) as min_voltage,
            MAX(AV) as max_voltage
        FROM cycles
        GROUP BY source_file, cycle_number
        ORDER BY source_file, cycle_number
    """)

    # Create file summary view
    conn.execute("""
        CREATE OR REPLACE VIEW file_summary AS
        SELECT 
            source_file,
            COUNT(DISTINCT cycle_number) as num_cycles,
            COUNT(*) as total_measurements,
            MIN(cycle_number) as first_cycle,
            MAX(cycle_number) as last_cycle
        FROM cycles
        GROUP BY source_file
        ORDER BY source_file
    """)

    conn.close()

    total_elapsed = time.time() - total_start

    print(f"\n{'=' * 60}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Files processed: {len(excel_files)}")
    print(f"Total time: {total_elapsed:.2f} seconds")
    print(f"Average time per file: {total_elapsed / len(excel_files):.2f} seconds")
    print(f"Database saved to: {db_path.absolute()}")

    return db_path


def query_db(db_path: str | Path, query: str) -> pl.DataFrame:
    """
    Run a SQL query on the DuckDB database and return a Polars DataFrame.

    Args:
        db_path: Path to the DuckDB database
        query: SQL query string

    Returns:
        Query results as a Polars DataFrame
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    result = conn.execute(query).pl()
    conn.close()
    return result
