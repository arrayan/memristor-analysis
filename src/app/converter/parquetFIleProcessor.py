import polars as pl
from pathlib import Path
from .models import ProcessingResult
import time


class ParquetFileProcessor:
    def process(self, file_path):

        file_id = Path(file_path).stem

        result = ProcessingResult(file_id=file_id)

        start = time.time()

        try:
            data_frame = pl.read_parquet(file_path)
            result.cycles_df = data_frame

        except Exception as e:
            result.warnings.append(str(e))

        end = time.time()

        result.elapsed = end - start

        return result
