import duckdb
import polars as pl
from pathlib import Path
from typing import Optional
from .models import FileMetadata, ProcessingResult
from .metadata import MetadataExtractor
from .sheets import SheetProcessor
from .file_processor import ExcelFileProcessor
from .writer import DuckDBWriter
from .batch import BatchConverter
from .convert_path_to_glob import path_to_glob


"""
Excel to DuckDB converter package
Usage:
    from converter import BatchConverter
    converter = BatchConverter("output.duckdb")
    converter.convert("excel_files/*.xlsx")
Or using convenience functions:
    from converter import batch_convert, convert_single, query_db
    batch_convert("excel_files/*.xlsx", "output.duckdb")
Or via:
    cli.py !Recommended!
"""


def batch_convert(
    input_pattern: str | list[str | Path],
    db_path: str | Path = "memristor_data.duckdb",
    exclude_sheets: Optional[list[str]] = None,
) -> Path:
    """Convert multiple Excel files to a single DuckDB database."""
    converter = BatchConverter(db_path)
    return converter.convert(input_pattern, exclude_sheets)


def convert_single(
    excel_path: str | Path,
    db_path: str | Path = "memristor_data.duckdb",
    exclude_sheets: Optional[list[str]] = None,
) -> Path:
    """Convert a single Excel file to DuckDB database."""
    return batch_convert([excel_path], db_path, exclude_sheets)


def export_to_parquet(
    db_path: str | Path, output_dir: str | Path = "parquet_data"
) -> Path:
    """Export DuckDB tables to Parquet files."""
    db_path = Path(db_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    conn = duckdb.connect(str(db_path), read_only=True)
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


def query_db(db_path: str | Path, query: str) -> pl.DataFrame:
    conn = duckdb.connect(str(db_path), read_only=True)
    result = conn.execute(query).pl()
    conn.close()
    return result

    # 7 classes and 4 functions[batch_convert..]


__all__ = [
    "FileMetadata",
    "ProcessingResult",
    "MetadataExtractor",
    "SheetProcessor",
    "ExcelFileProcessor",
    "DuckDBWriter",
    "BatchConverter",
    "batch_convert",
    "convert_single",
    "export_to_parquet",
    "query_db",
    "path_to_glob",
]
