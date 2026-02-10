#!/usr/bin/env python3
"""
Database utilities for memristor analysis.
Quick overview of DuckDB database contents with per-file sample values.
"""

import duckdb
import polars as pl
from pathlib import Path
import sys


def format_value(val, use_scientific=True):
    """Format value with scientific notation for small numbers."""
    if val is None:
        return "NULL"
    
    if isinstance(val, float):
        abs_val = abs(val)
        # Use scientific notation for very small or very large numbers
        if use_scientific and (abs_val < 0.001 or abs_val >= 1000000):
            return f"{val:.4E}"
        elif abs_val < 0.01:
            return f"{val:.6f}"
        elif abs_val < 1:
            return f"{val:.4f}"
        else:
            return f"{val:.2f}"
    
    return str(val)


def print_db_overview(db_path: str | Path) -> None:
    """Print comprehensive overview of a memristor database."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"DATABASE OVERVIEW: {db_path.name}")
    print(f"{'='*80}")
    print(f"Full path: {db_path.absolute()}")
    print(f"File size: {db_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"{'='*80}\n")
    
    conn = duckdb.connect(str(db_path), read_only=True)
    
    try:
        # List all tables
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"TABLES ({len(tables)} total):")
        print("-" * 40)
        for (table_name,) in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  * {table_name:<20} {count:>10,} rows")
        print()
        
        # Cycles overview
        if any(t[0] == 'cycles' for t in tables):
            print(f"CYCLES ANALYSIS:")
            print("-" * 40)
            
            total = conn.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
            print(f"  Total measurements: {total:,}")
            
            files = conn.execute("SELECT COUNT(DISTINCT source_file) FROM cycles").fetchone()[0]
            print(f"  Source files: {files}")
            
            columns = conn.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cycles'
                ORDER BY ordinal_position
            """).fetchall()
            col_names = [c[0] for c in columns]
            
            if 'stack_id' in col_names:
                stacks = conn.execute("SELECT COUNT(DISTINCT stack_id) FROM cycles").fetchone()[0]
                print(f"  Stacks: {stacks}")
            
            if 'device_id' in col_names:
                devices = conn.execute("SELECT COUNT(DISTINCT device_id) FROM cycles").fetchone()[0]
                print(f"  Devices: {devices}")
            
            cycle_stats = conn.execute("""
                SELECT MIN(cycle_number), MAX(cycle_number), COUNT(DISTINCT cycle_number)
                FROM cycles
            """).fetchone()
            print(f"  Cycle range: {cycle_stats[0]} - {cycle_stats[1]} ({cycle_stats[2]} unique cycles)")
            print()
            
            # Per-source-file sample values for key columns
            sample_cols = ['Time', 'AI', 'AV', 'I', 'RESISTANCE', 'NORM_COND']
            available_sample_cols = [c for c in sample_cols if c in col_names]
            
            if available_sample_cols:
                print(f"SAMPLE VALUES PER SOURCE FILE:")
                print(f"{'='*80}")
                
                source_files = conn.execute("""
                    SELECT DISTINCT source_file FROM cycles ORDER BY source_file
                """).fetchall()
                
                for file_num, (source_file,) in enumerate(source_files, 1):
                    print(f"\n[{file_num}/{len(source_files)}] {source_file}")
                    print("-" * 80)
                    
                    # File overview
                    file_stats = conn.execute(f"""
                        SELECT 
                            COUNT(*) as total_rows,
                            COUNT(DISTINCT cycle_number) as unique_cycles,
                            MIN(cycle_number) as min_cycle,
                            MAX(cycle_number) as max_cycle
                        FROM cycles
                        WHERE source_file = '{source_file}'
                    """).fetchone()
                    
                    print(f"  Total rows: {file_stats[0]:,} | Cycles: {file_stats[1]} (range: {file_stats[2]}-{file_stats[3]})")
                    print()
                    
                    # Sample values for each column (first 3 non-null values)
                    print(f"  {'Column':<15} {'Type':<12} {'First 3 Values'}")
                    print(f"  {'-'*70}")
                    
                    for col in available_sample_cols:
                        # Get data type
                        data_type = next((c[1] for c in columns if c[0] == col), 'UNKNOWN')
                        
                        # Get first 3 non-null values
                        sample_vals = conn.execute(f"""
                            SELECT "{col}"
                            FROM cycles
                            WHERE source_file = '{source_file}' AND "{col}" IS NOT NULL
                            ORDER BY rowid
                            LIMIT 3
                        """).fetchall()
                        
                        # Format values
                        if sample_vals:
                            val_str = ", ".join([format_value(v[0]) for v in sample_vals])
                        else:
                            val_str = "NULL / no data"
                        
                        print(f"  {col:<15} {data_type:<12} {val_str}")
                    
                    # Summary statistics for first 3 columns
                    print()
                    print(f"  {'Column':<15} {'Distinct':>10} {'Min':>15} {'Max':>15}")
                    print(f"  {'-'*60}")
                    
                    for col in available_sample_cols[:3]:
                        summary = conn.execute(f"""
                            SELECT 
                                COUNT(DISTINCT "{col}"),
                                MIN("{col}"),
                                MAX("{col}")
                            FROM cycles
                            WHERE source_file = '{source_file}'
                        """).fetchone()
                        
                        distinct = summary[0] if summary[0] is not None else 0
                        min_val = summary[1]
                        max_val = summary[2]
                        
                        print(f"  {col:<15} {distinct:>10,} {format_value(min_val):>15} {format_value(max_val):>15}")
                
                print(f"\n{'='*80}")
                print()
            
            # Detailed statistics per source file for numerical columns
            numerical_cols = ['AV', 'I', 'AI', 'RESISTANCE', 'NORM_COND']
            available_num_cols = [c for c in numerical_cols if c in col_names]
            
            if available_num_cols:
                print(f"DETAILED STATISTICS PER SOURCE FILE:")
                print(f"{'='*80}")
                
                source_files = conn.execute("""
                    SELECT DISTINCT source_file FROM cycles ORDER BY source_file
                """).fetchall()
                
                for file_num, (source_file,) in enumerate(source_files, 1):
                    print(f"\n[{file_num}/{len(source_files)}] {source_file}")
                    print("-" * 80)
                    
                    print(f"  {'Column':<15} {'Min':>15} {'Max':>15} {'Mean':>15} {'Std':>15} {'Nulls':>8}")
                    print(f"  {'-'*90}")
                    
                    for col in available_num_cols:
                        stats = conn.execute(f"""
                            SELECT 
                                MIN("{col}"), 
                                MAX("{col}"), 
                                AVG("{col}"),
                                STDDEV("{col}"),
                                COUNT(*) - COUNT("{col}")
                            FROM cycles
                            WHERE source_file = '{source_file}'
                        """).fetchone()
                        
                        min_val = stats[0]
                        max_val = stats[1]
                        mean_val = stats[2]
                        std_val = stats[3]
                        nulls = stats[4] if stats[4] is not None else 0
                        
                        print(f"  {col:<15} {format_value(min_val):>15} {format_value(max_val):>15} "
                              f"{format_value(mean_val):>15} {format_value(std_val):>15} {nulls:>8,}")
                
                print(f"\n{'='*80}")
                print()
        
        # Views
        views = conn.execute("""
            SELECT table_name FROM information_schema.tables WHERE table_type = 'VIEW'
        """).fetchall()
        if views:
            print(f"VIEWS ({len(views)} total):")
            print("-" * 40)
            for (view_name,) in views:
                print(f"  * {view_name}")
            print()
            
    finally:
        conn.close()
    
    print(f"{'='*80}\n")


