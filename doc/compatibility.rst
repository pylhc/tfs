MAD-X and MAD-NG Compatibility
==============================

As `tfs-pandas` allows one to write `TfsDataFrames` as files in the **TFS** format, compatibility of these files with simulation codes is crucial.
Specifically, `tfs-pandas` aims to ensure the files it writes to disk are accepted as input for `MAD-X <https://madx.web.cern.ch/>`_ and `MAD-NG <https://madx.web.cern.ch/releases/madng/html/>`_.

However, as ``MAD-NG`` is the successor to ``MAD-X``, it includes new features regarding the **TFS** format, and files including these features will not be accepted by ``MAD-X``.
To circumvent this issue, `tfs-pandas` offers functionality - named validation - to ensure compatibility with either code.

TfsDataFrame Validation
-----------------------

It is possible to perform automatic validation of a `TfsDataFrame` both when reading and writing, or to validate them at any time using the `tfs.frame.validate` function.
Validation enforces the rules described in the :ref:`caveats section <tfs-pandas caveats>`, both to guarantee the integrity of the dataframe and compatibility of written files with simulation codes.

.. admonition:: When Does Validation Happen?

    Validation is optional.
    It is by default turned off at read-time, and turned on at write-time.
    The default compability mode enforced before writing is ``MAD-X``, as this ensures the file would be accepted by both codes.

Validation is done by providing a `TfsDataFrame` and a compatibility mode to `tfs.frame.validate` (see the :ref:`API reference <modules/index:frame>`).
It goes as:

.. code-block:: python

    import tfs
    from tfs.frame import validate

    df = tfs.read("path/to/file.tfs")

    # To validate with MAD-X compatibility
    validate(df, compability="mad-x")

    # To validate with MAD-NG compability
    validate(df, compability="mad-ng")

In case of compability issue, an exception is raised which will point to the specific incompatible element.
All exceptions inherit from the `TfsFormatError`, which one can `except` as a catch-all for this package.

MAD-NG Compatibility
--------------------

Since ``MAD-NG`` implements and accepts more features into its **TFS** files, its compatibility mode is naturally less restrictive.



MAD-X Compatibility
-------------------

Meh.
