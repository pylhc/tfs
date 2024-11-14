# TFS-Pandas Changelog

## Version 3.9.0

- Added:
  - A module, `tfs.testing`, has been added and made publicly available. It provides an assert function to compare `TfsDataFrame` similar to that provided by `pandas`, destined for unit tests.

## Version 3.8.2

- Changed:
  - The headers of a `TfsDataFrame` are now stored as a `dict` and no longer an `OrderedDict`. This is transparent to the user.

- Fixed:
  - Removed a workaround function which is no longer necessary due to the higher minimum `pandas` version.

## Version 3.8.1

- Changed:
  - Migrated to standard `pyproject.toml`.
  - The minimum required `numpy` version is now `numpy 1.24`.

- Fixed:
  - The package is now compatible with `numpy 2.x`.
  - The package's HDF functionality is fully compatible with `numpy 2.x` on `Python >= 3.10` thanks to a `pytables` compatibility release.
  - The package's HDF functionality limits to `numpy < 2` on `Python 3.9` due to the lack of compatibility from `pytables` on this versions.

## Version 3.8.0

- Changed:
  - The minimum required `pandas` version is now `pandas 2.1`.
  - Support for `Python 3.8` has been dropped. The minimum required Python version is now `3.9`.

- Fixed:
  - Solved a `DeprecationWarning` appearing when writing a `TfsDataFrame` to disk due to the use of `.applymap`, byusing the now recommended `.map` method.
  - Solved a `DeprecationWarning` appearing when reading a file from disk due to the use of `delim_whitespace` in our reader, by using the now recommended `sep` option.
  - Solved a `FutureWarning` appearing when validating a `TfsDataFrame` due to the use of the `pd.option_context('mode.use_inf_as_na', True)` context manager during validation by explicitely casting infinite values to `NaNs`.
  - Solved a `FutureWarning` appearing when validating a `TfsDataFrame` due to object downcasting happening during validation by explicitely infering dtypes first.

## Version 3.7.3

- Fixed:
  - Fixed a regression where the writing of a `pd.Series`-like object to disk was raising an error. It is now possible again.  

## Version 3.7.2

- Fixed:
  - fixing the issues with `pandas` >= `v2.1.0` (see `tfs-pandas` `v3.7.1`) by overwriting the `_constructor_from_mgr` function.  

## Version 3.7.1

- Changed:
  - The dependency on `pandas` was restricted to avoid the latest version, `2.1.0` and above as a temporary workaround to an attribute access bug that arose with it.

## Version 3.7.0

Minor API changes to the `TFSCollections`:

- the old `write_to` and `get_filename` are renamed to `_write_to` and `_get_filename` as they
    could only be accessed internally (due to the input parameters not available to the user).
    This also means, that - in case they are overwritten by a user's implementation - they need to be renamed there!!

- The column which is set as index can now also be defined manually, by overwriting the attribute `INDEX`, which defaults to `"NAME"`.

- New Functions of `TFSCollection` Instances:
  - `get_filename(name)`: Returns the associated filename to the property with name `name`.
  - `get_path(name)`: Return the actual file path of the property `name`
  - `flush()`: Write the current state of the TFSDataFrames into their respective files.
  - `write_tfs(filename, data_frame)`: Write the `data_frame` to `self.directory` with the given `filename`.

- New Special Properties of `TFSCollection` Instances:
  - `defined_properties`: Tuple of strings of the defined properties on this instance.
  - `filenames` is a convenience wrapper for `get_filename()`:
    - When called (`filenames(exist: bool)`) returns a dictionary of the defined properties and their associated filenames.
        The `exist` boolean filters between existing files or filenames for all properties.
    - Can also be used either `filenames.name` or `filenames[name]` to call `get_filename(name)` on the instance.

