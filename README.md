# TFS-Pandas

[![Cron Testing](https://github.com/pylhc/tfs/workflows/Cron%20Testing/badge.svg)](https://github.com/pylhc/tfs/actions?query=workflow%3A%22Cron+Testing%22)
[![Code Climate coverage](https://img.shields.io/codeclimate/coverage/pylhc/tfs.svg?style=popout)](https://codeclimate.com/github/pylhc/tfs)
[![Code Climate maintainability (percentage)](https://img.shields.io/codeclimate/maintainability-percentage/pylhc/tfs.svg?style=popout)](https://codeclimate.com/github/pylhc/tfs)
[![GitHub last commit](https://img.shields.io/github/last-commit/pylhc/tfs.svg?style=popout)](https://github.com/pylhc/tfs/)
[![GitHub release](https://img.shields.io/github/release/pylhc/tfs.svg?style=popout)](https://github.com/pylhc/tfs/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5070986.svg)](https://doi.org/10.5281/zenodo.5070986)

This package provides reading and writing functionality for [**table format system (tfs)** files](http://mad.web.cern.ch/mad/madx.old/Introduction/tfs.html). 
The files are read into special `pandas` `Dataframes`, called `TfsDataFrames`, which in addition to the normal behaviour attach an `OrderedDict` of headers to the `DataFrame`.

## Installing

Installation is easily done via `pip`.

```
pip install tfs-pandas
```

## Example Usage

 The package is imported as `tfs`, and exports top-level functions for reading and writing:
```python
import tfs

data_frame = tfs.read("path_to_input.tfs", index="index_column")
# do things with the data
tfs.write("path_to_output.tfs", data_frame, save_index="index_column")
```

It also provides some tools to manipulate `TfsDataFrames` or lazily manage a collection of TFS files.
See the [API documentation](https://pylhc.github.io/tfs/) for details.

### Changelog

See the [CHANGELOG](CHANGELOG.md) file.

## Known Issues

- Combining multiple `TfsDataFrame` objects, for example via `pandas.DataFrame.append()` or `pandas.concat()`, will convert them back to a `pandas.DataFrame` and therefore lose the headers.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.