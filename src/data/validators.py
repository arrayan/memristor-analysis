from pathlib import Path


def is_valid_excel(file_path: str) -> bool:
    """
    Return True only if the file exists AND has .xlsx extension.
    """
    if not file_path:
        return False

    path = Path(file_path)

    # File must exist
    if not path.exists():
        return False

    # Must end with .xlsx
    return path.suffix.lower() == ".xlsx"
