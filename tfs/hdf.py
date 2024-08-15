"""
HDF5 I/O
--------

Additional tools for reading and writing ``TfsDataFrames`` into ``hdf5`` files.
"""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

import pandas as pd

from tfs import TfsDataFrame

if TYPE_CHECKING:
    from pathlib import Path

try:
    import h5py
except ImportError:
    h5py = None

try:
    import tables
except ImportError:
    tables = None

LOGGER = logging.getLogger(__name__)


def write_hdf(path: Path | str, df: TfsDataFrame, **kwargs) -> None:
    """Write TfsDataFrame to hdf5 file. The dataframe will be written into
    the group ``data``, the headers into the group ``headers``.
    Only one dataframe per file is allowed.

    Args:
        path (Path, str): Path of the output file.
        df (TfsDataFrame): TfsDataFrame to write.
        kwargs: kwargs to be passed to pandas ``DataFrame.to_hdf()``.
                ``key`` is not allowed and ``mode`` needs to be ``w`` if the
                output file already exists (``w`` will be used in any case,
                even if the file does not exist, but only a warning is logged
                in that case).
    """
    _check_imports()
    # Check for `key` kwarg (forbidden) ---
    if "key" in kwargs:
        errmsg = "The argument 'key' is not allowed here, as only one TfsDataFrame per file is supported."
        raise AttributeError(errmsg)

    # Check for `mode` kwarg (allowed under circumstances but generally ignored) ---
    user_mode = kwargs.pop("mode", None)
    if user_mode is not None and user_mode != "w":
        if path.exists():
            errmsg = (
                f"'mode=\"{user_mode}\"' is not allowed here."
                f"The output file at {path!s} will always be overwritten!"
            )
            raise AttributeError(errmsg)
        LOGGER.warning(f'\'mode="{user_mode}"\' is not allowed here. Mode "w" will be used.')

    # Actual writing of the output file ---
    df.to_hdf(path, key="data", mode="w", **kwargs)
    with h5py.File(path, mode="a") as hf:
        hf.create_group("headers")  # empty group in case of empty headers
        for key, value in df.headers.items():
            hf.create_dataset(f"headers/{key}", data=value)


def read_hdf(path: Path | str) -> TfsDataFrame:
    """Read TfsDataFrame from hdf5 file. The DataFrame needs to be stored
    in a group named ``data``, while the headers are stored in ``headers``.

    Args:
        path (Path, str): Path of the file to read.

    Returns:
        A ``TfsDataFrame`` object with the loaded data from the file.
    """
    _check_imports()
    df = pd.read_hdf(path, key="data")
    with h5py.File(path, mode="r") as hf:
        headers = hf.get("headers")
        headers = {key: headers[key][()] for key in headers}

    for key, value in headers.items():
        with contextlib.suppress(AttributeError):  # probably numeric
            headers[key] = value.decode("utf-8")  # converts byte-strings back
    return TfsDataFrame(df, headers=headers)


def _check_imports():
    """Checks if required packages for HDF5 functionality are installed. Raises ImportError if not."""
    not_imported = [name for name, package in (("tables", tables), ("h5py", h5py)) if package is None]
    if len(not_imported):
        names = ", ".join(f"`{name}`" for name in not_imported)
        errmsg = (
            f"Package(s) {names} could not be imported."
            "Please make sure that this package is installed to use hdf-functionality, "
            "e.g. install `tfs-pandas` with the `hdf5` extra-dependencies: `tfs-pandas[hdf5]`"
        )
        raise ImportError(errmsg)
