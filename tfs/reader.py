"""
Reader
------

Reading functionalty for **TFS** files.
"""

from __future__ import annotations  # for delayed type annotations

import logging
import pathlib
import shlex
from contextlib import contextmanager
from dataclasses import dataclass
from types import NoneType
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pandas._libs.parsers import STR_NA_VALUES
from pandas.io.common import get_handle

from tfs.constants import (
    COMMENTS,
    HEADER,
    ID_TO_TYPE,
    INDEX_ID,
    NAMES,
    TYPES,
    VALID_BOOLEANS_HEADERS,
    VALID_TRUE_BOOLEANS,
)
from tfs.errors import (
    AbsentColumnNameError,
    AbsentColumnTypeError,
    AbsentTypeIdentifierError,
    InvalidBooleanHeaderError,
    UnknownTypeIdentifierError,
)
from tfs.frame import TfsDataFrame
from tfs.frame import validate as validate_frame

if TYPE_CHECKING:
    from collections.abc import Callable
    from io import TextIOWrapper

    from pandas import DataFrame


LOGGER = logging.getLogger(__name__)

# Here we take the default NA values for pandas readers, and make a copy from which we
# remove "" (we want empty strings to stay empty strings) and adding "nil"
_NA_VALUES: list[str] = [*list(STR_NA_VALUES), "nil"]
_NA_VALUES.remove("")

# ----- Main Functionality ----- #


