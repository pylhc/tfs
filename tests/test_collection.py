import os
import pathlib
import pytest
from pandas.testing import assert_frame_equal

from tfs import read_tfs
from tfs.collection import Tfs, TfsCollection
from tfs.frame import TfsDataFrame

INPUT_DIR = pathlib.Path(__file__).parent / "inputs"


class CollectionTest(TfsCollection):
    file = Tfs("file_{}.tfs")
    nofile = Tfs("nofile_{}.tfs")
    filex = Tfs("file_x.tfs", two_planes=False)
    value = 10

    def _get_filename(self, template, plane=""):
        return template.format(plane)


class TestRead:

    def test_read_pathlib_input(self, _input_dir_pathlib: pathlib.Path, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame):
        c = CollectionTest(_input_dir_pathlib, allow_write=False)
        assert_frame_equal(_tfs_x, c.file_x)
        assert_frame_equal(_tfs_x, c.filex)
        # test that both capitalized and lowered plane keys are accepted
        assert_frame_equal(_tfs_x, c.file["x"])
        assert_frame_equal(_tfs_x, c.file["X"])
        assert_frame_equal(_tfs_y, c.file["y"])
        assert_frame_equal(_tfs_y, c.file["Y"])
        assert c.value == 10

    def test_read_str_input(self, _input_dir_str: str, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame):
        c = CollectionTest(_input_dir_str, allow_write=False)
        assert_frame_equal(_tfs_x, c.file_x)
        assert_frame_equal(_tfs_x, c.filex)
        # test that both capitalized and lowered plane keys are accepted
        assert_frame_equal(_tfs_x, c.file["x"])
        assert_frame_equal(_tfs_x, c.file["X"])
        assert_frame_equal(_tfs_y, c.file["y"])
        assert_frame_equal(_tfs_y, c.file["Y"])
        assert c.value == 10


