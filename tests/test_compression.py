"""
Here we only test that reading and writing with compression keeps the data intact.
"""
import pathlib
import sys

import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

from tfs import read_tfs, write_tfs

CURRENT_DIR = pathlib.Path(__file__).parent


# TODO: remove the skipif once Python 3.7 is EoL and we drop support for it
@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Not run on Python 3.7 for format protocol incompatibility reasons",
)
@pytest.mark.parametrize("extension", ["gz", "bz2", "zip", "xz", "zst", "tar", "tar.gz"])
def test_read_compressed_is_same_data(_tfs_filex, _tfs_compressed_filex_no_suffix, extension):
    """Compare the data from a compressed file with the original one."""
    ref_df = read_tfs(_tfs_filex, index="NAME")

    # Now read the compressed version, for a given extension in the parametrize
    compressed_file = _path_with_added_extension(_tfs_compressed_filex_no_suffix, extension)
    test_df = read_tfs(compressed_file, index="NAME")

    # Confirm the data is the same
    assert_dict_equal(ref_df.headers, test_df.headers)
    assert_frame_equal(ref_df, test_df)


# TODO: remove the skipif once Python 3.7 is EoL and we drop support for it
@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Not run on Python 3.7 for format protocol incompatibility reasons",
)
@pytest.mark.parametrize("extension", ["gz", "bz2", "zip", "xz", "zst", "tar", "tar.gz"])
def test_write_read_compressed(_tfs_filey, tmp_path, extension):
    """Ensure that writing in compressed format preserves data."""
    ref_df = read_tfs(_tfs_filey, index="NAME")

    # Now we write it in compressed form and check it's doing fine
    compressed_path = tmp_path.with_suffix(f".{extension}")
    write_tfs(compressed_path, ref_df, save_index="NAME")
    assert compressed_path.exists()
    assert compressed_path.stat().st_size > 0
    assert compressed_path.stat().st_size != _tfs_filey.stat().st_size
    assert str(compressed_path).endswith(f".{extension}")

    # Now we read it back and compare to initial data
    test_df = read_tfs(compressed_path, index="NAME")
    assert_dict_equal(ref_df.headers, test_df.headers)
    assert_frame_equal(ref_df, test_df)


# ----- Helpers ------ #


def _path_with_added_extension(path: pathlib.Path, extension: str) -> pathlib.Path:
    """Adds an extension on top of the existing one for a pathlib.Path object."""
    return path.with_suffix(path.suffix + f".{extension}")


# ------ Fixtures ------ #


@pytest.fixture()
def _tfs_filex() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"


@pytest.fixture()
def _tfs_filey() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_y.tfs"


@pytest.fixture()
def _tfs_compressed_filex_no_suffix() -> pathlib.Path:
    """Add the wanted compression suffix to this."""
    return CURRENT_DIR / "inputs" / "compressed" / "file_x.tfs"


@pytest.fixture()
def _tfs_compressed_filey_no_suffix() -> pathlib.Path:
    """Add the wanted compression suffix to this."""
    return CURRENT_DIR / "inputs" / "compressed" / "file_y.tfs"
