from pathlib import Path

from app.converter.convert_path_to_glob import path_to_glob
from app.core import Mode


# Testing if the import is limited only on .xlsx files
def test_device_import_uses_xlsx_only():
    pattern = path_to_glob(Path("/data"), Mode.DEVICE)
    assert pattern == "/data/*.xlsx"


def test_stack_import_uses_recursive_xlsx_only():
    pattern = path_to_glob(Path("/data"), Mode.STACK)
    assert pattern == "/data/**/*.xlsx"
