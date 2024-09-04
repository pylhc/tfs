The Table File System Format
============================

**TFS** is an acronym for the "Table File System", and the TFS format has been used at CERN since the LEP control system.
The accelerator physics codes MAD-X and MAD-NG output tables in the TFS format, and accept TFS files as input for tables.

The origin of the TFS definition [#f1]_ seems difficult to find, and no official standard has been maintained.
As such, this document aims to provide a comprehensive description of the TFS format, at the very least as it is parsed and written by the package.

Written TFS files follow a structure in two parts: first the ``headers`` lines and then the ``table`` itself.


.. rubric:: Footnotes

.. [#f1] Ph. Defert, Ph. Hofmann, and R. Keyser. *The Table File System, the C Interfaces*. LAW Note 9, CERN, 1989.