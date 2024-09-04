The Table File System Format
============================

**TFS** is an acronym for the "Table File System", and the TFS format has been used at CERN since the LEP control system.
The accelerator physics codes MAD-X and MAD-NG output tables in the TFS format, and accept TFS files as input for tables.

The origin of the TFS definition [#f1]_ seems difficult to find, and no official standard has been maintained.
As such, this document aims to provide a comprehensive description of the TFS format, at the very least as it is parsed and written by the package.

Written TFS files follow a structure in two parts: first the ``headers`` lines and then the ``table`` itself.

Headers
-------

The first section of the TFS file contains `headers`, lines each containing a parameter, its type and its value.
All headers lines start with the `@` character, and have the following structure:

- The `@` character.
- The name of the parameter.
- The type identifier of the parameter (see below).
- The value of the parameter.

An example header line is:

.. code-block::

    @ NAME                   %le             0.269975


Table
-----

After header lines, the `table` section follows.
A first line, starting with the `*` character, contains the names of the columns.
Just below, a line starting with the `$` character contains the type identifier of the columns.
These two lines look like:

.. code-block::

    *             INTEGERS              STRINGS               FLOATS
    $                   %d                   %s                  %le


Afterwards, all contain the data of the table, right-aligned with the column names.
Following the example above, a table line would look like:

.. code-block::

    *             INTEGERS              STRINGS               FLOATS
    $                   %d                   %s                  %le
                         1            SOMETHING              4.51395
                     21345         "WITH SPACE"             123.4825



.. rubric:: Footnotes

.. [#f1] Ph. Defert, Ph. Hofmann, and R. Keyser. *The Table File System, the C Interfaces*. LAW Note 9, CERN, 1989.