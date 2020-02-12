"""
Tools
-----------------

Additional functions to modify tfs files.


:author: Jaime
:module: tools

"""
import logging

import numpy as np

from tfs.handler import TfsFormatError, read_tfs, write_tfs

LOG = logging.getLogger(__name__)


def significant_digits(value: float, error: float) -> (str, str):
    """Computes value and its error properly rounded with respect to the size of the error"""
    if error == 0:
        raise ValueError("Input error of 0. Cannot compute significant digits.")
    digits = -int(np.floor(np.log10(error)))
    if np.floor(error * 10 ** digits) == 1:
        digits = digits + 1
    return (
        f"{round(value, digits):.{max(digits, 0)}f}",
        f"{round(error, digits):.{max(digits, 0)}f}",
    )


def remove_nan_from_files(list_of_files: list, replace: bool = None) -> None:
    """ Remove NAN-Entries from files in list_of_files.

    If replace=False a new file with .dropna appended to its name is created, otherwise the file is
    overwritten.
    """
    replace = False if replace is None else replace
    for filepath in list_of_files:
        try:
            tfs_data_frame = read_tfs(filepath)
            LOG.info(f"Read file {filepath:s}")
        except (IOError, TfsFormatError):
            LOG.info(f"Skipped file {filepath:s}")
        else:
            tfs_data_frame = tfs_data_frame.dropna(axis="index")
            if not replace:
                filepath += ".dropna"
            write_tfs(filepath, tfs_data_frame)


def remove_header_comments_from_files(list_of_files: list) -> None:
    """
    Check the files in the provided list for invalid headers (no type defined) and
    removes those when found.
    """
    for filepath in list_of_files:
        LOG.info(f"Checking file: {filepath}")
        with open(filepath, "r") as f:
            f_lines = f.readlines()

        detele_indicies = []
        for index, line in enumerate(f_lines):
            if line.startswith("*"):
                break
            if line.startswith("@") and len(line.split("%")) == 1:
                detele_indicies.append(index)

        if detele_indicies:
            LOG.info(f"    Found {len(detele_indicies):d} lines to delete.")
            for index in reversed(detele_indicies):
                deleted_line = f_lines.pop(index)
                LOG.info(f"    Deleted line: {deleted_line.strip():s}")

            with open(filepath, "w") as f:
                f.writelines(f_lines)


class DotDict(dict):
    """ Make dict fields accessible by . """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self:
            if isinstance(self[key], dict):
                self[key] = DotDict(self[key])

    # __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getattr__(self, key: object) -> object:
        """ Needed to raise the correct exceptions """
        try:
            return super().__getitem__(key)
        except KeyError as e:
            raise AttributeError(e).with_traceback(e.__traceback__) from e
