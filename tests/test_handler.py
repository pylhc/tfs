import os
import pathlib
import random
import string
import tempfile

import numpy
import pandas
import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal, assert_index_equal

import tfs
from tfs import TfsDataFrame, read_tfs, write_tfs
from tfs.handler import TfsFormatError

CURRENT_DIR = pathlib.Path(__file__).parent


class TestReadWrite:
    def test_tfs_read_pathlib_input(self, _tfs_file_pathlib: pathlib.Path):
        test_file = read_tfs(_tfs_file_pathlib, index="NAME")
        assert len(test_file.headers) > 0
        assert len(test_file.columns) > 0
        assert len(test_file.index) > 0
        assert len(str(test_file)) > 0
        assert isinstance(test_file.index[0], str)

        with pytest.raises(AttributeError):
            _ = test_file.Not_HERE

        with pytest.raises(KeyError):
            _ = test_file["Not_HERE"]

    def test_tfs_read_str_input(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str, index="NAME")
        assert len(test_file.headers) > 0
        assert len(test_file.columns) > 0
        assert len(test_file.index) > 0
        assert len(str(test_file)) > 0
        assert isinstance(test_file.index[0], str)

    def tfs_indx_pathlib_input(self, _tfs_file_pathlib: pathlib.Path):
        test_file = read_tfs(_tfs_file_pathlib)
        assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]

    def tfs_indx_str_input(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str)
        assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]

    def test_tfs_write_read(self, _tfs_dataframe, _test_file: str):
        write_tfs(_test_file, _tfs_dataframe)
        assert pathlib.Path(_test_file).is_file()

        new = read_tfs(_test_file)
        assert_frame_equal(
            _tfs_dataframe, new, check_exact=False
        )  # float precision can be an issue
        assert_dict_equal(_tfs_dataframe.headers, new.headers, compare_keys=True)

    def test_tfs_write_read_no_headers(
        self, _dataframe_empty_headers: TfsDataFrame, _test_file: str
    ):
        write_tfs(_test_file, _dataframe_empty_headers)
        assert pathlib.Path(_test_file).is_file()

        new = read_tfs(_test_file)
        assert_frame_equal(_dataframe_empty_headers, new, check_exact=False)  # float precision
        assert_dict_equal(_dataframe_empty_headers.headers, new.headers, compare_keys=True)

    def test_tfs_write_read_pandasdf(self, _pd_dataframe, _test_file: str):
        write_tfs(_test_file, _pd_dataframe)
        assert pathlib.Path(_test_file).is_file()

        new = read_tfs(_test_file)
        assert_frame_equal(
            _pd_dataframe,
            new,
            check_exact=False,  # float precision can be an issue
            check_frame_type=False,  # read df is TfsDF
        )

    def test_write_read_spaces_in_strings(self, _test_file: str):
        df = TfsDataFrame(data=["This is", "a test", "with spaces"], columns=["A"])
        write_tfs(_test_file, df)
        new = read_tfs(_test_file)
        assert_frame_equal(df, new)

    def test_tfs_write_read_autoindex(self, _tfs_dataframe, _test_file: str):
        df = _tfs_dataframe.set_index("a")
        df1 = _tfs_dataframe.set_index("a")
        write_tfs(_test_file, df, save_index=True)
        assert_frame_equal(df, df1)

        df_read = read_tfs(_test_file)
        assert_index_equal(df.index, df_read.index, check_exact=False)
        assert_dict_equal(_tfs_dataframe.headers, df_read.headers, compare_keys=True)

    def test_tfs_read_write_read_pathlib_input(
        self, _tfs_file_pathlib: pathlib.Path, _test_file: str
    ):
        original = read_tfs(_tfs_file_pathlib)
        write_tfs(_test_file, original)
        new = read_tfs(_test_file)
        assert_frame_equal(original, new)
        assert_dict_equal(original.headers, new.headers, compare_keys=True)

    def test_tfs_read_write_read_str_input(self, _tfs_file_str: str, _test_file: str):
        original = read_tfs(_tfs_file_str)
        write_tfs(_test_file, original)
        new = read_tfs(_test_file)
        assert_frame_equal(original, new)
        assert_dict_equal(original.headers, new.headers, compare_keys=True)

    def test_tfs_write_empty_columns_dataframe(self, _test_file: str):
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

    def test_tfs_write_empty_index_dataframe(self, _test_file: str):
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

    def test_write_int_float_str_columns(self, _test_file: str):
        """ This test is more of an extension of the test below
         (this dataframe was not affected by the bug) """
        df = TfsDataFrame(
            data=[[1, 1., "one"],
                  [2, 2., "two"],
                  [3, 3., "three"]],
            columns=["Int", "Float", "String"]
        )
        write_tfs(_test_file, df)
        new = read_tfs(_test_file)
        assert_frame_equal(df, new)

    def test_write_int_float_columns(self, _test_file: str):
        """ This test is here because of numeric conversion bug
        upon writing back in v2.0.1 """
        df = TfsDataFrame(
            data=[[1, 1.],
                  [2, 2.],
                  [3, 3.]],
            columns=["Int", "Float"]
        )
        write_tfs(_test_file, df)
        new = read_tfs(_test_file)
        assert_frame_equal(df, new)


