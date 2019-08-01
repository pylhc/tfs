import os
import pytest
import tempfile
from numpy.random import rand
from . import context
from tfs import read_tfs, write_tfs, TfsDataFrame


CURRENT_DIR = os.path.dirname(__file__)


def test_tfs_read(_tfs_file):
    test_file = read_tfs(_tfs_file, index="NAME")
    assert len(test_file.headers) > 0
    assert len(test_file.columns) > 0
    assert len(test_file.index) > 0
    assert isinstance(test_file.index[0], str)


def test_tfs_write_read(_dataframe, _test_file):
    write_tfs(_test_file, _dataframe)
    assert os.path.isfile(_test_file)

    new = read_tfs(_test_file)
    assert _dataframe.headers == new.headers
    assert all(_dataframe.columns == new.columns)
    for column in _dataframe:
        assert all(abs(_dataframe.loc[:, column] - new.loc[:, column]) < 1e-10)  # could go to 1E-12


def test_tfs_read_write_read(_tfs_file, _test_file):
    original = read_tfs(_tfs_file)
    write_tfs(_test_file, original)
    new = read_tfs(_test_file)
    assert original.headers == new.headers
    assert all(original.columns == new.columns)
    for column in original:
        assert all(original.loc[:, column] == new.loc[:, column])


@pytest.fixture()
def _tfs_file():
    return os.path.join(CURRENT_DIR, "inputs", "file_x.tfs")


@pytest.fixture()
def _test_file():
    with tempfile.TemporaryDirectory() as cwd:
        yield os.path.join(cwd, "test_file.tfs")


@pytest.fixture()
def _dataframe():
    return TfsDataFrame(
        index=range(3), columns="a b c d e".split(),
        data=rand(3, 5),
        headers={"Title": "Tfs Title", "Value": 3.3663}
    )
