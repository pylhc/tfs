"""
Collection
----------

Advanced **TFS** files reading and writing functionality.
"""

from __future__ import annotations  # for delayed type annotations

import pathlib
from typing import TYPE_CHECKING

from tfs.reader import read_tfs
from tfs.writer import write_tfs

if TYPE_CHECKING:
    from pandas import DataFrame

    from tfs.frame import TfsDataFrame


class _MetaTfsCollection(type):
    """
    Metaclass for TfsCollection. It takes the class attributes declared as
    `Tfs(...)` and replaces it for a property getter and setter. Check
    TfsCollection docs.
    """

    def __new__(cls, cls_name, bases, dct: dict):
        new_dict = dict(dct)
        new_dict["_stored_definitions"] = {}
        new_dict["_two_plane_names"] = []
        # for name in dct:
        for key, value in dct.items():
            try:
                new_props = value.get_property()
            except AttributeError:
                continue

            try:
                prop_x, prop_y = new_props
            except TypeError:
                new_dict[key] = new_props
                new_dict["_stored_definitions"][key] = value
            else:
                new_dict.pop(key)
                new_dict["_two_plane_names"].append(key)
                for plane, prop in zip("xy", (prop_x, prop_y)):
                    new_key = f"{key}_{plane}"
                    new_dict[new_key] = prop
                    new_dict["_stored_definitions"][new_key] = value.get_planed_copy(plane)
        return super().__new__(cls, cls_name, bases, new_dict)


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

    INDEX = "NAME"

    def __init__(self, directory: pathlib.Path, allow_write: bool | None = None):
        self.directory = pathlib.Path(directory) if isinstance(directory, str) else directory
        self.allow_write = False if allow_write is None else allow_write
        self.maybe_call = _MaybeCall(self)
        self.filenames = TfsCollection._FilenameGetter(self)
        self.defined_properties = tuple(self._stored_definitions.keys())
        self._buffer = {}

    def get_filename(self, name: str) -> str:
        """Return the actual filename of the property `name`.

        Arguments:
            name (str): Property name of the file.

        Returns:
            A `str` of the actual name of the file in `directory`.
            The path to the file is then `self.directory / filename`.
        """
        definition: Tfs = self._stored_definitions.get(name)
        if not definition:
            errmsg = f"TfsCollection does not have any property named {name}."
            raise AttributeError(errmsg)
        return self._get_filename(*definition.args, **definition.kwargs)

    def get_path(self, name: str) -> pathlib.Path:
        """Return the actual file path of the property `name` (convenience function).

        Arguments:
            name (str): Property name of the file.

        Returns:
            A `pathlib.Path` of the actual name of the file in `directory`.
            The path to the file is then `self.directory / filename`.
        """
        return self.directory / self.get_filename(name)

    def _get_filename(self, *args, **kwargs):  # noqa: ARG002
        """
        Return the filename to be loaded or written.

        This function will get as parameters any parameter given to the Tfs(...) attributes. It must
        return the filename to be written according to those parameters. If ``two_planes=False`` is
        not present in the Tfs(...) definition, it will also be given the keyword argument
        ``plane="x"`` or ``plane="y"``.
        """
        errmsg = "This is an abstract method, it should be implemented in subclasses."
        raise NotImplementedError(errmsg)

    def _write_to(self, *args, **kwargs):  # noqa: ARG002
        """
        Returns the filename and `TfsDataFrame` to be written on assignments.

        If this function is overwritten, it will replace ``get_filename(...)`` in file writes to
        find out the filename of the file to be written.
        Which means you can define different locations for reading and writing.
        It also gets the value assigned as first parameter. It must return a tuple (filename, tfs_data_frame).
        """
        errmsg = "This is an abstract method, it should be implemented in subclasses."
        raise NotImplementedError(errmsg)

    def clear(self):
        """
        Clear the file buffer.

        Any subsequent attribute access will try to load the corresponding file again.
        """
        self._buffer = {}

    def flush(self):
        """
        Write the current state of the TFSDataFrames into their respective files.
        """
        if not self.allow_write:
            errmsg = "Cannot flush TfsCollection, as `allow_write` is set to `False`."
            raise OSError(errmsg)

        for filename, data_frame in self._buffer.items():
            write_tfs(self.directory / filename, data_frame)

    def read_tfs(self, filename: str) -> TfsDataFrame:
        """
        Reads the **TFS** file from ``self.directory`` with the given filename.

        This function can be overwritten to use something instead of ``tfs-pandas``
        to load the files. It does not set the TfsDataframe into the buffer
        (that is the job of `_load_tfs`)!

        Arguments:
            filename (str): The name of the file to load.

        Returns:
            A ``TfsDataFrame`` built from reading the requested file.
        """
        tfs_data_df = read_tfs(self.directory / filename)
        if self.INDEX and self.INDEX in tfs_data_df:
            tfs_data_df = tfs_data_df.set_index(self.INDEX, drop=False)
        return tfs_data_df

    def write_tfs(self, filename: str, data_frame: DataFrame):
        """
        Write the **TFS** file to ``self.directory`` with the given filename.

        This function can be overwritten to use something instead of ``tfs-pandas``
        to write out the files. It does not  check for `allow_write` and
        does not set the Dataframe into the buffer (that is the job of `_write_tfs`)!

        Arguments:
            filename (str): The name of the file to load.
            data_frame (TfsDataFrame): TfsDataframe to write

        """
        write_tfs(self.directory / filename, data_frame)

    def __getattr__(self, attr: str) -> object:
        if attr in self._two_plane_names:
            return TfsCollection._TwoPlanes(self, attr)
        errmsg = f"{self.__class__.__name__} object has no attribute {attr}"
        raise AttributeError(errmsg)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def _load_tfs(self, filename: str):
        try:
            return self._buffer[filename]
        except KeyError:
            tfs_data = self.read_tfs(filename)
            if self.INDEX and self.INDEX in tfs_data:
                tfs_data = tfs_data.set_index(self.INDEX, drop=False)
            self._buffer[filename] = tfs_data
            return self._buffer[filename]

    def _write_tfs(self, filename: str, data_frame: DataFrame):
        if self.allow_write:
            self.write_tfs(filename, data_frame)
        self._buffer[filename] = data_frame

    class _TwoPlanes:
        def __init__(self, parent, attr):
            self.parent = parent
            self.attr = attr

        def __getitem__(self, plane: str):
            return getattr(self.parent, f"{self.attr}_{plane.lower()}")

        def __setitem__(self, plane: str, value):
            setattr(self.parent, f"{self.attr}_{plane.lower()}", value)

    class _FilenameGetter:
        def __init__(self, parent: TfsCollection):
            self.parent = parent

        def __getitem__(self, item) -> str:
            return self.parent.get_filename(item)

        def __getattr__(self, attr) -> str:
            return self[attr]

        def __call__(self, exist: bool = False) -> dict[str, str]:  # noqa: FBT001, FBT002
            all_filenames = {name: self.parent.get_filename(name) for name in self.parent.defined_properties}
            if not exist:
                return all_filenames
            return {
                name: filename
                for name, filename in all_filenames.items()
                if (self.parent.directory / filename).is_file()
            }


