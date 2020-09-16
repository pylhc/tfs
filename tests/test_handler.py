import os
import pathlib
import tempfile

import numpy
import pytest
from pandas import DataFrame
from pandas.util.testing import assert_dict_equal, assert_frame_equal, assert_index_equal

from tfs import TfsDataFrame, read_tfs, write_tfs
from tfs.handler import TfsFormatError

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
    assert_dict_equal(_dataframe.headers, new.headers, compare_keys=True)


def test_tfs_write_read_pandasdf(_pddataframe: DataFrame, _test_file: str):
    write_tfs(_test_file, _pddataframe)
    assert pathlib.Path(_test_file).is_file()

    new = read_tfs(_test_file)
    assert_frame_equal(
        _pddataframe,
        new,
        check_exact=False,  # float precision can be an issue
        check_frame_type=False,  # read df is TfsDF
    )


def test_write_read_spaces_in_strings(_test_file: str):
    df = TfsDataFrame(data=["This is", "a test", "with spaces"], columns=["A"])
    write_tfs(_test_file, df)
    new = read_tfs(_test_file)
    assert_frame_equal(df, new)


def test_tfs_write_read_autoindex(_dataframe: TfsDataFrame, _test_file: str):
    df = _dataframe.set_index("a")
    df1 = _dataframe.set_index("a")
    write_tfs(_test_file, df, save_index=True)
    assert_frame_equal(df, df1)

    df_read = read_tfs(_test_file)
    assert_index_equal(df.index, df_read.index, check_exact=False)
    assert_dict_equal(_dataframe.headers, df_read.headers, compare_keys=True)


def test_tfs_read_write_read_pathlib_input(_tfs_file_pathlib: pathlib.Path, _test_file: str):
    original = read_tfs(_tfs_file_pathlib)
    write_tfs(_test_file, original)
    new = read_tfs(_test_file)
    assert_frame_equal(original, new)
    assert_dict_equal(original.headers, new.headers, compare_keys=True)


def test_tfs_read_write_read_str_input(_tfs_file_str: str, _test_file: str):
    original = read_tfs(_tfs_file_str)
    write_tfs(_test_file, original)
    new = read_tfs(_test_file)
    assert_frame_equal(original, new)
    assert_dict_equal(original.headers, new.headers, compare_keys=True)


def test_tfs_write_empty_columns_dataframe(_test_file: str):
    df = TfsDataFrame(
        index=range(3),
        columns=[],
        data=numpy.random.rand(3, 0),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )

    write_tfs(_test_file, df, save_index=True)
    assert pathlib.Path(_test_file).is_file()

    new = read_tfs(_test_file)
    assert_frame_equal(df, new)
    assert_dict_equal(df.headers, new.headers, compare_keys=True)


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
    assert_frame_equal(df, new)
    assert_dict_equal(df.headers, new.headers, compare_keys=True)


def test_header_print():
    headers = {"param": 3, "other": "hello"}
    df = TfsDataFrame(headers=headers)
    print_out = str(df)
    assert "Headers" in print_out

    for key, val in headers.items():
        assert key in print_out
        assert str(val) in print_out


def test_fail_on_non_unique_columns():
    df = TfsDataFrame(columns=["A", "B", "A"])
    with pytest.raises(TfsFormatError):
        write_tfs("", df)


def test_fail_on_non_unique_index():
    df = TfsDataFrame(index=["A", "B", "A"])
    with pytest.raises(TfsFormatError):
        write_tfs("", df)


def test_fail_on_spaces_columns():
    df = TfsDataFrame(columns=["allowed", "not allowed"])
    with pytest.raises(TfsFormatError):
        write_tfs("", df)


def test_fail_on_spaces_headers():
    df = TfsDataFrame(headers={"allowed": 1, "not allowed": 2})
    with pytest.raises(TfsFormatError):
        write_tfs("", df)


@pytest.fixture()
def _tfs_file_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_X.tfs"


@pytest.fixture()
def _tfs_file_str() -> str:
    return os.path.join(os.path.dirname(__file__), "inputs", "file_X.tfs")


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


@pytest.fixture()
def _pddataframe() -> DataFrame:
    return DataFrame(index=range(3), columns="a b c d e".split(), data=numpy.random.rand(3, 5),)
