import pytest


@pytest.fixture
def make_file(tmp_path):
    """Create a temporary file in a stack/device directory structure.

    MetadataExtractor.extract() derives:
      - measurement_type from the filename  (e.g. "01 set.xlsx")
      - device_row / device_col from the device folder (e.g. "F11")
      - stack_id from the stack folder (e.g. "SC2025#4a")
    """

    def _make(filename="01 set.xlsx", device="A1", stack="stack1"):
        directory = tmp_path / stack / device
        directory.mkdir(parents=True, exist_ok=True)
        f = directory / filename
        f.touch()
        return f

    return _make