- Moved the define-properties functions directly into the `Tfs`-attribute marker class.
- Return of `None` for the `MaybeCall` class in case of attribute not found (instead of empty function, which didn't make sense).

## Version 3.6.0

- Removed:
  - The `append` and `join` methods of `TfsDataFrame` have been removed.

- Changed:
  - The dependency version on `pandas` has been restored to `>=1.0.0` as the above removal restores compatibility with `pandas` `2.0`.

## Version 3.5.3

- Changed:
  - Fixed a wrong deprecation of the `.merge` method of `TfsDataFrames`.

## Version 3.5.2

- Changed:
  - The dependency on `pandas` has been pinned to `<2.0` to guarantee the proper functionning of the compability `append` and `join` methods in `TfsDataFrames`. These will be removed with the next release of `tfs-pandas` and users should use the `tfs.frame.concat` compatibility function instead.

## Version 3.5.1

- Fixed:
  - Allow reading of empty lines in headers again.

## Version 3.5.0

- Fixed:
  - Any empty strings ("") in a file's columns will now properly be read as such and not converted to `NaN`.

- Added:
  - It is now possible to only read the headers of a file by using a new function, `read_headers`. The function API is not exported at the top level of the package but is available to import from `tfs.reader`.

## Version 3.4.0

- Added:
  - The `read_tfs` and `write_tfs` functions can now handle reading / writing compressed files, see documentation for details.

## Version 3.3.1

- Changed:
  - Column types are now assigned at read time instead of later on, which should improve performance for large data frames.

## Version 3.3.0

- Added:
  - The option is now given to the user to skip data frame validation after reading from file / before writing to file. Validation is left "on" by default, but can be turned off with a boolean argument.

- Changes:
  - The `tfs.frame.validate` function has seen its internal logic reworked to be more efficient and users performing validation on large data frames should notice a significant performance improvement.
  - The documentation has been expanded and improved, with notably the addition of example code snippets.

## Version 3.2.1

- Changed:
  - Allow spaces in header names.

## Version 3.2.0

- Added:
  - HDF5 read/write.
  
- Changed:
  - The minimum required Python version is now `3.7`.

## Version 3.1.0

- Fixed:
  - Removed dependency on depricated `numpy.str`

- Changed:
  - No logging of error messages internally for reading files and checking dataframes.
      Instead logging is either moved to `debug`-level or all info is now in the error message itself
      to be handled externally by the user.

## Version 3.0.2

- Fixed:
  - String representation of empty headers is fixed (accidentally printed 'None' before).

## Version 3.0.1

- Fixed:
  - Merging functionality from `TfsDataFrame.append`, `TfsDataFrame.join`, `TfsDataFrame.merge` and `tfs.concat` do not crash anymore when encountering a `pandas.DataFrame` (or more for `tfs.concat`) in their input. Signatures have been updated and tests were added for this behavior.

## Version 3.0.0

A long-standing issue where merging functionality used on `TfsDataFrame` (through `.merge` or `pandas.concat` for instance) would cause them to be cast back to `pandas.DataFrame` and lose their headers has been patched.

- Breaking changes:
  - The internal API has been reworked for clarity and consistency. Note that anyone previously using the high-level exports `tfs.read`, `tfs.write` and `tfs.TfsDataFrame` **will not be affected**.

- Added:
  - The `TfsDataFrame` class now has new `.append`, `.join` and `.merge` methods wrapping the inherited methods of the same name and fixing the aforementioned issue.
  - A `tfs.frame.concat` function, exported as `tfs.concat`, has been added to wrap `pandas.concat` and fix the aforementioned issue.
  - A `tfs.frame.merge_headers` function has been added.
  - Top level exports are now: `tfs.TfsDataFrame`, `tfs.read`, `tfs.write` and `tfs.concat`.

- Changes:
  - The `tfs.frame.validate` function is now a public-facing documented API and may be used stably.
  - The `write_tfs` function now appends an `EOL` (`\n`) at the end of the file when writing out for visual clarity and readability. This is a purely cosmetic and **does not** change functionality / compatibility of the files.
  - Documentation and README have been updated and cleared up.

Please do refer to the documentation for the use of the new merging functionality to be aware of caveats, especially when merging headers.

## Version 2.1.0

- Changes:
  - The parsing in `read_tfs` has been reworked to make use of `pandas`'s C engine, resulting in drastic performance improvements when loading files. No functionality was lost or changed.

## Version 2.0.3

- Fixed:
  - Took care of a numpy deprecation warning when using `np.str`, which should not appear anymore for users.

- Changes:
  - Prior to version `2.0.3`, reading and writing would raise a `TfsFormatError` in case of non-unique indices or columns. From now on, this behavior is an option in `read_tfs` and `write_tfs`called `non_unique_bahvior` which by default is set to log a warning. If explicitely asked by the user, the failed check will raise a `TfsFormatError`.

## Version 2.0.2

- Fixed:
  - Proper error on non-string columns
  - Writing numeric-only mixed type dataframes bug

## Version 2.0.1

- Fixed:
  - No longer warns on MAD-X styled string column types (`%[num]s`).
  - Documentation is up-to-date, and plays nicely with `Sphinx`'s parsing.
  - Fix a wrong type hint.

## Version 2.0.0

- Breaking Changes:
  - `FixedColumn`, `FixedColumnCollection` and `FixedTfs` have been removed from the package
  - Objects are not converted to strings upon read anymore, and will raise an error
  - Minimum pandas version is 1.0

- Fixed:
  - No longer writes an empty line to file in case of empty headers
  - "Planed" dataframes capitalize plane key attributes to be consistent with other `pylhc` packages, however they can be accessed with and without capitalizing your query.

- Changes:
  - Minimum required `numpy` version is now 1.19
  - TfsDataFrames now automatically cast themselves to pandas datatypes using `.convert_dtypes()`
  - Lighter dependency matrix
  - Full testing of supported Python versions across linux, macOS and windows systems through Github Actions

## Version 1.0.5

- Fixed:
  - Bug with testing for headers, also in pandas DataFrames
  - Same testing method for all data-frame comparisons
  - Some minor fixes

- Added:
  - Testing of writing of pandas DataFrames

## Version 1.0.4

- Added:
  - support for pathlib Paths
  - strings with spaces support (all strings in data are quoted)
  - more validation checks (no spaces in header/columns)
  - nicer string representation
  - left-align of index-column

- Removed:
  - `.indx` from class (use `index="NAME"` instead)

- Fixed:
  - Writing of empty dataframes
  - Doc imports
  - Minor bugfixes

## Version 1.0.3

- Fixed:
  - From relative to absolute imports (IMPORTANT FIX!!)

## Version 1.0.2

- Fixed:
  - Additional index column after writing is removed again
  - Renamded sigificant_numbers to significant_digits
  - significant_digits throws proper error if zero-error is given

- Added:
  - Fixed Dataframe Class
  - Type Annotations

## Version 1.0.1

- Fixed:
  - Metaclass-Bug in Collections

- Added:
  - Additional Unit Tests
  - Versioning
  - Changelog

## Version 1.0.0

- Initial Release