class TestFailures:
    def test_absent_attributes_and_keys(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str, index="NAME")
        with pytest.raises(AttributeError):
            _ = test_file.Not_HERE

        with pytest.raises(KeyError):
            _ = test_file["Not_HERE"]

    def test_raising_on_non_unique_columns(self, caplog):
        df = TfsDataFrame(columns=["A", "B", "A"])
        with pytest.raises(TfsFormatError):
            df.check_unique(check="columns")

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "Non-unique columns found" in caplog.text

    def test_raising_on_non_unique_index(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"])
        with pytest.raises(TfsFormatError):
            df.check_unique(check="indices")

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "Non-unique indices found" in caplog.text

    def test_raising_on_non_unique_both(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(TfsFormatError):
            df.check_unique()  # defaults to both

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "Non-unique indices or columns found" in caplog.text

    def test_fail_on_wrong_column_type(self, caplog):
        df = TfsDataFrame(columns=range(5))
        with pytest.raises(TfsFormatError):
            write_tfs("", df)

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "not of string-type" in caplog.text

    def test_fail_on_spaces_columns(self, caplog):
        df = TfsDataFrame(columns=["allowed", "not allowed"])
        with pytest.raises(TfsFormatError):
            write_tfs("", df)

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "Space(s) found in TFS columns" in caplog.text

    def test_fail_on_spaces_headers(self, caplog):
        df = TfsDataFrame(headers={"allowed": 1, "not allowed": 2})
        with pytest.raises(TfsFormatError):
            write_tfs("", df)

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "Space(s) found in TFS header names" in caplog.text

    def test_messed_up_dataframe_fails_writes(self, _messed_up_dataframe: TfsDataFrame):
        messed_tfs = _messed_up_dataframe
        with pytest.raises(ValueError):
            write_tfs("", messed_tfs)

    def test_dict_column_dataframe_fails_writes(
        self, _dict_column_in_dataframe: TfsDataFrame, _test_file
    ):
        dict_col_tfs = _dict_column_in_dataframe
        with pytest.raises(TypeError):  # tries to format dict.__dict__, can't get a % formatter
            write_tfs("", dict_col_tfs)

        del dict_col_tfs["d"]  # should work without the column of dicts
        write_tfs(_test_file, dict_col_tfs)
        assert pathlib.Path(_test_file).is_file()

    def test_list_column_dataframe_fails_writes(
        self, _list_column_in_dataframe: TfsDataFrame, _test_file
    ):
        list_col_tfs = _list_column_in_dataframe
        with pytest.raises(ValueError):  # truth value of nested can't be assesed in _validate
            write_tfs("", list_col_tfs)

        del list_col_tfs["d"]  # should work without the column of lists
        write_tfs(_test_file, list_col_tfs)
        assert pathlib.Path(_test_file).is_file()

    def test_dtype_to_format_fails_unexpected_dtypes(self):
        unexpected_list = [1, 2, 3]
        with pytest.raises(TypeError):
            _ = tfs.handler._dtype_to_formatter(unexpected_list, colsize=10)

    def test_dtype_to_str_fails_unexpected_dtypes(self):
        unexpected_list = [1, 2, 3]
        with pytest.raises(TypeError):
            _ = tfs.handler._dtype_to_id_string(unexpected_list)

    def test_id_to_type_fails_unexpected_identifiers(self):
        unexpected_id = "%t"
        with pytest.raises(TfsFormatError):
            _ = tfs.handler._id_to_type(unexpected_id)

    def test_header_line_raises_on_non_strings(self):
        not_a_string = dict()
        with pytest.raises(TypeError):
            _ = tfs.handler._get_header_line(not_a_string, 10, 10)

    def test_fail_read_no_coltypes(self, _no_coltypes_tfs_path, caplog):
        with pytest.raises(TfsFormatError):
            _ = read_tfs(_no_coltypes_tfs_path)

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "No column types in file" in caplog.text

    def test_fail_read_no_colnames(self, _no_colnames_tfs_path, caplog):
        with pytest.raises(TfsFormatError):
            _ = read_tfs(_no_colnames_tfs_path)

        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "No column names in file" in caplog.text

    def test_id_to_type_handles_typo_str_id(self):
        typoed_str_id = "%%s"
        with pytest.raises(TfsFormatError):
            _ = tfs.handler._id_to_type(typoed_str_id)


def test_id_to_type_handles_madx_string_identifier():
    madx_str_id = "%20s"
    assert tfs.handler._id_to_type(madx_str_id) is str


class TestWarnings:
    def test_warn_unphysical_values(self, caplog):
        nan_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME")
        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "contains non-physical values at Index:" in caplog.text

    def test_empty_df_warns_on_types_inference(self, caplog):
        empty_df = pandas.DataFrame()
        converted_df = tfs.handler._autoset_pandas_types(empty_df)
        assert_frame_equal(converted_df, empty_df)

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "An empty dataframe was provided, no types were infered" in caplog.text


class TestPrinting:
    def test_header_print(self):
        headers = {"param": 3, "other": "hello"}
        df = TfsDataFrame(headers=headers)
        print_out = str(df)
        assert "Headers" in print_out

        for key, val in headers.items():
            assert key in print_out
            assert str(val) in print_out


# ------ Fixtures ------ #


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
def _tfs_dataframe() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(3),
        columns="a b c d e".split(),
        data=numpy.random.rand(3, 5),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture()
def _dataframe_empty_headers() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(3), columns="a b c d e".split(), data=numpy.random.rand(3, 5), headers={},
    )


@pytest.fixture()
def _messed_up_dataframe() -> TfsDataFrame:
    """Returns a TfsDataFrame with mixed types in each column, some elements being lists."""
    int_row = numpy.array([random.randint(-1e5, 1e5) for _ in range(4)], dtype=numpy.float64)
    float_row = numpy.array(
        [round(random.uniform(-1e5, 1e5), 7) for _ in range(4)], dtype=numpy.float64
    )
    string_row = numpy.array([_rand_string() for _ in range(4)], dtype=numpy.str)
    list_floats_row = [[1.0, 14.777], [2.0, 1243.9], [3.0], [123414.0, 9909.12795]]
    return TfsDataFrame(
        index=range(4),
        columns="a b c d".split(),
        data=[int_row, float_row, string_row, list_floats_row],
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture()
def _dict_column_in_dataframe() -> TfsDataFrame:
    """Returns a TfsDataFrame with a column having dictionaries as elements."""
    int_elements = [random.randint(-1e5, 1e5) for _ in range(4)]
    float_elements = [round(random.uniform(-1e5, 1e5), 7) for _ in range(4)]
    string_elements = [_rand_string() for _ in range(4)]
    dict_elements = [{"a": "dict"}, {"b": 14}, {"c": 444.12}, {"d": [1, 2]}]
    data = [
        [e[i] for e in (int_elements, float_elements, string_elements, dict_elements)]
        for i in range(4)
    ]
    return TfsDataFrame(
        index=range(4),
        columns="a b c d".split(),
        data=data,
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture()
def _list_column_in_dataframe() -> TfsDataFrame:
    """Returns a TfsDataFrame with a column having lists as elements."""
    int_elements = [random.randint(-1e5, 1e5) for _ in range(4)]
    float_elements = [round(random.uniform(-1e5, 1e5), 7) for _ in range(4)]
    string_elements = [_rand_string() for _ in range(4)]
    list_elements = [[1.0, 14.777], [2.0, 1243.9], [3.0], [123414.0, 9909.12795]]
    data = [
        [e[i] for e in (int_elements, float_elements, string_elements, list_elements)]
        for i in range(4)
    ]
    return TfsDataFrame(
        index=range(4),
        columns="a b c d".split(),
        data=data,
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture()
def _no_coltypes_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "no_coltypes.tfs"


@pytest.fixture()
def _no_colnames_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "no_colnames.tfs"


@pytest.fixture()
def _pd_dataframe() -> pandas.DataFrame:
    return pandas.DataFrame(
        index=range(3), columns="a b c d e".split(), data=numpy.random.rand(3, 5),
    )


def _rand_string(string_length: int = 10) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(string_length))
