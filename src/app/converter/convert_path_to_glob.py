from pathlib import Path

def path_to_glob(path: Path | str) -> str:
    """
    Convert Windows Paths to Glob Pattern
    
    :param path: path
    :type path: Path | str
    :return: Path in Glob Pattern
    :rtype: str
    """
    folder = Path(path)
    glob_pattern = str(folder / "**" / "*.xlsx")

    return glob_pattern