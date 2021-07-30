import pathlib

import pytest

import tfs
from tfs import TfsDataFrame

CURRENT_DIR = pathlib.Path(__file__).parent


class TestFailures:
    def test_validate_raises_on_wrong_unique_behavior(self, caplog):
        df = TfsDataFrame(index=["A", "B", "A"], columns=["A", "B", "A"])
        with pytest.raises(KeyError):
            tfs.frame.validate(df, "", non_unique_behavior="invalid")


class TestPrinting:
    def test_header_print(self):
        headers = {"param": 3, "other": "hello"}
        df = TfsDataFrame(headers=headers)
        print_out = str(df)
        assert "Headers" in print_out

        for key, val in headers.items():
            assert key in print_out
            assert str(val) in print_out
