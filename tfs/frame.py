"""
Frame
-------------------

Contains the class definitiion of a TfsDataFrame, inherited from the ``pandas`` DataFrame.
"""
from contextlib import suppress
from typing import Sequence

import pandas as pd


class TfsDataFrame(pd.DataFrame):
    """
    Class to hold the information of the built an extended ``pandas`` DataFrame, together with a way of
    getting the headers of the **TFS** file. As the file headers are stored in a dictionary upon read,
    to get a header value use ``data_frame["header_name"]``.
    """

    _metadata = ["headers"]

    def __init__(self, *args, **kwargs):
        self.headers = {}
        with suppress(IndexError, AttributeError):
            self.headers = args[0].headers
        self.headers = kwargs.pop("headers", self.headers)
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: object) -> object:
        try:
            return super().__getitem__(key)
        except KeyError as error:
            try:
                return self.headers[key]
            except KeyError:
                raise KeyError(f"{key} is neither in the DataFrame nor in headers.")
            except TypeError:
                raise error

    def __getattr__(self, name: str) -> object:
        try:
            return super().__getattr__(name)
        except AttributeError:
            try:
                return self.headers[name]
            except KeyError:
                raise AttributeError(f"{name} is neither in the DataFrame nor in headers.")

    @property
    def _constructor(self):
        return TfsDataFrame

    def __repr__(self) -> str:
        space: str = " " * 4

        def _str_items(items_list: Sequence[str]) -> str:
            return "\n".join(f"{space}{k}: {v}" for k, v in items_list)

        s: str = ""
        if len(self.headers):
            s += "Headers:\n"
            if len(self.headers) > 7:
                items = list(self.headers.items())
                s += f"{_str_items(items[:3])}\n{space}...\n{_str_items(items[-3:])}\n"
            else:
                s += f"{_str_items(self.headers.items())}\n"
            s += "\n"
        return f"{s}{super().__repr__()}"
