from pathlib import Path
import polars as pl
from .duckdb_file_processor import DuckDBFileProcessor


class FormatConverter:
    """ways to convert --parquet or --duck db files to .csv .txt or excel"""

    def convert(self, input_path, output_path):

        print(">>> FormatConverter is running <<<")

        input_path = Path(input_path)
        output_path = Path(output_path)

        suffix = input_path.suffix.lower()

        # -------- parquet --------
        if suffix == ".parquet":
            data_frame = pl.read_parquet(input_path)
            self._write(data_frame, output_path)

        # -------- duckdb --------
        elif suffix == ".duckdb":
            processor = DuckDBFileProcessor(str(input_path))
            result = processor.process(str(input_path))

            if result.cycles_df is None:
                raise ValueError("No data in DuckDB file")

            self._write(result.cycles_df, output_path)

        else:
            raise ValueError(
                f"Unsupported file format '{suffix}'. Expected '.parquet' or '.duckdb'."
            )

        return output_path

    def _write(self, data_frame, output_path):

        suffix = output_path.suffix.lower()

        if suffix == ".csv":
            data_frame.write_csv(output_path)

        elif suffix == ".txt":
            data_frame.write_csv(output_path, separator="\t")

        elif suffix == ".xlsx":
            data_frame.write_excel(output_path)

        else:
            raise ValueError(
                f"Unsupported output format '{suffix}'. "
                "Supported formats are: .csv, .txt, .xlsx"
            )
