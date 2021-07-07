"""
Handler
-------------------

Basic tfs files IO functionality.
"""
import logging
import pathlib
import shlex
from collections import OrderedDict
from contextlib import suppress
from typing import List, Union

import numpy as np
import pandas as pd
from pandas.api import types as pdtypes

LOGGER = logging.getLogger(__name__)

HEADER = "@"
NAMES = "*"
TYPES = "$"
COMMENTS = "#"
INDEX_ID = "INDEX&&&"
ID_TO_TYPE = {  # used when reading files
    "%s": str,  # np.str is a deprecated alias to str
    "%bpm_s": str,  # np.str is a deprecated alias to str
    "%le": np.float64,
    "%f": np.float64,
    "%hd": np.int64,
    "%d": np.int64,
}
DEFAULT_COLUMN_WIDTH = 20
MIN_COLUMN_WIDTH = 10


class TfsDataFrame(pd.DataFrame):
    """
    Class to hold the information of the built extended `pandas` DataFrame, together with a way of
    getting the headers of the TFS file. As the file headers are stored in a dictionary upon read,
    to get a header value use ``data_frame["header_name"]``.
    """

    _metadata = ["headers"]

    def __init__(self, *args, **kwargs):
        self.headers = OrderedDict()
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

    def __repr__(self):
        space = " " * 4

        def _str_items(items_list):
            return "\n".join(f"{space}{k}: {v}" for k, v in items_list)

        s = ""
        if len(self.headers):
            s += "Headers:\n"
            if len(self.headers) > 7:
                items = list(self.headers.items())
                s += f"{_str_items(items[:3])}\n{space}...\n{_str_items(items[-3:])}\n"
            else:
                s += f"{_str_items(self.headers.items())}\n"
            s += "\n"
        return f"{s}{super().__repr__()}"


def read_tfs(
    tfs_file_path: Union[pathlib.Path, str], index: str = None, non_unique_behavior: str = "warn"
) -> TfsDataFrame:
    """
    Parses the TFS table present in **tfs_file_path** and returns a customized version of a Pandas
    DataFrame (a TfsDataFrame).

    Methodology: This function parses the first lines of the file until it gets to the `types` line.
    While parsed, the appropriate information is gathered (headers content, column names & types,
    number of lines parsed). After reaching the types lines, the rest of the file is given to parse
    to ``pandas.read_csv`` with the right options to make use of it's C engine's speed. After this,
    conversion to ``TfsDataDrame`` is made, proper types are applied to columns, the index is set and
    the frame is validated before being returned.

    Args:
        tfs_file_path (Union[pathlib.Path, str]): PosixPath object to the output TFS file. Can be
            a string, in which case it will be cast to a PosixPath object.
        index (str): Name of the column to set as index. If not given, looks in **tfs_file_path**
            for a column starting with `INDEX&&&`.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts **warn** and **raise** as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.

    Returns:
        A TfsDataFrame object with the loaded data from the file.
    """
    tfs_file_path = pathlib.Path(tfs_file_path)
    headers = OrderedDict()
    non_data_lines: int = 0
    column_names = column_types = None

    LOGGER.debug(f"Reading path: {tfs_file_path.absolute()}")
    with tfs_file_path.open("r") as tfs_data:
        for line in tfs_data:
            non_data_lines += 1
            line_components = shlex.split(line)
            if not line_components:
                continue
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

    if column_names is None:
        LOGGER.error(f"No column names in file {tfs_file_path.absolute()}, aborting")
        raise TfsFormatError("Column names have not been set.")
    if column_types is None:
        LOGGER.error(f"No column types in file {tfs_file_path.absolute()}, aborting")
        raise TfsFormatError("Column types have not been set.")

    LOGGER.debug("Parsing data part of the file")
    # DO NOT use comment=COMMENTS in here, if you do and the symbol is in an element for some
    # reason then the entire parsing will crash
    data_frame = pd.read_csv(
        tfs_file_path,
        engine="c",  # faster, and we do not need the features of the python engine
        skiprows=non_data_lines - 1,  # because we incremented for the first data line in loop above
        delim_whitespace=True,  # understands ' ' is our delimiter
        skipinitialspace=True,  # understands ' ' and '     ' are both valid delimiters
        quotechar='"',  # elements surrounded by " are one entry -> correct parsing of strings with spaces
        names=column_names,  # column names we have determined, avoids using first read row for columns
    )

    LOGGER.debug("Converting to TfsDataFrame")
    tfs_data_frame = TfsDataFrame(data_frame, headers=headers)
    _assign_column_types(tfs_data_frame, column_names, column_types)  # ensure proper types

    if index:
        LOGGER.debug(f"Setting '{index}' column as index")
        tfs_data_frame = tfs_data_frame.set_index(index)
    else:
        LOGGER.debug("Attempting to find index identifier in columns")
        tfs_data_frame = _find_and_set_index(tfs_data_frame)

    _validate(tfs_data_frame, f"from file {tfs_file_path.absolute()}", non_unique_behavior)
    return tfs_data_frame


