import os
import tempfile

import numpy as np
import pytest

from .helper import compare_dataframes
from tfs.fixed_dataframe import FixedColumn, FixedColumnCollection, FixedTfs
from tfs.handler import read_tfs, write_tfs, TfsDataFrame


class MyTfs(FixedTfs):
    filename = "mytfs_{}.tfs"
    two_planes = True

    class Columns(FixedColumnCollection):
        NAME = FixedColumn("NAME", str)
        OTHER = FixedColumn("STRING", str)
        VALUE = FixedColumn("VAL{}", float, "m")

    class Headers(FixedColumnCollection):
        TITLE = FixedColumn("Title", str)
        OFFSET = FixedColumn("Offset{}", float, "m")

    Index = Columns.NAME


class PlanelessTfs(FixedTfs):
    filename = "test{}"
    two_planes = False


# Tests ------------------------------------------------------------------------


def test_fixed_columns():
    columns = MyTfs.Columns("X")
    assert len(columns) == 3
    assert len([c for c in columns]) == 3
    assert all(a == b for a, b in zip(columns.names, ["NAME", "STRING", "VALX"]))
    assert all(a == b for a, b in zip(columns.dtypes, [str, str, float]))
    assert all(a == b for a, b in zip(columns.units, ["", "", "m"]))
    assert columns.NAME.dtype == str
    assert columns.VALUE.dtype == float
    # pointing out some curiosities:
    assert columns.NAME.name == MyTfs.Columns.NAME.name
    assert columns.VALUE.name != MyTfs.Columns.VALUE.name
    assert str(columns.VALUE) == "VALX"


def test_empty_df_creation():
    df = MyTfs(plane="X")
    assert len(df.Columns) == 2  # NAME is index
    assert df.index.name == MyTfs.Columns.NAME.name
    assert all(a == b for a, b in zip(df.Columns.names, df.columns))
    assert all(a == b for a, b in zip(df.Headers.names, df.headers))
    assert len(df) == 0
    assert len(df.headers) == 2


def test_setting_columns():
    df = MyTfs(plane="X")
    df["VALX"] = [1., 2., 3.]
    assert all(df["VALX"] == np.array([1, 2, 3]))

    with pytest.raises(TypeError):
        df["VALX"] = [1, 2, 3]

    with pytest.raises(KeyError):
        df["VALY"] = [1., 2., 3.]


def test_setting_loc():
    df = MyTfs(plane="Y")
    df.loc["A", "VALY"] = 1

    df.loc["B", :] = ["Moso", 2.]

    with pytest.raises(KeyError):
        df.loc["A", "Wrong"] = 10

    with pytest.raises(TypeError):
        df.loc["A", "VALY"] = "NOTANUMBER"


def test_setting_headers():
    df = MyTfs(plane="X")
    df.headers["Title"] = "File Stuff"
    assert df["Title"] == "File Stuff"
    df.validate_definitions()

    df.headers["Title"] = 10
    with pytest.raises(TypeError):
        df.validate_definitions()

    df.headers["OffsetY"] = 10.
    with pytest.raises(KeyError):
        df.validate_definitions()


def test_setting_indices():
    df = MyTfs(plane="X")
    df.index.name = "Nottherightname"
    with pytest.raises(KeyError):
        df.validate_definitions()

    df = MyTfs(plane="X", index=[1,2,3])
    assert df.index[0] == "1"
    df.index = df.index.astype(int)
    assert df.index[0] == 1
    with pytest.raises(TypeError):
        df.validate_definitions()


def test_init_with_data():
    df = MyTfs(plane="X", columns=["VALX"], data=[1., 2., 3.], headers={"OffsetX": 100.})
    assert all(df["VALX"] == np.array([1, 2, 3]))
    assert df.headers["OffsetX"] == 100

    with pytest.raises(KeyError):
        MyTfs(plane="X", columns=["VALY"], data=[1., 2., 3.])

    with pytest.raises(TypeError):
        MyTfs(plane="X", columns=["VALX"], data=[1, 2, 3])

    with pytest.raises(KeyError):
        MyTfs(plane="X", headers={"Something": 10})

    with pytest.raises(TypeError):
        MyTfs(plane="X", headers={"OffsetX": 100})


def test_single_plane_creation():
    with pytest.raises(ValueError):
        PlanelessTfs(plane="X", directory="")
    df = PlanelessTfs(directory="")
    assert PlanelessTfs.filename.format("") == df.get_filename()


def test_no_restrictions():
    df = PlanelessTfs(directory="")
    df["Allowed"] = 10
    df.headers["Write"]  = "Everything"
    df.validate_definitions()


# IO Tests ---------------------------------------------------------------------


def test_empty_write(_output_dir):
    df = MyTfs(plane="X", directory=_output_dir)
    df.write()
    assert os.path.isfile(df.get_filename())
    df_read = read_tfs(df.get_filename(), index="NAME")
    compare_dataframes(df, df_read)


def test_filled_write(_output_dir, _filled_tfs):
    df = _filled_tfs(plane="X", directory=_output_dir)
    df.write()
    assert os.path.isfile(df.get_filename())
    df_read = read_tfs(df.get_filename(), index="NAME")
    compare_dataframes(df, df_read)


def test_empty_read(_output_dir):
    df = MyTfs(plane="X", directory=_output_dir)
    write_tfs(df.get_filename(), df, save_index="NAME")
    df_read = MyTfs(plane="X", directory=_output_dir).read()
    compare_dataframes(df, df_read)


def test_filled_read(_output_dir, _filled_tfs):
    df = _filled_tfs(plane="X", directory=_output_dir)
    write_tfs(df.get_filename(), df, save_index="NAME")
    df_read = MyTfs(plane="X", directory=_output_dir).read()
    compare_dataframes(df, df_read)


def test_read_fail(_output_dir):
    mydf = MyTfs(plane="X", directory=_output_dir)
    df = TfsDataFrame(columns=["Does", "Not", "Exist"])
    write_tfs(mydf.get_filename(), df)
    with pytest.raises(KeyError):
        MyTfs(plane="X", directory=_output_dir).read()


def test_write_fail(_output_dir):
    mydf = MyTfs(plane="X", directory=_output_dir)
    mydf.headers["Nothere"] = "Still"
    with pytest.raises(KeyError):
        mydf.write()
    assert not os.path.isfile(mydf.get_filename())


# Little Helpers ---------------------------------------------------------------


@pytest.fixture()
def _output_dir():
    with tempfile.TemporaryDirectory() as cwd:
        yield cwd


@pytest.fixture()
def _filled_tfs():
    yield lambda plane, directory: MyTfs(plane=plane, directory=directory,
                                         index=["A", "B"], columns=MyTfs.Columns("X", exclude=[MyTfs.Index]).names,
               data=[["Wonder", 1.1], ["BAR", 4.4]], headers={"OffsetX": 100., "Title": "Test Title"})
