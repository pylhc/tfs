# TFS-Pandas

[![Cron Testing](https://github.com/pylhc/tfs/workflows/Cron%20Testing/badge.svg)](https://github.com/pylhc/tfs/actions?query=workflow%3A%22Cron+Testing%22)
[![Code Climate coverage](https://img.shields.io/codeclimate/coverage/pylhc/tfs.svg?style=popout)](https://codeclimate.com/github/pylhc/tfs)
[![Code Climate maintainability (percentage)](https://img.shields.io/codeclimate/maintainability-percentage/pylhc/tfs.svg?style=popout)](https://codeclimate.com/github/pylhc/tfs)
<!-- [![GitHub last commit](https://img.shields.io/github/last-commit/pylhc/tfs.svg?style=popout)](https://github.com/pylhc/tfs/) -->
[![PyPI Version](https://img.shields.io/pypi/v/tfs-pandas?label=PyPI&logo=pypi)](https://pypi.org/project/tfs-pandas/)
[![GitHub release](https://img.shields.io/github/v/release/pylhc/tfs?logo=github)](https://github.com/pylhc/tfs/)
[![Conda-forge Version](https://img.shields.io/conda/vn/conda-forge/tfs-pandas?color=orange&logo=anaconda)](https://anaconda.org/conda-forge/tfs-pandas)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5070986.svg)](https://doi.org/10.5281/zenodo.5070986)

This package provides reading and writing functionality for [**Table Format System (TFS)** files](http://mad.web.cern.ch/mad/madx.old/Introduction/tfs.html). 
Files are read into a `TfsDataFrame`, a class built on top of the famous `pandas.DataFrame`, which in addition to the normal behavior attaches an `OrderedDict` of headers to the `DataFrame`.

See the [API documentation](https://pylhc.github.io/tfs/) for details.

## Installing

Installation is easily done via `pip`:
```bash
python -m pip install tfs-pandas
```

One can also install in a `conda`/`mamba` environment via the `conda-forge` channel with:
```bash
conda install -c conda-forge tfs-pandas
```

## Example Usage

The package is imported as `tfs`, and exports top-level functions for reading and writing:
```python
import tfs

# Loading a TFS file is simple
data_frame = tfs.read("path_to_input.tfs", index="index_column")

# You can access and modify the headers with the .headers attribute
useful_variable = data_frame.headers["SOME_KEY"]
data_frame.headers["NEW_KEY"] = some_variable

# Manipulate data as you do with pandas DataFrames
data_frame["NEWCOL"] = data_frame.COL_A * data_frame.COL_B

# You can check the validity of a TfsDataFrame, and choose the behavior in case of errors
tfs.frame.validate(data_frame, non_unique_behavior="raise")  # or choose "warn"

# Writing out to disk is simple too
tfs.write("path_to_output.tfs", data_frame, save_index="index_column")
```

Reading and writing compressed files is also supported, and done automatically based on the provided file extension:
```python
import tfs

# Reading a compressed file is simple, compression format is inferred
df = tfs.read("path_to_input.tfs.gz")

# When writing choose the compression format by providing the appropriate file extension
tfs.write("path_to_output.tfs.bz2", df)
tfs.write("path_to_output.tfs.zip", df)
```

### Package Scope

The package also provides some tools to validate and manipulate `TfsDataFrames` and their headers; or lazily manage a collection of TFS files.
For instance with `tfs.read_hdf()` and `tfs.write_hdf()` the `TfsDataFames` can also be saved as `hdf5` files, if the `hdf5` extra requirements are fulfilled.

The package, however, is made to handle I/O of `TFS` files to `TfsDataFrames` only: it is not meant to implement various calculations on `TfsDataFrames`.
Some calculations are implemented in other packages of the ecosystem.

## License

This project is licensed under the `MIT License` - see the [LICENSE](LICENSE) file for details.
