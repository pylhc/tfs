"""
Writer
------

Writing functionalty for **TFS** files.
"""
import logging
import pathlib
from collections import OrderedDict
from typing import List, Union

import numpy as np
import pandas as pd
from pandas.api import types as pdtypes
from pandas.io.common import get_handle

from tfs.constants import DEFAULT_COLUMN_WIDTH, INDEX_ID, MIN_COLUMN_WIDTH
from tfs.frame import TfsDataFrame
from tfs.frame import validate as validate_frame

LOGGER = logging.getLogger(__name__)


def write_tfs(
    tfs_file_path: Union[pathlib.Path, str],
    data_frame: Union[TfsDataFrame, pd.DataFrame],
    headers_dict: dict = None,
    save_index: Union[str, bool] = False,
    colwidth: int = DEFAULT_COLUMN_WIDTH,
    headerswidth: int = DEFAULT_COLUMN_WIDTH,
    non_unique_behavior: str = "warn",
    validate: bool = True,
) -> None:
    """
    Writes the provided ``DataFrame`` to disk at **tfs_file_path**, eventually with the `headers_dict` as
    headers dictionary.

    .. note::
        Compression of the output file is possible, by simply providing a valid compression extension
        as the **tfs_file_path** suffix. Any compression format supported by ``pandas`` is accepted,
        which includes: ``.gz``, ``.bz2``, ``.zip``, ``.xz``, ``.zst``, ``.tar``, ``.tar.gz``, 
        ``.tar.xz`` or ``.tar.bz2``. See below for examples.

    .. warning::
        Through the *validate* argument, one can skip dataframe validation before writing it to file.
        While this can speed-up the execution time of this function , it is **not recommended** and
        is not the default behavior of this function. The option, however, is left for the user to
        use at their own risk should they wish to avoid lengthy validation of large `TfsDataFrames`
        (such as for instance a sliced FCC lattice).

    Args:
        tfs_file_path (Union[pathlib.Path, str]): Path object to the output **TFS** file. Can be
            a string, in which case it will be cast to a Path object.
        data_frame (Union[TfsDataFrame, pd.DataFrame]): ``TfsDataFrame`` or ``pandas.DataFrame`` to
            write to file.
        headers_dict (dict): Headers for the `data_frame`. If not provided, assumes a ``TfsDataFrame``
            was given and tries to use ``data_frame.headers``.
        save_index (Union[str, bool]): bool or string. Default to ``False``. If ``True``, saves
            the index of `data_frame` to a column identifiable by `INDEX&&&`. If given as string,
            saves the index of `data_frame` to a column named by the provided value.
        colwidth (int): Column width, can not be smaller than `MIN_COLUMN_WIDTH`.
        headerswidth (int): Used to format the header width for both keys and values.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
        validate (bool): Whether to validate the dataframe before writing it to file. Defaults to ``True``.

    Examples:
        Writing to file is simple, as most arguments have sane default values.
        The simplest usage goes as follows:

        .. code-block:: python

            >>> tfs.write("filename.tfs", dataframe)
        
        If one wants to, for instance, raise and error on non-unique indices or columns,
        one can do so as:

        .. code-block:: python

            >>> tfs.write("filename.tfs", dataframe, non_unique_behavior="raise")
        
        One can choose to skip dataframe validation **at one's own risk** before writing
        it to file. This is done as:

        .. code-block:: python

            >>> tfs.write("filename.tfs", dataframe, validate=False)
        
        It is possible to directly have the output file be compressed, by specifying a
        valid compression extension as the **tfs_file_path** suffix. The detection
        and compression is handled automatically. For instance:

        .. code-block:: python

            >>> tfs.write("filename.tfs.gz", dataframe)
    """
    left_align_first_column = False
    tfs_file_path = pathlib.Path(tfs_file_path)
    
    if validate:
        validate_frame(data_frame, f"to be written in {tfs_file_path.absolute()}", non_unique_behavior)

    if headers_dict is None:  # tries to get headers from TfsDataFrame
        try:
            headers_dict = data_frame.headers
        except AttributeError:
            headers_dict = OrderedDict()

    data_frame = _autoset_pandas_types(data_frame)  # will always make a copy of the provided df

    if save_index:
        left_align_first_column = True
        _insert_index_column(data_frame, save_index)

    colwidth = max(MIN_COLUMN_WIDTH, colwidth)
    headers_str = _get_headers_string(headers_dict, headerswidth)
    colnames_str = _get_colnames_string(data_frame.columns, colwidth, left_align_first_column)
    coltypes_str = _get_coltypes_string(data_frame.dtypes, colwidth, left_align_first_column)
    data_str = _get_data_string(data_frame, colwidth, left_align_first_column)

    LOGGER.debug(f"Attempting to write file: {tfs_file_path.name} in {tfs_file_path.parent}")
    with get_handle(tfs_file_path, mode="w", compression="infer") as output_path:
        tfs_handle = output_path.handle
        tfs_handle.write(  # the last "\n" is to have an EOL at EOF, which is UNIX standard
            "\n".join((line for line in (headers_str, colnames_str, coltypes_str, data_str) if line)) + "\n"
        )


