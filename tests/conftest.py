import pathlib

import numpy as np
import pytest
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

from tfs import TfsDataFrame

INPUTS_DIR = pathlib.Path(__file__).parent / "inputs"


# ----- Helpers ----- #


def assert_tfs_frame_equal(df1, df2, **kwargs):
    assert_frame_equal(df1, df2, **kwargs)
    assert_dict_equal(df1.headers, df2.headers, compare_keys=True)


# ----- Fixtures ----- #


@pytest.fixture
def _tfs_filex() -> pathlib.Path:
    return INPUTS_DIR / "file_x.tfs"


@pytest.fixture
def _tfs_filey() -> pathlib.Path:
    return INPUTS_DIR / "file_y.tfs"


@pytest.fixture
def _tfs_booleans_file() -> pathlib.Path:
    """A TFS file with BOOL in headers and in a column."""
    return INPUTS_DIR / "booleans.tfs"


@pytest.fixture
def _tfs_complex_file() -> pathlib.Path:
    """A TFS file with complex values in headers and in a column."""
    return INPUTS_DIR / "complex.tfs"


@pytest.fixture()
def _tfs_madng_file() -> pathlib.Path:
    """A TFS file withboth complex values and booleans, in headers and columns."""
    return INPUTS_DIR / "madng.tfs"


@pytest.fixture
def _tfs_dataframe() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(15),
        columns="a b c d e".split(),
        data=np.random.rand(15, 5),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )
