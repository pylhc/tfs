# TFS-Pandas

[![Tests](https://github.com/pylhc/tfs/actions/workflows/coverage.yml/badge.svg?branch=master)](https://github.com/pylhc/tfs/actions/workflows/coverage.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/pylhc/tfs.svg?style=popout)](https://github.com/pylhc/tfs/)
[![GitHub release](https://img.shields.io/github/v/release/pylhc/tfs?logo=github)](https://github.com/pylhc/tfs/)
[![PyPI Version](https://img.shields.io/pypi/v/tfs-pandas?label=PyPI&logo=pypi)](https://pypi.org/project/tfs-pandas/)
[![Conda-forge Version](https://img.shields.io/conda/vn/conda-forge/tfs-pandas?color=orange&logo=anaconda)](https://anaconda.org/conda-forge/tfs-pandas)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5070986.svg)](https://doi.org/10.5281/zenodo.5070986)

This package provides reading and writing functionality for [**Table Format System (TFS)**](https://pylhc.github.io/tfs/tfsformat.html) files.
Files are read into a `TfsDataFrame`, a class built on top of the `pandas.DataFrame`, which in addition to the normal behavior attaches a dictionary of headers to the `DataFrame`.

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

# You can check the validity of a TfsDataFrame, speficying the
# compatibility mode as well as the behavior in case of errors
tfs.frame.validate(
    data_frame,
    non_unique_behavior="raise",  # or choose "warn"
    compatibility="mad-x",  # or choose "mad-ng"
)

# Writing out to disk is simple too
tfs.write("path_to_output.tfs", data_frame, save_index="index_column")
```

Compression is automatically supported, based on the provided file extension (for supported formats):

```python
import tfs

# Reading a compressed file is simple, compression format is inferred
df = tfs.read("path_to_input.tfs.gz")

# When writing choose the compression format by providing the appropriate file extension
tfs.write("path_to_output.tfs.bz2", df)
tfs.write("path_to_output.tfs.zip", df)
```

## License

This project is licensed under the `MIT License` - see the [LICENSE](LICENSE) file for details.