def read_tfs(
    tfs_file_path: pathlib.Path | str,
    index: str | None = None,
    non_unique_behavior: str = "warn",
    validate: str | None = None,
) -> TfsDataFrame:
    """
    Parses the **TFS** table present in **tfs_file_path** and returns a ``TfsDataFrame``.
    Note that this function is also exported at the top-level of the package as `tfs.read`.

    .. note::
        Loading and reading compressed files is possible. Any compression format supported
        by ``pandas`` is accepted, which includes: ``.gz``, ``.bz2``, ``.zip``, ``.xz``,
        ``.zst``, ``.tar``, ``.tar.gz``, ``.tar.xz`` or ``.tar.bz2``. See below for examples.

    .. warning::
        Through the *validate* argument, one can activate dataframe validation after
        loading it from a file, which can significantly slow the execution of this
        function, e.g. in case of large `TfsDataFrames` such as a sliced FCC lattice.
        Note that validation can be performed at any time by using the `tfs.frame.validate`
        function.

    .. admonition:: **Methodology**

        This function first calls a helper which parses and returns all metadata
        from the file (headers content, column names & types, number of lines
        parsed). The rest of the file (dataframe part) is given to parse to
        ``pandas.read_csv`` with the right options to make use of its C engine's
        speed. After this, conversion to ``TfsDataDrame`` is made and, if requested,
        the index is set and validation performed, before the frame is being returned.

    Args:
        tfs_file_path (pathlib.Path | str): Path to the **TFS** file to read. Can be
            a string, in which case it will be cast to a Path object.
        index (str): Name of the column to set as index. If not given, looks in **tfs_file_path**
            for a column starting with `INDEX&&&`.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in
            the dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
        validate (str): If an accepted value is given, validation will be performed after loading.
            Defauts to `None`, which skips validation. Accepted validation modes are `madx`, `mad-x`,
            `madng` and `mad-ng`, case-insensitive. See the `tfs.frame.validate` function for more
            information on validation.

    Returns:
        A ``TfsDataFrame`` object with the loaded data from the file.

    Examples:
        Reading from a file is simple, as most arguments have sane default values.
        The simplest usage goes as follows:

        .. code-block:: python

            tfs.read("filename.tfs")

        One can also pass a `~pathlib.Path` object to the function:

        .. code-block:: python

            tfs.read(pathlib.Path("filename.tfs"))

        It is possible to load compressed files if the compression format is supported by `pandas`.
        (see above). The compression format detection is handled automatically from the extension
        of the provided **tfs_file_path** suffix. For instance:

        .. code-block:: python

            tfs.read("filename.tfs.gz")
            tfs.read("filename.tfs.bz2")
            tfs.read("filename.tfs.zip")

        If one wants to set a specific column as index (and drop it from the data),
        this is done as:

        .. code-block:: python

            tfs.read("filename.tfs", index="COLUMN_NAME")

        One can choose to perform dataframe validation after reading from file, for
        compatibility with a certain code, by providing a valid argument:

        .. code-block:: python

            tfs.read("filename.tfs", validate="MAD-NG")  # or validate="MAD-X"

        If one wants to raise an error on non-unique indices or columns when
        performing validation, one can do so as:

        .. code-block:: python

            tfs.read("filename.tfs", non_unique_behavior="raise")
    """
    tfs_file_path = pathlib.Path(tfs_file_path)
    LOGGER.debug(f"Reading path: {tfs_file_path.absolute()}")

    # First step: get the metadata from the file ()
    metadata: _TfsMetaData = _read_metadata(tfs_file_path)

    if metadata.column_names is None:
        raise AbsentColumnNameError(tfs_file_path)
    if metadata.column_types is None:
        raise AbsentColumnTypeError(tfs_file_path)

    # The pandas engines do NOT support reading complex numbers, we have to provide a function
    # We first create a dict from the metadata with column names and the associated types
    dtypes_dict: dict[str, type] = dict(zip(metadata.column_names, metadata.column_types, strict=False))
    converters: dict[str, Callable] = {}  # will be explained in a later comment

    # If we have complex-dtyped columns, they are popped from the first dict and added
    # to a converters dict as key, with as value our function to parse complex numbers
    # We also remove the column from the dtypes_dict: if we provide the column in both
    # dicts (for dtype AND converter), the pandas reader emits a ParserWarning
    if np.complex128 in metadata.column_types:
        LOGGER.debug("Complex columns detected, adding converter.")
        for colname, dtype in zip(metadata.column_names, metadata.column_types, strict=False):
            if dtype is np.complex128:
                converters[colname] = _parse_complex
                del dtypes_dict[colname]

    # By this point we have built the following two dictionaries:
    # - 'dtypes_dict' with all non-complex columns (key, value are: name, type)
    # - 'converters' with all complex columns (key, value are: name, function to parse)
    # And we will provide both of these to the pandas reader which uses either its own
    # API for the loading or our custom converters for the complex columns.
    LOGGER.debug("Parsing data part of the file")

    # DO NOT use `comment=COMMENTS` in this call: if the '#' symbol is in an element (a
    # string header or some value in the dataframe) then the entire parsing will crash
    data_frame: DataFrame = pd.read_csv(  # ty:ignore[no-matching-overload]
        tfs_file_path,
        sep=r"\s+",  # understands ' ' as delimiter | replaced deprecated 'delim_whitespace' in tfs-pandas 3.8.0
        names=metadata.column_names,  # column names we have determined, avoids using first read row for columns
        dtype=dtypes_dict,  # assign types at read-time to avoid conversions later
        engine="c",  # faster, and we do not need the features of the python engine
        converters=converters,  # more involved dtype conversion, e.g. for complex columns
        skiprows=metadata.non_data_lines,  # no need to read these lines again
        na_values=_NA_VALUES,  # includes MAD-NG's 'nil' which we cast to NaN in the data
        keep_default_na=False,  # we provided the list ourselves so it does not include ""
        quotechar='"',  # elements surrounded by " are one entry -> correct parsing of strings with spaces
    )

    LOGGER.debug("Converting to TfsDataFrame")
    tfs_data_frame = TfsDataFrame(data_frame, headers=metadata.headers)

    # In pandas.read_csv we read a 'nil' as NaN in columns, so we have to convert it back
    # to 'None' in the string-dtyped columns. For numeric columns we keep NaN
    LOGGER.debug("Ensuring preservation of None values in string columns")
    for column in tfs_data_frame.select_dtypes(include=["string", "object"]):
        tfs_data_frame[column] = tfs_data_frame[column].replace([np.nan], [None])

    if index:
        LOGGER.debug(f"Setting '{index}' column as index")
        tfs_data_frame: TfsDataFrame = tfs_data_frame.set_index(index)  # ty:ignore[invalid-assignment]
    else:
        LOGGER.debug("Attempting to find index identifier in columns")
        tfs_data_frame: TfsDataFrame = _find_and_set_index(tfs_data_frame)

    # Only perform validation if asked ('validate' defaults to None which skips this step)
    if validate is not None:  # validation function checks for valid values
        validate_frame(
            tfs_data_frame,
            info_str=f"from file {tfs_file_path.absolute()}",
            non_unique_behavior=non_unique_behavior,
            compatibility=validate,
        )

    return tfs_data_frame


