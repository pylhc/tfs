import pathlib

import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

import tfs
from tfs import read_tfs, write_tfs
from tfs.constants import HEADER
from tfs.errors import TfsFormatError

CURRENT_DIR = pathlib.Path(__file__).parent


class TestRead:
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

    def test_tfs_read_no_validation(self, _tfs_file_pathlib: pathlib.Path):
        test_file = read_tfs(_tfs_file_pathlib, index="NAME", validate=False)
        assert len(test_file.headers) > 0
        assert len(test_file.columns) > 0
        assert len(test_file.index) > 0
        assert len(str(test_file)) > 0
        assert isinstance(test_file.index[0], str)

    def test_tfs_read_wrong_file_no_validation(self, _space_in_colnames_tfs_path: pathlib.Path):
        # Read file has a space in a column name which should raise, we make sure that it 
        # goes through when explicitely skipping validation
        df = read_tfs(_space_in_colnames_tfs_path, index="NAME", validate=False)
        assert "BPM RES" in df.columns

    def test_tfs_read_no_validation_doesnt_warn(self, caplog):
        nan_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME", validate=False)
        assert "contains non-physical values at Index:" not in caplog.text

    def tfs_indx_pathlib_input(self, _tfs_file_pathlib: pathlib.Path):
        test_file = read_tfs(_tfs_file_pathlib)
        assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]

    def tfs_indx_str_input(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str)
        assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]

    def test_id_to_type_handles_madx_string_identifier(self):
        madx_str_id = "%20s"
        assert tfs.reader._id_to_type(madx_str_id) is str

    def test_tfs_read_write_read_pathlib_input(self, _tfs_file_pathlib: pathlib.Path, tmp_path):
        original = read_tfs(_tfs_file_pathlib)
        write_location = tmp_path / "test_file.tfs"
        write_tfs(write_location, original)
        new = read_tfs(write_location)
        assert_frame_equal(original, new)
        assert_dict_equal(original.headers, new.headers, compare_keys=True)

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


class TestFailures:
    def test_absent_attributes_and_keys(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str, index="NAME")
        with pytest.raises(AttributeError):
            _ = test_file.Not_HERE

        with pytest.raises(KeyError):
            _ = test_file["Not_HERE"]

    def test_id_to_type_fails_unexpected_identifiers(self):
        unexpected_id = "%t"
        with pytest.raises(TfsFormatError):
            _ = tfs.reader._id_to_type(unexpected_id)

    def test_fail_read_no_coltypes(self, _no_coltypes_tfs_path, caplog):
        with pytest.raises(TfsFormatError) as e:
            _ = read_tfs(_no_coltypes_tfs_path)
        assert "column types" in str(e)

    def test_fail_read_no_colnames(self, _no_colnames_tfs_path, caplog):
        with pytest.raises(TfsFormatError) as e:
            _ = read_tfs(_no_colnames_tfs_path)
        assert "column names" in str(e)

    def test_id_to_type_handles_typo_str_id(self):
        typoed_str_id = "%%s"
        with pytest.raises(TfsFormatError):
            _ = tfs.reader._id_to_type(typoed_str_id)

    def test_fail_space_in_colname(self, _space_in_colnames_tfs_path: pathlib.Path):
        # Read file has a space in a column name which should raise
        with pytest.raises(TfsFormatError):
            read_tfs(_space_in_colnames_tfs_path, index="NAME", validate=True)


class TestWarnings:
    def test_warn_unphysical_values(self, caplog):
        nan_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME", validate=True)
        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "contains non-physical values at Index:" in caplog.text


# ------ Fixtures ------ #


@pytest.fixture()
def _tfs_file_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"


@pytest.fixture()
def _tfs_file_str() -> str:
    return str((CURRENT_DIR / "inputs" / "file_x.tfs").absolute())


@pytest.fixture()
def _no_coltypes_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "no_coltypes.tfs"


@pytest.fixture()
def _no_colnames_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "no_colnames.tfs"


@pytest.fixture()
def _space_in_colnames_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "space_in_colname.tfs"


@pytest.fixture()
def _tfs_file_wise() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "wise_header.tfs"
