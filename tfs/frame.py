"""
Frame
-------------------

Contains the class definition of a ``TfsDataFrame``, inherited from the ``pandas`` ``DataFrame``, as well
as a utility function to validate the correctness of a ``TfsDataFrame``.
"""
import logging
from collections import OrderedDict
from contextlib import suppress
from functools import partial, reduce
from typing import Sequence, Union

import numpy as np
import pandas as pd

from tfs.errors import TfsFormatError

LOGGER = logging.getLogger(__name__)


class TfsDataFrame(pd.DataFrame):
    """
    Class to hold the information of the built an extended ``pandas`` ``DataFrame``, together with a way
    of getting the headers of the **TFS** file. The file headers are stored in a dictionary upon read.
    To get a header value use ``data_frame["header_name"]``.
    """

    _metadata = ["headers"]

    def __init__(self, *args, **kwargs):
        self.headers = {}
        with suppress(IndexError, AttributeError):
            self.headers = args[0].headers
        self.headers = kwargs.pop("headers", self.headers)
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: object) -> object:
        try:
            return super().__getitem__(key)
        except KeyError as error:
            try:
                return self.headers[key]
            except KeyError:
                raise KeyError(f"{key} is neither in the DataFrame nor in headers.")
            except TypeError:
                raise error

    def __getattr__(self, name: str) -> object:
        try:
            return super().__getattr__(name)
        except AttributeError:
            try:
                return self.headers[name]
            except KeyError:
                raise AttributeError(f"{name} is neither in the DataFrame nor in headers.")

    @property
    def _constructor(self):
        return TfsDataFrame

    def __repr__(self) -> str:
        space: str = " " * 4

        def _str_items(items_list: Sequence[str]) -> str:
            return "\n".join(f"{space}{k}: {v}" for k, v in items_list)

        s: str = ""
        if len(self.headers):
            s += "Headers:\n"
            if len(self.headers) > 7:
                items = list(self.headers.items())
                s += f"{_str_items(items[:3])}\n{space}...\n{_str_items(items[-3:])}\n"
            else:
                s += f"{_str_items(self.headers.items())}\n"
            s += "\n"
        return f"{s}{super().__repr__()}"

    def append(
        self, other: "TfsDataFrame", how_headers: str = None, new_headers: dict = None, **kwargs
    ) -> "TfsDataFrame":
        """
        Append rows of the other ``TfsDataFrame`` to the end of caller, returning a new object. Data
        manipulation is done by the ``pandas.Dataframe`` method of the same name. Resulting new_headers are
        either merged according to the provided **how_headers** method or as given via **new_headers**.

        Args:
            other (TfsDataFrame): The ``TfsDataFrame`` to append to the caller.
            how_headers (str): TODO. Defaults to None so that you can provide new_headers instead.
            new_headers (dict): If provided, will be used as new_headers for the merged ``TfsDataFrame``.
                Otherwise these are determined by merging the headers from the caller and the other
                ``TfsDataFrame`` according to the method defined by the **how_headers** argument.

        Keyword Args:
            Any keyword argument is given to ``pandas.DataFrame.append()``. The default values for all these
            parameters are left as set in the ``pandas`` codebase. To see these, refer to the pandas
            [DataFrame.append documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.append.html).

        Returns:
            A new ``TfsDataFrame`` with the appended data and merged headers.
        """
        LOGGER.debug("Appending data through 'pandas'")
        dframe = super().append(other, **kwargs)

        LOGGER.debug("Determining headers")
        new_headers = (
            new_headers
            if new_headers is not None
            else merge_headers(self.headers, other.headers, how=how_headers)
        )
        return TfsDataFrame(data=dframe, headers=new_headers)

    def join(
        self, other: "TfsDataFrame", how_headers: str = None, new_headers: dict = None, **kwargs
    ) -> "TfsDataFrame":
        """
        Join columns of another ``TfsDataFrame``. Data manipulation is done by the ``pandas.Dataframe``
        method of the same name. Resulting new_headers are either merged according to the provided
        **how_headers** method or as given via **new_headers**.

        Args:
            other (TfsDataFrame): The ``TfsDataFrame`` to join into the caller.
            how_headers (str): TODO. Defaults to None so that you can provide new_headers instead.
            new_headers (dict): If provided, will be used as new_headers for the merged ``TfsDataFrame``.
                Otherwise these are determined by merging the headers from the caller and the other
                ``TfsDataFrame`` according to the method defined by the **how_headers** argument.

        Keyword Args:
            Any keyword argument is given to ``pandas.DataFrame.join()``. The default values for all these
            parameters are left as set in the ``pandas`` codebase. To see these, refer to the pandas
            [DataFrame.join documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.join.html).

        Returns:
            A new ``TfsDataFrame`` with the joined columns and merged headers.
        """
        LOGGER.debug("Joining data through 'pandas'")
        dframe = super().join(other, **kwargs)

        LOGGER.debug("Determining headers")
        new_headers = (
            new_headers
            if new_headers is not None
            else merge_headers(self.headers, other.headers, how=how_headers)
        )
        return TfsDataFrame(data=dframe, headers=new_headers)

    def merge(
        self, right: "TfsDataFrame", how_headers: str = None, new_headers: dict = None, **kwargs
    ) -> "TfsDataFrame":
        """
        Merge ``TfsDataFrame`` objects with a database-style join. Data manipulation is done by the
        ``pandas.Dataframe`` method of the same name. Resulting new_headers are either merged according to the
        provided **how_headers** method or as given via **new_headers**.

        Args:
            right (TfsDataFrame): The ``TfsDataFrame`` to merge with the caller.
            how_headers (str): TODO. Defaults to None so that you can provide new_headers instead.
            new_headers (dict): If provided, will be used as headers for the merged ``TfsDataFrame``.
                Otherwise these are determined by merging the headers from the caller and the other
                ``TfsDataFrame`` according to the method defined by the **how_headers** argument.

        Keyword Args:
            Any keyword argument is given to ``pandas.DataFrame.merge()``. The default values for all these
            parameters are left as set in the ``pandas`` codebase. To see these, refer to the pandas
            [DataFrame.merge documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.merge.html).

        Returns:
            A new ``TfsDataFrame`` with the merged data and merged headers.
        """
        LOGGER.debug("Merging data through 'pandas'")
        dframe = super().merge(right, **kwargs)

        LOGGER.debug("Determining headers")
        new_headers = (
            new_headers
            if new_headers is not None
            else merge_headers(self.headers, right.headers, how=how_headers)
        )
        return TfsDataFrame(data=dframe, headers=new_headers)


