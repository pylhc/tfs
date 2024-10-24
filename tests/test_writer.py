import logging
import random
import string

import numpy as np
import pandas as pd
import pytest
from cpymad.madx import Madx
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal, assert_series_equal

import tfs
from tfs import TfsDataFrame, read_tfs, write_tfs
from tfs.errors import (
    DuplicateColumnsError,
    DuplicateIndicesError,
    IterableInDataFrameError,
    NonStringColumnNameError,
    SpaceinColumnNameError,
)

from .conftest import assert_tfs_frame_equal


class TestWrites:
    def test_tfs_write_empty_columns_dataframe(self, tmp_path):
        df = TfsDataFrame(
            index=range(3),
            columns=[],
            data=np.random.rand(3, 0),
            headers={"Title": "Tfs Title", "Value": 3.3663},
        )

        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df, save_index=True)
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_tfs_frame_equal(df, new)

    def test_tfs_write_series_like_dataframe(self, tmp_path):
        """Write-read a pandas.Series-like to disk and make sure all goes right."""
        df = pd.Series([1, 2, 3, 4, 5])
        write_location = tmp_path / "test.tfs"
        test_headers = {"test": 1, "test_string": "test_write_series_like"}
        write_tfs(write_location, df, headers_dict=test_headers, save_index=True)
        assert write_location.is_file()

        # Read data will be TfsDataFrame, so in pd.DataFrame-like form
        # For the comparison we only compare the column (as Series-like) and accept that the
        # user sees a little difference in the data format (Series vs DataFrame with 1 column)
        new = read_tfs(write_location)
        assert_series_equal(df, new["0"], check_names=False)
        assert_dict_equal(test_headers, new.headers, compare_keys=True)

    def test_madx_reads_written_tfsdataframes(self, _bigger_tfs_dataframe, tmp_path):
        dframe = _bigger_tfs_dataframe
        dframe.headers["TYPE"] = "TWISS"  # MAD-X complains on TFS files with no "TYPE" header
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, dframe)  # this will write an eol at eof

        # The written TFS file should be accepted by MAD-X
        with Madx() as madx:
            madx.command.readtable(file=str(write_location), table="test_table")
            assert madx.table.test_table is not None  # check table has loaded

            # Check validity of the loaded table, here we use pandas.Series and assert_series_equal instead
            # of numpy.array_equal to allow for (very) small relative numerical differences on loading
            for column in dframe.columns:
                assert column in madx.table.test_table
                assert_series_equal(pd.Series(madx.table.test_table[column]), dframe[column], check_names=False)

    def test_tfs_write_empty_index_dataframe(self, tmp_path):
        df = TfsDataFrame(
            index=[],
            columns=["a", "b", "c"],
            data=np.random.rand(0, 3),
            headers={"Title": "Tfs Title", "Value": 3.3663},
        )

        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df)
        assert write_location.is_file()

        new = read_tfs(write_location)
        # with pandas 2.0 the index of new is empty but of type integer, which is fine
        assert_tfs_frame_equal(df, new, check_index_type=False)

    def test_write_int_float_str_columns(self, tmp_path):
        """This test is more of an extension of the test below
        (this dataframe was not affected by the bug)"""
        df = TfsDataFrame(
            data=[[1, 1.0, "one"], [2, 2.0, "two"], [3, 3.0, "three"]],
            columns=["Int", "Float", "String"],
        )
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df)
        new = read_tfs(write_location)
        assert_tfs_frame_equal(df, new)

    def test_write_int_float_columns(self, tmp_path):
        """This test is here because of numeric conversion bug
        upon writing back in v2.0.1"""
        df = TfsDataFrame(data=[[1, 1.0], [2, 2.0], [3, 3.0]], columns=["Int", "Float"])
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df)
        new = read_tfs(write_location)
        assert_tfs_frame_equal(df, new)

    def test_tfs_write_read_with_validation(self, _tfs_dataframe, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _tfs_dataframe)
        assert write_location.is_file()

        new = read_tfs(write_location, validate="madx")
        assert_tfs_frame_equal(_tfs_dataframe, new, check_exact=False)  # float precision can be an issue

    def test_tfs_write_read_no_validation(self, _tfs_dataframe, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _tfs_dataframe, validate=None)
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_tfs_frame_equal(_tfs_dataframe, new, check_exact=False)  # float precision can be an issue

    def test_tfs_write_read_no_headers(self, _dataframe_empty_headers: TfsDataFrame, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _dataframe_empty_headers)
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_tfs_frame_equal(_dataframe_empty_headers, new, check_exact=False)  # float precision can be an issue

    def test_tfs_write_read_pandasdf(self, _pd_dataframe, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _pd_dataframe, validate=None)  # validation would complain 'no headers'
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_frame_equal(  # no headers in this df
            _pd_dataframe,
            new,
            check_exact=False,  # float precision can be an issue
            check_frame_type=False,  # read df is TfsDF
        )

    def test_tfs_write_read_spaces_in_strings(self, tmp_path):
        df = TfsDataFrame(data=["This is", "a test", "with spaces"], columns=["A"])
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df)
        new = read_tfs(write_location)
        assert_tfs_frame_equal(df, new)

    def test_tfs_write_read_autoindex(self, _tfs_dataframe, tmp_path):
        df = _tfs_dataframe.set_index("a")
        df1 = _tfs_dataframe.set_index("a")
        assert_tfs_frame_equal(df, df1)

        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df, save_index=True)
        df_read = read_tfs(write_location)
        assert_tfs_frame_equal(df, df_read)  # checks (auto-)index and headers

    def test_no_warning_on_non_unique_columns_if_no_validate(self, tmp_path, caplog):
        df = TfsDataFrame(columns=["A", "B", "A"])
        write_tfs(tmp_path / "temporary.tfs", df, validate=None)
        assert (tmp_path / "temporary.tfs").is_file()
        assert "Non-unique column names found" not in caplog.text

    def test_tfs_write_no_headers_dataframe(self, tmp_path, _pd_dataframe):
        # We make sure providing a df without headers (a pd.DataFrame for
        # instance) still writes a valid TFS file to disk. This is NOT
        # the same as having empty headers (empty dict)!
        df = _pd_dataframe
        write_tfs(tmp_path / "temporary.tfs", df, validate=None)  # need to discard validation
        new = read_tfs(tmp_path / "temporary.tfs")
        # I use assert_frame_equal here and not our helper assert_tfs_frame_equal
        # since Dataframe and TfsDataFrame are different df types and with no
        # headers present in the former the check would fail
        assert_frame_equal(df, new, check_frame_type=False)

    def test_tfs_write_read_with_path_in_headers(self, tmp_path, _tfs_dataframe):
        # We will insert a pathlib.Path in the headers and ensure it is
        # written as a string, in its current (relative in this case) form
        df = _tfs_dataframe
        df.headers["PATH"] = tmp_path  # this is a pathlib i

        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df, validate=None)  # don't care to validate
        assert write_location.is_file()

        written = write_location.read_text()
        assert "PATH" in written
        assert str(tmp_path) in written  # should be in its .__str__ form here

    # ----- Below are tests for files with MAD-NG features ----- #

    def test_tfs_write_read_with_booleans(self, _tfs_dataframe_booleans, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _tfs_dataframe_booleans, validate="madng")  # booleans are MAD-NG feature
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_tfs_frame_equal(_tfs_dataframe_booleans, new, check_exact=False)  # float precision can be an issue

    def test_tfs_write_read_with_complex(self, _tfs_dataframe_complex, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _tfs_dataframe_complex, validate="madng")  # booleans are MAD-NG feature
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_tfs_frame_equal(_tfs_dataframe_complex, new, check_exact=False)  # float precision can be an issue

    def test_tfs_write_with_nil_in_headers(self, _tfs_dataframe, tmp_path):
        df = _tfs_dataframe
        df.headers["WRITETONIL"] = None

        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, df, validate="madng")

        written = write_location.read_text()
        assert "WRITETONIL" in written
        assert "%n" in written
        assert "nil" in written

    def test_tfs_write_read_madng_like(self, _tfs_dataframe_madng, tmp_path):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _tfs_dataframe_madng, validate="madng")  # booleans are MAD-NG feature
        assert write_location.is_file()

        new = read_tfs(write_location)
        assert_tfs_frame_equal(_tfs_dataframe_madng, new, check_exact=False)  # float precision can be an issue

    def test_tfs_write_madng_compatible_is_read_by_madng(self, _tfs_dataframe_madng, tmp_path, capsys):
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, _tfs_dataframe_madng, validate="madng")  # booleans are MAD-NG feature
        assert write_location.is_file()

        # TODO: now read the file with pymadng and check there is not error from MADNG in the sys output
        # madng = MAD()  # might need to chmod the executable shipped with the package first
        # madng.send(f"local mtbl = mtable:read('{str(write_location.absolute())}')")

        # captured = capsys.readouterr()
        # assert "Error" not in captured.out  # TODO: correct message to check for
        # assert "Error" not in captured.err  # TODO: correct message to check for


