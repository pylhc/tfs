import pathlib
from shutil import copyfile

import pytest

from tfs.errors import AbsentTypeIdentifierError
from tfs.reader import read_tfs
from tfs.tools import remove_header_comments_from_files, remove_nan_from_files, significant_digits

from .conftest import INPUTS_DIR


def test_clean_file_pathlib_input(_bad_file_pathlib: pathlib.Path, tmp_path):
    clean_location = tmp_path / "clean_file.tfs"
    copyfile(_bad_file_pathlib, clean_location)
    with pytest.raises(AbsentTypeIdentifierError):
        _ = read_tfs(_bad_file_pathlib)

    remove_header_comments_from_files([clean_location])
    df = read_tfs(clean_location)
    assert df.isna().any().any()

    remove_nan_from_files([str(clean_location)])
    df = read_tfs(str(clean_location) + ".dropna")
    assert len(df) > 0
    assert not df.isna().any().any()


def test_clean_file_str_input(_bad_file_str: str, tmp_path):
    clean_location = tmp_path / "clean_file.tfs"
    copyfile(_bad_file_str, clean_location)
    with pytest.raises(AbsentTypeIdentifierError):
        read_tfs(_bad_file_str)

    remove_header_comments_from_files([clean_location])
    df = read_tfs(clean_location)
    assert df.isna().any().any()

    remove_nan_from_files([str(clean_location)])
    df = read_tfs(str(clean_location) + ".dropna")
    assert len(df) > 0
    assert not df.isna().any().any()


def test_remove_nan_raises(caplog):
    remove_nan_from_files(["no_a_file.tfs"])
    for record in caplog.records:
        assert record.levelname == "WARNING"
    assert "could not be loaded" in caplog.text


def test_significant_digits():
    s = significant_digits(0.637282, 1e-3)
    assert s[0] == "0.6373"

    s = significant_digits(0.9837473385, 0.000065323)
    assert s[0] == "0.98375"
    assert s[1] == "0.00007"

    s = significant_digits(0.0338577, 0.0015473)
    assert s[0] == "0.0339"
    assert s[1] == "0.0015"

    s = significant_digits(0.0338577, 0.0015473, return_floats=True)
    assert s[0] == 0.0339
    assert s[1] == 0.0015

    with pytest.raises(ValueError, match="Input error of 0."):
        s = significant_digits(0.0338577, 0.0)


# ----- Helpers & Fixtures ----- #


@pytest.fixture
def _bad_file_pathlib() -> pathlib.Path:
    return INPUTS_DIR / "bad_file.tfs"


@pytest.fixture
def _bad_file_str(_bad_file_pathlib) -> str:
    return str(_bad_file_pathlib.absolute())
