import os
import tempfile

import pytest
from numpy.random import rand

from .helper import compare_dataframes, compare_float_dataframes
from tfs import read_tfs, write_tfs, TfsDataFrame

CURRENT_DIR = os.path.dirname(__file__)


def test_tfs_read(_tfs_file):
    test_file = read_tfs(_tfs_file, index="NAME")
    assert len(test_file.headers) > 0
    assert len(test_file.columns) > 0
    assert len(test_file.index) > 0
    assert len(str(test_file)) > 0
    assert isinstance(test_file.index[0], str)

    with pytest.raises(AttributeError):
        test_file.Not_HERE

    with pytest.raises(KeyError):
        test_file["Not_HERE"]


def tfs_indx(_tfs_file):
    test_file = read_tfs(_tfs_file)
    assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]


def test_tfs_write_read(_dataframe, _test_file):
    write_tfs(_test_file, _dataframe)
    assert os.path.isfile(_test_file)

    new = read_tfs(_test_file)
    compare_float_dataframes(_dataframe, new)


def test_tfs_write_read_autoindex(_dataframe, _test_file):
    df = _dataframe.set_index("a")
    df1 = _dataframe.set_index("a")
    write_tfs(_test_file, df, save_index=True)
    compare_dataframes(df, df1)  # writing should not change things

    df_read = read_tfs(_test_file)
    assert df_read.index.name == df.index.name
    assert all((df_read.index.values - df.index.values) <= 1E-12)


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
