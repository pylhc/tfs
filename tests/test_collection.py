import os
import pathlib

import pytest
from pandas.testing import assert_frame_equal

from tfs import read_tfs
from tfs.collection import Tfs, TfsCollection
from tfs.frame import TfsDataFrame

CURRENT_DIR = pathlib.Path(__file__).parent


def test_tfscollection_getfilename_not_implemented():
    with pytest.raises(NotImplementedError):
        TfsCollection.get_filename("doesnt matter")


class CollectionTest(TfsCollection):
    file = Tfs("file_{}.tfs")
    nofile = Tfs("nofile_{}.tfs")
    filex = Tfs("file_x.tfs", two_planes=False)
    value = 10

    def get_filename(self, template, plane=""):
        return template.format(plane)


def test_read_pathlib_input(_input_dir_pathlib: pathlib.Path, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame):
    c = CollectionTest(_input_dir_pathlib)
    assert_frame_equal(_tfs_x, c.file_x)
    assert_frame_equal(_tfs_x, c.filex)
    # test that both capitalized and lowered plane keys are accepted
    assert_frame_equal(_tfs_x, c.file["x"])
    assert_frame_equal(_tfs_x, c.file["X"])
    assert_frame_equal(_tfs_y, c.file["y"])
    assert_frame_equal(_tfs_y, c.file["Y"])
    assert c.value == 10


def test_read_str_input(_input_dir_str: str, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame):
    c = CollectionTest(_input_dir_str)
    assert_frame_equal(_tfs_x, c.file_x)
    assert_frame_equal(_tfs_x, c.filex)
    # test that both capitalized and lowered plane keys are accepted
    assert_frame_equal(_tfs_x, c.file["x"])
    assert_frame_equal(_tfs_x, c.file["X"])
    assert_frame_equal(_tfs_y, c.file["y"])
    assert_frame_equal(_tfs_y, c.file["Y"])
    assert c.value == 10


def test_write(_tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame, tmp_path):
    c = CollectionTest(tmp_path)
    file_x_path = tmp_path / "nofile_x.tfs"
    assert not file_x_path.is_file()

    c.nofile_x = _tfs_x  # will not throw error, but does nothing
    assert not file_x_path.is_file()

    c.allow_write = True
    c.nofile_x = _tfs_x
    assert file_x_path.is_file()
    assert_frame_equal(_tfs_x, c.nofile_x)

    c.nofile["y"] = _tfs_y
    file_y_path = tmp_path / "nofile_y.tfs"
    assert file_y_path.is_file()
    assert_frame_equal(_tfs_y, c.nofile["y"])
    assert_frame_equal(_tfs_y, c.nofile["Y"])


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


def test_collection_buffer_clear(_dummy_collection):
    _dummy_collection._buffer["some_key"] = 5
    assert _dummy_collection._buffer["some_key"]
    _dummy_collection.clear()
    assert not _dummy_collection._buffer


def test_tfs_collection_no_attribute(_dummy_collection):
    with pytest.raises(AttributeError):
        _ = _dummy_collection.absent_attribute


@pytest.fixture()
def _tfs_x() -> TfsDataFrame:
    return read_tfs(CURRENT_DIR / "inputs" / "file_x.tfs").set_index("NAME", drop=False)


@pytest.fixture()
def _tfs_y() -> TfsDataFrame:
    return read_tfs(CURRENT_DIR / "inputs" / "file_y.tfs").set_index("NAME", drop=False)


@pytest.fixture()
def _input_dir_pathlib() -> pathlib.Path:
    return CURRENT_DIR / "inputs"


@pytest.fixture()
def _input_dir_str() -> str:
    return os.path.join(os.path.dirname(__file__), "inputs")


@pytest.fixture()
def _dummy_collection() -> TfsCollection:
    return TfsCollection("")
