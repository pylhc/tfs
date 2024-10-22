"""
Reader
------

Reading functionalty for **TFS** files.
"""

from __future__ import annotations

import logging
import pathlib
import shlex
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from tfs.constants import (
    COMMENTS,
    HEADER,
    ID_TO_TYPE,
    INDEX_ID,
    NAMES,
    TYPES,
    VALID_BOOLEANS_HEADERS,
    VALID_TRUE_BOOLEANS,
    VALIDATION_MODES,
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

LOGGER = logging.getLogger(__name__)

# A string not expected to be found in the headers
# I generated this randomly with: "".join(random.choice(string.ascii_letters) for _ in range(100))
_UNEXPECTED_SEP: str = (
    "baBfHIhwOdMnuBVHDDZcysbmwRgWaBnukQPIWNHpFVqjrIcOryhvyJwIRRHfqOQLGKhtZPLJhziZKomfVhXsoqfoGkvyFKuNhhst"
)


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

        If one wants to, for instance, raise and error on non-unique indices or columns
        when performing validation, one can do so as:

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
    dtypes_dict: dict[str, type] = dict(zip(metadata.column_names, metadata.column_types))
    converters: dict[str, Callable] = {}  # will be explained in a later comment

    # If we have complex-dtyped columns, they are popped from the first dict and added
    # to a converters dict as key, with as value our function to parse complex numbers
    if np.complex128 in metadata.column_types:
        LOGGER.debug("Complex columns detected, reading as strings and casting later")
        for colname, dtype in zip(metadata.column_names, metadata.column_types):
            if dtype is np.complex128:
                converters[colname] = _parse_complex  # register it with our converter
                del dtypes_dict[colname]  # remove to avoid ParserWarning saying we provided both

    # By this point we have built the following two dictionaries:
    # - 'dtypes_dict' with all non-complex columns (key, value are: name, type)
    # - 'converters' with all complex columns (key, value are: name, function to parse)
    # And we will provide both of these to the pandas reader which uses either its own
    # API for the loading or our custom converters for the complex columns.
    LOGGER.debug("Parsing data part of the file")
    # DO NOT use comment=COMMENTS in here, if you do and the symbol is
    # in an element for some reason then the entire parsing will crash
    data_frame = pd.read_csv(
        tfs_file_path,
        engine="c",  # faster, and we do not need the features of the python engine
        skiprows=metadata.non_data_lines,  # no need to read these lines again
        sep=r"\s+",  # understands ' ' as delimiter | replaced deprecated 'delim_whitespace' in tfs-pandas 3.8.0
        quotechar='"',  # elements surrounded by " are one entry -> correct parsing of strings with spaces
        names=metadata.column_names,  # column names we have determined, avoids using first read row for columns
        dtype=dtypes_dict,  # assign types at read-time to avoid conversions later
        converters=converters,  # special handling for complex columns
    )

    LOGGER.debug("Converting to TfsDataFrame")
    tfs_data_frame = TfsDataFrame(data_frame, headers=metadata.headers)

    # In pandas.read_csv an empty string ("") will be read a NaN, but we want to preserve them
    LOGGER.debug("Ensuring preservation of empty strings")
    for column in tfs_data_frame.select_dtypes(include=["string", "object"]):
        tfs_data_frame[column] = tfs_data_frame[column].fillna("")

    if index:
        LOGGER.debug(f"Setting '{index}' column as index")
        tfs_data_frame = tfs_data_frame.set_index(index)
    else:
        LOGGER.debug("Attempting to find index identifier in columns")
        tfs_data_frame = _find_and_set_index(tfs_data_frame)

    # Only perform validation if a valid mode is given (MAD-X or MAD-NG compatibility)
    # By default 'validate' is None which will skip this step
    if isinstance(validate, str) and validate.lower() in VALIDATION_MODES:
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
            to read. Can be a string, in which case it will be cast to
            a `Path` object.

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


def _read_metadata(tfs_file_path: pathlib.Path | str) -> _TfsMetaData:
    """
    Parses the beginning of the **tfs_file_path** to extract metadata (all non dataframe lines).

    .. admonition:: **Methodology**

        This function parses the first lines of the file until it gets to the `types` line.
        While parsed, the appropriate information is gathered (headers content, column names & types,
        number of lines parsed). After reaching the `types` line, the loop is broken to avoid reading
        the whole file. The gathered metadata is assembled in a single ``_TfsMetaData`` object and
        returned.

    Args:
        tfs_file_path (pathlib.Path | str): Path to the **TFS** file to read. Can be
            a string, in which case it will be cast to a Path object.

    Returns:
        A ``_TfsMetaData`` object with the metadata read from the file.
    """
    LOGGER.debug("Reading headers and metadata from file")
    tfs_file_path = pathlib.Path(tfs_file_path)
    headers = {}
    column_names = column_types = None

    # Read the headers, chunk by chunk (line by line) with pandas.read_csv as a
    # context manager. Very important: the value of 'sep' here should not be a
    # value that can be found in headers (key or value)
    with pd.read_csv(
        tfs_file_path,
        header=None,  # don't look for a line with column names
        chunksize=1,  # read one chunk at a time (each is a line)
        skip_blank_lines=False,  # do not skip blank lines, so they count as header lines
        na_filter=False,  # Do not convert empty lines to NA
        sep=_UNEXPECTED_SEP,  # a string not expected to be found in the headers
        engine="python",  # only engine that supports this sep argument
        dtype=str,  # we are reading the headers so we only expect and want strings, they are parsed afterwards
    ) as file_reader:
        # Now each read chunk / line is made into a DataFrame, colname 0 and value is the read line
        for line_record in file_reader:
            line = line_record.loc[:, 0].values[0]  # this is the value of the line as a string
            if not line:
                continue  # empty line
            line_components = shlex.split(line)
            if line_components[0] == HEADER:
                name, value = _parse_header(line_components[1:])
                headers[name] = value
            elif line_components[0] == NAMES:
                LOGGER.debug("Parsing column names.")
                column_names = np.array(line_components[1:])
            elif line_components[0] == TYPES:
                LOGGER.debug("Parsing column types.")
                column_types = _compute_types(line_components[1:])
            elif line_components[0] == COMMENTS:
                continue
            else:  # After all previous cases should only be data lines. If not, file is fucked.
                break  # Break to not go over all lines, saves a lot of time on big files

    return _TfsMetaData(
        headers=headers,
        non_data_lines=line_record.index[0],  # skip these lines
        column_names=column_names,
        column_types=column_types,
    )


def _parse_header(str_list: list[str]) -> tuple[str, bool | str | int | float]:
    """
    Expects a parsed header line content after the '@' header identifier,
    as a .

    Args:
        str_list (list[str]): list of parsed elements from the header line
            (we use parse in reader with 'shlex.split`).

    Returns:
        A tuple with the name of the header parameter for this line, as
        well as its value cast to the proper type (as determined by the
        type identifier).

    Raises:
        AbsentTypeIdentifierError: if no type identifier is found in the header line.
        InvalidBooleanHeaderError: if the identifier type indicates a boolean
            but the corresponding value is not an accepted boolean.
    """
    type_index = next((index for index, part in enumerate(str_list) if part.startswith("%")), None)
    if type_index is None:
        raise AbsentTypeIdentifierError(str_list)

    # Get name and string of the header, and determine its type
    name: str = " ".join(str_list[0:type_index])
    value_string: str = " ".join(str_list[(type_index + 1) :])
    value_string: str = value_string.strip('"')
    value_type: type = _id_to_type(str_list[type_index])

    if value_type is bool:  # special handling for boolean values
        return name, _string_to_bool(value_string)
    elif value_type is np.complex128:  # MAD-NG uses i or I for imaginary but Python needs j
        value_string = value_string.replace("i", "j").replace("I", "j")
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
        data_frame = data_frame.set_index(index_column)
        index_name = index_column[0].replace(INDEX_ID, "")
        if index_name == "":
            index_name = None  # to remove it completely (Pandas makes a difference)
        data_frame = data_frame.rename_axis(index=index_name)
    return data_frame


def _compute_types(str_list: list[str]) -> list[type]:
    return [_id_to_type(string) for string in str_list]


def _string_to_bool(val_str: str) -> bool:
    """
    Infers the boolean value from a string value in the headers.
    Raises ``InvalidBooleanHeaderError`` when encountering invalid value.
    """
    if val_str.lower().capitalize() not in VALID_BOOLEANS_HEADERS:
        raise InvalidBooleanHeaderError(val_str)

    if val_str.lower().capitalize() in VALID_TRUE_BOOLEANS:
        return True
    return False


def _id_to_type(type_identifier: str) -> type:
    try:
        return ID_TO_TYPE[type_identifier]
    except KeyError as err:  # could be a "%[num]s" that MAD-X likes to output
        if _is_madx_string_col_identifier(type_identifier):
            return str
        raise UnknownTypeIdentifierError(type_identifier) from err


def _is_madx_string_col_identifier(type_str: str) -> bool:
    """
    ``MAD-X`` likes to return the string columns by also indicating their width, so trying to parse
    `%s` identifiers only we might miss those looking like `%20s` specifying (here) a 20-character
     wide column for strings.

    Args:
        type_str (str): the suspicious identifier.

    Returns:
        ``True`` if the identifier is identified as coming from ``MAD-X``, ``False`` otherwise.
    """
    if not (type_str.startswith("%") and type_str.endswith("s")):
        return False
    try:
        _ = int(type_str[1:-1])
        return True
    except ValueError:
        return False


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
