"""
Writer
------

Writing functionalty for **TFS** files.
"""

from __future__ import annotations  # for delayed type annotations

import logging
import pathlib
import string
from types import NoneType
from typing import TYPE_CHECKING

import numpy as np
from pandas.api import types as pdtypes
from pandas.io.common import get_handle

from tfs.constants import DEFAULT_COLUMN_WIDTH, INDEX_ID, MIN_COLUMN_WIDTH
from tfs.frame import TfsDataFrame
from tfs.frame import validate as validate_frame

if TYPE_CHECKING:
    import pandas as pd


LOGGER = logging.getLogger(__name__)


def write_tfs(
    tfs_file_path: pathlib.Path | str,
    data_frame: TfsDataFrame | pd.DataFrame | pd.Series,
    headers_dict: dict | None = None,
    save_index: str | bool = False,  # noqa: FBT002
    colwidth: int = DEFAULT_COLUMN_WIDTH,
    headerswidth: int = DEFAULT_COLUMN_WIDTH,
    non_unique_behavior: str = "warn",
    validate: str | None = None,
) -> None:
    """
    Writes the provided `DataFrame` to disk at **tfs_file_path**. If `headers_dict`
    is provided it is written to dist as the headers. Note that this function is
    exported also at the top-level of the package as `tfs.write`.

    .. note::
        Compression of the output file is possible, by simply providing a valid compression extension
        as the **tfs_file_path** suffix. Any compression format supported by ``pandas`` is accepted,
        which includes: ``.gz``, ``.bz2``, ``.zip``, ``.xz``, ``.zst``, ``.tar``, ``.tar.gz``,
        ``.tar.xz`` or ``.tar.bz2``. See below for examples.

    .. warning::
        Through the *validate* argument, one can skip dataframe validation before writing
        to file which can improve performance. This is **not recommended** if the file needs
        to be read by ``MAD-X`` or ``MAD-NG``. The default behaviour is to check for ``MAD-X``
        compatibility. The option to skip validation is left for the user to use (at their own
        risk) should they wish to avoid lengthy validation of large `TfsDataFrames` (such as
        for instance a sliced FCC lattice).

    Args:
        tfs_file_path (pathlib.Path | str): Path to the output **TFS** file.
        data_frame (TfsDataFrame | pd.DataFrame | pd.Series): The dataframe to write to file. If
            a Series-like object is given, it will be converted to a `TfsDataFrame` first and
            written with a single column.
        headers_dict (dict): Headers for the `data_frame`. If not provided, assumes a
            `TfsDataFrame` was given and tries to use ``data_frame.headers``. Writes with
            empty headers is those are not found either.
        save_index (str | bool): bool or string. Default to ``False``. If ``True``, saves
            the index of `data_frame` to a column identifiable by `INDEX&&&`. If given as string,
            saves the index of `data_frame` to a column named by the provided value.
        colwidth (int): Column width, can not be smaller than `MIN_COLUMN_WIDTH`.
        headerswidth (int): Used to format the header width for both keys and values.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
        validate (str): Determines if and which validation will be performed before writing. By
            default no validation is performed. Accepted values are `madx`, `mad-x`, `madng` and
            `mad-ng` (case-insensitive), for compatibility with ``MAD-X`` and ``MAD-NG`` codes,
            respectively. See the `tfs.frame.validate` function for more information on the
            validation steps.

    Examples:
        Writing to file is simple, as most arguments have sane default values.
        The simplest usage goes as follows:

        .. code-block:: python

            tfs.write("filename.tfs", dataframe)

        One can choose to perform dataframe validation before writing
        it to file. This can be done by providing an accepted compatibility
        mode to check for (either `madx` or `madng`), as:

        .. code-block:: python

            tfs.write("filename.tfs", dataframe, validate="madx")

        If one wants to, for instance, raise and error on non-unique indices or
        columns when validating the dataframe, one can do so as:

        .. code-block:: python

            tfs.write(
                "filename.tfs", dataframe, non_unique_behavior="raise", validate="madng"
            )

        It is possible to directly have the output file be compressed, by specifying a
        valid compression extension as the **tfs_file_path** suffix. The detection
        and compression is handled automatically. For instance:

        .. code-block:: python

            tfs.write("filename.tfs.gz", dataframe)
    """
    left_align_first_column = False
    tfs_file_path = pathlib.Path(tfs_file_path)

    # Check for provided headers. If None, try to get them from the df
    # and default to empty dict (will not write any lines to file)
    if headers_dict is None:
        headers_dict = getattr(data_frame, "headers", {})

    # We case to a TfsDataFrame anyway for validation and writing
    # We ensure column names as strings in case it was a pd.Series-like (and colname is 0)
    data_frame = TfsDataFrame(data_frame, headers=headers_dict)
    data_frame.columns = data_frame.columns.astype(str)

    # Only perform validation if asked (validation is OFF by default)
    # We also check for False as it was the way to skip it in tfs-pandas 3.x
    if validate is not None and validate is not False:  # validation function will check for valid values
        validate_frame(
            data_frame,
            info_str=f"to be written in {tfs_file_path.absolute()}",
            non_unique_behavior=non_unique_behavior,
            compatibility=validate,
        )

    # Let pandas try to infer the best dtypes for the data to write (only to write, the
    # actual dataframe provided by the user is not changed so this operation is fine).
    # Passed options: don't convert float to ints, don't try (and fail) to convert complex
    # to floats, and don't try to convert strings to its special StringDtype (as then 'None'
    # would be transformed into <pd.NA> and if we write this to file we are very much cooked.)
    # Overall we do not care to infer specialized dtypes, just that it makes the best inference
    # to valid dtypes (i.e. an object column should be inferred as strings if that makes sense).
    data_frame = data_frame.convert_dtypes(convert_integer=False, convert_floating=False, convert_string=False)

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
            "\n".join(line for line in (headers_str, colnames_str, coltypes_str, data_str) if line) + "\n"
        )


