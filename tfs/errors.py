"""
Errors
------

Errors that can be raised during the handling of **TFS** files.
"""

# ----- Exceptions Relating to Headers ----- #

class InvalidBooleanHeaderError(Exception):
    """
    Raised when an unaccepted boolean header
    value is read in the **TFS** file.
    """

    def __init__(self, header_value: str) -> None:
        errmsg = f"Invalid boolean header value parsed: '{header_value}'"
        super().__init__(errmsg)

# ----- Main Exception to Inherit From ----- #

class TfsFormatError(Exception):
    """Raised when a wrong format is detected in the **TFS** file."""


# ----- Exceptions Relating to Validation ----- #

class TfsValidationError(TfsFormatError):
    """Raised when a **TFS** file or dataframe does not pass validation."""


class IterableInDataframeError(TfsValidationError):
    """Raised when an list / tuple is found in the column of a **TfsDataFrame**."""

    def __init__(self) -> None:
        errmsg = "Lists or tuple elements are not accepted in a TfsDataFrame"
        super().__init__(errmsg)
