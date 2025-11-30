import pandas as pd
from pathlib import Path


class DataHandler:
    """
    Centralized helper class for loading, validating,
    and preprocessing data files used in the Memristor Analysis Tool.
    """

    @staticmethod
    def load_excel(file_path: str) -> pd.DataFrame:
        """
        Load a .xlsx file into a pandas DataFrame.

        Parameters
        ----------
        file_path : str
            Path to the Excel file.

        Returns
        -------
        pd.DataFrame
            The loaded data.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.

        ValueError
            If the file cannot be read.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = pd.read_excel(path)
            return df

        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

    @staticmethod
    def load_multiple(files: list[str]) -> list[pd.DataFrame]:
        """
        Load several Excel files and return a list of DataFrames.

        Parameters
        ----------
        files : list[str]
            List of .xlsx file paths.

        Returns
        -------
        list[pd.DataFrame]
        """
        datasets = []
        for fp in files:
            datasets.append(DataHandler.load_excel(fp))
        return datasets

    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns=None) -> bool:
        """
        Optional: Validate structure of the memristor dataset.

        Example: required_columns = ["Voltage", "Current", "Time"]

        Returns True if valid, False otherwise.
        """
        if required_columns is None:
            return True  # nothing to validate yet

        for col in required_columns:
            if col not in df.columns:
                return False
        return True
