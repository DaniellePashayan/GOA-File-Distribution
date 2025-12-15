
import pytest

from functions import _ensure_list_destination, move_single_file


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


if __name__ == "__main__":
    pytest.main(["-q"])