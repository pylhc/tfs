from pathlib import Path

import numpy as np
import pytest

from tfs import TfsDataFrame, read_hdf, read_tfs, write_hdf
from tfs.testing import assert_tfs_frame_equal


class TestHDF:
    def test_read_write(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame):
        """Basic read-write loop test for TfsDataFrames to hdf5 format."""
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, _tfs_dataframe)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(_tfs_dataframe, df_read)

    def test_read_write_madng_features(self, _tfs_madng_file, tmp_path):
        """Same as the above for a dataframe which includes MAD-NG features."""
        original = read_tfs(_tfs_madng_file)
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, original)  # should work without error

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(original, df_read)

    def test_write_empty_header(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame):
        """Test writing a TfsDataFrame with empty headers."""
        _tfs_dataframe.headers = {}
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, _tfs_dataframe)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(_tfs_dataframe, df_read)

    def test_write_empty_data(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame):
        """Test writing a TfsDataFrame with empty data."""
        _tfs_dataframe = TfsDataFrame(headers=_tfs_dataframe.headers)
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, _tfs_dataframe)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(_tfs_dataframe, df_read)

    def test_write_empty_frame(self, tmp_path: Path):
        """Test writing an empty TfsDataFrame."""
        _tfs_dataframe = TfsDataFrame()
        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, _tfs_dataframe)

        assert out_file.is_file()

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(_tfs_dataframe, df_read)

    def test_write_compression(self, tmp_path: Path):
        """Test that compression works and compressed files are readable."""
        n = 1000
        _tfs_dataframe = TfsDataFrame(
            data=np.zeros([n, n]), headers={"Random": "Data"}
        )  # highly compressible data

        out_file = tmp_path / "data_frame.h5"
        write_hdf(out_file, _tfs_dataframe, complevel=0)
        assert out_file.is_file()

        out_file_compressed = tmp_path / "data_frame_comp.h5"
        write_hdf(out_file_compressed, _tfs_dataframe, complevel=9)
        assert out_file_compressed.is_file()

        assert out_file.stat().st_size > out_file_compressed.stat().st_size

        df_read = read_hdf(out_file)
        assert_tfs_frame_equal(_tfs_dataframe, df_read)

        df_read_compressed = read_hdf(out_file_compressed)
        assert_tfs_frame_equal(_tfs_dataframe, df_read_compressed)

    def test_write_key_and_mode(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame, caplog):
        """Test the functionality/error handling of the kwars ``key`` and ``mode`` in ``write_hdf``"""
        out_file = tmp_path / "data_frame.h5"
        with pytest.raises(AttributeError) as e:
            write_hdf(out_file, _tfs_dataframe, key="something")
        assert "key" in str(e)

        write_hdf(out_file, _tfs_dataframe, mode="a")  # creates file
        assert "mode" in caplog.text
        assert out_file.is_file()

        with pytest.raises(AttributeError) as e:
            write_hdf(out_file, _tfs_dataframe, mode="a")  # tries to append to file
        assert "mode" in str(e)


class TestImports:
    def test_tables_import_fail(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame, monkeypatch):
        out_file = tmp_path / "data_frame.h5"
        monkeypatch.setattr("tfs.hdf.tables", None)
        with pytest.raises(ImportError) as e:
            write_hdf(out_file, _tfs_dataframe)
        assert "tables" in str(e)

        with pytest.raises(ImportError) as e:
            read_hdf(out_file)
        assert "tables" in str(e)

    def test_h5py_import_fail(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame, monkeypatch):
        out_file = tmp_path / "data_frame.h5"
        monkeypatch.setattr("tfs.hdf.h5py", None)
        with pytest.raises(ImportError) as e:
            write_hdf(out_file, _tfs_dataframe)
        assert "h5py" in str(e)

        with pytest.raises(ImportError) as e:
            read_hdf(out_file)
        assert "h5py" in str(e)

    def test_full_import_fail(self, tmp_path: Path, _tfs_dataframe: TfsDataFrame, monkeypatch):
        out_file = tmp_path / "data_frame.h5"
        monkeypatch.setattr("tfs.hdf.h5py", None)
        monkeypatch.setattr("tfs.hdf.tables", None)
        with pytest.raises(ImportError) as e:
            write_hdf(out_file, _tfs_dataframe)
        assert "h5py" in str(e)
        assert "tables" in str(e)

        with pytest.raises(ImportError) as e:
            read_hdf(out_file)
        assert "h5py" in str(e)
        assert "tables" in str(e)
