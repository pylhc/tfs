"""
Errors
------

Errors that can be raised during the handling of **TFS** files.
"""


class TfsFormatError(Exception):
    """Raised when a wrong format is detected in the **TFS** file."""


class InvalidBooleanHeader(Exception):
    """
    Raised when an unaccepted boolean header
    value is read in the **TFS** file.
    """

    def __init__(self, header_value: str) -> None:
        errmsg = f"Invalid boolean header value parsed: '{header_value}'"
        super().__init__(errmsg)