def read_headers(tfs_file_path: pathlib.Path | str) -> dict:
    """
    Parses the top of the **tfs_file_path** and returns the headers.

    Args:
        tfs_file_path (pathlib.Path | str): Path to the **TFS** file
            to read.

    Returns:
        An dictionary with the headers read from the file.

    Examples:

        .. code-block:: python

            headers = read_headers("filename.tfs")

        Just as with the `read_tfs` function, it is possible to load from compressed
        files if the compression format is supported by `pandas`. The compression
        format detection is handled automatically from the extension of the provided
        **tfs_file_path** suffix. For instance:

        .. code-block:: python

            headers = read_headers("filename.tfs.gz")
    """
    metadata: _TfsMetaData = _read_metadata(tfs_file_path)
    return metadata.headers


# ----- Helpers ----- #


@dataclass
class _TfsMetaData:
    """A dataclass to encapsulate the metadata read from a TFS file."""

    headers: dict
    non_data_lines: int
    column_names: np.ndarray
    column_types: np.ndarray


@contextmanager
def _metadata_handle(file_path: pathlib.Path | str) -> TextIOWrapper:  # type: ignore
    """
    A contextmanager to provide a handle for the file, to iterate through.
    The handle is obtained via a pandas function which handles the potential
    file compression for us. Whatever happens after yielding, the handle is
    closed when the context exits.

    Args:
        tfs_file_path (pathlib.Path | str): Path to the **TFS** file to read. Can be
            a string, in which case it will be cast to a Path object.

    Yields:
        A ``TextIOWrapper`` as the handle of the file.
    """
    handles = get_handle(file_path, mode="r", is_text=True, errors="strict", compression="infer")
    try:
        yield handles.handle
    finally:
        handles.close()


def _read_metadata(tfs_file_path: pathlib.Path | str) -> _TfsMetaData:
    """
    Parses the beginning of the **tfs_file_path** to extract metadata
    (all non dataframe lines).

    .. admonition:: **Methodology**

        This function parses the first lines of the file until it gets to
        the `types` line. While parsed, all the appropriate information is
        gathered (headers content, column names and types, number of lines
        parsed). After reaching the `types` line, the loop is broken to avoid
        reading the whole file. The gathered metadata is assembled in a single
        ``_TfsMetaData`` object and returned.

    Args:
        tfs_file_path (pathlib.Path | str): Path to the **TFS** file to read. Can be
            a string, in which case it will be cast to a Path object.

    Returns:
        A ``_TfsMetaData`` object with the metadata read from the file.
    """
    LOGGER.debug("Reading headers and metadata from file")
    tfs_file_path = pathlib.Path(tfs_file_path)
    column_names = column_types = None
    headers = {}

    # Note: the helper contextmanager handles compression for us
    # and provides and handle to iterate through, line by line
    with _metadata_handle(tfs_file_path) as file_reader:
        for line_number, line in enumerate(file_reader):
            if not (stripped_line := line.strip()):
                continue  # empty line
            line_components = shlex.split(stripped_line)
            if line_components[0] == HEADER:
                name, value = _parse_header_line(line_components[1:])
                headers[name] = value
            elif line_components[0] == NAMES:
                LOGGER.debug("Parsing column names.")
                column_names = np.array(line_components[1:])
            elif line_components[0] == TYPES:
                LOGGER.debug("Parsing column types.")
                column_types = _compute_column_types(line_components[1:])
            elif line_components[0] == COMMENTS:
                continue
            else:  # After all previous cases should only be data lines. If not, file is fucked.
                break  # Break to not go over all lines, saves a lot of time on big files

    return _TfsMetaData(
        headers=headers,
        non_data_lines=line_number,  # skip these lines
        column_names=column_names,
        column_types=column_types,
    )


