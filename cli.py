#!/usr/bin/env python3
import argparse

from app.converter import convert_single, batch_convert, export_to_parquet
from app.converter.format_converter import FormatConverter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel file(s) to DuckDB database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  python cli.py data/file.xlsx -o output.duckdb
  
  # Batch processing with glob pattern
  python cli.py "data/*.xlsx" --batch -o all_data.duckdb
  
  # Recursive batch processing
  python cli.py "data/**/*.xlsx" --batch -o all_data.duckdb
  
  # Multiple specific files
  python cli.py file1.xlsx file2.xlsx file3.xlsx --batch
  
  # Export to Parquet as well
  python cli.py "data/*.xlsx" --batch --parquet
  
  # Convert DuckDB to CSV
  python cli.py data/file.duckdb --convert -o output.csv
  
  # Convert Parquet to TXT
  python cli.py data/file.parquet --convert -o output.txt
  
  # Convert DuckDB to XLSX
  python cli.py data/file.duckdb --convert -o output.xlsx
        """,
    )
    parser.add_argument(
        "excel_files",
        nargs="+",
        help="Path(s) to Excel file(s) or glob pattern (use --batch for multiple files)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="memristor_data.duckdb",
        help="Output DuckDB file path",
    )
    parser.add_argument(
        "--batch", action="store_true", help="Batch process multiple files"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: auto)",
    )
    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel processing"
    )
    parser.add_argument(
        "--parquet", action="store_true", help="Also export to Parquet format"
    )
    parser.add_argument(
        "--parquet-dir", default="parquet_data", help="Directory for Parquet output"
    )
    parser.add_argument(
        "--convert", action="store_true", help="Convert parquet/duckdb to csv/txt/xlsx (independent mode)",
    )

    args = parser.parse_args()

    if args.convert and args.parquet:
        parser.error("parquet cannot be used with convert")
    if args.convert and args.batch:
        parser.error("batch cannot be used with convert")
    if args.convert and args.workers is not None:
        parser.error("workers cannot be used with convert")
    if args.convert and args.no_parallel:
        parser.error("no-parallel cannot be used with convert")

    if args.convert:
        input_file = Path(args.excel_files[0])
        if not input_file.exists():
            parser.error(f"File not found: {input_file}")

        output_file = Path(args.output)

        converter = FormatConverter()
        converter.convert(input_file, output_file)

        print(f"Converted {input_file} -> {output_file}")

    else:
        # Determine if batch or single file mode
        if args.batch or len(args.excel_files) > 1:
            # Batch mode
            if len(args.excel_files) == 1 and (
                "*" in args.excel_files[0] or "?" in args.excel_files[0]
            ):
                input_pattern = args.excel_files[0]
            else:
                input_pattern = args.excel_files  # List of files

            db_path = batch_convert(
                input_pattern,
                args.output,
                exclude_sheets=None,
            )
        else:
            db_path = convert_single(args.excel_files[0], args.output)

        if args.parquet:
            export_to_parquet(db_path, args.parquet_dir)


if __name__ == "__main__":
    main()
