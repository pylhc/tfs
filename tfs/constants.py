"""
Constants
---------

General constants used throughout ``tfs-pandas``, relating to the standard of **TFS** files.
"""

from __future__ import annotations  # for delayed type annotations

from types import NoneType

import numpy as np

# ----- TFS Format Details ----- #

HEADER: str = "@"
NAMES: str = "*"
TYPES: str = "$"
COMMENTS: str = "#"
INDEX_ID: str = "INDEX&&&"

# ----- Types Mapping ----- #

# These are used when reading files
ID_TO_TYPE: dict[str, type] = {
    "%s": str,
    "%b": bool,
    "%bpm_s": str,
    "%le": np.float64,
    "%f": np.float64,
    "%hd": np.int64,
    "%d": np.int64,
    "%lz": np.complex128,
    "%n": NoneType,
}

# ----- Specific Accepted Values ----- #

VALID_TRUE_BOOLEANS: set[str] = {"True", "1"}  # checks resolve to capitalized case
VALID_FALSE_BOOLEANS: set[str] = {"False", "0"}  # checks resolve to capitalized case
VALID_BOOLEANS_HEADERS: set[str] = VALID_TRUE_BOOLEANS | VALID_FALSE_BOOLEANS

VALIDATION_MODES: set[str] = {"madx", "mad-x", "madng", "mad-ng"}

# ----- Default Values ----- #

DEFAULT_COLUMN_WIDTH: int = 20
MIN_COLUMN_WIDTH: int = 10
