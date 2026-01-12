"""
Frame
-----

Contains the class definition of a ``TfsDataFrame``, inherited from the ``pandas`` ``DataFrame``, as well
as a utility function to validate the correctness of a ``TfsDataFrame``.
"""

from __future__ import annotations  # for delayed type annotations

import logging
from contextlib import suppress
from functools import partial, reduce
from typing import TYPE_CHECKING, ClassVar

import numpy as np
import pandas as pd
from pandas.api import types as pdtypes

from tfs.constants import VALIDATION_MODES
from tfs.errors import (
    DuplicateColumnsError,
    DuplicateIndicesError,
    IterableInDataFrameError,
    MADXCompatibilityError,
    NonStringColumnNameError,
    SpaceinColumnNameError,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


LOGGER = logging.getLogger(__name__)


class TfsDataFrame(pd.DataFrame):
    """
    Class to hold the information of the built an extended `pandas.DataFrame`, together with a way
    of getting the headers of the **TFS** file. The file headers are stored in a dictionary upon read.
    To get a header value use ``data_frame.headers["header_name"]``, or ``data_frame["header_name"]`` if
    it does not conflict with a column name in the dataframe.
    """

    _metadata: ClassVar = ["headers"]

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
            except KeyError as kerror:
                errmsg = f"{key} is neither in the DataFrame nor in headers."
                raise KeyError(errmsg) from kerror
            except TypeError as terror:
                raise error from terror

    def __getattr__(self, name: str) -> object:
        try:
            return super().__getattr__(name)
        except AttributeError:
            try:
                return self.headers[name]
            except KeyError as error:
                errmsg = f"{name} is neither in the DataFrame nor in headers."
                raise AttributeError(errmsg) from error

    @property
    def _constructor(self):
        """Function called, whenever a new ``TfsDataFrame`` is created
        by pandas functionality, to ensure the new object is also a ``TfsDataFrame``.
        """
        return TfsDataFrame

    def _constructor_from_mgr(self, mgr, axes):
        """Initialize new ``TfsDataFrame`` from a dataframe manager.
        This function is needed since pandas v2.1.0 to ensure the new object
        given to __init__() already contains the headers.
        See https://github.com/pandas-dev/pandas/issues/55120"""
        obj = self._from_mgr(mgr, axes)
        obj.headers = {}
        return obj

    def _headers_repr(self) -> str:
        space: str = " " * 4

        def _str_items(items_list: Sequence[str]) -> str:
            return "\n".join(f"{space}{k}: {v}" for k, v in items_list)

        s: str = ""
        if len(self.headers):
            s += "Headers:\n"
            if len(self.headers) > 7:  # noqa: PLR2004
                items = list(self.headers.items())
                s += f"{_str_items(items[:3])}\n{space}...\n{_str_items(items[-3:])}\n"
            else:
                s += f"{_str_items(self.headers.items())}\n"
            s += "\n"
        return s

    def __repr__(self) -> str:
        headers_string = self._headers_repr()
        return f"{headers_string}{super().__repr__()}"

    def merge(
        self,
        right: TfsDataFrame | pd.DataFrame,
        how_headers: str | None = None,
        new_headers: dict | None = None,
        **kwargs,
    ) -> TfsDataFrame:
        """
        Merge ``TfsDataFrame`` objects with a database-style join. Data manipulation is done by the
        ``pandas.Dataframe`` method of the same name. Resulting headers are either merged according to the
        provided **how_headers** method or as given via **new_headers**.

        Args:
            right (TfsDataFrame | pd.DataFrame): The ``TfsDataFrame`` to merge with the caller.
            how_headers (str): Type of merge to be performed for the headers. Either **left** or **right**.
                Refer to `tfs.frame.merge_headers` for behavior. If ``None`` is provided and
                **new_headers** is not provided, the final headers will be empty. Case insensitive,
                defaults to ``None``.
            new_headers (dict): If provided, will be used as headers for the merged ``TfsDataFrame``.
                Otherwise these are determined by merging the headers from the caller and the other
                ``TfsDataFrame`` according to the method defined by the **how_headers** argument.
            **kwargs: Arguments for `pandas.DataFrame.merge`, with the same default values as set in
            the ``pandas`` codebase.

        Returns:
            A new ``TfsDataFrame`` with the merged data and merged headers.
        """
        LOGGER.debug("Merging data through 'pandas'")
        if not hasattr(right, "headers"):
            LOGGER.debug("Converting 'right' to TfsDataFrame for merging")
            right = TfsDataFrame(right)  # so we accept pandas.DataFrame input here
        dframe = super().merge(right, **kwargs)

        LOGGER.debug("Determining headers")
        # fmt: off
        new_headers = (
            new_headers
            if new_headers is not None
            else merge_headers(self.headers, right.headers, how=how_headers)
        )
        return TfsDataFrame(data=dframe, headers=new_headers)
        # fmt: on


def merge_headers(headers_left: dict, headers_right: dict, how: str) -> dict:
    """
    Merge headers of two ``TfsDataFrames`` together.

    Args:
        headers_left (dict): Headers of caller (left) ``TfsDataFrame`` when calling
            ``.append``, ``.join`` or ``.merge``. Headers of the left (preceeding)
            ``TfsDataFrame`` when calling ``tfs.frame.concat``.
        headers_right (dict): Headers of other (right) ``TfsDataFrame`` when calling
            ``.append``, ``.join`` or ``.merge``. Headers of the left (preceeding)
            ``TfsDataFrame`` when calling ``tfs.frame.concat``.
        how (str): Type of merge to be performed, either **left** or **right**. If
            **left**, prioritize keys from **headers_left** in case of duplicate keys.
            If **right**, prioritize keys from **headers_right** in case of duplicate
            keys. Case-insensitive. If ``None`` is given, an empty dictionary will be
            returned.

    Returns:
        A new dictionary as the merge of the two provided dictionaries.
    """
    accepted_merges: set[str] = {"left", "right", "none"}
    if str(how).lower() not in accepted_merges:  # handles being given None
        errmsg = f"Invalid 'how' argument, should be one of {accepted_merges}"
        raise ValueError(errmsg)

    LOGGER.debug(f"Merging headers with method '{how}'")
    if str(how).lower() == "left":  # we prioritize the contents of headers_left
        result: dict = headers_right.copy()
        result.update(headers_left)
    elif str(how).lower() == "right":  # we prioritize the contents of headers_right
        result: dict = headers_left.copy()
        result.update(headers_right)
    else:  # we were given None, result will be an empty dict
        result = {}
    return result


def concat(
    objs: Sequence[TfsDataFrame | pd.DataFrame],
    how_headers: str | None = None,
    new_headers: dict | None = None,
    **kwargs,
) -> TfsDataFrame:
    """
    Concatenate ``TfsDataFrame`` objects along a particular axis with optional set logic along the other
    axes. Data manipulation is done by the `pandas.concat` function. Resulting headers are either
    merged according to the provided **how_headers** method or as given via **new_headers**.

    .. warning::
        Please note that when using this function on many ``TfsDataFrames``, leaving the contents of the
        final headers dictionary to the automatic merger can become unpredictable. In this case it is
        recommended to provide the **new_headers** argument to ensure the final result, or leave both
        **how_headers** and **new_headers** as ``None`` (their defaults) to end up with empty headers.

    Args:
        objs (Sequence[TfsDataFrame | pd.DataFrame]): the ``TfsDataFrame`` objects to be concatenated.
        how_headers (str): Type of merge to be performed for the headers. Either **left** or **right**.
            Refer to `tfs.frame.merge_headers` for behavior. If ``None`` is provided and **new_headers**
            is not provided, the final headers will be empty. Case insensitive, defaults to ``None``.
        new_headers (dict): If provided, will be used as headers for the merged ``TfsDataFrame``.
            Otherwise these are determined by successively merging the headers from all concatenated
            ``TfsDataFrames`` according to the method defined by the **how_headers** argument.
        **kwargs: Any keyword argument is given to `pandas.concat`.

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
    data_frame: TfsDataFrame | pd.DataFrame,
    info_str: str = "",
    non_unique_behavior: str = "warn",
    compatibility: str = "madx",
) -> None:
    """
    Enforce validity rules on a `TfsDataFrame` (see admonition below).
    Additional checks are performed for compatibility with either ``MAD-X``
    or ``MAD-NG`` as provided by the `compatibility` parameter.

    .. admonition:: Methodology

        This function performs several different checks on the provided dataframe. The following
        checks are performed for all compatibility modes (``MAD-X`` and ``MAD-NG``):

          1. Checking no single element in the data is a `list` or `tuple`.
          2. Checking for non-physical values in the dataframe (uses `.isna()` with the right option context).
          3. Checking for duplicates in either indices or columns.
          4. Checking for column names that are not strings.
          5. Checking for column names including spaces.

        When checking for ``MAD-X`` compatibility, which is more restrictive than ``MAD-NG``,
        the following additional checks are performed:

          1. Checking the dataframe has headers.
          2. Checking no boolean values are in the dataframe headers.
          3. Checking no complex values are in the dataframe headers.
          4. Checking for a 'TYPE' entry is in the dataframe headers.
          5. Checking no boolean-dtype columns are in the dataframe.
          6. Checking no complex-dtype columns are in the dataframe.

    Args:
        data_frame (TfsDataFrame | pd.DataFrame): the dataframe to check on.
        info_str (str): additional information to include in logging statements.
        compatibility (str): Which code to check for compatibility with. Accepted values
            are `madx`, `mad-x`, `madng` and `mad-ng`, case-insensitive. Defauts to `madx`.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
    """
    if not isinstance(compatibility, str) or compatibility.lower() not in VALIDATION_MODES:
        errmsg = f"Invalid compatibility mode provided: '{compatibility}'."
        raise ValueError(errmsg)

    if non_unique_behavior.lower() not in ("warn", "raise"):
        errmsg = "Invalid value for parameter 'non_unique_behavior'."
        raise ValueError(errmsg)

    # ----- Check that no element is a list / tuple in the dataframe ----- #
    def _element_is_list(element):
        return isinstance(element, list | tuple)

    _element_is_list = np.vectorize(_element_is_list)

    list_or_tuple_bool_df = data_frame.apply(_element_is_list)
    if list_or_tuple_bool_df.to_numpy().any():
        LOGGER.error(
            f"DataFrame {info_str} contains list/tuple values at Index: "
            f"{list_or_tuple_bool_df.index[list_or_tuple_bool_df.any(axis='columns')].tolist()}"
        )
        raise IterableInDataFrameError

    # -----  Check that no element is non-physical value in the data and headers ----- #
    # The pd.option_context('mode.use_inf_as_na', True) context manager raises FutureWarning
    # and will likely disappear in pandas 3.0 so we replace 'inf' values by NaNs before calling
    # .isna(). Additionally, the downcasting behaviour of .replace() is deprecated and raises a
    # FutureWarning, so we use .infer_objects() first to attemps soft conversion to a better dtype
    # for object-dtype columns (which strings can be). Since .infer_objects() and .replace() return
    # (lazy for the former) copies we're not modifying the original dataframe during validation :)
    inf_or_nan_bool_df = data_frame.infer_objects().replace([np.inf, -np.inf], np.nan).isna()
    if inf_or_nan_bool_df.to_numpy().any():
        LOGGER.warning(
            f"DataFrame {info_str} contains non-physical values at Index: "
            f"{inf_or_nan_bool_df.index[inf_or_nan_bool_df.any(axis='columns')].tolist()}"
        )

    if (
        getattr(data_frame, "headers", None) is not None
        and pd.Series(data_frame.headers.values()).isna().any()
    ):
        LOGGER.warning(f"DataFrame {info_str} contains non-physical values in headers.")

    # ----- Other sanity checks ----- #
    # These are not deal-breakers but might raise
    # issues being read back by some other codes
    if data_frame.index.has_duplicates:
        LOGGER.warning("Non-unique indices found.")
        if non_unique_behavior.lower() == "raise":
            raise DuplicateIndicesError

    if data_frame.columns.has_duplicates:
        LOGGER.warning("Non-unique column names found.")
        if non_unique_behavior.lower() == "raise":
            raise DuplicateColumnsError

    # The following are deal-breakers for the TFS format,
    # but might be accepted by MAD-X or MAD-NG
    if any(not isinstance(c, str) for c in data_frame.columns):
        LOGGER.debug(f"Some column-names are not of string-type, dataframe {info_str} is invalid.")
        raise NonStringColumnNameError

    if any(" " in c for c in data_frame.columns):
        LOGGER.debug(f"Space(s) found in TFS columns, dataframe {info_str} is invalid")
        raise SpaceinColumnNameError

    # ----- Additional checks for MAD-X compatibility mode ----- #
    if compatibility.lower() in ("madx", "mad-x"):
        # MAD-X really wants a 'TYPE' header in the file, which is not possible to
        # enforce if there are no headers in the df (we can't add, we don't modify
        # and return the df in this function). In this case we error.
        if getattr(data_frame, "headers", None) is None:
            errmsg = "Headers should be present in MAD-X compatibility mode."
            raise MADXCompatibilityError(errmsg)

        # ----- Otherwise we can check the existing headers
        # Check that no boolean values are in the headers - MAD-X does not accept them
        if any(isinstance(header, bool) for header in data_frame.headers.values()):
            LOGGER.debug(
                f"Boolean values found in headers of dataframe {info_str}, which is incompatible with MAD-X. "
                "Change their types in order to keep compatibility with MAD-X."
            )
            errmsg = "TFS-Headers can not contain boolean values in MAD-X compatibility mode."
            raise MADXCompatibilityError(errmsg)

        # Check that no complex values are in the headers - MAD-X does not accept them
        if any(isinstance(header, complex) for header in data_frame.headers.values()):
            LOGGER.debug(
                f"Complex values found in headers of dataframe {info_str}, which is incompatible with MAD-X. "
                "Change their types in order to keep compatibility with MAD-X."
            )
            errmsg = "TFS-Headers can not contain complex values in MAD-X compatibility mode."
            raise MADXCompatibilityError(errmsg)

        # Check that no 'None' values are in the headers - it would
        # write as 'nil' which MAD-X does not accept
        if any(header is None for header in data_frame.headers.values()):
            LOGGER.debug(
                f"'None' values found in headers of dataframe {info_str}, which is incompatible with MAD-X. "
                "Remove them or assign a value in order to keep compatibility with MAD-X."
            )
            errmsg = "TFS-Headers can not contain 'None' values in MAD-X compatibility mode."
            raise MADXCompatibilityError(errmsg)

        # MAD-X will not accept back in a TFS file with no 'TYPE' entry in the headers (as string)
        if "TYPE" not in data_frame.headers:
            LOGGER.warning("MAD-X expects a 'TYPE' header in the TFS file, which is missing. Adding it.")
            data_frame.headers["TYPE"] = "Added by tfs-pandas for MAD-X compatibility"

        # ----- The following checks are regarding the data itself ----- #
        # Check that the dataframe contains no boolean dtype columns
        if any(pdtypes.is_bool_dtype(type_) for type_ in data_frame.dtypes):
            LOGGER.debug(
                f"Boolean dtype column found in dataframe {info_str}, which is incompatible with MAD-X. "
                "Change the column dtypes to keep compatibility with MAD-X."
            )
            errmsg = "TFS-Dataframe can not contain boolean dtype columns in MAD-X compatibility mode."
            raise MADXCompatibilityError(errmsg)

        # Check that the dataframe contains no complex dtype columns
        if any(pdtypes.is_complex_dtype(type_) for type_ in data_frame.dtypes):
            LOGGER.debug(
                f"Complex dtype column found in dataframe {info_str}, which is incompatible with MAD-X. "
                "Change the column dtypes or split it into real and imaginary values to keep compatibility with MAD-X."
            )
            errmsg = "TFS-Dataframe can not contain complex dtype columns in MAD-X compatibility mode."
            raise MADXCompatibilityError(errmsg)

    LOGGER.debug(f"DataFrame {info_str} validated")
