import pathlib

import pytest

from tfs.errors import InvalidBooleanHeaderError, SpaceinColumnNameError
from tfs.frame import TfsDataFrame, validate
from tfs.reader import read_tfs

INPUTS_DIR = pathlib.Path(__file__).parent / "inputs"


class TestWarnings:
    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_warn_unphysical_values(self, validation_mode, caplog):
        nan_tfs_path = INPUTS_DIR / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME", validate=validation_mode)
        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "contains non-physical values at Index:" in caplog.text


class TestFailures:
    def test_validate_raises_on_wrong_unique_behavior(self):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(ValueError):
            validate(df, "", non_unique_behavior="invalid")

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_validation_raises_space_in_colname(self, _space_in_colnames_tfs_path: pathlib.Path, validation_mode):
        # Read file has a space in a column name which should raise
        with pytest.raises(SpaceinColumnNameError, match="TFS-Columns can not contain spaces."):
            _ = read_tfs(_space_in_colnames_tfs_path, index="NAME", validate=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_validation_raises_wrong_boolean_header(self, _invalid_bool_in_header_tfs_file, validation_mode):
        # The file header has a boolean value that is not accepted
        with pytest.raises(InvalidBooleanHeaderError, match="Invalid boolean header value parsed"):
            _ = read_tfs(_invalid_bool_in_header_tfs_file, validate=validation_mode)


# TODO: validation tests for MAD-X and MAD-NG with different files,
# especially ones that include MAD-NG features

# ------ Fixtures ------ #


@pytest.fixture
def _space_in_colnames_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "space_in_colname.tfs"


@pytest.fixture
def _invalid_bool_in_header_tfs_file() -> pathlib.Path:
    """TFS file with invalid value for bool header."""
    return INPUTS_DIR / "invalid_bool_header.tfs"
