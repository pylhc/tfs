"""
Tools
-----

Additional functions to modify **TFS** files.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from tfs.errors import TfsFormatError
from tfs.reader import read_tfs
from tfs.writer import write_tfs

LOGGER = logging.getLogger(__name__)


def significant_digits(
    value: float,
    error: float,
    return_floats: bool = False,  # noqa: FBT001, FBT002
) -> tuple[str, str] | tuple[float, float]:
    """
    Computes `value` and its error properly rounded with respect to the size of `error`.

    Args:
        value (float): a number.
        error (float): the error on the number.
        return_floats (bool): if ``True``, returns significant digits as floats. Otherwise as
            strings. Defaults to ``False``.

    Returns:
        A tuple of the rounded value and error with regards to the size of the error.
    """
    if error == 0:
        errmsg = "Input error of 0. Cannot compute significant digits."
        raise ValueError(errmsg)
    digits = -int(np.floor(np.log10(error)))
    if np.floor(error * 10**digits) == 1:
        digits = digits + 1
    res = (
        f"{round(value, digits):.{max(digits, 0)}f}",
        f"{round(error, digits):.{max(digits, 0)}f}",
    )
    if return_floats:
        return tuple([float(val) for val in res])
    return res


def remove_nan_from_files(list_of_files: list[str | Path], replace: bool = False) -> None:  # noqa: FBT001, FBT002
    """
    Remove ``NaN`` entries from files in `list_of_files`.

    Args:
        list_of_files (list[str | Path]): list of Paths to **TFS** files meant to
            be sanitized. The elements of the list can be strings or Path objects.
        replace (bool): if ``True``, the provided files will be overwritten. Otherwise
            new files with `.dropna` appended to the original filenames will be written
            to disk. Defaults to ``False``.
    """
    for filepath in list_of_files:
        try:
            tfs_data_frame = read_tfs(filepath)
            LOGGER.info(f"Read file {filepath:s}")
        except (OSError, TfsFormatError):
            LOGGER.warning(f"Skipped file {filepath:s} as it could not be loaded")
        else:
            tfs_data_frame = tfs_data_frame.dropna(axis="index")
            exit_filepath = filepath if replace is True else f"{filepath}.dropna"
            write_tfs(exit_filepath, tfs_data_frame)


def remove_header_comments_from_files(list_of_files: list[str | Path]) -> None:
    """
    Check the files in the provided list for invalid headers (no type defined)
    and removes those inplace when found.

    Args:
        list_of_files (list[str | Path]): list of Paths to **TFS** files meant to be checked.
            The entries of the list can be strings or Path objects.
    """
    for filepath in list_of_files:
        LOGGER.info(f"Checking file: {filepath}")
        f_lines = Path(filepath).read_text().splitlines(keepends=True)

        delete_indicies = []
        for index, line in enumerate(f_lines):
            if line.startswith("*"):
                break
            if line.startswith("@") and len(line.split("%")) == 1:
                delete_indicies.append(index)

        if delete_indicies:
            LOGGER.info(f"    Found {len(delete_indicies):d} lines to delete.")
            for index in reversed(delete_indicies):
                deleted_line = f_lines.pop(index)
                LOGGER.info(f"    Deleted line: {deleted_line.strip():s}")

            Path(filepath).write_text("".join(f_lines))