def _autoset_pandas_types(data_frame: Union[TfsDataFrame, pd.DataFrame]) -> Union[TfsDataFrame, pd.DataFrame]:
    """
    Tries to apply the ``.convert_dtypes()`` method of pandas on a copy on the provided dataframe.
    If the operation is not possible, checks if the provided dataframe is empty (which prevents
    ``convert_dtypes()`` to internally use ``pd.concat``) and then return only a copy of the original
    dataframe. Otherwise, raise the exception given by ``pandas``.

    NOTE: Starting with pandas 1.3.0, this behavior which was a bug has been fixed. This means no
    ``ValueError`` is raised by calling ``.convert_dtypes()`` on an empty ``DataFrame``, and from
    this function a warning is logged. The function is kept as to not force a new min version
    requirement on ``pandas`` or Python for users. When one day we make ``pandas >= 1.3.0`` the
    minimum requirement, we can remove the checks altogether and just call ``.convert_dtypes()``.
    See my comment at https://github.com/pylhc/tfs/pull/83#issuecomment-874208869

    Args:
        data_frame (Union[TfsDataFrame, pd.DataFrame]): ``TfsDataFrame`` or ``pandas.DataFrame`` to
            determine the types of.

    Returns:
        The dataframe with dtypes inferred as much as possible to the ``pandas`` dtypes.
    """
    LOGGER.debug("Attempting conversion of dataframe to pandas dtypes")
    try:
        return data_frame.copy().convert_dtypes(convert_integer=False)  # do not force floats to int
    except ValueError as pd_convert_error:  # If used on empty dataframes (uses concat internally)
        if not data_frame.size and "No objects to concatenate" in pd_convert_error.args[0]:
            LOGGER.warning("An empty dataframe was provided, no types were inferred")
            return data_frame.copy()  # since it's empty anyway, nothing to convert
        else:
            raise pd_convert_error


def _insert_index_column(data_frame: Union[TfsDataFrame, pd.DataFrame], save_index: str) -> None:
    if isinstance(save_index, str):  # save index into column by name given
        idx_name = save_index
    else:  # save index into column, which can be found by INDEX_ID
        try:
            idx_name = INDEX_ID + data_frame.index.name
        except TypeError:
            idx_name = INDEX_ID
    data_frame.insert(0, idx_name, data_frame.index)


def _get_headers_string(headers_dict: dict, width: int) -> str:
    """
    Returns the string to write a ``TfsDataFrame`` headers to file. Will return an empty string if
    called for an empty headers dictionary, in order not write an line to file.

    Args:
        headers_dict (dict): the ``TfsDataFrame`` headers.
        width (int): column width to use when formatting keys and values from the headers dict.

    Returns:
        A full string representation for the headers dictionary.
    """
    if headers_dict:
        return "\n".join(_get_header_line(name, headers_dict[name], width) for name in headers_dict)
    else:
        return ""


