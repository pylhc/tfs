"""
Here we only test that reading and writing with compression keeps the data intact.
"""

import pathlib

import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

from tfs.reader import read_headers, read_tfs
from tfs.writer import write_tfs

from .conftest import INPUTS_DIR


# ----- Compression tests with 'classic' TFS files (no MAD-NG features) ----- #


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


@pytest.mark.parametrize("extension", ["gz", "bz2", "zip", "xz", "zst", "tar", "tar.gz"])
def test_read_headers_compressed(_tfs_compressed_filex_no_suffix, extension):
    compressed_file = _path_with_added_extension(_tfs_compressed_filex_no_suffix, extension)
    headers = read_headers(compressed_file)
    assert isinstance(headers, dict)
    assert len(headers) > 0
    assert len(str(headers)) > 0
    assert all(key in headers for key in ["TITLE", "DPP", "Q1", "Q1RMS", "NATQ1", "NATQ1RMS", "BPMCOUNT"])


# ----- Compression tests with TFS files including MAD-NG features ----- #


@pytest.mark.parametrize("extension", ["gz", "bz2", "zip", "xz", "zst", "tar", "tar.gz"])
def test_read_madng_compressed_is_same_data(_tfs_madng_file, _tfs_compressed_madng_no_suffix, extension):
    """Compare the data from a compressed file with the original one."""
    ref_df = read_tfs(_tfs_madng_file, index="NAME")

    # Now read the compressed version, for a given extension in the parametrize
    compressed_file = _path_with_added_extension(_tfs_compressed_madng_no_suffix, extension)
    test_df = read_tfs(compressed_file, index="NAME")

    # Confirm the data is the same
    assert_dict_equal(ref_df.headers, test_df.headers)
    assert_frame_equal(ref_df, test_df)


@pytest.mark.parametrize("extension", ["gz", "bz2", "zip", "xz", "zst", "tar", "tar.gz"])
def test_write_read_madng_compressed(_tfs_madng_file, tmp_path, extension):
    """Ensure that writing in compressed format preserves data."""
    ref_df = read_tfs(_tfs_madng_file, index="NAME")

    # Now we write it in compressed form and check it's doing fine
    compressed_path = tmp_path.with_suffix(f".{extension}")
    write_tfs(compressed_path, ref_df, save_index="NAME", validate="madng")
    assert compressed_path.exists()
    assert compressed_path.stat().st_size > 0
    assert compressed_path.stat().st_size != _tfs_madng_file.stat().st_size
    assert str(compressed_path).endswith(f".{extension}")

    # Now we read it back and compare to initial data
    test_df = read_tfs(compressed_path, index="NAME")
    assert_dict_equal(ref_df.headers, test_df.headers)
    assert_frame_equal(ref_df, test_df)


@pytest.mark.parametrize("extension", ["gz", "bz2", "zip", "xz", "zst", "tar", "tar.gz"])
def test_read_headers_madng_compressed(_tfs_compressed_madng_no_suffix, extension):
    compressed_file = _path_with_added_extension(_tfs_compressed_madng_no_suffix, extension)
    headers = read_headers(compressed_file)
    assert isinstance(headers, dict)
    assert len(headers) > 0
    assert len(str(headers)) > 0
    assert all(
        key in headers
        for key in [
            "TITLE",
            "DPP",
            "Q1",
            "Q1RMS",
            "NATQ1",
            "NATQ1RMS",
            "BPMCOUNT",
            "BOOLEAN1",
            "BOOLEAN2",
            "COMPLEX",
        ]
    )


# ----- Helpers & Fixtures ------ #


def _path_with_added_extension(path: pathlib.Path, extension: str) -> pathlib.Path:
    """Adds an extension on top of the existing one for a pathlib.Path object."""
    return path.with_suffix(path.suffix + f".{extension}")


@pytest.fixture
def _tfs_compressed_filex_no_suffix() -> pathlib.Path:
    """Add the wanted compression suffix to this."""
    return INPUTS_DIR / "compressed" / "file_x.tfs"


@pytest.fixture
def _tfs_compressed_madng_no_suffix() -> pathlib.Path:
    """Add the wanted compression suffix to this."""
    return INPUTS_DIR / "compressed" / "madng.tfs"