class TestWrite:

    def test_write(self, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame, tmp_path):
        c = CollectionTest(tmp_path)
        file_x_path = tmp_path / "nofile_x.tfs"
        assert not file_x_path.is_file()

        c.nofile_x = _tfs_y  # only assigns dataframe without writing (use _tfs_y so that we can set _tfs_x below)
        assert not file_x_path.is_file()
        assert_frame_equal(_tfs_y, c.nofile_x)

        c.allow_write = True
        c.nofile_x = _tfs_x  # should overwrite _tfs_y in buffer
        assert file_x_path.is_file()
        assert_frame_equal(_tfs_x, c.nofile_x)

        tfs_x_loaded = _read_tfs(file_x_path)
        assert_frame_equal(_tfs_x, tfs_x_loaded)

        c.nofile["y"] = _tfs_y
        file_y_path = tmp_path / "nofile_y.tfs"
        assert file_y_path.is_file()
        assert_frame_equal(_tfs_y, c.nofile["y"])
        assert_frame_equal(_tfs_y, c.nofile["Y"])

    def test_write_tfs(self, _tfs_x: TfsDataFrame, tmp_path):
        c = CollectionTest(tmp_path)
        name = "nofile_x.tfs"
        assert not (tmp_path / name).is_file()
        c.write_tfs(name, _tfs_x)
        assert (tmp_path / name).is_file()

    def test_write_to(self, _tfs_x: TfsDataFrame, tmp_path):
        class WriteToCollectionTest(TfsCollection):
            file = Tfs("file_{}.tfs")
            filex = Tfs("file_x.tfs", two_planes=False)

            def _get_filename(self, template, plane=""):
                return template.format(plane)

            def _write_to(self, df, template, plane=""):
                return f"out_{self._get_filename(template, plane)}", df

        c = WriteToCollectionTest(tmp_path, allow_write=True)
        filepath = tmp_path / "out_file_x.tfs"

        assert not filepath.exists()
        c.file_x = _tfs_x
        assert filepath.exists()

        filepath.unlink()

        assert not filepath.exists()
        c.filex = _tfs_x
        assert filepath.exists()

    def test_buffer_flush(self, _input_dir_str: str, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame, tmp_path):
        c = CollectionTest(tmp_path, allow_write=True)

        c.file_x = _tfs_x.copy()
        c.nofile_y = _tfs_y.copy()
        tfs_x = _tfs_x.drop(columns="NAME")  # index reading below drops columns, TfsCollections does not
        tfs_y = _tfs_y.drop(columns="NAME")

        c.file_x.loc["BPMSX.4L2.B1", "NUMBER"] = -199
        c.nofile_y.loc["BPMSX.4L2.B1", "NUMBER"] = -19

        assert_frame_equal(tfs_x, read_tfs(c.get_path("file_x"), index=c.INDEX))
        assert_frame_equal(tfs_y, read_tfs(c.get_path("nofile_y"), index=c.INDEX))

        c.flush()

        tfs_x_after_flush = read_tfs(c.get_path("file_x"), index=c.INDEX)
        tfs_y_after_flush = read_tfs(c.get_path("nofile_y"), index=c.INDEX)
        with pytest.raises(AssertionError):
            assert_frame_equal(tfs_x, tfs_x_after_flush )

        with pytest.raises(AssertionError):
            assert_frame_equal(tfs_y, tfs_y_after_flush)

        assert tfs_x_after_flush.loc["BPMSX.4L2.B1", "NUMBER"] == -199
        assert tfs_y_after_flush.loc["BPMSX.4L2.B1", "NUMBER"] == -19

    def test_buffer_flush_nowrite(self, _input_dir_str: str, _tfs_x: TfsDataFrame, _tfs_y: TfsDataFrame, tmp_path):
        c = CollectionTest(tmp_path, allow_write=True)

        c.file_x = _tfs_x.copy()
        c.nofile_y = _tfs_y.copy()
        tfs_x = _tfs_x.drop(columns="NAME")  # index reading below drops columns, TfsCollections does not
        tfs_y = _tfs_y.drop(columns="NAME")

        c.file_x.loc["BPMSX.4L2.B1", "NUMBER"] = -199
        c.nofile_y.loc["BPMSX.4L2.B1", "NUMBER"] = -19

        assert_frame_equal(tfs_x, read_tfs(c.get_path("file_x"), index=c.INDEX))
        assert_frame_equal(tfs_y, read_tfs(c.get_path("nofile_y"), index=c.INDEX))

        c.allow_write = False
        with pytest.raises(IOError):
            c.flush()

        tfs_x_after_flush = read_tfs(c.get_path("file_x"), index=c.INDEX)
        tfs_y_after_flush = read_tfs(c.get_path("nofile_y"), index=c.INDEX)
        assert_frame_equal(tfs_x, tfs_x_after_flush)
        assert_frame_equal(tfs_y, tfs_y_after_flush)


class TestFilenames:

    def test_tfscollection_getfilename_not_implemented(self):
        with pytest.raises(NotImplementedError):
            TfsCollection._get_filename("doesnt matter")

    def test_get_filename(self, _input_dir_pathlib: pathlib.Path):
        c = CollectionTest(_input_dir_pathlib, allow_write=False)
        assert c.get_filename("file_y") == "file_y.tfs"
        assert c.get_filename("filex") == "file_x.tfs"
        assert c.get_filename("nofile_x") == "nofile_x.tfs"

    def test_get_filename_not_there(self, _input_dir_pathlib: pathlib.Path):
        c = CollectionTest(_input_dir_pathlib, allow_write=False)
        with pytest.raises(AttributeError):
            c.get_filename("doesn't matter either")

    def test_filenames(self, _input_dir_pathlib: pathlib.Path):
        c = CollectionTest(_input_dir_pathlib, allow_write=False)
        assert c.filenames.file_y == "file_y.tfs"
        assert c.filenames.filex == "file_x.tfs"
        assert c.filenames.nofile_x == "nofile_x.tfs"

        assert c.filenames["file_x"] == "file_x.tfs"
        assert c.filenames["nofile_y"] == "nofile_y.tfs"

        exist_properties = "file_x", "file_y", "filex"
        not_exist_properties = "nofile_x", "nofile_y"
        exist_files = "file_x.tfs", "file_y.tfs"
        not_exist_files = "nofile_x.tfs", "nofile_y.tfs"

        assert c.filenames()["file_x"] == "file_x.tfs"
        assert c.filenames()["nofile_y"] == "nofile_y.tfs"

        assert all(f in c.filenames().keys() for f in exist_properties)
        assert all(f in c.filenames().keys() for f in not_exist_properties)
        assert all(f in c.filenames().values() for f in exist_files)
        assert all(f in c.filenames().values() for f in not_exist_files)

        assert all(f in c.filenames(exist=True).keys() for f in exist_properties)
        assert all(f not in c.filenames(exist=True).keys() for f in not_exist_properties)
        assert all(f in c.filenames(exist=True).values() for f in exist_files)
        assert all(f not in c.filenames(exist=True).values() for f in not_exist_files)

    def test_get_path(self, _input_dir_pathlib: pathlib.Path):
        c = CollectionTest(_input_dir_pathlib, allow_write=False)
        assert c.get_path("file_y") == _input_dir_pathlib / "file_y.tfs"
        assert c.get_path("filex") == _input_dir_pathlib / "file_x.tfs"
        assert c.get_path("nofile_x") == _input_dir_pathlib / "nofile_x.tfs"


