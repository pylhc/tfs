# TFS-Pandas Changelog
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