def _get_header_line(name: str, value, width: int) -> str:
    if not isinstance(name, str):
        raise TypeError(f"{name} is not a string")
    type_str = _value_to_type_string(value)
    if type_str == "%s":
        value = f'"{value}"'
    return f"@ {name:<{width}} {type_str} {value:>{width}}"


def _get_colnames_string(colnames: List[str], colwidth: int, left_align_first_column: bool) -> str:
    format_string = _get_row_format_string([None] * len(colnames), colwidth, left_align_first_column)
    return "* " + format_string.format(*colnames)


def _get_coltypes_string(types: pd.Series, colwidth: int, left_align_first_column: bool) -> str:
    fmt = _get_row_format_string([str] * len(types), colwidth, left_align_first_column)
    return "$ " + fmt.format(*[_dtype_to_id_string(type_) for type_ in types])


def _get_data_string(
    data_frame: Union[TfsDataFrame, pd.DataFrame],
    colwidth: int,
    left_align_first_column: bool,
) -> str:
    if len(data_frame.index) == 0 or len(data_frame.columns) == 0:
        return "\n"
    format_strings = "  " + _get_row_format_string(data_frame.dtypes, colwidth, left_align_first_column)
    data_frame = _quote_string_columns(data_frame)
    data_frame = data_frame.astype(object)  # overrides pandas auto-conversion (lead to format bug)
    return "\n".join(data_frame.apply(lambda series: format_strings.format(*series), axis=1))


def _get_row_format_string(dtypes: List[type], colwidth: int, left_align_first_column: bool) -> str:
    return " ".join(
        f"{{{indx:d}:"
        f"{'<' if (not indx) and left_align_first_column else '>'}"
        f"{_dtype_to_formatter(type_, colwidth)}}}"
        for indx, type_ in enumerate(dtypes)
    )


def _quote_string_columns(data_frame: Union[TfsDataFrame, pd.DataFrame]) -> Union[TfsDataFrame, pd.DataFrame]:
    def quote_strings(s):
        if isinstance(s, str):
            if not (s.startswith('"') or s.startswith("'")):
                return f'"{s}"'
        return s

    data_frame = data_frame.applymap(quote_strings)
    return data_frame


def _value_to_type_string(value) -> str:
    dtype_ = np.array(value).dtype  # let numpy handle conversion to it dtypes
    return _dtype_to_id_string(dtype_)


def _dtype_to_id_string(type_: type) -> str:
    """
    Return the proper **TFS** identifier for the provided dtype.

    Args:
        type_ (type): an instance of the built-in type (in this package, one of ``numpy`` or ``pandas``
            types) to get the ID string for.

    Returns:
        The ID string.
    """
    if pdtypes.is_integer_dtype(type_) or pdtypes.is_bool_dtype(type_):
        return "%d"
    elif pdtypes.is_float_dtype(type_):
        return "%le"
    elif pdtypes.is_string_dtype(type_):
        return "%s"
    raise TypeError(
        f"Provided type '{type_}' could not be identified as either a bool, int, float or string dtype"
    )


def _dtype_to_formatter(type_: type, colsize: int) -> str:
    """
    Return the proper string formatter for the provided dtype.

    Args:
        type_ (type): an instance of the built-in type (in this package, one of ``numpy`` or ``pandas``
            types) to get the formatter for.
        colsize (int): size of the written column to use for the formatter.

    Returns:
        The formatter.
    """
    if type_ is None:
        return f"{colsize}"
    if pdtypes.is_integer_dtype(type_) or pdtypes.is_bool_dtype(type_):
        return f"{colsize}d"
    elif pdtypes.is_float_dtype(type_):
        return f"{colsize}.{colsize - len('-0.e-000')}g"
    elif pdtypes.is_string_dtype(type_):
        return f"{colsize}s"
    raise TypeError(
        f"Provided type '{type_}' could not be identified as either a bool, int, float or string dtype"
    )