class TestOther:

    def test_access_methods(self, _input_dir_pathlib: pathlib.Path):
        c = CollectionTest(_input_dir_pathlib, allow_write=False)

        # Getting (partly tested in read-test as well)
        assert_frame_equal(c.file_x, c.file["x"])
        assert_frame_equal(c.file_x, c.file["X"])
        assert_frame_equal(c.file_x, c["file_x"])

        # Setting
        c.nofile_y = c.file_y
        assert_frame_equal(c.nofile_y, c.file_y)

        c["nofile_y"] = c.file_x
        assert_frame_equal(c.nofile_y, c.file_x)

        c.nofile["y"] = c.file_y
        assert_frame_equal(c.nofile_y, c.file_y)

        c.nofile["Y"] = c.file_x
        assert_frame_equal(c.nofile_y, c.file_x)

    def test_index(self, _input_dir_pathlib: pathlib.Path, _tfs_x: TfsDataFrame):
        c = CollectionTest(_input_dir_pathlib)
        c.INDEX = "S"
        assert all(c.filex.index == _tfs_x["S"])

    def test_defined_properties(self, _input_dir_pathlib: pathlib.Path):
        c = CollectionTest(_input_dir_pathlib)
        exist_properties = {"file_x", "file_y", "filex", "nofile_x", "nofile_y"}
        assert set(c.defined_properties) == exist_properties

    def test_maybe(self, _input_dir_pathlib: pathlib.Path):
        def _test_fun(df, a, b):
            return df.BPMCOUNT, a + b

        c = CollectionTest(_input_dir_pathlib)
        res_no = c.maybe_call.nofile_x(_test_fun, 10, 20)
        assert res_no is None

        res_file = c.maybe_call.file_x(_test_fun, 10, 20)
        assert res_file[0] == 9
        assert res_file[1] == 30

        # same but with item:
        res_file = c.maybe_call.file["x"](_test_fun, 5, 8)
        assert res_file[0] == 9
        assert res_file[1] == 13

    def test_buffer_clear(self, _dummy_collection):
        _dummy_collection._buffer["some_key"] = 5
        assert _dummy_collection._buffer["some_key"]
        _dummy_collection.clear()
        assert not _dummy_collection._buffer

    def test_no_attribute(self, _dummy_collection):
        with pytest.raises(AttributeError):
            _ = _dummy_collection.absent_attribute


def _read_tfs(path):
    """ Reads tfs like in _load_tfs() of the collection (here we know we have NAME in tfs). """
    return read_tfs(path).set_index("NAME", drop=False)


@pytest.fixture()
def _tfs_x() -> TfsDataFrame:
    return _read_tfs(INPUT_DIR / "file_x.tfs")


@pytest.fixture()
def _tfs_y() -> TfsDataFrame:
    return _read_tfs(INPUT_DIR / "file_y.tfs")


@pytest.fixture()
def _input_dir_pathlib() -> pathlib.Path:
    return INPUT_DIR


@pytest.fixture()
def _input_dir_str() -> str:
    return str(INPUT_DIR)


@pytest.fixture()
def _dummy_collection() -> TfsCollection:
    return TfsCollection("")
