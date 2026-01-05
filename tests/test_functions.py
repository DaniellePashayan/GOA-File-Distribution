
import pytest

from functions import _ensure_list_destination, move_single_file, _apply_filename_transform


def test_ensure_list_destination_with_string():
    assert _ensure_list_destination('a') == ['a']


def test_ensure_list_destination_with_list():
    assert _ensure_list_destination(['a', 'b']) == ['a', 'b']


def test_move_single_file_with_secondary_copy(tmp_path):
    # create a temporary source file
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "example.txt"
    src_file.write_text("hello")

    # primary and secondary destinations
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"

    # Ensure they don't exist yet
    assert not primary.exists()
    assert not secondary.exists()

    # run move_single_file with a list destination
    move_single_file(str(src_file), [str(primary), str(secondary)])

    # after run: primary should contain the moved file, source should not exist
    assert not src_file.exists()
    assert (primary / "example.txt").exists()

    # secondary should have a copy
    assert (secondary / "example.txt").exists()


def test_apply_filename_transform_date_offset():
    # Test date offset: add 1 day to filename date
    transform = {
        "date_offset_days": 1,
        "date_format": "YYYYMMDD",
        "date_format_dt": "%Y%m%d"
    }
    result = _apply_filename_transform("BundlingImport20250105.txt", transform)
    assert result == "BundlingImport20250106.txt"

    # Test negative offset: subtract 1 day
    transform_negative = {
        "date_offset_days": -1,
        "date_format": "YYYYMMDD",
        "date_format_dt": "%Y%m%d"
    }
    result = _apply_filename_transform("BundlingImport20250105.txt", transform_negative)
    assert result == "BundlingImport20250104.txt"


def test_move_single_file_with_date_offset(tmp_path):
    # Create a file with a date in the name
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "BundlingImport20250105.txt"
    src_file.write_text("test data")

    primary = tmp_path / "primary"
    secondary = tmp_path / "archive"

    # Define transforms: primary gets +1 day, archive gets no transform (original)
    transforms = [
        {"date_offset_days": 1, "date_format": "YYYYMMDD", "date_format_dt": "%Y%m%d"},
        None  # No transform for archive
    ]

    move_single_file(str(src_file), [str(primary), str(secondary)], transforms)

    # Primary should have the offset filename
    assert (primary / "BundlingImport20250106.txt").exists()
    # Archive should have the original filename
    assert (secondary / "BundlingImport20250105.txt").exists()
    # Source should not exist
    assert not src_file.exists()


if __name__ == "__main__":
    pytest.main(["-q"])
