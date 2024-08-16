"""
Errors
------

Errors that can be raised during the handling of **TFS** files.
"""

# ----- Main Exception to Inherit From ----- #


class TfsFormatError(Exception):
    """
    Raised when an issue is detected in the **TFS** file or dataframe.
    """


# ----- Exceptions Relating to Headers ----- #


class InvalidBooleanHeaderError(TfsFormatError):
    """
    Raised when an unaccepted boolean header
    value is read in the **TFS** file.
    """

    def __init__(self, header_value: str) -> None:
        errmsg = f"Invalid boolean header value parsed: '{header_value}'"
        super().__init__(errmsg)


# ----- Exceptions for DataFrame Content ----- #


class DuplicateColumnsError(TfsFormatError):
    """Raised when a **TfsDataFrame** has duplicate columns."""

    def __init__(self) -> None:
        errmsg = "The dataframe contains non-unique columns."
        super().__init__(errmsg)

class DuplicateIndicesError(TfsFormatError):
    """Raised when a **TfsDataFrame** has duplicate columns."""

    def __init__(self) -> None:
        errmsg = "The dataframe contains non-unique indices."
        super().__init__(errmsg)


# ----- Exceptions for Validation ----- #


class IterableInDataFrameError(TfsFormatError):
    """Raised when an list / tuple is found in the column of a **TfsDataFrame**."""

    def __init__(self) -> None:
        errmsg = "Lists or tuple elements are not accepted in a TfsDataFrame"
        super().__init__(errmsg)
