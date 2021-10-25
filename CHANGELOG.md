# TFS-Pandas Changelog

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
