from pathlib import Path
import polars as pl
import duckdb


class FormatConverter:
    """ways to convert --parquet or --duck db files to .csv .txt or excel"""

    def convert(self, input_path, output_path):

        input_path = Path(input_path)
        output_path = Path(output_path)

        suffix = input_path.suffix.lower()

        # -------- parquet --------
        if suffix == ".parquet":
            data_frame = pl.read_parquet(input_path)
            self._write(data_frame, output_path)

        # -------- duckdb --------
        elif suffix == ".duckdb":
            connection = duckdb.connect(str(input_path))
            tables = connection.execute("show tables").fetchall()

            data = {}

            for table in tables:
                table_name = table[0]
                data_frame = connection.execute(f"SELECT * FROM {table_name}").pl()
                data[table_name] = data_frame

            connection.close()

            if not data:
                raise ValueError("No tables in DuckDB file")

            first_data_frame = list(data.values())[0]
            self._write(first_data_frame, output_path)

        else:
            raise ValueError("false format")

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
            raise ValueError("false format")
