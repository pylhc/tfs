"""
Utils
-------------------

Private utility functions used in the reading, writing and modifying of **TFS** files.
"""
import logging
from typing import Union

import numpy as np
import pandas as pd

from tfs.errors import TfsFormatError
from tfs.frame import TfsDataFrame

LOGGER = logging.getLogger(__name__)


def validate(
    data_frame: Union[TfsDataFrame, pd.DataFrame],
    info_str: str = "",
    non_unique_behavior: str = "warn",
) -> None:
    """
    Check if Dataframe contains finite values only, strings as column names and no empty headers
    or column names.

    Args:
        data_frame (Union[TfsDataFrame, pd.DataFrame]): the dataframe to check on.
        info_str (str): additional information to includ in logging statements.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts **warn** and **raise** as values, case-insensitively, which dictates
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
