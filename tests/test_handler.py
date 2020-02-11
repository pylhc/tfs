import os
import pathlib
import tempfile

import numpy
import pytest
from pandas.testing import assert_frame_equal

from tfs import read_tfs, write_tfs, TfsDataFrame
from .helper import compare_float_dataframes

CURRENT_DIR = pathlib.Path(__file__).parent


def test_tfs_read_pathlib_input(_tfs_file_pathlib: pathlib.Path):
    test_file = read_tfs(_tfs_file_pathlib, index="NAME")
    assert len(test_file.headers) > 0
    assert len(test_file.columns) > 0
    assert len(test_file.index) > 0
    assert len(str(test_file)) > 0
    assert isinstance(test_file.index[0], str)

    with pytest.raises(AttributeError):
        test_var = test_file.Not_HERE

    with pytest.raises(KeyError):
        test_var = test_file["Not_HERE"]


def test_tfs_read_str_input(_tfs_file_str: str):
    test_file = read_tfs(_tfs_file_str, index="NAME")
    assert len(test_file.headers) > 0
    assert len(test_file.columns) > 0
    assert len(test_file.index) > 0
    assert len(str(test_file)) > 0
    assert isinstance(test_file.index[0], str)

    with pytest.raises(AttributeError):
        test_var = test_file.Not_HERE

    with pytest.raises(KeyError):
        test_var = test_file["Not_HERE"]


def tfs_indx_pathlib_input(_tfs_file_pathlib: pathlib.Path):
    test_file = read_tfs(_tfs_file_pathlib)
    assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]


def tfs_indx_str_input(_tfs_file_str: str):
    test_file = read_tfs(_tfs_file_str)
    assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]


def test_tfs_write_read(_dataframe: TfsDataFrame, _test_file: str):
    write_tfs(_test_file, _dataframe)
    assert pathlib.Path(_test_file).is_file()

    new = read_tfs(_test_file)
    assert_frame_equal(_dataframe, new, check_exact=False)  # float precision can be an issue


def test_tfs_write_read_autoindex(_dataframe: TfsDataFrame, _test_file: str):
    df = _dataframe.set_index("a")
    df1 = _dataframe.set_index("a")
    write_tfs(_test_file, df, save_index=True)
    assert_frame_equal(df, df1)

    df_read = read_tfs(_test_file)
    assert df_read.index.name == df.index.name
    assert all((df_read.index.values - df.index.values) <= 1e-12)


def test_tfs_read_write_read_pathlib_input(_tfs_file_pathlib: pathlib.Path, _test_file: str):
    original = read_tfs(_tfs_file_pathlib)
    write_tfs(_test_file, original)
    new = read_tfs(_test_file)
    assert original.headers == new.headers
    assert numpy.array_equal(original.columns, new.columns)
    for column in original:
        assert numpy.array_equal(original.loc[:, column].values, new.loc[:, column].values)


def test_tfs_read_write_read_str_input(_tfs_file_str: str, _test_file: str):
    original = read_tfs(_tfs_file_str)
    write_tfs(_test_file, original)
    new = read_tfs(_test_file)
    assert original.headers == new.headers
    assert numpy.array_equal(original.columns, new.columns)
    for column in original:
        assert numpy.array_equal(original.loc[:, column].values, new.loc[:, column].values)


def test_tfs_write_empty_columns_dataframe(_test_file: str):
    df = TfsDataFrame(
        index=range(3),
        columns=[],
        data=numpy.random.rand(3, 0),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )

    write_tfs(_test_file, df)
    assert pathlib.Path(_test_file).is_file()

    new = read_tfs(_test_file)
    compare_float_dataframes(df, new)


def test_tfs_write_empty_index_dataframe(_test_file: str):
    df = TfsDataFrame(
        index=[],
        columns=["a", "b", "c"],
        data=numpy.random.rand(0, 3),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )

    write_tfs(_test_file, df)
    assert pathlib.Path(_test_file).is_file()

    new = read_tfs(_test_file)
    compare_float_dataframes(df, new)


@pytest.fixture()
def _tfs_file_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"


@pytest.fixture()
def _tfs_file_str() -> str:
    return os.path.join(os.path.dirname(__file__), "inputs", "file_x.tfs")


@pytest.fixture()
def _test_file() -> str:
    with tempfile.TemporaryDirectory() as cwd:
        yield os.path.join(cwd, "test_file.tfs")


@pytest.fixture()
def _dataframe() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(3),
        columns="a b c d e".split(),
        data=numpy.random.rand(3, 5),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )
