"""
Handler
-------------------

Basic tfs-to-pandas io-functionality.

:module: handler

"""
import logging
import pathlib
import shlex
from collections import OrderedDict
from contextlib import suppress
from typing import Union

import numpy as np
import pandas
from pandas import DataFrame

LOGGER = logging.getLogger(__name__)

HEADER = "@"
NAMES = "*"
TYPES = "$"
COMMENTS = "#"
INDEX_ID = "INDEX&&&"
ID_TO_POSSIBLE_TYPES = {  # only numpy types allowed in np.issubdtype
    "%le": (np.floating,),
    "%d":  (np.integer, np.bool_),
    "%s":  (np.str_, np.object_),
}

ID_TO_TYPE = {
    "%s": np.str,
    "%bpm_s": np.str,
    "%le": np.float64,
    "%f": np.float64,
    "%hd": np.int,
    "%d": np.int,
}
DEFAULT_COLUMN_WIDTH = 20
MIN_COLUMN_WIDTH = 10


class TfsDataFrame(pandas.DataFrame):
    """
    Class to hold the information of the built Pandas DataFrame,
    together with a way of getting the headers of the TFS file.
    To get a header value do: data_frame["header_name"] or
    data_frame.header_name.
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
        except KeyError as e:
            try:
                return self.headers[key]
            except KeyError:
                raise KeyError(f"{key} is neither in the DataFrame nor in headers.")
            except TypeError:
                raise e

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

        def _str_items(items):
            return '\n'.join(f'{space}{k}: {v}' for k, v in items)

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


def read_tfs(tfs_file_path: Union[pathlib.Path, str], index: str = None) -> TfsDataFrame:
    """
    Parses the TFS table present in tfs_path and returns a custom Pandas DataFrame (TfsDataFrame).

    Args:
        tfs_file_path: pathlib.Path of the input TFS file, can be str but will be cast to pathlib.Path
        index: Name of the column to set as index. If not given looks for INDEX_ID-column

    Returns:
        TfsDataFrame object
    """
    tfs_file_path = pathlib.Path(tfs_file_path)
    LOGGER.debug(f"Reading path: {tfs_file_path.absolute()}")
    headers = OrderedDict()
    rows_list = []
    column_names = column_types = None

    with tfs_file_path.open("r") as tfs_data:
        for line in tfs_data:
            parts = shlex.split(line)
            if len(parts) == 0:
                continue
            if parts[0] == HEADER:
                name, value = _parse_header(parts[1:])
                headers[name] = value
            elif parts[0] == NAMES:
                LOGGER.debug("Setting column names.")
                column_names = np.array(parts[1:])
            elif parts[0] == TYPES:
                LOGGER.debug("Setting column types.")
                column_types = _compute_types(parts[1:])
            elif parts[0] == COMMENTS:
                continue
            else:
                if column_names is None:
                    raise TfsFormatError("Column names have not been set.")
                if column_types is None:
                    raise TfsFormatError("Column types have not been set.")
                parts = [part.strip('"') for part in parts]
                rows_list.append(parts)
    data_frame = _create_data_frame(column_names, column_types, rows_list, headers)

    if index is not None:  # Use given column as index
        data_frame = data_frame.set_index(index)
    else:  # Try to find Index automatically
        index_column = [colname for colname in data_frame.columns if colname.startswith(INDEX_ID)]
        if index_column:
            data_frame = data_frame.set_index(index_column)
            index_name = index_column[0].replace(INDEX_ID, "")
            if index_name == "":
                index_name = None  # to remove it completely (Pandas makes a difference)
            data_frame = data_frame.rename_axis(index_name)

    _validate(data_frame, f"from file {tfs_file_path.absolute()}")
    return data_frame


def write_tfs(
    tfs_file_path: Union[pathlib.Path, str],
    data_frame: DataFrame,
    headers_dict: dict = None,
    save_index: Union[str, bool] = False,
    colwidth: int = DEFAULT_COLUMN_WIDTH,
    headerswidth: int = DEFAULT_COLUMN_WIDTH,
) -> None:
    """
    Writes the DataFrame into tfs_path with the headers_dict as headers dictionary.
    If you want to keep the order of the headers, use collections.OrderedDict.

    Args:
        tfs_file_path: pathlib.Path to the output TFS file, can be str but will be cast to pathlib.Path
        data_frame: TfsDataFrame or pandas.DataFrame to save
        headers_dict: Headers of the data_frame, if empty tries to use data_frame.headers
        save_index: bool or string. Default: False
            If True, saves the index of the data_frame to a column identifiable by INDEX_ID.
            If string, it saves the index of the data_frame to a column named by string.
        colwidth: Column width, can not be smaller than MIN_COLUMN_WIDTH
        headerswidth: Formats the header width for both, keys and values
    """
    tfs_file_path = pathlib.Path(tfs_file_path)
    _validate(data_frame, f"to be written in {tfs_file_path.absolute()}")
    data_frame = data_frame.copy()  # as it might be changed
    left_align_first_column = False
    if save_index:
        left_align_first_column = True
        _insert_index_column(data_frame, save_index)

    if headers_dict is None:  # tries to get headers from TfsDataFrame
        try:
            headers_dict = data_frame.headers
        except AttributeError:
            headers_dict = {}

    colwidth = max(MIN_COLUMN_WIDTH, colwidth)
    headers_str = _get_headers_string(headers_dict, headerswidth)
    colnames_str = _get_colnames_string(data_frame.columns, colwidth, left_align_first_column)
    coltypes_str = _get_coltypes_string(data_frame.dtypes, colwidth, left_align_first_column)
    data_str = _get_data_string(data_frame, colwidth, left_align_first_column)

    LOGGER.debug(f"Attempting to write file: {tfs_file_path.name} in {tfs_file_path.parent}")
    with tfs_file_path.open("w") as tfs_data:
        tfs_data.write("\n".join((headers_str, colnames_str, coltypes_str, data_str)))


def _insert_index_column(data_frame, save_index):
    if isinstance(save_index, str):  # save index into column by name given
        idx_name = save_index
    else:  # save index into column, which can be found by INDEX_ID
        try:
            idx_name = INDEX_ID + data_frame.index.name
        except TypeError:
            idx_name = INDEX_ID
    data_frame.insert(0, idx_name, data_frame.index)


def _get_headers_string(headers_dict, width) -> str:
    return "\n".join(_get_header_line(name, headers_dict[name], width) for name in headers_dict)


def _get_header_line(name: str, value, width: int) -> str:
    if not isinstance(name, str):
        raise ValueError(f"{name} is not a string")
    type_str = _value_to_type_string(value)
    if type_str == "%s":
        value = f'"{value}"'
    return f"@ {name:<{width}} {type_str} {value:>{width}}"


def _get_colnames_string(colnames, colwidth, left_align_first_column) -> str:
    format_string = _get_row_format_string([None] * len(colnames), colwidth, left_align_first_column)
    return "* " + format_string.format(*colnames)


def _get_coltypes_string(types, colwidth, left_align_first_column) -> str:
    fmt = _get_row_format_string([str] * len(types), colwidth, left_align_first_column)
    return "$ " + fmt.format(*[_dtype_to_str(type_) for type_ in types])


def _get_data_string(data_frame, colwidth, left_align_first_column) -> str:
    if len(data_frame.index) == 0 or len(data_frame.columns) == 0:
        return "\n"
    format_strings = "  " + _get_row_format_string(
        data_frame.dtypes, colwidth, left_align_first_column
    )
    data_frame = _quote_string_columns(data_frame)
    return "\n".join(data_frame.apply(lambda series: format_strings.format(*series), axis=1))


def _get_row_format_string(dtypes, colwidth, left_align_first_column) -> str:
    return " ".join(
        f"{{{indx:d}:"
        f"{'<' if (not indx) and left_align_first_column else '>'}"
        f"{_dtype_to_format(type_, colwidth)}}}"
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
    except KeyError:
        if type_str.startswith("%") and type_str.endswith("s"):
            return str
        raise TfsFormatError(f"Unknown data type: {type_str}")


def _dtype_to_str(type_) -> str:
    for id, types in ID_TO_POSSIBLE_TYPES.items():
        if any(np.issubdtype(type_, t) for t in types):
            return id
    else:
        raise ValueError(f"{type_} does not correspond to any recognized type.")


def _value_to_type_string(value) -> str:
    dtype_ = np.array(value).dtype  # let numpy handle conversion to it dtypes
    return _dtype_to_str(dtype_)


def _dtype_to_format(type_, colsize) -> str:
    if type_ is None:
        return f"{colsize}"
    if np.issubdtype(type_, np.integer) or np.issubdtype(type_, np.bool_):
        return f"{colsize}d"
    if np.issubdtype(type_, np.floating):
        return f"{colsize}.{colsize - len('-0.e-000')}g"
    return f"{colsize}s"


class TfsFormatError(Exception):
    """Raised when wrong format is detected in the TFS file."""
    pass


def _validate(data_frame, info_str=""):
    """
    Check if Dataframe contains finite values only
    and both indices and columns are unique.
    """

    def isnotfinite(x):
        try:
            return ~np.isfinite(x)
        except TypeError:  # most likely string
            try:
                return np.zeros(x.shape, dtype=bool)
            except AttributeError:  # single entry
                return np.zeros(1, dtype=bool)

    boolean_df = data_frame.apply(isnotfinite)

    if boolean_df.values.any():
        LOGGER.warning(
            f"DataFrame {info_str} contains non-physical values at Index: "
            f"{boolean_df.index[boolean_df.any(axis='columns')].tolist()}"
        )

    if len(set(data_frame.index)) != len(data_frame.index):
        raise TfsFormatError("Indices are not Unique.")

    if len(set(data_frame.columns)) != len(data_frame.columns):
        raise TfsFormatError("Column names not Unique.")

    if any(" " in c for c in data_frame.columns):
        raise TfsFormatError("TFS-Columns can not contain spaces.")

    if any(" " in h for h in data_frame.headers.keys()):
        raise TfsFormatError("TFS-Header names can not contain spaces.")

    LOGGER.debug(f"DataFrame {info_str} validated.")
