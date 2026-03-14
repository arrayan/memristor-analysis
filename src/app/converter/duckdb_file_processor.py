import duckdb
from pathlib import Path
from app.converter.models import ProcessingResult


class DuckDBFileProcessor:
    def __init__(self, output_path):
        self.output_path = output_path

    def process(self, file_path):

        file_id = Path(file_path).stem
        result = ProcessingResult(file_id=file_id)

        try:
            connection = duckdb.connect(file_path)

            df = connection.execute("SELECT * FROM cycles").pl()

            result.cycles_df = df
            connection.close()

        except Exception as e:
            result.warnings.append(str(e))

        return result