class TestFailures:
    def test_raising_on_non_unique_columns(self, caplog):
        df = TfsDataFrame(columns=["A", "B", "A"])
        with pytest.raises(DuplicateColumnsError, match="The dataframe contains non-unique columns."):
            write_tfs("", df, non_unique_behavior="raise")

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique column names found" in caplog.text

    def test_raising_on_non_unique_index(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"])
        with pytest.raises(DuplicateIndicesError, match="The dataframe contains non-unique indices."):
            write_tfs("", df, non_unique_behavior="raise")

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique indices found" in caplog.text

    def test_raising_on_non_unique_both(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(DuplicateIndicesError, match="The dataframe contains non-unique indices."):
            write_tfs("", df, non_unique_behavior="raise")

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique indices found" in caplog.text  # first checked and raised

    def test_fail_on_wrong_column_type(self, caplog):
        caplog.set_level(logging.DEBUG)
        df = TfsDataFrame(columns=range(5))
        with pytest.raises(NonStringColumnNameError, match="TFS-Columns need to be strings."):
            write_tfs("", df)

        for record in caplog.records:
            assert record.levelname == "DEBUG"
        assert "not of string-type" in caplog.text

    def test_fail_on_spaces_columns(self, caplog):
        caplog.set_level(logging.DEBUG)
        df = TfsDataFrame(columns=["allowed", "not allowed"])
        with pytest.raises(SpaceinColumnNameError, match="TFS-Columns can not contain spaces."):
            write_tfs("", df)

        for record in caplog.records:
            assert record.levelname == "DEBUG"
        assert "Space(s) found in TFS columns" in caplog.text

    def test_messed_up_dataframe_fails_writes(self, _messed_up_dataframe: TfsDataFrame):
        messed_tfs = _messed_up_dataframe
        # This df raises in validate because of list elements
        with pytest.raises(
            IterableInDataFrameError, match="Lists or tuple elements are not accepted in a TfsDataFrame"
        ):
            write_tfs("", messed_tfs)

    def test_dict_column_dataframe_fails_writes(self, _dict_column_in_dataframe: TfsDataFrame, tmp_path):
        dict_col_tfs = _dict_column_in_dataframe
        with pytest.raises(TypeError):  # tries to format dict.__dict__, can't get a % formatter
            write_tfs("", dict_col_tfs)

        del dict_col_tfs["d"]  # should work without the column of dicts
        write_location = tmp_path / "test.tfs"
        write_tfs(write_location, dict_col_tfs)
        assert write_location.is_file()

    def test_list_column_dataframe_fails_writes(self, _list_column_in_dataframe: TfsDataFrame, tmp_path, caplog):
        list_col_tfs = _list_column_in_dataframe
        write_location = tmp_path / "test.tfs"
        # This df raises in validate because of list colnames
        with pytest.raises(
            IterableInDataFrameError, match="Lists or tuple elements are not accepted in a TfsDataFrame"
        ):
            write_tfs(write_location, list_col_tfs)

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "contains list/tuple values at Index:" in caplog.text

        with pytest.raises(TypeError):  # this time crashes on writing
            write_tfs(write_location, list_col_tfs, validate=None)

        del list_col_tfs["d"]  # should work now without the column of lists
        write_tfs(write_location, list_col_tfs)
        assert write_location.is_file()

    def test_dtype_to_formatter_string_fails_unexpected_dtypes(self):
        unexpected_list = [1, 2, 3]
        with pytest.raises(TypeError):
            _ = tfs.writer._dtype_to_formatter_string(unexpected_list, colsize=10)  # noqa: SLF001

    def test_dtype_to_tfs_format_id_fails_unexpected_dtypes(self):
        unexpected_list = [1, 2, 3]
        with pytest.raises(TypeError):
            _ = tfs.writer._dtype_to_tfs_format_identifier(unexpected_list)  # noqa: SLF001

    def test_header_line_raises_on_non_strings(self):
        not_a_string = {}
        with pytest.raises(TypeError):
            _ = tfs.writer._get_header_line(not_a_string, 10, 10)  # noqa: SLF001


# ----- Helpers & Fixtures ----- #


@pytest.fixture
def _bigger_tfs_dataframe() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(50),
        columns=list(string.ascii_lowercase),
        data=np.random.rand(50, len(list(string.ascii_lowercase))),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture
def _dataframe_empty_headers() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(3),
        columns="a b c d e".split(),
        data=np.random.rand(3, 5),
        headers={},
    )


@pytest.fixture
def _messed_up_dataframe() -> TfsDataFrame:
    """Returns a TfsDataFrame with mixed types in each column, some elements being lists."""
    int_row = np.array([random.randint(int(-1e5), int(1e5)) for _ in range(4)], dtype=np.float64)
    float_row = np.array([round(random.uniform(-1e5, 1e5), 7) for _ in range(4)], dtype=np.float64)
    string_row = np.array([_rand_string() for _ in range(4)], dtype=str)
    list_floats_row = [[1.0, 14.777], [2.0, 1243.9], [3.0], [123414.0, 9909.12795]]
    return TfsDataFrame(
        index=range(4),
        columns="a b c d".split(),
        data=[int_row, float_row, string_row, list_floats_row],
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture
def _dict_column_in_dataframe() -> TfsDataFrame:
    """Returns a TfsDataFrame with a column having dictionaries as elements."""
    int_elements = [random.randint(int(-1e5), int(1e5)) for _ in range(4)]
    float_elements = [round(random.uniform(-1e5, 1e5), 7) for _ in range(4)]
    string_elements = [_rand_string() for _ in range(4)]
    dict_elements = [{"a": "dict"}, {"b": 14}, {"c": 444.12}, {"d": [1, 2]}]
    data = [[e[i] for e in (int_elements, float_elements, string_elements, dict_elements)] for i in range(4)]
    return TfsDataFrame(
        index=range(4),
        columns="a b c d".split(),
        data=data,
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture
def _list_column_in_dataframe() -> TfsDataFrame:
    """Returns a TfsDataFrame with a column having lists as elements."""
    int_elements = [random.randint(int(-1e5), int(1e5)) for _ in range(4)]
    float_elements = [round(random.uniform(-1e5, 1e5), 7) for _ in range(4)]
    string_elements = [_rand_string() for _ in range(4)]
    list_elements = [[1.0, 14.777], [2.0, 1243.9], [3.0], [123414.0, 9909.12795]]
    data = [[e[i] for e in (int_elements, float_elements, string_elements, list_elements)] for i in range(4)]
    return TfsDataFrame(
        index=range(4),
        columns="a b c d".split(),
        data=data,
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


def _rand_string(string_length: int = 10) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(string_length))
