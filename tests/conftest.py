import pathlib

import numpy as np
import pandas as pd
import pytest

from tfs import TfsDataFrame

INPUTS_DIR = pathlib.Path(__file__).parent / "inputs"


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


@pytest.fixture
def _tfs_madng_file() -> pathlib.Path:
    """A TFS file withboth complex values and booleans, in headers and columns."""
    return INPUTS_DIR / "madng.tfs"


# The below return (Tfs)DataFrames for the write tests
# as we start with writing, and don't want to start by
# reading the files from disk.


@pytest.fixture
def _pd_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        index=range(3),
        columns="a b c d e".split(),
        data=np.random.rand(3, 5),
    )


@pytest.fixture
def _tfs_dataframe() -> TfsDataFrame:
    return TfsDataFrame(
        index=range(15),
        columns="a b c d e".split(),
        data=np.random.rand(15, 5),
        headers={"Title": "Tfs Title", "Value": 3.3663},
    )


@pytest.fixture
def _tfs_dataframe_booleans() -> TfsDataFrame:
    """TfsDataFrame with boolean values in the headers and data (1 column)."""
    df = TfsDataFrame(
        index=range(15),
        columns="a b c d e".split(),
        data=np.random.rand(15, 5),
        headers={"Title": "Bool Test", "Bool1": True, "Bool2": False, "Bool3": 1},
    )
    df["bools"] = np.random.rand(15) > 0.5  # random from 0 to 1 and then boolean check
    return df


@pytest.fixture
def _tfs_dataframe_complex() -> TfsDataFrame:
    """TfsDataFrame with complex values in the headers and data (1 column)."""
    df = TfsDataFrame(
        index=range(15),
        columns="a b c d e".split(),
        data=np.random.rand(15, 5),
        headers={"Title": "Complex Test", "Complex1": 1 + 2j, "Complex2": -4 - 17.9j},
    )
    df["complex"] = np.random.rand(15) + np.random.rand(15) * 1j
    return df


@pytest.fixture
def _tfs_dataframe_madng() -> TfsDataFrame:
    """
    TfsDataFrame with both booleans and complex
    values in the headers and data (1 column each).
    """
    df = TfsDataFrame(
        index=range(15),
        columns="a b c d e".split(),
        data=np.random.rand(15, 5),
        headers={
            "Title": "MADNG Test",
            "Bool1": True,
            "Bool2": False,
            "A_NIL": None,
            "Complex1": 19.3 + 39.4j,
            "Complex2": -94.6 - 67.9j,
        },
    )
    df["bools"] = np.random.rand(15) > 0.5  # random from 0 to 1 and then boolean check
    df["complex"] = np.random.rand(15) + np.random.rand(15) * 1j
    return df
