"""
Collection
----------

Advanced **TFS** files reading and writing functionality.
"""
import pathlib

from pandas import DataFrame

from tfs.frame import TfsDataFrame
from tfs.reader import read_tfs
from tfs.writer import write_tfs


class _MetaTfsCollection(type):
    """
    Metaclass for TfsCollection. It takes the class attributes declared as
    `Tfs(...)` and replaces it for a property getter and setter. Check
    TfsCollection docs.
    """

    def __new__(mcs, cls_name, bases, dct: dict):
        new_dict = dict(dct)
        new_dict["_two_plane_names"] = []
        # for name in dct:
        for key, value in dct.items():
            try:
                args = value.args
                kwargs = value.kwargs
            except AttributeError:
                continue
            new_props = _define_property(args, kwargs)
            try:
                prop_x, prop_y = new_props
                new_dict.pop(key)
                new_dict["_two_plane_names"].append(key)
                new_dict[key + "_x"] = prop_x
                new_dict[key + "_y"] = prop_y
            except TypeError:
                new_dict[key] = new_props
        return super().__new__(mcs, cls_name, bases, new_dict)


class TfsCollection(metaclass=_MetaTfsCollection):
    """
    Abstract class to lazily load and write **TFS** files.

    Classes inheriting from this abstract class will be able to define **TFS** files
    as readable or writable, and read or write them just as attribute access or
    assignments. All attributes will be read and written as `~tfs.TfsDataFrame` objects.

    Example:
        If **./example** is a directory that contains two **TFS** files **beta_phase_x.tfs**
        and **beta_phase_y.tfs** with `BETX` and `BETY` columns respectively:

    .. code-block:: python

        >>> # All TFS attributes must be marked with the Tfs(...) class,
        ... # and generated attribute names will be appended with _x / _y 
        ... # depending on files found in "./example"
        ... class ExampleCollection(TfsCollection): 
        ...     beta = Tfs("beta_phase_{}.tfs")  # A TFS attribute
        ...     other_value = 7  # A traditional attribute.

        ...     def get_filename(template: str, plane: str) -> str:
        ...         return template.format(plane)

        >>> example = ExampleCollection("./example")

        >>> # Get the BETX / BETY column from "beta_phase_x.tfs":
        >>> beta_x_column = example.beta_x.BETX  # / example.beta_x.BETY

        >>> # Get the BETY column from "beta_phase_y.tfs":
        >>> beta_y_column = example.beta_y.BETY

        >>> # The planes can also be accessed as items (both examples below work):
        >>> beta_y_column = example.beta["y"].BETY
        >>> beta_y_column = example.beta["Y"].BETY

        >>> # This will write an empty DataFrame to "beta_phase_y.tfs":
        >>> example.allow_write = True
        >>> example.beta["y"] = DataFrame()


    If the file to be loaded is not defined for two planes then the attribute can be declared 
    and accessed as:
    
    .. code-block:: python

        >>> coupling = Tfs("getcouple.tfs", two_planes=False)  # declaration
        >>> f1001w_column = example.coupling.F1001W  # access

    No file will be loaded until the corresponding attribute is accessed and the loaded
    `~tfs.TfsDataFrame` will be buffered, thus the user should expect an ``IOError`` if the requested
    file is not in the provided directory (only the first time, but is better to always take it
    into account!).

    When a ``TfsDataFrame`` is assigned to one attribute, it will be set as the buffer value. If the
    ``self.allow_write`` attribute is set to ``True``, an assignment on one of the attributes will
    trigger the corresponding file write.
    """

    def __init__(self, directory: pathlib.Path, allow_write: bool = None):
        self.directory = pathlib.Path(directory) if isinstance(directory, str) else directory
        self.allow_write = False if allow_write is None else allow_write
        self.maybe_call = _MaybeCall(self)
        self._buffer = {}

    def get_filename(self, *args, **kwargs):
        """
        Return the filename to be loaded or written.

        This function will get as parameters any parameter given to the Tfs(...) attributes. It must
        return the filename to be written according to those parameters. If ``two_planes=False`` is
        not present in the Tfs(...) definition, it will also be given the keyword argument
        ``plane="x"`` or ``plane="y"``.
        """
        raise NotImplementedError("This is an abstract method, it should be implemented in subclasses.")

    def write_to(self, *args, **kwargs):
        """
        Returns the filename and `TfsDataFrame` to be written on assignments.

        If this function is overwritten, it will replace ``get_filename(...)`` in file writes to
        find out the filename of the file to be written. It also gets the value assigned as first
        parameter. It must return a tuple (filename, tfs_data_frame).
        """
        raise NotImplementedError("This is an abstract method, it should be implemented in subclasses.")

    def clear(self):
        """
        Clear the file buffer.

        Any subsequent attribute access will try to load the corresponding file again.
        """
        self._buffer = {}

    def read_tfs(self, filename: str) -> TfsDataFrame:
        """
        Reads the **TFS** file from ``self.directory`` with the given filename.

        This function can be overwritten to use something instead of ``tfs-pandas`` to load the
        files.

        Arguments:
            filename (str): The name of the file to load.

        Returns:
            A ``TfsDataFrame`` built from reading the requested file.
        """
        tfs_data_df = read_tfs(self.directory / filename)
        if "NAME" in tfs_data_df:
            tfs_data_df = tfs_data_df.set_index("NAME", drop=False)
        return tfs_data_df

    def __getattr__(self, attr: str) -> object:
        if attr in self._two_plane_names:
            return TfsCollection._TwoPlanes(self, attr)
        raise AttributeError(f"{self.__class__.__name__} object has no attribute {attr}")

    def _load_tfs(self, filename: str):
        try:
            return self._buffer[filename]
        except KeyError:
            tfs_data = self.read_tfs(filename)
            if "NAME" in tfs_data:
                tfs_data = tfs_data.set_index("NAME", drop=False)
            self._buffer[filename] = tfs_data
            return self._buffer[filename]

    def _write_tfs(self, filename: str, data_frame: DataFrame):
        if self.allow_write:
            write_tfs(self.directory / filename, data_frame)
        self._buffer[filename] = data_frame

    class _TwoPlanes(object):
        def __init__(self, parent, attr):
            self.parent = parent
            self.attr = attr

        def __getitem__(self, plane: str):
            return getattr(self.parent, self.attr + "_" + plane.lower())

        def __setitem__(self, plane: str, value):
            setattr(self.parent, self.attr + "_" + plane.lower(), value)