def _parse_header_line(str_list: list[str]) -> tuple[str, bool | str | int | float | np.complex128 | None]:
    """
    Parses the data in the provided header line. Expects a valid header
    line starting with the '@' identifier, and parses the content that
    follows.

    Args:
        str_list (list[str]): list of parsed elements from the header
            line (we get these with 'shlex.split`).

    Returns:
        A tuple with the name of the header parameter for this line, as
        well as its value cast to the proper type (as determined by the
        type identifier).

    Raises:
        AbsentTypeIdentifierError: if no type identifier is found in the header line.
        InvalidBooleanHeaderError: if the identifier type indicates a boolean
            but the corresponding value is not an accepted boolean.
    """
    # Find the index of elements at which the type identifier is located
    # For instance for ['q2', '%le', '60.31999175'] this would be 1
    type_index: int | None = next(
        (index for index, part in enumerate(str_list) if part.startswith("%")), None
    )
    if type_index is None:
        raise AbsentTypeIdentifierError(str_list)

    # Get name and string of the header, and determine its type
    name: str = " ".join(str_list[0:type_index])
    value_string: str = " ".join(str_list[(type_index + 1) :])
    value_string: str = value_string.strip('"')
    value_type: type = _id_to_type(str_list[type_index])

    # Some special cases we handle first
    if value_type is NoneType:  # special handling for 'nil's
        return name, None
    if value_type is bool:  # special handling for boolean values
        return name, _string_to_bool(value_string)
    if value_type is np.complex128:  # special handling for complex values
        return name, _parse_complex(value_string)
    # Otherwise we just cast to the determined type (no special handling)
    return name, value_type(value_string)


def _find_and_set_index(data_frame: TfsDataFrame) -> TfsDataFrame:
    """
    Looks for a column with a name starting with the index identifier, and sets it as index if found.
    The index identifier will be stripped from the column name first.

    Args:
        data_frame (TfsDataFrame): the ``TfsDataFrame`` to look for an index in.

    Returns:
        The ``TfsDataFrame`` after operation, whether an index was found or not.
    """
    index_column = [colname for colname in data_frame.columns if colname.startswith(INDEX_ID)]
    if index_column:
        data_frame: TfsDataFrame = data_frame.set_index(index_column)  # ty:ignore[invalid-assignment]
        index_name = index_column[0].replace(INDEX_ID, "")
        if index_name == "":
            index_name = None  # to remove it completely (Pandas makes a difference)
        data_frame = data_frame.rename_axis(index=index_name)
    return data_frame


def _compute_column_types(identifiers: list[str]) -> list[type]:
    """
    Returns the data type for each column based on the
    corresponding provided type identifier strings. The
    type identifier strings are written on the line just
    below the column names (the %le, %d, %s, etc.).
    """
    return [_id_to_type(type_id) for type_id in identifiers]


def _string_to_bool(val_str: str) -> bool:
    """
    Infers the boolean value from a string value in the headers.
    Raises ``InvalidBooleanHeaderError`` when encountering invalid value.
    """
    if val_str.lower().capitalize() not in VALID_BOOLEANS_HEADERS:
        raise InvalidBooleanHeaderError(val_str)

    return val_str.lower().capitalize() in VALID_TRUE_BOOLEANS


def _id_to_type(type_identifier: str) -> type:
    try:
        return ID_TO_TYPE[type_identifier]
    except KeyError as err:  # could be a "%[num]s" that MAD-X likes to output
        if _is_madx_string_col_identifier(type_identifier):
            return str
        raise UnknownTypeIdentifierError(type_identifier) from err


def _is_madx_string_col_identifier(type_str: str) -> bool:
    """
    ``MAD-X`` likes to return the string columns by also indicating their width, so
    by trying to parse `%s` identifiers only we might miss those looking like `%20s`
    specifying (here) a 20-character wide column for strings.

    Args:
        type_str (str): the suspicious identifier.

    Returns:
        ``True`` if the identifier is identified as coming from ``MAD-X``, ``False`` otherwise.
    """
    if not (type_str.startswith("%") and type_str.endswith("s")):
        return False
    try:
        _ = int(type_str[1:-1])
    except ValueError:
        return False
    else:
        return True


def _parse_complex(complex_string: str) -> np.complex128:
    """
    Helper for pandas (as a converter) to handles complex columns. Assumes the file
    might be from MAD-NG, in which case it uses 'i' (or 'I') for the imaginary part
    and we need to convert it to 'j' for Python.

    Args:
        complex_string (str): the string representation of the complex number, for
            instance '1.0+2.0i' or '7.5342+164j'.

    Returns:
        The (potentially adapted) value as a numpy.complex128.
    """
    # We replace both 'i' and 'I' as each can happen in the MAD-NG output
    # (the second one is a special case, if there is no real part - said Laurent)
    return np.complex128(complex_string.replace("i", "j").replace("I", "j"))
