import re
import polars as pl
from typing import Optional
from .models import FileMetadata


class SheetProcessor:
    """Processes individual Excel sheets into DataFrames."""

    """ .xslsx -> FastExcel -> PolarsDF(In process) -> ..... """

    @staticmethod
    def clean_column_names(df: pl.DataFrame) -> pl.DataFrame:
        """Clean column names by removing special characters."""
        clean_cols = {
            col: col.strip().replace("#", "").replace(" ", "_") for col in df.columns
        }
        return df.rename(clean_cols)

    @staticmethod
    def fix_norm_cond(df: pl.DataFrame) -> pl.DataFrame:
        """Fix NORM_COND column if present (handles #REF errors, etc)."""
        if "NORM_COND" not in df.columns:
            return df

        return df.with_columns(
            pl.col("NORM_COND")
            .cast(pl.Utf8)
            .str.strip_chars()
            .str.replace_all(r"(?i)#REF", "")
            .str.replace(",", ".")
            .replace("", None)
            .str.strip_chars()
            .cast(pl.Float64, strict=False)
            .alias("NORM_COND")
        )

    @staticmethod
    def sanitize_table_name(name: str) -> str:
        """Sanitize a string to be a valid SQL table name."""
        clean = name.lower().strip()
        clean = clean.replace(" ", "_").replace("-", "_")
        clean = re.sub(r"[^a-z0-9_]", "", clean)

        if clean and clean[0].isdigit():
            clean = f"tbl_{clean}"
        if not clean:
            clean = "unnamed_table"

        return clean

    def process_run_sheet(
        self,
        excel_file,
        sheet_name: str,
        metadata: FileMetadata,
    ) -> tuple[Optional[pl.DataFrame], Optional[str]]:
        """
        Process a single Run sheet.

        Returns:
            Tuple of (DataFrame or None, warning message or None)
        """
        try:
            cycle_num = int(sheet_name.replace("Run", ""))
        except ValueError as e:
            return None, f"Could not parse cycle number from '{sheet_name}': {e}"

        try:
            df = excel_file.load_sheet_by_name(sheet_name).to_polars()

            # Add metadata columns
            df = df.with_columns(
                [
                    pl.lit(cycle_num).alias("cycle_number"),
                    pl.lit(metadata.source_id).alias("source_file"),
                    pl.lit(metadata.stack_id).alias("stack_id"),
                    pl.lit(metadata.device_id).alias("device_id"),
                    pl.lit(metadata.device_row).alias("device_row"),
                    pl.lit(metadata.device_col).alias("device_col"),
                    pl.lit(metadata.measurement_type).alias("measurement_type"),
                    pl.lit(metadata.file_path).alias("file_path"),
                ]
            )

            df = self.clean_column_names(df)
            df = self.fix_norm_cond(df)

            return df, None

        except Exception as e:
            return None, f"Error processing sheet '{sheet_name}': {e}"

    def process_metadata_sheet(
        self,
        excel_file,
        sheet_name: str,
        source_id: str,
    ) -> tuple[Optional[pl.DataFrame], str, Optional[str]]:
        """
        Process a metadata sheet (Settings, Calc etc.).
        Returns:
            Tuple of (DataFrame(or None),table_name, warning message((or None))
        """
        ### each sheet becomes its own table with a Sanitized name.
        table_name = self.sanitize_table_name(sheet_name)

        try:
            df = excel_file.load_sheet_by_name(sheet_name).to_polars()
            df = self.clean_column_names(df)
            df = self.fix_norm_cond(df)
            df = df.with_columns(pl.lit(source_id).alias("source_file"))

            return df, table_name, None

        except Exception as e:
            return (
                None,
                table_name,
                f"Error processing metadata sheet '{sheet_name}': {e}",
            )
