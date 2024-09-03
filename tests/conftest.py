import pathlib
import pytest

INPUT_DIR = pathlib.Path(__file__).parent / "inputs"


@pytest.fixture
def _tfs_filex() -> pathlib.Path:
    return INPUT_DIR / "file_x.tfs"


@pytest.fixture
def _tfs_filey() -> pathlib.Path:
    return INPUT_DIR / "file_y.tfs"
