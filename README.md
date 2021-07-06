# TFS-Pandas
[![Cron Testing](https://github.com/pylhc/tfs/workflows/Cron%20Testing/badge.svg)](https://github.com/pylhc/tfs/actions?query=workflow%3A%22Cron+Testing%22)
[![Code Climate coverage](https://img.shields.io/codeclimate/coverage/pylhc/tfs.svg?style=popout)](https://codeclimate.com/github/pylhc/tfs)
[![Code Climate maintainability (percentage)](https://img.shields.io/codeclimate/maintainability-percentage/pylhc/tfs.svg?style=popout)](https://codeclimate.com/github/pylhc/tfs)
[![GitHub last commit](https://img.shields.io/github/last-commit/pylhc/tfs.svg?style=popout)](https://github.com/pylhc/tfs/)
[![GitHub release](https://img.shields.io/github/release/pylhc/tfs.svg?style=popout)](https://github.com/pylhc/tfs/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5070986.svg)](https://doi.org/10.5281/zenodo.5070986)

This package provides reading and writing functionality for **table format system (tfs)** files. 

## Getting Started

### Prerequisites

The package depends heavily on `pandas` and also on `numpy`, so these packages need
to be installed in your python environment.

### Installing

Installation is easily done via `pip`. The package is then used as `tfs`.

```
pip install tfs-pandas
```

Example:

```python
import tfs

data_frame = tfs.read('path_to_input.tfs', index="index_column")
tfs.write('path_to_output.tfs', data_frame, save_index="index_column")
```
## Description

Reading and writing capabilities for [tfs-files](http://mad.web.cern.ch/mad/madx.old/Introduction/tfs.html)
are provided by this package. The files are read into special `pandas` `Dataframes`, called `TfsDataFrames`,
which in addition to the normal behaviour attach an `OrderedDict` of headers to the `DataFrame`.

### Changelog

See the [CHANGELOG](CHANGELOG.md) file.

## Known Issues

- Creating a new `DataFrame` by combining multiple `TfsDataFrame`,
for example via `pandas.DataFrame.append()` or `pandas.concat()`, 
will convert the `TfsDataFrame` back to a `DataFrame` and lose therefore the headers.

## Authors

* **Jaime** - [jaimecp89](https://github.com/jaimecp89)
* **Lukáš** - [lmalina](https://github.com/lmalina)
* **Josch** - [JoschD](https://github.com/JoschD)
* **Felix** - [fsoubelet](https://github.com/fsoubelet)
* **pyLHC/OMC-Team** - *Working Group* - [pyLHC](https://github.com/orgs/pylhc/teams/omc-team)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.