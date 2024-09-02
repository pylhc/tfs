import pathlib
from functools import partial, reduce

import pandas as pd
import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

import tfs
from tfs.frame import TfsDataFrame, concat, merge_headers

CURRENT_DIR = pathlib.Path(__file__).parent


class TestFailures:
    @pytest.mark.parametrize("how", ["invalid", "not_left", "not_right"])
    def test_merge_headers_raises_on_invalid_how_key(self, how):
        headers_left = {}
        headers_right = {}

        with pytest.raises(ValueError, match="Invalid 'how' argument"):
            merge_headers(headers_left, headers_right, how=how)

    def test_access_errors(self):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"], headers={"HEADER": 10})
        with pytest.raises(AttributeError):
            _ = df.does_not_exist

        with pytest.raises(KeyError):
            _ = df["does also not exist"]

        with pytest.raises(KeyError):  # raises KeyError in pandas, TypeError in dict
            _ = df[[1, 2, 3]]


class TestTfsDataFrameMerging:
    @pytest.mark.parametrize("how_headers", [None, "left", "right"])
    @pytest.mark.parametrize("how", ["left", "right", "outer", "inner"])
    @pytest.mark.parametrize("on", ["NAME", "S", "NUMBER", "CO", "CORMS", "BPM_RES"])
    def test_correct_merging(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how_headers, how, on):
        dframe_x = tfs.read(_tfs_file_x_pathlib)
        dframe_y = tfs.read(_tfs_file_y_pathlib)
        result = dframe_x.merge(dframe_y, how_headers=how_headers, how=how, on=on)

        assert isinstance(result, TfsDataFrame)
        assert isinstance(result.headers, dict)
        assert_dict_equal(result.headers, merge_headers(dframe_x.headers, dframe_y.headers, how=how_headers))
        assert_frame_equal(result, pd.DataFrame(dframe_x).merge(pd.DataFrame(dframe_y), how=how, on=on))

    @pytest.mark.parametrize("how_headers", [None, "left", "right"])
    @pytest.mark.parametrize("how", ["left", "right", "outer", "inner"])
    @pytest.mark.parametrize("on", ["NAME", "S", "NUMBER", "CO", "CORMS", "BPM_RES"])
    def test_merging_accepts_pandas_dataframe(
        self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how_headers, how, on
    ):
        dframe_x = tfs.read(_tfs_file_x_pathlib)
        dframe_y = pd.DataFrame(tfs.read(_tfs_file_y_pathlib))  # for test, loses headers here
        result = dframe_x.merge(dframe_y, how_headers=how_headers, how=how, on=on)

        assert isinstance(result, TfsDataFrame)
        assert isinstance(result.headers, dict)

        # using empty dict here as it's what dframe_y is getting when converted in the call
        assert_dict_equal(result.headers, merge_headers(dframe_x.headers, headers_right={}, how=how_headers))
        assert_frame_equal(result, pd.DataFrame(dframe_x).merge(pd.DataFrame(dframe_y), how=how, on=on))


class TestHeadersMerging:
    @pytest.mark.parametrize("how", ["left", "LEFT", "Left", "lEfT"])  # we're case-insensitive
    def test_headers_merging_left(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how):
        headers_left = tfs.read(_tfs_file_x_pathlib).headers
        headers_right = tfs.read(_tfs_file_y_pathlib).headers
        result = merge_headers(headers_left, headers_right, how=how)

        assert isinstance(result, dict)
        assert len(result) >= len(headers_left)  # no key disappeared
        assert len(result) >= len(headers_right)  # no key disappeared
        for key in result:  # check that we prioritized headers_left's contents
            if key in headers_left and key in headers_right:
                assert result[key] == headers_left[key]

    @pytest.mark.parametrize("how", ["right", "RIGHT", "Right", "RigHt"])  # we're case-insensitive
    def test_headers_merging_right(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how):
        headers_left = tfs.read(_tfs_file_x_pathlib).headers
        headers_right = tfs.read(_tfs_file_y_pathlib).headers
        result = merge_headers(headers_left, headers_right, how=how)

        assert isinstance(result, dict)
        assert len(result) >= len(headers_left)  # no key disappeared
        assert len(result) >= len(headers_right)  # no key disappeared
        for key in result:  # check that we prioritized headers_right's contents
            if key in headers_left and key in headers_right:
                assert result[key] == headers_right[key]

    @pytest.mark.parametrize("how", [None, "none", "None", "nOnE"])  # we're case-insensitive
    def test_headers_merging_none_returns_empty_dict(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how):
        headers_left = tfs.read(_tfs_file_x_pathlib).headers
        headers_right = tfs.read(_tfs_file_y_pathlib).headers
        result = merge_headers(headers_left, headers_right, how=how)
        assert result == {}  # giving None returns empty headers

    def test_providing_new_headers_overrides_merging(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib):
        dframe_x = tfs.read(_tfs_file_x_pathlib)
        dframe_y = tfs.read(_tfs_file_y_pathlib)

        assert dframe_x.merge(right=dframe_y, new_headers={}).headers == {}
        assert dframe_y.merge(right=dframe_x, new_headers={}).headers == {}

        assert tfs.concat([dframe_x, dframe_y], new_headers={}).headers == {}
        assert tfs.concat([dframe_y, dframe_x], new_headers={}).headers == {}


