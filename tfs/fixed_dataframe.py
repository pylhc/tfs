"""
Fixed Dataframe
-----------------------

This classes allow you to pre-define your dataframes and only allow specific columns and headers.


:Example:

.. sourcecode:: python

    class KickTfs(FixedTfs):
        filename = "kick_{}.tfs"
        two_planes = True

        class Columns(FixedColumnCollection):
            NAME = FixedColumn("NAME", str)
            S = FixedColumn("S", float, "m")
            ALPHA = FixedColumn("ALF{}", float, "m")
            BETA = FixedColumn("BET{}", float, "m")

        class Headers(FixedColumnCollection):
            TITLE = FixedColumn("Title", str)
            TUNEX = FixedColumn("Q1", float)
            RESCALE = FixedColumn("RescaleFactor{}", float)

        Index = Columns.NAME

    kick_x = KickTfs(plane="X", directory="measurement_output")

    kick_x[kick_x.Columns.ALPHA] = calculate_alpha()
    # is equivalent to
    kick_x.ALFX = calculate_alpha()

    # the following will fail:
    kick_x["ALFY"] = calculate_alpha()

    # to write the file as kick_x.tfs into measurement_output:
    kick_x.write()

    # the class still has the old definitions stored
    KickTfs.Columns.ALPHA != kick_x.Columns.ALPHA

    # Getting a plane into the columns can be done at any level
    planed_columns = KickTfs.Columns("X")
    planed_columns.ALPHA == KickTfs.Columns.ALPHA("X")


``kick_x`` has now all columns defined, including their ``dtype``, which ensures successfull writing
into a file. Otherwise ``kick_x`` will behave like a normal TfsDataFrame.

The naming of the classes as ``Columns`` and ``Headers`` is important, as otherwise the definitions
will not be found. Not including them will result in unrestricted DataFrames.


:Issues:

* If a lower-level function creating a new dataframe (e.g. ``append()`` or ``concat``) is called,
  the definitions might be lost.
* Tricks can be used to temporarily create new columns and headers (e.g. writing to the headers object directly).
  It is in your hand to control for this once in a while by calling
  :meth:`FixedTfs.validate_definitions`.
  The dataframe is also checked before writing.

"""
import os
from collections import defaultdict, OrderedDict, namedtuple
from contextlib import suppress

from tools import DotDict
from handler import TfsDataFrame, read_tfs, write_tfs

DEFAULTS = defaultdict(float, {int: 0, str: ''})


class FixedColumn(DotDict):
    """ Class to define columns by name and dtype and possibly unit.
    The unit is not used internally so far, but might be useful for some applications."""
    def __init__(self, name: str, dtype: type, unit: str = ""):
        super().__init__(dict(name=name, dtype=dtype, unit=unit))

    def __str__(self):
        return self.name

    def __call__(self, plane):
        return FixedColumn(self.name.format(plane), self.dtype, self.unit)


class FixedColumnCollection(object):
    """ Abstract class to define TFS-Columns with name and Type.

    The columns are sorted into `names` and `types`, or as named-tuples in `columns`.
    Order of the properties is preserved since python 3.6 (see:
    https://stackoverflow.com/a/36060212/5609590
    https://docs.python.org/3.6/whatsnew/3.6.html#whatsnew36-pep520 )

    """
    def __init__(self, plane: str = "", exclude: FixedColumn = None):
        type_and_unit = namedtuple("type_and_unit", ["dtype", "unit"])

        self.plane = plane
        if exclude is None:
            exclude = []
        columns = [c for c in type(self).__dict__.items() if isinstance(c[1], FixedColumn) and c[1] not in exclude]
        self.mapping = OrderedDict()
        for attribute, column in columns:
            new_column = column(plane)
            setattr(self, attribute, new_column)  # use same attributes but now 'planed'
            self.mapping[new_column.name] = type_and_unit(dtype=new_column.dtype, unit=new_column.unit)
        self.names, (self.dtypes, self.units) = self.mapping.keys(), zip(*self.mapping.values())

    def __iter__(self):
        return zip(self.names, self.dtypes, self.units)

    def __len__(self):
        return len(self.names)


