import pathlib

import pytest
from pandas.api import types as pdtypes
from pandas.core.arrays.string_ import StringDtype
from pandas.testing import assert_frame_equal

import tfs
from tfs.constants import HEADER
from tfs.errors import AbsentColumnNameError, AbsentColumnTypeError, UnknownTypeIdentifierError
from tfs.reader import read_headers, read_tfs
from tfs.testing import assert_tfs_frame_equal
from tfs.writer import write_tfs

from .conftest import INPUTS_DIR


class TestRead:
    def test_tfs_read_pathlib_input(self, _tfs_filex: pathlib.Path):
        test_file = read_tfs(_tfs_filex, index="NAME")
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

    def test_tfs_read_no_validation(self, _tfs_filex: pathlib.Path):
        test_file = read_tfs(_tfs_filex, index="NAME")
        assert len(test_file.headers) > 0
        assert len(test_file.columns) > 0
        assert len(test_file.index) > 0
        assert len(str(test_file)) > 0
        assert isinstance(test_file.index[0], str)

    def test_tfs_read_wrong_file_no_validation(self, _space_in_colnames_tfs_path: pathlib.Path):
        # Read file has a space in a column name which should raise, we make sure that it
        # goes through when explicitely skipping validation
        df = read_tfs(_space_in_colnames_tfs_path, index="NAME")
        assert "BPM RES" in df.columns

    def test_tfs_read_no_validation_doesnt_warn(self, caplog):
        # The loaded file has NaNs inside, which should emit a warning on validation
        nan_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME")
        assert "contains non-physical values at Index:" not in caplog.text

    def test_id_to_type_handles_madx_string_identifier(self):
        madx_str_id = "%20s"
        assert tfs.reader._id_to_type(madx_str_id) is str  # noqa: SLF001

    def test_tfs_read_write_read_pathlib_input(self, _tfs_filex: pathlib.Path, tmp_path):
        original = read_tfs(_tfs_filex)
        write_location = tmp_path / "test_file.tfs"
        write_tfs(write_location, original)
        new = read_tfs(write_location)
        assert_tfs_frame_equal(original, new)

    def test_read_write_wise_header(self, _tfs_file_wise, tmp_path):
        original_text = _tfs_file_wise.read_text()
        original_header_lines = [line for line in original_text.splitlines() if line.strip().startswith(HEADER)]
        df = read_tfs(_tfs_file_wise)

        assert len(df.headers) == len(original_header_lines)

        out_path = tmp_path / "wise_test.tfs"
        write_tfs(out_path, df)

        new_text = out_path.read_text()
        new_header_lines = [line for line in new_text.splitlines() if line.strip().startswith(HEADER)]

        assert len(new_header_lines) == len(original_header_lines)

        for header, value in df.headers.items():
            assert header in new_text
            assert str(value) in new_text  # all

    def test_read_headers(self, _tfs_filex):
        headers = read_headers(_tfs_filex)
        assert isinstance(headers, dict)
        assert len(headers) > 0
        assert len(str(headers)) > 0
        assert all(key in headers for key in ["TITLE", "DPP", "Q1", "Q1RMS", "NATQ1", "NATQ1RMS", "BPMCOUNT"])

    def test_read_empty_strings_ok(self, _empty_strings_tfs_path):
        df = read_tfs(_empty_strings_tfs_path)

        # Make sure the NAME column is properly inferred to string dtype
        assert isinstance(df.convert_dtypes().NAME.dtype, StringDtype)
        # Make sure there are no nans in the NAME column
        assert not any(df.NAME.isna())
        # Make sure we have exactly 5 empty strings in the NAME column
        assert sum(df.NAME == "") == 5

    def test_read_file_with_empty_lines_in_header(self, _tfs_file_empty_lines, _tfs_filex):
        df = read_tfs(_tfs_file_empty_lines)
        assert df.headers
        df_for_compare = read_tfs(_tfs_filex)
        assert_tfs_frame_equal(df, df_for_compare)

    def test_read_file_single_header_empty_line_in_header(self, _tfs_file_single_header_empty_line, _tfs_filex):
        """Very special, but this was a case that failed in the past."""
        df = read_tfs(_tfs_file_single_header_empty_line)
        assert len(df.headers) == 1
        df_for_compare = read_tfs(_tfs_filex)
        assert_frame_equal(df, df_for_compare)  # no headers, just check dframe

    def test_read_file_without_header_empty_line(self, _tfs_file_without_header_but_empty_line, _tfs_filex):
        df = read_tfs(_tfs_file_without_header_but_empty_line)
        assert not df.headers
        df_for_compare = read_tfs(_tfs_filex)
        assert_frame_equal(df, df_for_compare)  # no headers, just check dframe

    def test_read_file_with_whitespaces_in_header(self, _tfs_file_with_whitespaces, _tfs_filex):
        df = read_tfs(_tfs_file_with_whitespaces)
        assert df.headers
        df_for_compare = read_tfs(_tfs_filex)
        assert_tfs_frame_equal(df, df_for_compare)

    def test_read_file_without_header(self, _tfs_file_without_header, _tfs_filex):
        df = read_tfs(_tfs_file_without_header)
        assert not df.headers
        df_for_compare = read_tfs(_tfs_filex)
        assert_frame_equal(df, df_for_compare)  # no headers, just check dframe

    # ----- Below are tests for files with MAD-NG features ----- #

    def test_tfs_read_file_with_nil_headers(self):
        # This is kind of "MAD-NG feature" as 'nil' is specific ot it
        # In tfs-pandas a 'nil' in headers is read as 'None'
        nil_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nils.tfs"
        headers = tfs.reader.read_headers(nil_tfs_path)  # no validation in here

        # Make sure it has been read correctly
        assert headers["NILVALUE"] is None

    def test_tfs_read_file_with_nil_values_in_data(self):
        # This is kind of "MAD-NG feature" as 'nil' is specific ot it
        nil_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nils.tfs"
        df = tfs.read(nil_tfs_path)  # no validation in here

        # In the data part of the file, we read a 'nil' values as NaN
        # There is are nil values in S, CO and BPM_RES columns which
        # we want to make sure are now NaNs
        assert df.S.isna().any()
        assert df.CO.isna().any()
        assert df.BPM_RES.isna().any()

        # If the 'nil' is in a string-dtyped column we read it as None
        # This is the case in the first element of the NAME columns,
        # so we make sure that one is indeed None
        assert df.loc[0, "NAME"] is None

    def test_tfs_read_file_with_booleans(self, _tfs_booleans_file):
        df = read_tfs(_tfs_booleans_file)
        assert df.headers["BOOLTRUE1"] is True  # true resolves to True
        assert df.headers["BOOLTRUE2"] is True  # True resolves to True
        assert df.headers["BOOLTRUE3"] is True  # 1 resolves to True
        assert df.headers["BOOLFALSE1"] is False  # false resolves to False
        assert df.headers["BOOLFALSE2"] is False  # False resolves to False
        assert df.headers["BOOLFALSE3"] is False  # 0 resolves to False

        assert "boolean" in df.columns
        assert pdtypes.is_bool_dtype(df["boolean"].dtype)

    def test_tfs_read_write_read_with_booleans(self, _tfs_booleans_file, tmp_path):
        original = read_tfs(_tfs_booleans_file)
        write_location = tmp_path / "boolean_headers_and_column.tfs"
        write_tfs(write_location, original, validate="madng")  # booleans are MAD-NG feature

        new = read_tfs(write_location)
        assert_tfs_frame_equal(original, new)

    def test_tfs_read_file_with_complex_values(self, _tfs_complex_file):
        df = read_tfs(_tfs_complex_file)
        assert "complex" in df.headers
        assert pdtypes.is_complex_dtype(df.headers["complex"])
        assert df.headers["complex"] == 1.3 + 1.2j

        assert "complex" in df.columns
        assert pdtypes.is_complex_dtype(df["complex"].dtype)

    def test_tfs_read_write_read_with_complex(self, _tfs_complex_file, tmp_path):
        original = read_tfs(_tfs_complex_file)
        write_location = tmp_path / "complex_headers_and_column.tfs"
        write_tfs(write_location, original, validate="madng")  # complex values are MAD-NG feature

        new = read_tfs(write_location)
        assert_tfs_frame_equal(original, new)

    def test_tfs_read_write_madng_features(self, _tfs_madng_file):
        df = read_tfs(_tfs_madng_file)
        assert df.headers["BOOLEAN1"] is True  # true resolves to True
        assert df.headers["BOOLEAN2"] is False  # false resolves to False
        assert pdtypes.is_complex_dtype(df.headers["COMPLEX"])
        assert df.headers["COMPLEX"] == 1.3 + 1.2j

        assert "complex" in df.columns
        assert "boolean" in df.columns
        assert pdtypes.is_complex_dtype(df["complex"].dtype)
        assert pdtypes.is_bool_dtype(df["boolean"].dtype)

    def test_tfs_read_write_read_madng_features(self, _tfs_madng_file, tmp_path):
        original = read_tfs(_tfs_madng_file)
        write_location = tmp_path / "madng_headers_and_columns.tfs"
        write_tfs(write_location, original, validate="madng")  # need madng validation for MAD-NG feature

        new = read_tfs(write_location)
        assert_tfs_frame_equal(original, new)


