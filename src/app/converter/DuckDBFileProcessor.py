import duckdb
import polars as pl
from pathlib import Path
from .models import ProcessingResult
import time

class DuckDBFileProcessor:

    def process(self, file_path):

        file_id = Path(file_path).stem

        result = ProcessingResult(file_id = file_id)

        start = time.time()

        try:
            connection = duckdb.connect(str(file_path))
            tables = connection.execute("show tables").fetchall()

            if tables:
                table_name = tables[0][0]
                data_frame = connection.execute(f"SELECT * FROM {table_name}").pl()
                result.cycles_df = data_frame

            connection.close()

        except Exception as e:
            result.warnings.append(str(e))

        end = time.time()

        result.elapsed = end - start

        return result

