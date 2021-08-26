import pathlib
from collections import OrderedDict

import pytest

import tfs
from tfs.frame import TfsDataFrame, concat, merge_headers, validate

CURRENT_DIR = pathlib.Path(__file__).parent


class TestFailures:
    def test_validate_raises_on_wrong_unique_behavior(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(KeyError):
            validate(df, "", non_unique_behavior="invalid")

    @pytest.mark.parametrize("how", ["invalid", "not_left", "not_right"])
    def test_merge_headers_raises_on_invalid_how_key(self, caplog, how):
        headers_left = OrderedDict()
        headers_right = OrderedDict()

        with pytest.raises(ValueError):
            merge_headers(headers_left, headers_right, how=how)


class TestHeadersMerging:
    @pytest.mark.parametrize("how", ["left", "LEFT", "Left", "lEfT"])  # we're case-insensitive
    def test_headers_merging_left(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how):
        headers_left = tfs.read(_tfs_file_x_pathlib).headers
        headers_right = tfs.read(_tfs_file_y_pathlib).headers
        result = merge_headers(headers_left, headers_right, how=how)

        assert isinstance(result, OrderedDict)
        assert len(result) >= len(headers_left) and len(result) >= len(headers_right)  # no key disappeared
        for key in result:  # check that we prioritized headers_left's contents
            if key in headers_left and key in headers_right:
                assert result[key] == headers_left[key]

    @pytest.mark.parametrize("how", ["right", "RIGHT", "Right", "RigHt"])  # we're case-insensitive
    def test_headers_merging_right(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how):
        headers_left = tfs.read(_tfs_file_x_pathlib).headers
        headers_right = tfs.read(_tfs_file_y_pathlib).headers
        result = merge_headers(headers_left, headers_right, how=how)

        assert isinstance(result, OrderedDict)
        assert len(result) >= len(headers_left) and len(result) >= len(headers_right)  # no key disappeared
        for key in result:  # check that we prioritized headers_right's contents
            if key in headers_left and key in headers_right:
                assert result[key] == headers_right[key]

    @pytest.mark.parametrize("how", [None, "none", "None", "nOnE"])  # we're case-insensitive
    def test_headers_merging_none_returns_empty_dict(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how):
        headers_left = tfs.read(_tfs_file_x_pathlib).headers
        headers_right = tfs.read(_tfs_file_y_pathlib).headers
        result = merge_headers(headers_left, headers_right, how=how)
        assert result == OrderedDict()  # giving None returns empty headers

    def test_providing_new_headers_overrides_merging(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib):
        dframe_x = tfs.read(_tfs_file_x_pathlib)
        dframe_y = tfs.read(_tfs_file_y_pathlib)

        assert dframe_x.append(other=dframe_y, new_headers={}).headers == OrderedDict()
        assert dframe_y.append(other=dframe_x, new_headers={}).headers == OrderedDict()

        # we provide lsuffix (or rsuffix) since dframes have the same columns
        assert dframe_x.join(other=dframe_y, lsuffix="_l", new_headers={}).headers == OrderedDict()
        assert dframe_y.join(other=dframe_x, lsuffix="_l", new_headers={}).headers == OrderedDict()

        assert dframe_x.merge(right=dframe_y, new_headers={}).headers == OrderedDict()
        assert dframe_y.merge(right=dframe_x, new_headers={}).headers == OrderedDict()


class TestPrinting:
    def test_header_print(self):
        headers = {"param": 3, "other": "hello"}
        df = TfsDataFrame(headers=headers)
        print_out = str(df)
        assert "Headers" in print_out

        for key, val in headers.items():
            assert key in print_out
            assert str(val) in print_out


# TODO: Write the following. Check that result is a TfsDataFrame. Check that headers behave properly. Check
#  that data part is similar to pd.DataFrame(tfsdframe).append(...)/.join(...)/.merge(...)
class TestTfsDataFrameAppending:
    pass


class TestTfsDataFrameJoining:
    pass


class TestTfsDataFrameMerging:
    pass


class TestTfsDataFramesConcatenating:
    pass


# ------ Fixtures ------ #


@pytest.fixture()
def _tfs_file_x_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"


@pytest.fixture()
def _tfs_file_y_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"