class TestFailures:
    def test_absent_attributes_and_keys(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str, index="NAME")
        with pytest.raises(AttributeError):
            _ = test_file.Not_HERE

        with pytest.raises(KeyError):
            _ = test_file["Not_HERE"]

    def test_id_to_type_fails_unexpected_identifiers(self):
        unexpected_id = "%t"
        with pytest.raises(UnknownTypeIdentifierError, match="Unknown data type"):
            _ = tfs.reader._id_to_type(unexpected_id)  # noqa: SLF001

    def test_fail_read_no_coltypes(self, _no_coltypes_tfs_path):
        with pytest.raises(AbsentColumnTypeError):
            _ = read_tfs(_no_coltypes_tfs_path)

    def test_fail_read_no_colnames(self, _no_colnames_tfs_path):
        with pytest.raises(AbsentColumnNameError):
            _ = read_tfs(_no_colnames_tfs_path)

    def test_id_to_type_handles_typo_str_id(self):
        typoed_str_id = "%%s"
        with pytest.raises(UnknownTypeIdentifierError, match="Unknown data type"):
            _ = tfs.reader._id_to_type(typoed_str_id)  # noqa: SLF001


# ----- Helpers & Fixtures ----- #


@pytest.fixture
def _tfs_file_str(_tfs_filex) -> str:
    return str(_tfs_filex.absolute())


@pytest.fixture
def _no_coltypes_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "no_coltypes.tfs"


@pytest.fixture
def _no_colnames_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "no_colnames.tfs"


@pytest.fixture
def _space_in_colnames_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "space_in_colname.tfs"


@pytest.fixture
def _tfs_file_wise() -> pathlib.Path:
    return INPUTS_DIR / "wise_header.tfs"


@pytest.fixture
def _tfs_file_empty_lines() -> pathlib.Path:
    return INPUTS_DIR / "empty_lines_in_header.tfs"


@pytest.fixture
def _tfs_file_single_header_empty_line() -> pathlib.Path:
    return INPUTS_DIR / "single_header_line_and_empty_line.tfs"


@pytest.fixture
def _tfs_file_with_whitespaces() -> pathlib.Path:
    return INPUTS_DIR / "line_with_whitespaces_in_header.tfs"


@pytest.fixture
def _tfs_file_without_header() -> pathlib.Path:
    return INPUTS_DIR / "no_header.tfs"


@pytest.fixture
def _tfs_file_without_header_but_empty_line() -> pathlib.Path:
    return INPUTS_DIR / "no_header_just_an_empty_line.tfs"


@pytest.fixture
def _empty_strings_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "empty_strings.tfs"