class Tfs:
    """Class to mark attributes as **TFS** attributes.

    Any parameter given to this class will be passed to the ``get_filename()`` and ``write_to()``
    methods, together with the plane if ``two_planes=False`` is not present.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


# Private methods to define the properties ##################################


def _define_property(args, kwargs):
    if "two_planes" not in kwargs:
        return _define_property_two_planes(args, kwargs)
    elif kwargs["two_planes"]:
        kwargs.pop("two_planes")
        return _define_property_two_planes(args, kwargs)
    else:
        kwargs.pop("two_planes")

        def getter_funct(self):
            return _getter(self, *args, **kwargs)

        def setter_funct(self, tfs_data):
            return _setter(self, tfs_data, *args, **kwargs)

        return property(fget=getter_funct, fset=setter_funct)


def _define_property_two_planes(args, kwargs) -> tuple:
    x_kwargs = dict(kwargs)
    y_kwargs = dict(kwargs)
    x_kwargs["plane"] = "x"
    y_kwargs["plane"] = "y"

    def x_getter_funct(self):
        return _getter(self, *args, **x_kwargs)

    def x_setter_funct(self, tfs_data):
        return _setter(self, tfs_data, *args, **x_kwargs)

    def y_getter_funct(self):
        return _getter(self, *args, **y_kwargs)

    def y_setter_funct(self, tfs_data):
        return _setter(self, tfs_data, *args, **y_kwargs)

    property_x = property(fget=x_getter_funct, fset=x_setter_funct)
    property_y = property(fget=y_getter_funct, fset=y_setter_funct)
    return property_x, property_y


def _getter(self, *args, **kwargs):
    filename = self.get_filename(*args, **kwargs)
    return self._load_tfs(filename)


def _setter(self, value, *args, **kwargs):
    try:
        filename, data_frame = self.write_to(value, *args, **kwargs)
        self._write_tfs(filename, data_frame)
    except NotImplementedError:
        filename = self.get_filename(*args, **kwargs)
        self._write_tfs(filename, value)


class _MaybeCall:
    """
    Handles the maybe_call feature of the TfsCollection.

    This class defines the `maybe_call` attribute in the instances of `TfsCollection`. To avoid
    repetitive try / except blocks, this class allows you to do:
    ``meas.maybe_call.beta["x"](some_funct, args, kwargs)``.
    If the requested file is available, the call is equivalent to: ``some_funct(args, kwargs)``, if
    not then no function is called and the program continues.
    """

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return _MaybeCall.MaybeCallAttr(self.parent, attr)

    class MaybeCallAttr:
        def __init__(self, parent, attr):
            self.parent = parent
            self.attr = attr

        def __getitem__(self, item):
            return _MaybeCall.MaybeCallAttr(self.parent, self.attr + "_" + item)

        def __call__(self, function_call, *args, **kwargs):
            try:
                tfs_file = getattr(self.parent, self.attr)
            except IOError:
                return lambda funct: None  # Empty function
            return function_call(tfs_file, *args, **kwargs)