def write_tfs(
    tfs_file_path: Union[pathlib.Path, str],
    data_frame: Union[TfsDataFrame, pd.DataFrame],
    headers_dict: dict = None,
    save_index: Union[str, bool] = False,
    colwidth: int = DEFAULT_COLUMN_WIDTH,
    headerswidth: int = DEFAULT_COLUMN_WIDTH,
    non_unique_behavior: str = "warn",
) -> None:
    """
    Writes the DataFrame into **tfs_file_path** with the `headers_dict` as headers dictionary. If
    you want to keep the order of the headers upon write, use a ``collections.OrderedDict``.

    Args:
        tfs_file_path (Union[pathlib.Path, str]): PosixPath object to the output TFS file. Can be
            a string, in which case it will be cast to a PosixPath object.
        data_frame (Union[TfsDataFrame, pd.DataFrame]): `TfsDataFrame` or `pandas.DataFrame` to
            write to file.
        headers_dict (dict): Headers of the data_frame. If not provided, assumes a `TfsDataFrame`
            was given and tries to use ``data_frame.headers``.
        save_index (Union[str, bool]): bool or string. Default to ``False``. If ``True``, saves
            the index of the data_frame to a column identifiable by `INDEX&&&`. If given as string,
            saves the index of the data_frame to a column named by the provided value.
        colwidth (int): Column width, can not be smaller than `MIN_COLUMN_WIDTH`.
        headerswidth (int): Used to format the header width for both keys and values.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts **warn** and **raise** as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.
    """
    left_align_first_column = False
    tfs_file_path = pathlib.Path(tfs_file_path)
    _validate(data_frame, f"to be written in {tfs_file_path.absolute()}", non_unique_behavior)

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
    with tfs_file_path.open("w") as tfs_data:
        tfs_data.write(
            "\n".join(
                (line for line in (headers_str, colnames_str, coltypes_str, data_str) if line)
            )
        )


