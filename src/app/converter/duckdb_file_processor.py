import duckdb
from pathlib import Path
from app.converter.models import ProcessingResult
import polars as pl

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


if __name__ == "__main__":
    # 临时测试代码
    test_db = "../../../memristor_data.duckdb"
    print(f"--- 正在测试: {test_db} ---")

    # 检查文件是否存在
    import os

    if not os.path.exists(test_db):
        print(f"❌ 错误：在当前目录下没找到 {test_db}")
    else:
        processor = DuckDBFileProcessor("test_out.csv")
        result = processor.process(test_db)

        if result.cycles_df is not None:
            print(f"✅ 成功！抓取到 {len(result.cycles_df)} 行数据")
            print(f"表格列名: {result.cycles_df.columns}")
        else:
            print("❌ 失败：cycles_df 为 None")
            print(f"⚠️ 报错信息: {result.warnings}")