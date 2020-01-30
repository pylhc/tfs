import os
import pathlib
import tempfile
from shutil import copyfile

import pytest

from tfs.handler import read_tfs, TfsFormatError
from tfs.tools import remove_header_comments_from_files, remove_nan_from_files, significant_digits

CURRENT_DIR = pathlib.Path(__file__).parent


def test_clean_file(_bad_file: pathlib.Path, _clean_file: str):
    copyfile(_bad_file, _clean_file)
    with pytest.raises(TfsFormatError):
        read_tfs(_bad_file)

    remove_header_comments_from_files([_clean_file])
    df = read_tfs(_clean_file)
    assert df.isna().any().any()

    remove_nan_from_files([_clean_file])
    df = read_tfs(_clean_file + ".dropna")
    assert len(df) > 0
    assert not df.isna().any().any()


def test_significant_digits():
    s = significant_digits(0.637282, 1e-3)
    assert s[0] == "0.6373"

    s = significant_digits(0.9837473385, 0.000065323)
    assert s[0] == "0.98375"
    assert s[1] == "0.00007"

    s = significant_digits(0.0338577, 0.0015473)
    assert s[0] == "0.0339"
    assert s[1] == "0.0015"


@pytest.fixture()
def _bad_file() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "bad_file.tfs"


@pytest.fixture()
def _clean_file() -> str:
    with tempfile.TemporaryDirectory() as cwd:
        yield os.path.join(cwd, "clean_file.tfs")
