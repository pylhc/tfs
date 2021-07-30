import pathlib
import tempfile

import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

import tfs
from tfs import read_tfs, write_tfs
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

    def tfs_indx_pathlib_input(self, _tfs_file_pathlib: pathlib.Path):
        test_file = read_tfs(_tfs_file_pathlib)
        assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]

    def tfs_indx_str_input(self, _tfs_file_str: str):
        test_file = read_tfs(_tfs_file_str)
        assert test_file.indx["BPMYB.5L2.B1"] == test_file.set_index("NAME")["BPMYB.5L2.B1"]

    def test_id_to_type_handles_madx_string_identifier(self):
        madx_str_id = "%20s"
        assert tfs.reader._id_to_type(madx_str_id) is str

    def test_tfs_read_write_read_pathlib_input(self, _tfs_file_pathlib: pathlib.Path, _test_file: str):
        original = read_tfs(_tfs_file_pathlib)
        write_tfs(_test_file, original)
        new = read_tfs(_test_file)
        assert_frame_equal(original, new)
        assert_dict_equal(original.headers, new.headers, compare_keys=True)


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
            _ = tfs.reader._id_to_type(typoed_str_id)


class TestWarnings:
    def test_warn_unphysical_values(self, caplog):
        nan_tfs_path = pathlib.Path(__file__).parent / "inputs" / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME")
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
def _test_file() -> str:
    with tempfile.TemporaryDirectory() as cwd:
        yield str(pathlib.Path(cwd) / "test_file.tfs")


@pytest.fixture()
def _no_coltypes_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "no_coltypes.tfs"


@pytest.fixture()
def _no_colnames_tfs_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "inputs" / "no_colnames.tfs"
