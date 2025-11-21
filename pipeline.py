import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def excel_to_parquet():
    path = Path(r"C:\Users\pineapple\Downloads\test.xls")

    xl = pd.ExcelFile(path, engine="xlrd")

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)

        # Convert all object columns to string to avoid PyArrow errors
        for col in df.select_dtypes(['object']):
            df[col] = df[col].astype(str)

        # Save to Parquet
        out_path = path.with_suffix(f".{sheet_name}.parquet")
        df.to_parquet(out_path, engine="pyarrow")
        print("Saved:", out_path)

    df_sheet = pd.read_parquet(Path(r"C:\Users\pineapple\Downloads\test.Cycle19.parquet"))

    plt.figure(figsize=(10, 6))
    plt.plot(df_sheet['Time'], df_sheet['RESISTANCE'], label="Cycle19")
    plt.xlabel('Time')
    plt.ylabel('Resistance')
    plt.title(f'Resistance over Time for Cycle19')
    plt.legend()
    plt.show()


excel_to_parquet()





