import pytest
from converter.metadata import MetadataExtractor

ext = MetadataExtractor()


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("01 set.xlsx", "set"),
        ("02 reset.xlsx", "reset"),
        ("03 leakage.xlsx", "leakage"),
        ("04 electroforming.xlsx", "electroforming"),
        ("05 endurance reset.xlsx", "endurance_reset"),
        ("06 endurance set.xlsx", "endurance_set"),
        ("07 endurance ratio.xlsx", "endurance_ratio"),
    ],
)
def test_all_known_measurement_types(make_file, filename, expected):
    f = make_file(filename=filename)
    assert ext.extract(f).measurement_type == expected


def test_unknown_type_gets_underscored(make_file):
    f = make_file(filename="99 custom sweep.xlsx")
    assert (
        ext.extract(f).measurement_type == "custom_sweep"
    )  # extraction makes no difference since it wont be assigned to any of the values in type map


def test_bad_filename_gives_no_type(make_file):
    f = make_file(filename="random_name.xlsx")
    assert ext.extract(f).measurement_type is None


def test_device_row_col_from_folder(make_file):
    f = make_file(device="F11")
    m = ext.extract(f)
    assert m.device_row == "F"
    assert m.device_col == 11


def test_lowercase_device_folder_uppercased(make_file):
    f = make_file(device="z5")
    assert ext.extract(f).device_row == "Z"


def test_non_standard_folder_gives_no_row_col(make_file):
    f = make_file(device="some_folder")
    m = ext.extract(f)
    assert m.device_row is None
    assert m.device_col is None


def test_stack_and_device_ids(make_file):
    f = make_file(stack="SC2025#4a", device="G7")
    m = ext.extract(f)
    assert m.stack_id == "SC2025#4a"
    assert m.device_id == "SC2025#4a_G7"


def test_case_insensitive_extension(make_file):
    f = make_file(filename="02 Reset.XLSX")
    assert ext.extract(f).measurement_type == "reset"  # map to one of type map values!


def test_filename_pattern_rejects_edge_cases():
    pat = MetadataExtractor.FILENAME_PATTERN
    assert pat.match("~$02 reset.xlsx") is None  # temp files
    assert pat.match("reset.xlsx") is None
    assert pat.match("2 reset.xlsx") is None
