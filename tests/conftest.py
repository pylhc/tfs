import pathlib

import pytest

INPUTS_DIR = pathlib.Path(__file__).parent / "inputs"


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
