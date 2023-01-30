"""
Constants
---------

General constants used throughout ``tfs-pandas``, relating to the standard of **TFS** files.
"""
from typing import Dict

import numpy as np

# ----- TFS Format Details ----- #
HEADER: str = "@"
NAMES: str = "*"
TYPES: str = "$"
COMMENTS: str = "#"
INDEX_ID: str = "INDEX&&&"

# ----- Types Mapping ----- #

ID_TO_TYPE: Dict[str, type] = {  # used when reading files
    "%s": str,
    "%bpm_s": str,
    "%le": np.float64,
    "%f": np.float64,
    "%hd": np.int64,
    "%d": np.int64,
}

# ----- Default Values ----- #

DEFAULT_COLUMN_WIDTH: int = 20
MIN_COLUMN_WIDTH: int = 10
