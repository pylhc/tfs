The Table File System Format
============================

**TFS** is an acronym for "Table File System", and the TFS format has been used at `CERN <https://home.cern/>`_ since the LEP control system.
The accelerator physics codes `MAD-X <https://madx.web.cern.ch/>`_ and `MAD-NG <https://madx.web.cern.ch/releases/madng/html/>`_ output tables in the TFS format, and accept TFS files as input for tables.

The origin of the TFS definition [#f1]_ seems more than difficult to find, and no official spec has been maintained since then.
As such, this document aims to provide a comprehensive description of the TFS format, at the very least as it is parsed and written by `tfs-pandas`.

Written TFS files follow a structure in two parts: first the ``headers`` lines and then the ``table`` itself.
They are described below, including their specifics.

Headers
-------

The first section of the TFS file contains `headers`, lines each containing a parameter, its type and its value.
All headers lines start with the `@` character, and have the following structure:

- The `@` character, to identify the line as a header.
- The name of the parameter.
- The type identifier of the parameter (see `Types and Identifiers`_ below).
- The value of the parameter.

An example header line is:

.. code-block::

    @ NAME                   %le             0.269975

There is no limit on the number of header lines in a TFS file, and there can be no header lines at all.

Table
-----

After header lines follows the `table` section.
A first line, starting with the `*` character, contains the names of the columns.
Just below, a line starting with the `$` character contains the type identifiers of the columns' data (see `Types and Identifiers`_ below).
These two lines look like:

.. code-block::

    *             INTEGERS              STRINGS               FLOATS
    $                   %d                   %s                  %le


Afterwards all lines contain the data of the table, one row per line and columns separated by at least one blank space.
For readability the entries are traditionally right-aligned with their column names,
and the column width is chosen to accomodate the longest column name or value, but neither is mandatory.
Following the example above, a few table lines would look like:

.. code-block::

    *             INTEGERS              STRINGS               FLOATS
    $                   %d                   %s                  %le
                         1            SOMETHING              4.51395
                     21345         "WITH SPACE"             123.4825


Types and Identifiers
---------------------

Type identifiers are specific strings that indicate as which type to interpret the given data as, in the individual entries of the `Headers`_ as well as for the columns of the `Table`_.
The following type identifiers and their corresponding Python types are accepted and used by `tfs-pandas`:

================  ======================  =============== =========================
Type Indentifier  Associated Python Type          Example               Accepted by
================  ======================  =============== =========================
%s                                string        `%s name`  ``MAD-X`` and ``MAD-NG``
%bpm_s                            string    `%bpm_s name` ``MAD-X`` and ``MAD-NG``
%d                        64-bit integer         `%d 174`  ``MAD-X`` and ``MAD-NG``
%hd                       64-bit integer        `%hd 174`  ``MAD-X`` and ``MAD-NG``
%f                          64-bit float       `%f 0.946`  ``MAD-X`` and ``MAD-NG``
%le                         64-bit float      `%hf 0.946`  ``MAD-X`` and ``MAD-NG``
%b                               boolean        `%b true`           Only ``MAD-NG``
%lz                      128-bit complex   `%lz 1.4+2.6i`           Only ``MAD-NG``
================  ======================  =============== =========================

It is also possible to include the length of the value into the type identifier, as in `%10s` for a string of length 10.
`MAD-X` and `MAD-NG` inlcude the length in their output files, yet they are not mandatory to be able to read the files back into these programms. 
`tfs-pandas` does not write length-values out and ignores any length-values when parsing files.
It treats the identifier as if given without, meaning that the given data does not need to comply to the given length.

.. admonition:: MAD-NG Specific Types

    Both boolean and complex types are specific to the ``MAD-NG`` code, and would not be accepted by ``MAD-X``.
    Please see the :doc:`compatibility section <compatibility>` for more information.

.. _tfs-pandas caveats:

TFS-Pandas Caveats
------------------

The following caveats apply to the `tfs-pandas` package:

- Column names should be strings.
- No spaces should be present in column names.
- The table should not contain duplicate indices.
- The table should not contain duplicate columns.
- If spaces are present in strings, they should be enclosed in either single or double quotes.
- The table data should not contain nested structures (lists, tuples, etc.).
- The table data should not contain non-physical values (``NaN``, ``Inf``, etc.) as they would not be read back by either ``MAD-X`` or ``MAD-NG``.

.. admonition:: DataFrame Validation

    It is possible to perform automatic validation of the `TfsDataFrame` both when reading and writing, or to validate them at any time using the `tfs.frame.validate` function.
    See the :ref:`API reference <modules/index:frame>` for more information.

Not respecting the above does not necessarily lead to an issue when reading or writing a TFS file (without validation), but it might be an issue trying to get such a file accepted by `MAD-X` or `MAD-NG`.

TFS File Example
----------------

Many examples of TFS files can be found in the repository's tests files, and a simple one is included below:

.. code-block::

    @ TITLE                %s         "Table title"
    @ DPP                  %le                    1
    @ Q1                   %le             0.269975
    @ Q1RMS                %le          1.75643e-07
    @ NATQ1                %le             0.280041
    @ NATQ1RMS             %le           0.00102479
    @ BPMCOUNT             %d                     9
    *                 NAME                    S                   CO                CORMS              BPM_RES
    $                   %s                  %le                  %le                  %le                  %le
            "BPMYB.5L2.B1"               28.288      -0.280727353099     0.00404721900879       0.121264541395
            "BPMYB.4L2.B1"               48.858       0.601472827003     0.00301396244054       0.129738519811
            "BPMWI.4L2.B1"              73.3255      -0.610294990396      0.0039123010318      0.0952864848273
            "BPMSX.4L2.B1"             123.4825       0.778206651453     0.00542543379504      0.0578581425476
            "BPMS.2L2.B1"               161.394       0.585105573645     0.00291016910226         0.1223625619
            "BPMSW.1L2.B1"              171.328        2.50235465023     0.00275350035218       0.148603785488
            "BPMSW.1R2.B1"              214.518        1.81036167087     0.00282138482457       0.164954082556
            "BPMS.2R2.B1"               224.452      0.0791371365672     0.00474290041487       0.122265653712
            "BPMSX.4R2.B1"             262.3635    -0.00665768479832     0.00350302654669       0.187320306406



.. rubric:: Footnotes

.. [#f1] Ph. Defert, Ph. Hofmann, and R. Keyser. *The Table File System, the C Interfaces*. LAW Note 9, CERN, 1989.