def quick_stats(db_path: str | Path) -> dict:
    """Get quick statistics as dictionary for programmatic use."""
    db_path = Path(db_path)
    if not db_path.exists():
        return {"error": "Database not found"}
    
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        stats = {
            "file": str(db_path),
            "size_mb": round(db_path.stat().st_size / (1024*1024), 2),
        }
        
        tables = conn.execute("SHOW TABLES").fetchall()
        stats["tables"] = {t[0]: conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0] 
                          for t in tables}
        
        if 'cycles' in stats["tables"]:
            stats["total_measurements"] = stats["tables"]["cycles"]
            stats["files"] = conn.execute("SELECT COUNT(DISTINCT source_file) FROM cycles").fetchone()[0]
            
        return stats
    finally:
        conn.close()


def compare_databases(db_paths: list[str | Path]) -> None:
    """Compare multiple databases side by side."""
    print(f"\n{'='*80}")
    print(f"DATABASE COMPARISON")
    print(f"{'='*80}\n")
    
    all_stats = []
    for path in db_paths:
        stats = quick_stats(path)
        all_stats.append((Path(path).name, stats))
    
    print(f"{'Database':<30} {'Size (MB)':>12} {'Measurements':>15} {'Files':>10}")
    print("-" * 80)
    for name, stats in all_stats:
        if "error" in stats:
            print(f"{name:<30} {'ERROR':>12}")
        else:
            size = stats.get("size_mb", 0)
            meas = stats.get("total_measurements", 0)
            files = stats.get("files", 0)
            print(f"{name:<30} {size:>12.2f} {meas:>15,} {files:>10}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils.py <database.duckdb>")
        print("       python utils.py compare <db1.duckdb> <db2.duckdb> ...")
        sys.exit(1)
    
    if sys.argv[1] == "compare":
        compare_databases(sys.argv[2:])
    else:
        print_db_overview(sys.argv[1])