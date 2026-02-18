from pathlib import Path
from core import Mode


def path_to_glob(path: Path | str, mode: Mode) -> str:
    """
    Convert Windows Paths to Glob Pattern

    :param path: path
    :type path: Path | str
    :return: Path in Glob Pattern
    :rtype: str
    """
    folder = Path(path)

    match mode:
        case Mode.DEVICE:
            glob_pattern = str(folder / "*.xlsx")
        case Mode.STACK:
            glob_pattern = str(folder / "**" / "*.xlsx")
        case _:
            print("This is unexpected.")  # Can never happen

    return glob_pattern
