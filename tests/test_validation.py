import pathlib

import pytest

from tfs.errors import InvalidBooleanHeaderError, MADXCompatibilityError, SpaceinColumnNameError
from tfs.frame import TfsDataFrame, validate
from tfs.reader import read_tfs

from .conftest import INPUTS_DIR


class TestWarnings:
    """Tests for common warnings in validation, both in MAD-X and MAD-NG compatibility mode."""

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_warn_unphysical_values(self, validation_mode, caplog):
        nan_tfs_path = INPUTS_DIR / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME", validate=validation_mode)
        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "contains non-physical values at Index:" in caplog.text

    def test_warning_on_non_unique_columns(self, caplog):
        df = TfsDataFrame(columns=["A", "B", "A"])
        # validate in most restrictive (MADX) mode but this is in common checks
        validate(df, compatibility="madx")

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique column names found" in caplog.text

    def test_warning_on_non_unique_index(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"])
        # validate in most restrictive (MADX) mode but this is in common checks
        validate(df, compatibility="madx")

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique indices found" in caplog.text

    def test_warning_on_non_unique_both(self, tmp_path, caplog):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        # validate in most restrictive (MADX) mode but this is in common checks
        validate(df, compatibility="madx")

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique column names found" in caplog.text
        assert "Non-unique indices found" in caplog.text


class TestCommonFailures:
    """Tests for common failures in validation, both in MAD-X and MAD-NG compatibility mode."""

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_validate_raises_on_wrong_unique_behavior(self, validation_mode):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(ValueError):
            validate(df, "", non_unique_behavior="invalid", compatibility=validation_mode)

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

    @pytest.mark.parametrize("validation_mode", ["not ok", "ma-Dx", "nope", "madngg"])
    def test_validation_raises_on_invalid_compatibility_mode(self, _tfs_dataframe, validation_mode):
        with pytest.raises(ValueError, match="Invalid compatibility mode provided"):
            validate(_tfs_dataframe, compatibility=validation_mode)


class TestMADXFailures:
    """Tests for failures in MAD-X validation mode, when df has MAD-NG features."""

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_boolean_headers(self, _tfs_booleans_file, validation_mode):
        df = read_tfs(_tfs_booleans_file)
        with pytest.raises(
            MADXCompatibilityError, match="TFS-Headers can not contain boolean values in MAD-X compatibility mode"
        ):
            validate(df, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_complex_headers(self, _tfs_complex_file, validation_mode):
        df = read_tfs(_tfs_complex_file)
        with pytest.raises(
            MADXCompatibilityError, match="TFS-Headers can not contain complex values in MAD-X compatibility mode"
        ):
            validate(df, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_boolean_columns(self, _tfs_booleans_file, validation_mode):
        df = read_tfs(_tfs_booleans_file)
        df.headers = {}  # or else the first validation check raises because of boolean headers
        with pytest.raises(
            MADXCompatibilityError,
            match="TFS-Dataframe can not contain boolean dtype columns in MAD-X compatibility mode",
        ):
            validate(df, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_complex_columns(self, _tfs_complex_file, validation_mode):
        df = read_tfs(_tfs_complex_file)
        df.headers = {}  # or else the first validation check raises because of complex headers
        with pytest.raises(
            MADXCompatibilityError,
            match="TFS-Dataframe can not contain complex dtype columns in MAD-X compatibility mode",
        ):
            validate(df, compatibility=validation_mode)


class TestMADNGValidation:
    """Tests validation step is all fine in MAD-NG mode, when df has MAD-NG features."""

    @pytest.mark.parametrize("validation_mode", ["madng", "MAD-NG", "mAD-nG"])
    def test_madng_validation_passes_on_madng_features(self, _tfs_madng_file, validation_mode):
        read_tfs(_tfs_madng_file, validate=validation_mode)  # trigger validation here


# ------ Fixtures ------ #


@pytest.fixture
def _space_in_colnames_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "space_in_colname.tfs"


@pytest.fixture
def _invalid_bool_in_header_tfs_file() -> pathlib.Path:
    """TFS file with invalid value for bool header."""
    return INPUTS_DIR / "invalid_bool_header.tfs"
