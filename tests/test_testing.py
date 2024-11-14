import pytest

from tfs.frame import TfsDataFrame
from tfs.testing import assert_tfs_frame_equal


class TestAssertTfsDataFrameEqual:

    def test_no_headers_equal(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        assert_tfs_frame_equal(df1, df1)  # we expect True

    def test_no_headers_different_data(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df2 = TfsDataFrame({"a": [1, 2, 2], "b": [4, 5, 6]})
        with pytest.raises(AssertionError):
            assert_tfs_frame_equal(df1, df2)

    def test_no_headers_different_order(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df2 = TfsDataFrame({"b": [4, 5, 6], "a": [1, 2, 3]})
        with pytest.raises(AssertionError):
            assert_tfs_frame_equal(df1, df2)
        assert_tfs_frame_equal(df1, df2, check_like=True)

    def test_with_headers_equal(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        df2 = TfsDataFrame({"b": [4, 5, 6], "a": [1, 2, 3]}, headers={"a": "a", "b": "b"})
        assert_tfs_frame_equal(df1, df1)
        with pytest.raises(AssertionError):
            assert_tfs_frame_equal(df1, df2)
        assert_tfs_frame_equal(df1, df2, check_like=True)

    def test_with_headers_different_data(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        df2 = TfsDataFrame({"a": [1, 2, 2], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        with pytest.raises(AssertionError):
            assert_tfs_frame_equal(df1, df2)

    def test_with_headers_different_datatypes(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        df2 = TfsDataFrame({"a": [1, 2, 3], "b": ["4", "5", "6"]}, headers={"a": "a", "b": "b"})
        with pytest.raises(AssertionError):
            assert_tfs_frame_equal(df1, df2)

        df3 = TfsDataFrame({"a": [1.0, 2.0, 3.0], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        with pytest.raises(AssertionError) as e:
            assert_tfs_frame_equal(df1, df3)
        assert "dtype" in str(e)

    def test_with_headers_different_headers_values(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        df2 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "c"})
        with pytest.raises(AssertionError) as e:
            assert_tfs_frame_equal(df1, df2)
        assert "b != c" in str(e)

        with pytest.raises(AssertionError) as e:
            assert_tfs_frame_equal(df1, df2, compare_keys=False)
        assert "b != c" in str(e)

    def test_with_headers_different_headers_keys(self):
        df1 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "b"})
        df2 = TfsDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, headers={"a": "a", "b": "b", "c": "c"})
        with pytest.raises(AssertionError):
            assert_tfs_frame_equal(df1, df2)  # `compare_keys=True` is default

        # compare only common keys ---
        assert_tfs_frame_equal(df1, df2, compare_keys=False)