class TestPrinting:
    def test_header_print(self):
        headers = {"param": 3, "other": "hello"}
        df = TfsDataFrame(headers=headers)
        print_out = str(df)
        assert "Headers" in print_out

        for key, val in headers.items():
            assert key in print_out
            assert str(val) in print_out

    def test_long_headers_print(self):
        headers = {"p1": 1, "p2": "hello", "p3": 3, "p4": 4, "p5": 5, "p6": 6, "p7": "string", "p8": "long"}
        df = TfsDataFrame(headers=headers)
        print_out = str(df)
        assert "Headers" in print_out

        # Check that the ellipsis worked
        assert not all(key in print_out for key in headers)
        assert not all(str(val) in print_out for val in headers.values())
        assert "..." in print_out

    def test_empty_headers_print(self):
        print_tfs = str(TfsDataFrame())
        print_df = str(pd.DataFrame())
        assert print_tfs == print_df.replace(pd.DataFrame.__name__, TfsDataFrame.__name__)


class TestTfsDataFramesConcatenating:
    @pytest.mark.parametrize("how_headers", [None, "left", "right"])
    @pytest.mark.parametrize("axis", [0, 1])
    @pytest.mark.parametrize("join", ["inner", "outer"])
    def test_correct_concatenating(self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how_headers, axis, join):
        dframe_x = tfs.read(_tfs_file_x_pathlib)
        dframe_y = tfs.read(_tfs_file_y_pathlib)
        objs = [dframe_x] * 4 + [dframe_y] * 4
        result = concat(objs, how_headers=how_headers, axis=axis, join=join)

        merger = partial(merge_headers, how=how_headers)
        all_headers = (tfsdframe.headers for tfsdframe in objs)
        assert isinstance(result, TfsDataFrame)
        assert isinstance(result.headers, dict)
        assert_dict_equal(result.headers, reduce(merger, all_headers))
        assert_frame_equal(result, pd.concat(objs, axis=axis, join=join))

    @pytest.mark.parametrize("how_headers", [None, "left", "right"])
    @pytest.mark.parametrize("axis", [0, 1])
    @pytest.mark.parametrize("join", ["inner", "outer"])
    def test_concatenating_accepts_pandas_dataframes(
        self, _tfs_file_x_pathlib, _tfs_file_y_pathlib, how_headers, axis, join
    ):
        dframe_x = tfs.read(_tfs_file_x_pathlib)
        dframe_y = pd.DataFrame(tfs.read(_tfs_file_y_pathlib))  # for test, loses headers here
        objs = [dframe_x] * 4 + [dframe_y] * 4  # now has a mix of TfsDataFrames and pandas.DataFrames
        result = concat(objs, how_headers=how_headers, axis=axis, join=join)

        merger = partial(merge_headers, how=how_headers)
        # all_headers = (tfsdframe.headers for tfsdframe in objs)
        assert isinstance(result, TfsDataFrame)
        assert isinstance(result.headers, dict)

        all_headers = [  # empty dicts here as it's what objects are getting when converted in the call
            dframe.headers if isinstance(dframe, TfsDataFrame) else {} for dframe in objs
        ]
        assert_dict_equal(result.headers, reduce(merger, all_headers))
        assert_frame_equal(result, pd.concat(objs, axis=axis, join=join))


# ------ Fixtures ------ #


@pytest.fixture
def _tfs_file_x_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"


@pytest.fixture
def _tfs_file_y_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs" / "file_x.tfs"