class FixedTfs(TfsDataFrame):
    """ Abstract class to handle fixed TfsDataFrames.

    The final class needs to define filename, columns and headers.
    The instance directory and plane.
    """

    filename = ""
    two_planes = True
    _initialized = False

    def __init__(self, plane: str = "", directory: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls = type(self)
        self._directory = directory
        self._plane = plane
        if not cls.two_planes and len(plane):
            raise ValueError(f"{cls.__name__} is planeless, but a plane was defined.")
        self._filename = os.path.join(directory, cls.filename.format(plane))

        self.Columns = None
        with suppress(AttributeError, TypeError):
            self.Columns = cls.Columns(plane, exclude=[cls.Index])

        self.Index = None
        with suppress(AttributeError, TypeError):
            self.Index = cls.Index(plane)

        self.Headers = None
        with suppress(AttributeError, TypeError):
            self.Headers = cls.Headers(plane)

        self._fill_missing_definitions()
        self.validate_definitions()
        self._initialized = True

    def __setitem__(self, key, value):
        try:
            return super().__setitem__(key, value)
        finally:
            if self._initialized and key in self.columns:
                for attribute in ("name", "dtype"):
                    self._validate(attribute, "Columns", key)

    # Fill function --------------------

    def _fill_missing_definitions(self):
        if self.Columns is not None:
            self._fill_missing_columns()

        if self.Headers is not None:
            self._fill_missing_headers()

        if self.Index is not None:
            self._fill_missing_index()

    # ---

    def _fill_missing_columns(self):
        for name, datatype, _ in self.Columns:
            if name not in self.columns:
                self[name] = DEFAULTS[datatype]
        self.reindex(self.Columns.names)
        self.astype({name: dtype for name, dtype, _ in self.Columns}, copy=False)

    def _fill_missing_headers(self):
        for name, datatype, _ in self.Headers:
            if name not in self.headers:
                self.headers[name] = DEFAULTS[datatype]
        new_headers = OrderedDict([(key, self.headers.pop(key)) for key in self.Headers.names])
        new_headers.update(self.headers)  # should be error, will raised in validation step!
        self.headers = new_headers

    def _fill_missing_index(self):
        self.index.name = self.Index.name
        self.index = self.index.astype(self.Index.dtype)

    # Validation --------------------

    def _is_valid_name(self, kind, key):
        if getattr(self, kind) is None:
            return True
        return key in getattr(self, kind).names

    def _is_valid_dtype(self, kind, key):
        if getattr(self, kind) is None:
            return True

        check_type = getattr(self, kind).mapping[key].dtype
        try:
            dtype = self[key].dtype
        except AttributeError:
            return isinstance(self[key], check_type)

        if check_type == str and dtype == object:
            return True
        return dtype == check_type

    def _validate(self, attribute, kind, key=None):
        keys = getattr(self, kind.lower()) if key is None else [key]
        map_ = {
            "name": (self._is_valid_name, KeyError),
            "dtype": (self._is_valid_dtype, TypeError)
        }
        accepted, error = map_[attribute]
        invalid_name = [k for k in keys if not accepted(kind, k)]
        if len(invalid_name):
            raise error(f"Found invalid {kind} {attribute}s '{str(invalid_name)}'")

    def _validate_index_name(self):
        if self.Index is not None:
            if not self.index.name == self.Index.name:
                raise KeyError("Invalid index in DataFrame.")

    def _validate_index_type(self):
        if self.Index is not None and len(self.index) > 0:
            if not isinstance(self.index[0], self.Index.dtype):
                raise TypeError("Invalid index type in DataFrame.")

    def validate_definitions(self):
        """ Validate the column, header and index present. """
        for kind in ("Columns", "Headers"):
            for attribute in ("dtype", "name"):
                self._validate(attribute, kind)
        self._validate_index_name()
        self._validate_index_type()

    # IO Functions --------------------

    def get_filename(self) -> str:
        return self._filename

    def write(self):
        self.validate_definitions()
        write_tfs(self._filename, self, save_index=self.index.name)

    def read(self) -> 'FixedTfs':
        return type(self)(self._plane, self._directory,
                          read_tfs(self._filename, index=self.index.name))
