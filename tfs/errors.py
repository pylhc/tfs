"""
Errors
------

Errors that can be raised during the handling of **TFS** files.
"""

from __future__ import annotations  # for delayed type annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# ----- Main Exception to Inherit From ----- #


class TfsFormatError(Exception):
    """
    Raised when an issue is detected in the **TFS** file or dataframe.
    """


# ----- Specific Exceptions ----- #


class AbsentColumnNameError(TfsFormatError):
    """Raised when a **TFS** file does not provide column names."""

    def __init__(self, file_path: Path) -> None:
        errmsg = f"Missing column name(s) in file {file_path.absolute()}. File not read."
        super().__init__(errmsg)


class AbsentColumnTypeError(TfsFormatError):
    """Raised when a **TFS** file does not provide column type identifiers."""

    def __init__(self, file_path: Path) -> None:
        errmsg = f"Missing column type(s) in file {file_path.absolute()}. File not read."
        super().__init__(errmsg)


class AbsentTypeIdentifierError(TfsFormatError):
    """Raised when a **TFS** file's header line does not provide type identifier."""

    def __init__(self, header_line_elements: list[str]) -> None:
        errmsg = f"No data type found in header: '{''.join(header_line_elements)}'"
        super().__init__(errmsg)


class DuplicateColumnsError(TfsFormatError):
    """Raised when a **TfsDataFrame** has duplicate columns."""

    def __init__(self) -> None:
        errmsg = "The dataframe contains non-unique columns."
        super().__init__(errmsg)


class DuplicateIndicesError(TfsFormatError):
    """Raised when a **TfsDataFrame** has duplicate indices."""

    def __init__(self) -> None:
        errmsg = "The dataframe contains non-unique indices."
        super().__init__(errmsg)


class InvalidBooleanHeaderError(TfsFormatError):
    """
    Raised when an unaccepted boolean header
    value is read in the **TFS** file.
    """

    def __init__(self, header_value: str) -> None:
        errmsg = f"Invalid boolean header value parsed: '{header_value}'"
        super().__init__(errmsg)


class IterableInDataFrameError(TfsFormatError):
    """Raised when an list / tuple is found in the column of a **TfsDataFrame**."""

    def __init__(self) -> None:
        errmsg = "Lists or tuple elements are not accepted in a TfsDataFrame"
        super().__init__(errmsg)


class MADXCompatibilityError(TfsFormatError):
    """Raised when validation for **MADX** compatibility fails."""


class NonStringColumnNameError(TfsFormatError):
    """Raised when a **TfsDataFrame** has non-string type column names."""

    def __init__(self) -> None:
        errmsg = "TFS-Columns need to be strings."
        super().__init__(errmsg)


class SpaceinColumnNameError(TfsFormatError):
    """Raised when a **TfsDataFrame** has spaces in column names."""

    def __init__(self) -> None:
        errmsg = "TFS-Columns can not contain spaces."
        super().__init__(errmsg)


class UnknownTypeIdentifierError(TfsFormatError):
    """Raised when a **TFS** file contains an unknown type identifier."""

    def __init__(self, type_identifier: str) -> None:
        errmsg = f"Unknown data type: {type_identifier}"
        super().__init__(errmsg)
