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



MAD-X Compatibility
-------------------

Meh.


MAD-NG Compatibility
--------------------

Meh.