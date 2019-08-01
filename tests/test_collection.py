import os
import pytest
import tempfile
from . import context
from tfs import read_tfs
from collection import TfsCollection, Tfs


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
    _compare_dataframes(_tfs_x, c.file_x)
    _compare_dataframes(_tfs_x, c.filex)
    _compare_dataframes(_tfs_y, c.file_y)
    assert c.value == 10


def test_write(_tfs_x, _output_dir):
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

    _compare_dataframes(_tfs_x, c.nofile_x)


def test_maybe(_input_dir):
    c = CollectionTest(_input_dir)
    tfs = c.maybe_call.nofile_x
    with pytest.raises(IOError):
        tfs = c.nofile_x


def _compare_dataframes(df1, df2):
    assert df1.headers == df2.headers
    for header in df1.headers:
        assert df1[header] == df2[header]
    assert all(df1.columns == df2.columns)
    for column in df1:
        assert all(df1.loc[:, column] == df2.loc[:, column])


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

