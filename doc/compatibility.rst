MAD-X and MAD-NG Compatibility
==============================

As `tfs-pandas` allows one to write `TfsDataFrames` as files in the **TFS** format, which are typically output by simulations codes, compatibility of these files with said codes is crucial.
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
    The default compatibility mode enforced before writing is ``MAD-X``, as this ensures the file would be accepted by both codes.

Validation is done by providing a `TfsDataFrame` and a compatibility mode to `tfs.frame.validate` (see the :ref:`API reference <modules/index:frame>`).
It goes as:

.. code-block:: python

    import tfs
    from tfs.frame import validate

    df = tfs.read("path/to/file.tfs")

    # To validate with MAD-X compatibility
    validate(df, compatibility="mad-x")  # or use "madx"

    # To validate with MAD-NG compatibility
    validate(df, compatibility="mad-ng")  # or use "madng"

In case of compatibility issue, an exception is raised which will point to the specific incompatible element.
All exceptions inherit from the `TfsFormatError`, which one can `except` as a catch-all for this package.

.. _common rules:

Common Validation Rules
-----------------------

In either compatibility mode, some common rules are enforced.
These rules are listed and described in the :ref:`API reference <modules/index:frame>` for the `tfs.frame.validate` function.

When validating a `TfsDataFrame`, the behavior in case one of these rules is violated depends on the value of the `non_unique_behavior` parameter.
These rules are *always* checked against when validating a `TfsDataFrame`.
Additional checks can be performed by setting the `compatibility` parameter, as described in the :ref:`MAD-NG <madng mode>` and :ref:`MAD-X <madx mode>` below.

.. _madng mode:

MAD-NG Compatibility
--------------------

Since ``MAD-NG`` implements and accepts more features into its **TFS** files, its compatibility mode is naturally less restrictive.
Namely, the following are accepted by ``MAD-NG`` and ``MAD-NG`` only:

- Boolean dtype for header parameters and table columns.
- Complex dtype for header parameters and table columns.

.. admonition:: Complex Number Representation

    In Python, the imaginary part of a complex number is represented by the letter ``j``, as in `1.4 + 2.6j`.
    When writing complex values to file, `tfs-pandas` will instead use the ``MAD-NG`` (read `Lua`) representation, and uses the letter ``i``, as in `1.4 + 2.6i`, so that ``MAD-NG`` can properly read such a file.
    Both of these representations will be correctly read by `tfs-pandas` (including when ``MAD-NG`` uses ``I`` for special complex numbers cases).

.. attention::

    The exotic "features" of ``MAD-NG`` such as the ``Lua`` operator overloading for ranges and their inclusion in **TFS** files are not supported by `tfs-pandas`.
    Should one need to use these features, it is recommended to go through the `pymadng <https://pymadng.readthedocs.io/en/latest/>`_ package to handle them in-memory.

.. _madx mode:

MAD-X Compatibility
-------------------

The ``MAD-X`` compatibility mode is more restrictive, and enforces that none of the features listed in the :ref:`MAD-NG section <madng mode>` do not appear in the `TfsDataFrame`.

.. admonition:: Default mode

    The default compatibility mode enforced before writing is ``MAD-X``.
    This decision is to ensure the file would be accepted by both codes when using default values.