def merge_headers(headers_left: dict, headers_right: dict, how: str) -> OrderedDict:
    """
    Merge new_headers of two ``TfsDataFrames`` together.

    Args:
        headers_left (dict): TODO.
        headers_right (dict): TODO.
        how (str): Type of merge to be performed, either **left** or **right**. If **left*, prioritize keys
            from **headers_left** in case of duplicate keys. If **right**, prioritize keys from
            **headers_right** in case of duplicate keys. Case insensitive.

    Returns:
        A new ``OrderedDict`` as the merge of the two provided dictionaries.
    """
    accepted_merges: Set[str] = {"left", "right"}
    if how.lower() not in accepted_merges:
        raise ValueError(f"Invalid 'how' argument, should be one of {accepted_merges}")
    LOGGER.debug(f"Merging headers with method '{how}'")
    if how.lower() == "left":  # we prioritize the contents of headers_left
        result = headers_right.copy()
        result.update(headers_left)
    else:  # we prioritize the contents of headers_right
        result = headers_left.copy()
        result.update(headers_right)
    return OrderedDict(result)  # so that the TfsDataFrame still has an OrderedDict as header


def concat(
    objs: Sequence[TfsDataFrame],
    how_headers: str,
    new_headers: dict = None,
    **kwargs,
) -> TfsDataFrame:
    """
    Concatenate ``TfsDataFrame`` objects along a particular axis with optional set logic along the other
    axes. Data manipulation is done by the ``pandas.concat`` function. Resulting new_headers are either
    merged according to the provided **how_headers** method or as given via **new_headers**.

    Args:
        objs (Sequence[TfsDataFrame]): the ``TfsDataFrame`` objects to be concatenated.
        how_headers (str): TODO.
        new_headers (dict): If provided, will be used as headers for the merged ``TfsDataFrame``.
            Otherwise these are determined by successively merging the headers from all concatenated
            ``TfsDataFrames`` according to the method defined by the **how_headers** argument.

    Keyword Args:
        Any keyword argument is given to ``pandas.concat()``. The default values for all these parameters
        are left as set in the ``pandas`` codebase. To see these, refer to the [pandas.concat
        documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.concat.html).

    Returns:
        A new ``TfsDataFrame`` with the merged data and merged headers.
    """
    LOGGER.debug("Concatenating data through 'pandas'")
    dframe = pd.concat(objs, **kwargs)

    LOGGER.debug("Determining headers")
    merger = partial(merge_headers, how=how_headers)  # so we can reduce on all objs, and use 'how_headers'
    new_headers = new_headers if new_headers is not None else reduce(merger, objs)
    return TfsDataFrame(data=dframe, headers=new_headers)


