import os
import pathlib
import tempfile

import pytest
from pandas.testing import assert_frame_equal

from tfs import read_tfs
from tfs.collection import TfsCollection, Tfs
from tfs.handler import TfsDataFrame

CURRENT_DIR = pathlib.Path(__file__).parent


class CollectionTest(TfsCollection):
    file = Tfs("file_{}.tfs")
    nofile = Tfs("nofile_{}.tfs")
    filex = Tfs("file_X.tfs", two_planes=False)
    value = 10

    def get_filename(self, template, plane=""):
        return template.format(plane)


def test_read_pathlib_input(_input_dir_pathlib: pathlib.Path, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame):
    c = CollectionTest(_input_dir_pathlib)
    assert_frame_equal(_tfs_x, c.file_x)
    assert_frame_equal(_tfs_x, c.filex)
    assert_frame_equal(_tfs_y, c.file["y"])
    assert c.value == 10


def test_read_str_input(_input_dir_str: str, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame):
    c = CollectionTest(_input_dir_str)
    assert_frame_equal(_tfs_x, c.file_x)
    assert_frame_equal(_tfs_x, c.filex)
    assert_frame_equal(_tfs_y, c.file["y"])
    assert c.value == 10


def test_write(_tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame, _output_dir: str):
    c = CollectionTest(_output_dir)
    file_x_path = pathlib.Path(_output_dir) / "nofile_X.tfs"
    assert not file_x_path.is_file()

    c.nofile_x = _tfs_x  # will not throw error, but does nothing
    assert not file_x_path.is_file()

    c.allow_write = True
    c.nofile_x = _tfs_x
    assert file_x_path.is_file()
    assert_frame_equal(_tfs_x, c.nofile_x)

    c.nofile["y"] = _tfs_y
    file_y_path = pathlib.Path(_output_dir) / "nofile_Y.tfs"
    assert file_y_path.is_file()
    assert_frame_equal(_tfs_y, c.nofile["y"])


def test_maybe_pathlib_input(_input_dir_pathlib: pathlib.Path):
    c = CollectionTest(_input_dir_pathlib)
    c.maybe_call.nofile_x
    with pytest.raises(IOError):
        c.nofile_x


def test_maybe_str_input(_input_dir_str: str):
    c = CollectionTest(_input_dir_str)
    c.maybe_call.nofile_x
    with pytest.raises(IOError):
        c.nofile_x


@pytest.fixture()
def _tfs_x() -> TfsDataFrame:
    return read_tfs(CURRENT_DIR / "inputs" / "file_X.tfs").set_index("NAME", drop=False)


@pytest.fixture()
def _tfs_y() -> TfsDataFrame:
    return read_tfs(CURRENT_DIR / "inputs" / "file_Y.tfs").set_index("NAME", drop=False)


@pytest.fixture()
def _input_dir_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs"


@pytest.fixture()
def _input_dir_str() -> str:
    return os.path.join(os.path.dirname(__file__), "inputs")


@pytest.fixture()
def _output_dir() -> str:
    with tempfile.TemporaryDirectory() as cwd:
        yield cwd
