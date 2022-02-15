"""
Reader
-------------------

Reading functionalty for **TFS** files.
"""
import logging
import pathlib
import shlex
from collections import OrderedDict
from typing import List, Union

import numpy as np
import pandas as pd

from tfs.constants import COMMENTS, HEADER, ID_TO_TYPE, INDEX_ID, NAMES, TYPES
from tfs.errors import TfsFormatError
from tfs.frame import TfsDataFrame, validate

LOGGER = logging.getLogger(__name__)


def read_tfs(
    tfs_file_path: Union[pathlib.Path, str], index: str = None, non_unique_behavior: str = "warn"
) -> TfsDataFrame:
    """
    Parses the **TFS** table present in **tfs_file_path** and returns a ``TfsDataFrame``.

    Methodology: This function parses the first lines of the file until it gets to the `types` line.
    While parsed, the appropriate information is gathered (headers content, column names & types,
    number of lines parsed). After reaching the `types` line, the rest of the file is given to parse
    to ``pandas.read_csv`` with the right options to make use of its C engine's speed. After this,
    conversion to ``TfsDataDrame`` is made, proper types are applied to columns, the index is set and
    the frame is validated before being returned.

    Args:
        tfs_file_path (Union[pathlib.Path, str]): Path object to the **TFS** file to read. Can be
            a string, in which case it will be cast to a Path object.
        index (str): Name of the column to set as index. If not given, looks in **tfs_file_path**
            for a column starting with `INDEX&&&`.
        non_unique_behavior (str): behavior to adopt if non-unique indices or columns are found in the
            dataframe. Accepts `warn` and `raise` as values, case-insensitively, which dictates
            to respectively issue a warning or raise an error if non-unique elements are found.

    Returns:
        A ``TfsDataFrame`` object with the loaded data from the file.
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
        raise TfsFormatError(f"No column names in file {tfs_file_path.absolute()}. File not read.")
    if column_types is None:
        raise TfsFormatError(f"No column types in file {tfs_file_path.absolute()}. File not read.")

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

    validate(tfs_data_frame, f"from file {tfs_file_path.absolute()}", non_unique_behavior)
    return tfs_data_frame


def _parse_header(str_list: List[str]) -> tuple:
    type_index = next((index for index, part in enumerate(str_list) if part.startswith("%")), None)
    if type_index is None:
        raise TfsFormatError(f"No data type found in header: '{''.join(str_list)}'")

    name = " ".join(str_list[0:type_index])
    value_string = " ".join(str_list[(type_index + 1) :])
    return name, _id_to_type(str_list[type_index])(value_string.strip('"'))


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


def _assign_column_types(data_frame: TfsDataFrame, column_names: List[str], column_types: List[type]) -> None:
    names_to_types = dict(zip(column_names, column_types))
    for name in names_to_types:
        data_frame[name] = data_frame[name].astype(names_to_types[name])


def _compute_types(str_list: List[str]) -> List[type]:
    return [_id_to_type(string) for string in str_list]


def _id_to_type(type_str: str) -> type:
    try:
        return ID_TO_TYPE[type_str]
    except KeyError:  # could be a "%[num]s" that MAD-X likes to output
        if _is_madx_string_col_identifier(type_str):
            return str
        raise TfsFormatError(f"Unknown data type: {type_str}")


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
