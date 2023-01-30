"""
Frame
-----

Contains the class definition of a ``TfsDataFrame``, inherited from the ``pandas`` ``DataFrame``, as well
as a utility function to validate the correctness of a ``TfsDataFrame``.
"""
import logging
from collections import OrderedDict
from contextlib import suppress
from functools import partial, reduce
from typing import Sequence, Set, Union

import numpy as np
import pandas as pd

from tfs.errors import TfsFormatError

LOGGER = logging.getLogger(__name__)


class TfsDataFrame(pd.DataFrame):
    """
    Class to hold the information of the built an extended ``pandas`` ``DataFrame``, together with a way
    of getting the headers of the **TFS** file. The file headers are stored in a dictionary upon read.
    To get a header value use ``data_frame.headers["header_name"]``, or ``data_frame["header_name"]`` if
    it does not conflict with a column name in the dataframe.
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

    def _headers_repr(self) -> str:
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
        return s

    def __repr__(self) -> str:
        headers_string = self._headers_repr()
        return f"{headers_string}{super().__repr__()}"

    def append(
        self,
        other: Union["TfsDataFrame", pd.DataFrame],
        how_headers: str = None,
        new_headers: dict = None,
        **kwargs,
    ) -> "TfsDataFrame":
        """
        Append rows of the other ``TfsDataFrame`` to the end of caller, returning a new object. Data
        manipulation is done by the ``pandas.Dataframe`` method of the same name. Resulting headers are
        either merged according to the provided **how_headers** method or as given via **new_headers**.

        Args:
            other (Union[TfsDataFrame, pd.DataFrame]): The ``TfsDataFrame`` to append to the caller.
            how_headers (str): Type of merge to be performed for the headers. Either **left** or **right**.
                Refer to :func:`tfs.frame.merge_headers` for behavior. If ``None`` is provided and
                **new_headers** is not provided, the final headers will be empty. Case insensitive,
                defaults to ``None``.
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
        if not hasattr(other, "headers"):
            LOGGER.debug("Converting 'other' to TfsDataFrame for appending")
            other = TfsDataFrame(other)  # so we accept pandas.DataFrame input here

        dframe = super().append(other, **kwargs)

        LOGGER.debug("Determining headers")
        new_headers = (
            new_headers
            if new_headers is not None
            else merge_headers(self.headers, other.headers, how=how_headers)
        )
        return TfsDataFrame(data=dframe, headers=new_headers)

    def join(
        self,
        other: Union["TfsDataFrame", pd.DataFrame],
        how_headers: str = None,
        new_headers: dict = None,
        **kwargs,
    ) -> "TfsDataFrame":
        """
        Join columns of another ``TfsDataFrame``. Data manipulation is done by the ``pandas.Dataframe``
        method of the same name. Resulting headers are either merged according to the provided
        **how_headers** method or as given via **new_headers**.

        Args:
            other (Union[TfsDataFrame, pd.DataFrame]): The ``TfsDataFrame`` to join into the caller.
            how_headers (str): Type of merge to be performed for the headers. Either **left** or **right**.
                Refer to :func:`tfs.frame.merge_headers` for behavior. If ``None`` is provided and
                **new_headers** is not provided, the final headers will be empty. Case insensitive,
                defaults to ``None``.
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
        if not hasattr(other, "headers"):
            LOGGER.debug("Converting 'other' to TfsDataFrame for joining")
            other = TfsDataFrame(other)  # so we accept pandas.DataFrame input here
        dframe = super().join(other, **kwargs)

        LOGGER.debug("Determining headers")
        new_headers = (
            new_headers
            if new_headers is not None
            else merge_headers(self.headers, other.headers, how=how_headers)
        )
        return TfsDataFrame(data=dframe, headers=new_headers)

    def merge(
        self,
        right: Union["TfsDataFrame", pd.DataFrame],
        how_headers: str = None,
        new_headers: dict = None,
        **kwargs,
    ) -> "TfsDataFrame":
        """
        Merge ``TfsDataFrame`` objects with a database-style join. Data manipulation is done by the
        ``pandas.Dataframe`` method of the same name. Resulting headers are either merged according to the
        provided **how_headers** method or as given via **new_headers**.

        Args:
            right (Union[TfsDataFrame, pd.DataFrame]): The ``TfsDataFrame`` to merge with the caller.
            how_headers (str): Type of merge to be performed for the headers. Either **left** or **right**.
                Refer to :func:`tfs.frame.merge_headers` for behavior. If ``None`` is provided and
                **new_headers** is not provided, the final headers will be empty. Case insensitive,
                defaults to ``None``.
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
        if not hasattr(right, "headers"):
            LOGGER.debug("Converting 'right' to TfsDataFrame for merging")
            right = TfsDataFrame(right)  # so we accept pandas.DataFrame input here
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
    Merge headers of two ``TfsDataFrames`` together.

    Args:
        headers_left (dict): Headers of caller (left) ``TfsDataFrame`` when calling ``.append``, ``.join`` or
            ``.merge``. Headers of the left (preceeding) ``TfsDataFrame`` when calling ``tfs.frame.concat``.
        headers_right (dict): Headers of other (right) ``TfsDataFrame`` when calling ``.append``, ``.join``
            or ``.merge``. Headers of the left (preceeding) ``TfsDataFrame`` when calling
            ``tfs.frame.concat``.
        how (str): Type of merge to be performed, either **left** or **right**. If **left*, prioritize keys
            from **headers_left** in case of duplicate keys. If **right**, prioritize keys from
            **headers_right** in case of duplicate keys. Case insensitive. If ``None`` is given,
            an empty dictionary will be returned.

    Returns:
        A new ``OrderedDict`` as the merge of the two provided dictionaries.
    """
    accepted_merges: Set[str] = {"left", "right", "none"}
    if str(how).lower() not in accepted_merges:  # handles being given None
        raise ValueError(f"Invalid 'how' argument, should be one of {accepted_merges}")

    LOGGER.debug(f"Merging headers with method '{how}'")
    if str(how).lower() == "left":  # we prioritize the contents of headers_left
        result = headers_right.copy()
        result.update(headers_left)
    elif str(how).lower() == "right":  # we prioritize the contents of headers_right
        result = headers_left.copy()
        result.update(headers_right)
    else:  # we were given None, result will be an empty dict
        result = {}
    return OrderedDict(result)  # so that the TfsDataFrame still has an OrderedDict as header


def concat(
    objs: Sequence[Union[TfsDataFrame, pd.DataFrame]],
    how_headers: str = None,
    new_headers: dict = None,
    **kwargs,
) -> TfsDataFrame:
    """
    Concatenate ``TfsDataFrame`` objects along a particular axis with optional set logic along the other
    axes. Data manipulation is done by the ``pandas.concat`` function. Resulting headers are either
    merged according to the provided **how_headers** method or as given via **new_headers**.

    .. warning::
        Please note that when using this function on many ``TfsDataFrames``, leaving the contents of the
        final headers dictionary to the automatic merger can become unpredictable. In this case it is
        recommended to provide the **new_headers** argument to ensure the final result, or leave both
        **how_headers** and **new_headers** as ``None`` (their defaults) to end up with empty headers.

    Args:
        objs (Sequence[Union[TfsDataFrame, pd.DataFrame]]): the ``TfsDataFrame`` objects to be concatenated.
        how_headers (str): Type of merge to be performed for the headers. Either **left** or **right**.
            Refer to :func:`tfs.frame.merge_headers` for behavior. If ``None`` is provided and
            **new_headers** is not provided, the final headers will be empty. Case insensitive, defaults to
            ``None``.
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
    objs = [dframe if hasattr(dframe, "headers") else TfsDataFrame(dframe) for dframe in objs]
    dframe = pd.concat(objs, **kwargs)

    LOGGER.debug("Determining headers")
    merger = partial(merge_headers, how=how_headers)  # so we can reduce on all objs, and use 'how_headers'
    all_headers = (tfsdframe.headers for tfsdframe in objs)
    new_headers = new_headers if new_headers is not None else reduce(merger, all_headers)
    return TfsDataFrame(data=dframe, headers=new_headers)


