import os
import tempfile

import pytest

from .helper import compare_dataframes
from tfs import read_tfs
from tfs.collection import TfsCollection, Tfs

CURRENT_DIR = os.path.dirname(__file__)


class CollectionTest(TfsCollection):
    file = Tfs("file_{}.tfs")
    nofile = Tfs("nofile_{}.tfs")
    filex = Tfs("file_x.tfs", two_planes=False)
    value = 10

    def get_filename(self, template, plane=""):
        return template.format(plane)


def test_read(_input_dir, _tfs_x, _tfs_y):
    c = CollectionTest(_input_dir)
    compare_dataframes(_tfs_x, c.file_x)
    compare_dataframes(_tfs_x, c.filex)
    compare_dataframes(_tfs_y, c.file["y"])
    assert c.value == 10


def test_write(_tfs_x, _tfs_y, _output_dir):
    c = CollectionTest(_output_dir)
    assert not os.path.isfile(
        os.path.join(_output_dir, "nofile_x.tfs"))

    c.nofile_x = _tfs_x  # will not throw error, but does nothing
    assert not os.path.isfile(
        os.path.join(_output_dir, "nofile_x.tfs"))

    c.allow_write = True
    c.nofile_x = _tfs_x
    assert os.path.isfile(
        os.path.join(_output_dir, "nofile_x.tfs"))
    compare_dataframes(_tfs_x, c.nofile_x)

    c.nofile["y"] = _tfs_y
    assert os.path.isfile(
        os.path.join(_output_dir, "nofile_y.tfs"))
    compare_dataframes(_tfs_y, c.nofile["y"])


def test_maybe(_input_dir):
    c = CollectionTest(_input_dir)
    c.maybe_call.nofile_x
    with pytest.raises(IOError):
        c.nofile_x


@pytest.fixture()
def _tfs_x():
    return read_tfs(os.path.join(CURRENT_DIR, "inputs", "file_x.tfs")).set_index("NAME", drop=False)


@pytest.fixture()
def _tfs_y():
    return read_tfs(os.path.join(CURRENT_DIR, "inputs", "file_y.tfs")).set_index("NAME", drop=False)


@pytest.fixture()
def _input_dir():
    return os.path.join(CURRENT_DIR, "inputs")


@pytest.fixture()
def _output_dir():
    with tempfile.TemporaryDirectory() as cwd:
        yield cwd


@pytest.fixture()
def _test_file():
    with tempfile.TemporaryDirectory() as cwd:
        yield os.path.join(cwd, "test_file.tfs")

