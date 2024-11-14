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


def assert_tfs_frame_equal(
    df1: TfsDataFrame, df2: TfsDataFrame, compare_keys: bool = True, **kwargs
):
    """
    Compare two `TfsDataFrame` objects, with `df1` being the reference
    that `df2` is compared to. This is mostly intended for unit tests.
    Comparison is done on both the contents of the headers dictionaries
    (with `pandas`'s `assert_dict_equal`) as well as the data itself
    (with `pandas`'s `assert_frame_equal`).

    .. note::
        The `compare_keys` argument is inherited from `pandas`'s
        `assert_dict_equal` function and is quite unintuitive. It
        means to check that both dictionaries have *the exact same
        set of keys*.

        Whether this is given as `True` or `False`, the values are
        compared anyway for all keys in the first (reference) dict.
        In the case of this helper function, all keys present in
        `df1`'s headers will be checked for in `df2`'s headers and
        their corresponding values compared. If given as `True`,
        then both headers should be the exact same dictionary.

    Args:
        df1 (TfsDataFrame): The first `TfsDataFrame` to compare.
        df2 (TfsDataFrame): The second `TfsDataFrame` to compare.
        compare_keys (bool): If `True`, checks that both headers
            have the exact same set of keys. See the above note
            for exact meaning and caveat. Defaults to `True`.
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
    assert_dict_equal(df1.headers, df2.headers, compare_keys=compare_keys)
