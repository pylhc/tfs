import logging
import pathlib

import numpy as np
import pytest

from tfs.errors import (
    InvalidBooleanHeaderError,
    MADXCompatibilityError,
    NonStringColumnNameError,
    SpaceinColumnNameError,
)
from tfs.frame import TfsDataFrame, validate
from tfs.reader import read_tfs
from tfs.writer import write_tfs

from .conftest import INPUTS_DIR


class TestWarnings:
    """Tests for common warnings in validation, both in MAD-X and MAD-NG compatibility mode."""

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_warn_unphysical_values_in_data(self, validation_mode, caplog):
        nan_tfs_path = INPUTS_DIR / "has_nans.tfs"
        _ = read_tfs(nan_tfs_path, index="NAME", validate=validation_mode)
        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "contains non-physical values at Index:" in caplog.text

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_warn_unphysical_values_in_headers(self, _tfs_dataframe, validation_mode, caplog):
        df = _tfs_dataframe
        df.headers["NANVALUE"] = np.nan  # make sure there is a NaN in there
        validate(df, compatibility=validation_mode)

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "contains non-physical values in headers" in caplog.text

    def test_warning_on_non_unique_columns(self, caplog):
        df = TfsDataFrame(columns=["A", "B", "A"])
        validate(df)

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique column names found" in caplog.text

    def test_warning_on_non_unique_index(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"])
        validate(df)

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique indices found" in caplog.text

    def test_warning_on_non_unique_both(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        validate(df)

        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Non-unique column names found" in caplog.text
        assert "Non-unique indices found" in caplog.text


class TestCommonFailures:
    """Tests for common failures in validation, both in MAD-X and MAD-NG compatibility mode."""

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_validate_raises_on_wrong_unique_behavior(self, validation_mode):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(ValueError, match="Invalid value for parameter 'non_unique_behavior'"):
            validate(df, "", non_unique_behavior="invalid", compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_validation_raises_space_in_colname(
        self, _space_in_colnames_tfs_path: pathlib.Path, validation_mode
    ):
        # Read file has a space in a column name which should raise
        with pytest.raises(SpaceinColumnNameError, match="TFS-Columns can not contain spaces."):
            _ = read_tfs(_space_in_colnames_tfs_path, index="NAME", validate=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "madng", "MAD-NG"])
    def test_validation_raises_wrong_boolean_header(self, _invalid_bool_in_header_tfs_file, validation_mode):
        # The file header has a boolean value that is not accepted
        with pytest.raises(InvalidBooleanHeaderError, match="Invalid boolean header value parsed"):
            _ = read_tfs(_invalid_bool_in_header_tfs_file, validate=validation_mode)

    def test_validation_raises_on_wrong_column_name_type(self, caplog):
        # Catch a column name not being str typed
        caplog.set_level(logging.DEBUG)
        df = TfsDataFrame(columns=range(5))
        with pytest.raises(NonStringColumnNameError, match="TFS-Columns need to be strings."):
            validate(df)

        for record in caplog.records:
            assert record.levelname == "DEBUG"
        assert "not of string-type" in caplog.text

    @pytest.mark.parametrize("validation_mode", ["not ok", "ma-Dx", "nope", "madngg"])
    def test_validation_raises_on_invalid_compatibility_mode(self, _tfs_dataframe, validation_mode):
        with pytest.raises(ValueError, match="Invalid compatibility mode provided"):
            validate(_tfs_dataframe, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["not ok", "ma-Dx", "nope", "madngg"])
    def test_reader_raises_on_invalid_compatibility_mode(self, _tfs_filex: pathlib.Path, validation_mode):
        # Same as above but we check that it triggers validation and raises from the reader
        # function (since we do not give a None value)
        with pytest.raises(ValueError, match="Invalid compatibility mode provided"):
            _ = read_tfs(_tfs_filex, validate=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["not ok", "ma-Dx", "nope", "madngg"])
    def test_writer_raises_on_invalid_compatibility_mode(self, tmp_path, _tfs_dataframe, validation_mode):
        # Same as above but we check that it triggers validation and raises from the reader
        # function (since we do not give a None value)
        location = tmp_path / "test.tfs"  # if we mess up and it writes, it's a temp file anyway
        with pytest.raises(ValueError, match="Invalid compatibility mode provided"):
            _ = write_tfs(location, _tfs_dataframe, validate=validation_mode)


class TestMADXFailures:
    """Tests for failures in MAD-X validation mode, when df has MAD-NG features."""

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_if_no_headers(self, _pd_dataframe, validation_mode):
        """MAD-X expects at least a 'TYPE' header. If there are no headers, we raise."""
        df = _pd_dataframe
        with pytest.raises(
            MADXCompatibilityError, match="Headers should be present in MAD-X compatibility mode"
        ):
            validate(df, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_boolean_headers(self, _tfs_booleans_file, validation_mode):
        df = read_tfs(_tfs_booleans_file)
        with pytest.raises(
            MADXCompatibilityError,
            match="TFS-Headers can not contain boolean values in MAD-X compatibility mode",
        ):
            validate(df, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_complex_headers(self, _tfs_complex_file, validation_mode):
        df = read_tfs(_tfs_complex_file)
        with pytest.raises(
            MADXCompatibilityError,
            match="TFS-Headers can not contain complex values in MAD-X compatibility mode",
        ):
            validate(df, compatibility=validation_mode)

    @pytest.mark.parametrize("validation_mode", ["madx", "mad-x", "mAd-X"])
    def test_madx_validation_raises_on_none_headers(self, _tfs_dataframe, validation_mode):
        df = _tfs_dataframe
        df.headers["NONEVALUE"] = None
        with pytest.raises(
            MADXCompatibilityError,
            match="TFS-Headers can not contain 'None' values in MAD-X compatibility mode",
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
