import pathlib

import pytest

from tfs.frame import TfsDataFrame, validate

CURRENT_DIR = pathlib.Path(__file__).parent


class TestFailures:
    def test_validate_raises_on_wrong_unique_behavior(self):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(ValueError):
            validate(df, "", non_unique_behavior="invalid")
