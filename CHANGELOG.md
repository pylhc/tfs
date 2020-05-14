# TFS-Pandas Changelog

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