class Tfs:
    """Class to mark attributes as **TFS** attributes.

    Any parameter given to this class will be passed to the ``_get_filename()`` method,
    together with the plane if ``two_planes=False`` is not present.
    """

    PLANES = "x", "y"

    def __init__(self, *args, **kwargs):
        self._two_planes = kwargs.pop("two_planes", True)
        self.args = args
        self.kwargs = kwargs

    def get_planed_copy(self, plane: str):
        return self.__class__(*self.args, plane=plane, **self.kwargs)

    def get_property(self):
        if self._two_planes:
            return self._get_property_two_planes()
        return self._get_property_single_plane()

    def _get_property_two_planes(self) -> tuple[property, property]:
        properties = [None, None]
        for idx, plane in enumerate(self.PLANES):
            planed = self.get_planed_copy(plane)
            properties[idx] = planed._get_property_single_plane()  # noqa: SLF001
        return tuple(properties)

    def _get_property_single_plane(self) -> property:
        def getter_funct(other: TfsCollection):
            filename = other._get_filename(*self.args, **self.kwargs)  # noqa: SLF001
            return other._load_tfs(filename)  # noqa: SLF001

        def setter_funct(other: TfsCollection, value):
            try:
                filename, data_frame = other._write_to(value, *self.args, **self.kwargs)  # noqa: SLF001
                other._write_tfs(filename, data_frame)  # noqa: SLF001
            except NotImplementedError:
                filename = other._get_filename(*self.args, **self.kwargs)  # noqa: SLF001
                other._write_tfs(filename, value)  # noqa: SLF001

        return property(fget=getter_funct, fset=setter_funct)


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
            return _MaybeCall.MaybeCallAttr(self.parent, f"{self.attr}_{item}")

        def __call__(self, function_call, *args, **kwargs):
            try:
                tfs_file = getattr(self.parent, self.attr)
            except OSError:
                return None
            return function_call(tfs_file, *args, **kwargs)
