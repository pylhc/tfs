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

Type Identifiers
----------------

Caveats
-------

No spaces in column names.
If spaces in strings, they should be enclosed in quotes or double quotes.

Example
-------

Many examples of a TFS file can be found in the repository's tests files, and one is included below:

.. code-block::

    @ TITLE                %s         "Table title"
    @ DPP                  %le                    1
    @ Q1                   %le             0.269975
    @ Q1RMS                %le          1.75643e-07
    @ NATQ1                %le             0.280041
    @ NATQ1RMS             %le           0.00102479
    @ BPMCOUNT             %d                     9
    *                 NAME                    S               NUMBER                   CO                CORMS              BPM_RES
    $                   %s                  %le                   %d                  %le                  %le                  %le
            "BPMYB.5L2.B1"               28.288                    1      -0.280727353099     0.00404721900879       0.121264541395
            "BPMYB.4L2.B1"               48.858                    2       0.601472827003     0.00301396244054       0.129738519811
            "BPMWI.4L2.B1"              73.3255                    3      -0.610294990396      0.0039123010318      0.0952864848273
            "BPMSX.4L2.B1"             123.4825           3472136972       0.778206651453     0.00542543379504      0.0578581425476
            "BPMS.2L2.B1"               161.394             59055944       0.585105573645     0.00291016910226         0.1223625619
            "BPMSW.1L2.B1"              171.328              9202215        2.50235465023     0.00275350035218       0.148603785488
            "BPMSW.1R2.B1"              214.518                 3117        1.81036167087     0.00282138482457       0.164954082556
            "BPMS.2R2.B1"               224.452          18943819309      0.0791371365672     0.00474290041487       0.122265653712
            "BPMSX.4R2.B1"             262.3635                  105    -0.00665768479832     0.00350302654669       0.187320306406



.. rubric:: Footnotes

.. [#f1] Ph. Defert, Ph. Hofmann, and R. Keyser. *The Table File System, the C Interfaces*. LAW Note 9, CERN, 1989.