def _autoset_pandas_types(
    data_frame: Union[TfsDataFrame, pd.DataFrame]
) -> Union[TfsDataFrame, pd.DataFrame]:
    """
    Tries to apply the .convert_dtypes() method of pandas on a copy on the provided dataframe. If
    the operation is not possible, checks if the provided dataframe is empty (which prevents
    convert_dtypes() to internally use concat) and then return only a copy of the original
    dataframe. Otherwise, raise the exception given by pandas.

    NOTE: Starting with pandas 1.3.0, this behavior which was a bug has been fixed. This means no
    ValueError is raised by calling .convert_dtypes() on an empty DataFrame, and from this function
    no warning is logged. Testing of this behavior is disabled for Python 3.7+ workers, but the
    function is kept as to not force a new min version requirement on pandas or Python for users.
    See my comment at https://github.com/pylhc/tfs/pull/83#issuecomment-874208869

    Args:
        data_frame (Union[TfsDataFrame, pd.DataFrame]): TfsDataFrame or pandas.DataFrame to
            determine the types of.

    Returns:
        The dataframe with dtypes inferred as much as possible to the pandas dtypes.
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


def _insert_index_column(data_frame, save_index):
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
    Returns the string to write a `TfsDataFrame`'s headers to file. Will return an empty string if
    called for an empty headers dictionary, in order not write an line to file.

    Args:
        headers_dict (dict): the `TfsDataFrame`'s headers.
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


def _get_colnames_string(colnames, colwidth, left_align_first_column) -> str:
    format_string = _get_row_format_string(
        [None] * len(colnames), colwidth, left_align_first_column
    )
    return "* " + format_string.format(*colnames)


def _get_coltypes_string(types, colwidth, left_align_first_column) -> str:
    fmt = _get_row_format_string([str] * len(types), colwidth, left_align_first_column)
    return "$ " + fmt.format(*[_dtype_to_id_string(type_) for type_ in types])


def _get_data_string(data_frame, colwidth, left_align_first_column) -> str:
    if len(data_frame.index) == 0 or len(data_frame.columns) == 0:
        return "\n"
    format_strings = "  " + _get_row_format_string(
        data_frame.dtypes, colwidth, left_align_first_column
    )
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


def _quote_string_columns(data_frame):
    def quote_strings(s):
        if isinstance(s, str):
            if not (s.startswith('"') or s.startswith("'")):
                return f'"{s}"'
        return s

    data_frame = data_frame.applymap(quote_strings)
    return data_frame


def _find_and_set_index(data_frame: TfsDataFrame) -> TfsDataFrame:
    """
    Looks for a column with a name starting with the index identifier, and sets it as index if found.
    The index identifier will be stripped from the column name first.

    Args:
        data_frame (TfsDataFrame): the TfsDataFrame to look for an index in.

    Returns:
        The TfsDataFrame after operation, whether an index was found or not.
    """
    index_column = [colname for colname in data_frame.columns if colname.startswith(INDEX_ID)]
    if index_column:
        data_frame = data_frame.set_index(index_column)
        index_name = index_column[0].replace(INDEX_ID, "")
        if index_name == "":
            index_name = None  # to remove it completely (Pandas makes a difference)
        data_frame = data_frame.rename_axis(index=index_name)
    return data_frame


def _create_data_frame(column_names, column_types, rows_list, headers) -> TfsDataFrame:
    data = np.array(rows_list) if rows_list else None  # case of empty dataframe
    tfs_data_frame = TfsDataFrame(data=data, columns=column_names, headers=headers)
    _assign_column_types(tfs_data_frame, column_names, column_types)
    return tfs_data_frame


def _assign_column_types(data_frame, column_names, column_types) -> None:
    names_to_types = dict(zip(column_names, column_types))
    for name in names_to_types:
        data_frame[name] = data_frame[name].astype(names_to_types[name])


def _compute_types(str_list: list) -> list:
    return [_id_to_type(string) for string in str_list]


def _parse_header(str_list: list) -> tuple:
    type_index = next((index for index, part in enumerate(str_list) if part.startswith("%")), None)
    if type_index is None:
        raise TfsFormatError(f"No data type found in header: '{''.join(str_list)}'")

    name = " ".join(str_list[0:type_index])
    value_string = " ".join(str_list[(type_index + 1) :])
    return name, _id_to_type(str_list[type_index])(value_string.strip('"'))


def _id_to_type(type_str: str) -> type:
    try:
        return ID_TO_TYPE[type_str]
    except KeyError:  # could be a "%[num]s" that MAD-X likes to output
        if _is_madx_string_col_identifier(type_str):
            return str
        raise TfsFormatError(f"Unknown data type: {type_str}")


def _is_madx_string_col_identifier(type_str: str) -> bool:
    """
    `MAD-X` likes to return the string columns by also indicating their width, so trying to parse
    `%s` identifiers only we might miss those looking like `%20s` specifying (here) a 20-character
     wide column for strings.

    Args:
        type_str (str): the suspicious identifier.

    Returns:
        ``True`` if the identifier is identified as coming from `MAD-X`, ``False`` otherwise.
    """
    if not (type_str.startswith("%") and type_str.endswith("s")):
        return False
    try:
        _ = int(type_str[1:-1])
        return True
    except ValueError:
        return False


def _value_to_type_string(value) -> str:
    dtype_ = np.array(value).dtype  # let numpy handle conversion to it dtypes
    return _dtype_to_id_string(dtype_)


def _dtype_to_id_string(type_: type) -> str:
    """
    Return the proper TFS identifier for the provided dtype.

    Args:
        type_ (type): an instance of the built-in type (in this package, one of numpy or pandas
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
        f"Provided type '{type_}' could not be identified as either a bool, int, "
        f"float or string dtype"
    )


def _dtype_to_formatter(type_: type, colsize: int) -> str:
    """
    Return the proper string formatter for the provided dtype.

    Args:
        type_ (type): an instance of the built-in type (in this package, one of numpy or pandas
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
        f"Provided type '{type_}' could not be identified as either a bool, int, "
        f"float or string dtype"
    )


class TfsFormatError(Exception):
    """Raised when a wrong format is detected in the TFS file."""

    pass


def _validate(
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