# ----- Helpers ----- #


def _insert_index_column(
    data_frame: TfsDataFrame | pd.DataFrame, save_index: str | bool | None = None
) -> None:
    """
    Inserts the index of the dataframe into it as a column, naming it according to
    'save_index' if it was provided. Otherwise it tries to use the existing index's
    name (if present) and falls back to a default.
    """
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
    called for an empty headers dictionary, in order not write a line to file.

    Args:
        headers_dict (dict): the ``TfsDataFrame`` headers.
        width (int): column width to use when formatting keys and values from the headers dict.

    Returns:
        A full string representation for the headers dictionary, TFS compliant.
    """
    if headers_dict:
        return "\n".join(_get_header_line(name, value, width) for name, value in headers_dict.items())
    return ""


def _get_header_line(name: str, value, width: int) -> str:
    """
    Creates and returns the string value for a single header line, based
    on the name of the header parameter and its value.

    For instance, calling this for 'param' header which is a float equal to
    1.792 and using the DEFAULT_COLUMN_WIDTH of the package would yield:
    "@ param                %le                1.792"


    Args:
        name (str): name of the header parameter.
        value: value of the header parameter. Any valid type is accepted here
            (int, float, str, potentially bool, complex etc.) and the type
            of this value is used to infer the formatting.
        width (int): column width to use when formatting the header line.

    Returns:
        The full, formatted header line string.
    """
    if not isinstance(name, str):
        errmsg = f"{name} is not a string"
        raise TypeError(errmsg)
    type_identifier = _value_to_tfs_type_identifier(value)
    dtype_ = (
        NoneType if value is None else np.array(value).dtype
    )  # otherwise numpy gives 'Object' for 'None's
    # Strip the following as it might have trailing spaces and we leave that to the alignment formatting below
    value_str = (
        ValueToStringFormatter().format_field(value, _dtype_to_formatter_string(dtype_, width)).strip()
    )
    return f"@ {name:<{width}} {type_identifier} {value_str.strip():>{width}}"


def _get_colnames_string(colnames: list[str], colwidth: int, left_align_first_column: bool) -> str:  # noqa: FBT001
    """Returns the string for the line with the column names."""
    format_string = _get_row_format_string([None] * len(colnames), colwidth, left_align_first_column)
    return "* " + format_string.format(*colnames)


def _get_coltypes_string(types: pd.Series, colwidth: int, left_align_first_column: bool) -> str:  # noqa: FBT001
    """Returns the string for the line with the column type specifiers."""
    fmt = _get_row_format_string([str] * len(types), colwidth, left_align_first_column)
    return "$ " + fmt.format(*[_dtype_to_tfs_format_identifier(type_) for type_ in types])


def _get_data_string(
    data_frame: TfsDataFrame | pd.DataFrame,
    colwidth: int,
    left_align_first_column: bool,  # noqa: FBT001
) -> str:
    """
    Returns the complete string to be written for the data part of the dataframe.
    This corresponds to all the data rows, after the column names and the column
    type specifiers.

    Args:
        data_frame (TfsDataFrame | pd.DataFrame): the dataframe to write.
        colwidth (int): column width to use when formatting the data.
        left_align_first_column (bool): whether to left-align the first column or not.

    Returns:
        The full string representation of the data part of the dataframe.
    """
    if len(data_frame.index) == 0 or len(data_frame.columns) == 0:
        return "\n"

    format_strings = "  " + _get_row_format_string(data_frame.dtypes, colwidth, left_align_first_column)
    data_frame = data_frame.astype(object)  # overrides pandas auto-conversion (lead to format bug)
    string_formatter = ValueToStringFormatter()

    # A bit ugly but we go line per line and determine the string on the fly
    return "\n".join(
        data_frame.apply(lambda series: string_formatter.format(format_strings, *series), axis=1)
    )


def _get_row_format_string(
    dtypes: list[type],
    colwidth: int,
    left_align_first_column: bool,  # noqa: FBT001
) -> str:
    """
    Returns the formatter string for a given row of the data part of the dataframe,
    based on the dtypes of the columns and the column width to use for writing. It is
    a string with the formatting speficiers (for fstrings), one slot per column. For
    instance: {0:>20s} {1:>20.12g} {2:>20d} {3:>20.12g}".

    Args:
        dtypes (list): list of the dtypes of the columns.
        colwidth (int): column width to use when formatting the row.
        left_align_first_column (bool): whether to left-align the first column or not.

    Returns:
        The full formatter string for any data row.
    """
    return " ".join(
        f"{{{indx:d}:"
        f"{'<' if (not indx) and left_align_first_column else '>'}"
        f"{_dtype_to_formatter_string(type_, colwidth)}}}"
        for indx, type_ in enumerate(dtypes)
    )


def _value_to_tfs_type_identifier(value) -> str:
    """
    Returns the **TFS** dtype identifier for the provided value,
    as a string. For instance for a float, it would return "%le".
    """
    # First intercept for None values (MAD-NG writes nil) to return %n
    # (as the inferred dtype is object and that would be a mess later)
    if value is None:
        return "%n"

    # Otherwise we infer the dtype and return the corresponding identifier
    dtype_ = np.array(value).dtype  # let numpy handle conversion to it dtypes
    return _dtype_to_tfs_format_identifier(dtype_)


def _dtype_to_tfs_format_identifier(type_: type) -> str:
    """
    Return the proper **TFS** identifier for the provided dtype. This is
    the function called behind the scenes by `_value_to_type_identifier`,
    but it takes the inferred dtype as argument. For a float dtype it
    would return '%le', for a string '%s' etc.

    Args:
        type_ (type): an instance of the built-in type (in this package, one of ``numpy`` or ``pandas``
            types) to get the ID string for.

    Returns:
        The ID string.

    Raises:
        TypeError: if the provided type could not be identified as a valid dtype.
    """
    if pdtypes.is_integer_dtype(type_):
        return "%d"
    if pdtypes.is_float_dtype(type_):
        return "%le"
    if pdtypes.is_string_dtype(type_):
        return "%s"
    if pdtypes.is_bool_dtype(type_):
        return "%b"
    if pdtypes.is_complex_dtype(type_):
        return "%lz"
    errmsg = f"Provided type '{type_}' could not be identified as either a bool, int, float complex or string dtype"
    raise TypeError(errmsg)


def _dtype_to_formatter_string(type_: type, colsize: int) -> str:
    """
    Return the proper formatter string for the provided dtype. This is
    the function called behind the scenes by `_value_to_string_format_id`,
    but it takes the inferred dtype as argument. For a float dtype it
    would return 'g', for a complex 'c' etc. It is used later for string
    formatting (you know, when you do f'{variable:.2f}' etc).

    Args:
        type_ (type): an instance of the built-in type (in this package, one of
            ``numpy`` or ``pandas`` types) to get the formatter for.
        colsize (int): size of the written column to use for the formatter.

    Returns:
        The formatter string for the provided dtype.
    """
    type_id = _dtype_to_python_string_formatter(type_)  # for Python: 'd' or 'g' or 's' etc
    if pdtypes.is_float_dtype(type_) or pdtypes.is_complex_dtype(type_):
        return f"{colsize}.{colsize - len('-0.e-000')}{type_id}"  # make sure we don't round and lose info
    return f"{colsize}{type_id}"


def _dtype_to_python_string_formatter(type_: type) -> str:
    """
    Return the (Python) string-formatter for the provided dtype,
    a.k.a the formatter passed to f-strings ('d' for integers for
    instance).

    Of special note are here "b" for boolean and "c" for complex
    numbers, but those are only for our own internal formatter.

    Args:
        type_ (type): an instance of the built-in type (in this package, one of
            ``numpy`` or ``pandas`` types) to get the formatter for.

    Returns:
        str: the formatter type-identifier.

    Raises:
        TypeError: if the provided type could not be identified as a valid dtype.
    """

    if type_ is None:  # don't know when that triggers
        return ""
    if type_ is NoneType:  # this means the value was None
        return "s"  # formatted as string since we will write 'nil'
    if pdtypes.is_integer_dtype(type_):
        return "d"
    if pdtypes.is_bool_dtype(type_):
        return "b"  # can only be used with TfsStringFormatter
    if pdtypes.is_float_dtype(type_):
        return "g"
    if pdtypes.is_string_dtype(type_):
        return "s"
    if pdtypes.is_complex_dtype(type_):
        return "c"  # can only be used with TfsStringFormatter

    errmsg = f"Provided type '{type_}' could not be identified as either a bool, int, float, complex or string dtype"
    raise TypeError(errmsg)


# ----- Formatter Class ----- #


class ValueToStringFormatter(string.Formatter):
    """
    Formatter class to be called for proper formatting of values
    (headers, dataframe data) into strings to write to file.
    """

    def format_field(self, value, format_spec):
        if format_spec.endswith("b"):  # value is a boolean
            return self._format_boolean(value, format_spec)

        if format_spec.endswith("c"):  # value is a complex number
            return self._format_complex(value, format_spec)

        if format_spec.endswith("s"):  # value is a string or None
            return self._format_string(value, format_spec)

        return super().format_field(value, format_spec)

    def _format_boolean(self, value, format_spec: str):
        """
        Special case for booleans, as from their written version
        will always be either 'true' or 'false' (lowercase) as
        done by MAD-NG.
        """
        bool_str = str(bool(value)).lower()
        return super().format_field(bool_str, f"{format_spec[:-1]}s")

    def _format_complex(self, value, format_spec: str):
        """
        Special case for complex numbers, MAD-X and MAD-NG use 'i' for
        the imaginary part and not 'j', so we have to replace that in.
        """
        return super().format_field(value, f"{format_spec[:-1]}g").replace("j", "i")

    def _format_string(self, value: str | pathlib.Path, format_spec: str) -> str:
        """
        Special case as we need to ensure that strings are enclosed
        in either " or ' quotes. This also handles `pathlib.Path`
        objects and makes sure they are converted to strings first.
        """
        # First a check so that passing a Path works (i.e. if we
        # have a Path in the headers it will be written as a string)
        if isinstance(value, pathlib.Path):
            value = str(value)  # convert its current form (can be relative)

        # Now we go on with the formatting
        try:
            if not value.startswith(('"', "'")):
                value = f'"{value}"'
        except AttributeError:
            pass

        # Special case for None values which we always write as 'nil'. In case
        # value is None we end up here as we want 'nil' and format it as string
        # We do this here as we want to write nil and not "nil"
        if value is None:
            value = "nil"

        return super().format_field(value, format_spec)
