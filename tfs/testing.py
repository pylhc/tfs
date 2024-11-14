"""
Testing
-------

Testing functionalty for TfsDataFrames.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

if TYPE_CHECKING:
    from tfs.frame import TfsDataFrame


# ----- Helpers ----- #


def assert_tfs_frame_equal(df1: TfsDataFrame, df2: TfsDataFrame, **kwargs):
    """
    Assert that two `TfsDataFrame` objects are equal,
    comparing both the contents of the headers dictionaries
    as well as the data.

    Args:
        df1 (TfsDataFrame): The first `TfsDataFrame` to compare.
        df2 (TfsDataFrame): The second `TfsDataFrame` to compare.
        **kwargs: Additional keyword arguments are transmitted to
        `pandas.testing.assert_frame_equal` for the comparison of
        the dataframe parts themselves.
    
    Example:
        .. code-block:: python

            reference_df = tfs.read("path/to/file.tfs")
            new_df = some_function(*args, **kwargs)
            assert_tfs_frame_equal(reference_df, new_df)
    """
    assert_frame_equal(df1, df2, **kwargs)
    assert_dict_equal(df1.headers, df2.headers, compare_keys=True)