def validate(
    data_frame: Union[TfsDataFrame, pd.DataFrame],
    info_str: str = "",
    non_unique_behavior: str = "warn",
) -> None:
    """
    Check if a data frame contains finite values only, strings as column names and no empty headers
    or column names.

    .. admonition:: **Methodology**

        This function performs several different checks on the provided dataframe:
         1. Checking no single element is a `list` or `tuple`, which is done with a 
            custom vectorized function applied column-by-column on the dataframe.
         2. Checking for non-physical values in the dataframe, which is done by
            applying the ``isna`` function with the right option context.
         3. Checking for duplicates in either indices or columns.
         4. Checking for column names that are not strings.
         5. Checking for column names including spaces.


    Args:
        data_frame (Union[TfsDataFrame, pd.DataFrame]): the dataframe to check on.
        info_str (str): additional information to include in logging statements.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
    """
    if non_unique_behavior.lower() not in ("warn", "raise"):
        raise KeyError("Invalid value for parameter 'non_unique_behavior'")

    # ----- Check that no element is a list / tuple in the dataframe ----- #
    def _element_is_list(element):
        return isinstance(element, (list, tuple))
    _element_is_list = np.vectorize(_element_is_list)

    list_or_tuple_bool_df = data_frame.apply(_element_is_list)
    if list_or_tuple_bool_df.to_numpy().any():
        LOGGER.error(
            f"DataFrame {info_str} contains list/tuple values at Index: "
            f"{list_or_tuple_bool_df.index[list_or_tuple_bool_df.any(axis='columns')].tolist()}"
        )
        raise TfsFormatError("Lists or tuple elements are not accepted in a TfsDataFrame")

    # -----  Check that no element is non-physical value in the dataframe ----- #
    with pd.option_context('mode.use_inf_as_na', True):
        inf_or_nan_bool_df = data_frame.isna()

    if inf_or_nan_bool_df.to_numpy().any():
        LOGGER.warning(
            f"DataFrame {info_str} contains non-physical values at Index: "
            f"{inf_or_nan_bool_df.index[inf_or_nan_bool_df.any(axis='columns')].tolist()}"
        )

    # Other sanity checks
    if data_frame.index.has_duplicates:
        LOGGER.warning("Non-unique indices found.")
        if non_unique_behavior.lower() == "raise":
            raise TfsFormatError("The dataframe contains non-unique indices")

    if data_frame.columns.has_duplicates:
        LOGGER.warning("Non-unique column names found.")
        if non_unique_behavior.lower() == "raise":
            raise TfsFormatError("The dataframe contains non-unique columns.")

    # The following are deal-breakers for the TFS format and would not, for instance, be accepted by MAD-X
    if any(not isinstance(c, str) for c in data_frame.columns):
        LOGGER.debug(f"Some column-names are not of string-type, dataframe {info_str} is invalid.")
        raise TfsFormatError("TFS-Columns need to be strings.")

    if any(" " in c for c in data_frame.columns):
        LOGGER.debug(f"Space(s) found in TFS columns, dataframe {info_str} is invalid")
        raise TfsFormatError("TFS-Columns can not contain spaces.")

    LOGGER.debug(f"DataFrame {info_str} validated")