def validate(
    data_frame: Union[TfsDataFrame, pd.DataFrame],
    info_str: str = "",
    non_unique_behavior: str = "warn",
) -> None:
    """
    Check if a data frame contains finite values only, strings as column names and no empty new_headers
    or column names.

    Args:
        data_frame (Union[TfsDataFrame, pd.DataFrame]): the dataframe to check on.
        info_str (str): additional information to includ in logging statements.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
    """
    if non_unique_behavior.lower() not in ("warn", "raise"):
        raise KeyError("Invalid value for parameter 'validate_unique'")

    def is_not_finite(x):
        try:
            return ~np.isfinite(x)
        except TypeError:  # most likely string
            try:
                return np.zeros(x.shape, dtype=bool)
            except AttributeError:  # single entry
                return np.zeros(1, dtype=bool)

    boolean_df = data_frame.applymap(is_not_finite)

    if boolean_df.to_numpy().any():
        LOGGER.warning(
            f"DataFrame {info_str} contains non-physical values at Index: "
            f"{boolean_df.index[boolean_df.any(axis='columns')].tolist()}"
        )

    if data_frame.index.has_duplicates:
        LOGGER.warning("Non-unique indices found.")
        if non_unique_behavior.lower() == "raise":
            raise TfsFormatError("The dataframe contains non-unique indices")

    if data_frame.columns.has_duplicates:
        LOGGER.warning("Non-unique column names found.")
        if non_unique_behavior.lower() == "raise":
            raise TfsFormatError("The dataframe contains non-unique columns.")

    if any(not isinstance(c, str) for c in data_frame.columns):
        LOGGER.error(f"Some column-names are not of string-type, dataframe {info_str} is invalid.")
        raise TfsFormatError("TFS-Columns need to be strings.")

    if any(" " in c for c in data_frame.columns):
        LOGGER.error(f"Space(s) found in TFS columns, dataframe {info_str} is invalid")
        raise TfsFormatError("TFS-Columns can not contain spaces.")

    if hasattr(data_frame, "headers") and any(" " in h for h in data_frame.headers.keys()):
        LOGGER.error(f"Space(s) found in TFS header names, dataframe {info_str} is invalid")
        raise TfsFormatError("TFS-Header names can not contain spaces.")

    LOGGER.debug(f"DataFrame {info_str} validated")
