import sys

import numpy as np
import pytest
from pathlib import Path

from tfs import TfsDataFrame, write_hdf, read_hdf
from pandas.testing import assert_frame_equal
from pandas._testing import assert_dict_equal


class TestHDF:
    def test_read_write(self, tmp_path: Path, df_example: TfsDataFrame):
        """Basic read-write loop test for TfsDataFrames to hdf5 format."""
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, df_example)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(df_example, df_read)

    def test_write_empty_header(self, tmp_path: Path, df_example: TfsDataFrame):
        """Test writing a TfsDataFrame with empty headers."""
        df_example.headers = {}
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, df_example)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(df_example, df_read)

    def test_write_empty_data(self, tmp_path: Path, df_example: TfsDataFrame):
        """Test writing a TfsDataFrame with empty data."""
        df_example = TfsDataFrame(headers=df_example.headers)
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, df_example)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(df_example, df_read)

    def test_write_empty_frame(self, tmp_path: Path):
        """Test writing an empty TfsDataFrame."""
        df_example = TfsDataFrame()
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, df_example)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(df_example, df_read)

    def test_write_compression(self, tmp_path: Path):
        """Test that compression works and compressed files are readable."""
        n = 1000
        df_example = TfsDataFrame(
            data=np.zeros([n, n]),  # highly compressible data
            headers={"Random": "Data"}
        )

        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, df_example, complevel=0)
        assert out_file.is_file()

        out_file_compressed = tmp_path / "data_frame_comp.h5"
        write_hdf(out_file_compressed, df_example, complevel=9)
        assert out_file_compressed.is_file()

        assert out_file.stat().st_size > out_file_compressed.stat().st_size

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(df_example, df_read)

        df_read_compressed = read_hdf(out_file_compressed)
        assert_tfs_frame_equal(df_example, df_read_compressed)

    def test_write_key_and_mode(self, tmp_path: Path, df_example: TfsDataFrame, caplog):
        """Test the functionality/error handling of the kwars ``key`` and ``mode`` in ``write_hdf``"""
        out_file = tmp_path / "data_frame.h5"
        with pytest.raises(AttributeError) as e:
            write_hdf(out_file, df_example, key="something")
        assert 'key' in str(e)

        write_hdf(out_file, df_example, mode='a')  # creates file
        assert "mode" in caplog.text
        assert out_file.is_file()

        with pytest.raises(AttributeError) as e:
            write_hdf(out_file, df_example, mode='a')  # tries to append to file
        assert 'mode' in str(e)


class TestImports:
    def test_tables_import_fail(self, tmp_path: Path, df_example: TfsDataFrame, monkeypatch):
        out_file = tmp_path / "data_frame.h5"
        monkeypatch.setattr('tfs.hdf.tables', None)
        with pytest.raises(ImportError) as e:
            write_hdf(out_file, df_example)
        assert 'tables' in str(e)

        with pytest.raises(ImportError) as e:
            read_hdf(out_file)
        assert 'tables' in str(e)

    def test_h5py_import_fail(self, tmp_path: Path, df_example: TfsDataFrame,  monkeypatch):
        out_file = tmp_path / "data_frame.h5"
        monkeypatch.setattr('tfs.hdf.h5py', None)
        with pytest.raises(ImportError) as e:
            write_hdf(out_file, df_example)
        assert 'h5py' in str(e)

        with pytest.raises(ImportError) as e:
            read_hdf(out_file)
        assert 'h5py' in str(e)

    def test_full_import_fail(self, tmp_path: Path, df_example: TfsDataFrame,  monkeypatch):
        out_file = tmp_path / "data_frame.h5"
        monkeypatch.setattr('tfs.hdf.h5py', None)
        monkeypatch.setattr('tfs.hdf.tables', None)
        with pytest.raises(ImportError) as e:
            write_hdf(out_file, df_example)
        assert 'h5py' in str(e)
        assert 'tables' in str(e)

        with pytest.raises(ImportError) as e:
            read_hdf(out_file)
        assert 'h5py' in str(e)
        assert 'tables' in str(e)


# Helper -----------------------------------------------------------------------


def assert_tfs_frame_equal(df1, df2):
    assert_frame_equal(df1, df2)
    assert_dict_equal(df1.headers, df2.headers, compare_keys=True)


@pytest.fixture
def df_example():
    return TfsDataFrame(
        data=[[1, "Aha", 4.], [2, "Blubb", 10]],
        index=["X", "Y"],
        columns=["Int", "String", "Float"],
        headers={"Hello": "A String", "Number": 2382.2288, "AnInt": 10}
    )
