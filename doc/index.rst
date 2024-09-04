Welcome to tfs-pandas' documentation!
=====================================

``tfs-pandas`` is a library for reading and writing capabilities for **TFS** files used at `CERN <https://home.cern/>`_, namely by codes such as `MAD-X <https://madx.web.cern.ch/>`_ and `MAD-NG <https://madx.web.cern.ch/releases/madng/html/>`_.

It provides functionality through a ``TfsDataFrame`` object, an extension of the popular **pandas** ``DataFrame``, which in addition to the normal behaviour attaches a dictionary of headers to the dataframe.
Functions are also exported that handle reading and writing of **TFS** files to and from ``TfsDataFrames`` as well as merging and validating for ``TfsDataFrames``.

.. admonition:: **Package Scope**

   The package only has as a goal to provide a simple and easy to use interface from **TFS** files to a familiar object build upon the `pandas.DataFrame`.
   It is not meant to implement various calculations on `TfsDataFrames`.

   Tools relative to the **TFS** format are provided, such as validating a `TfsDataFrame` and its headers; or lazily managing a collection of **TFS** files.


Installation
============

Installation is easily done via `pip`:

.. code-block:: bash

   python -m pip install tfs-pandas

One can also install in a `conda`/`mamba` environment via the `conda-forge` channel with:

.. code-block:: bash

   conda install -c conda-forge tfs-pandas

You can now start using the package.
You can find here a :doc:`quickstart guide  <quickstart>` to walk you through functionalities and their usage.


Contents
========

.. toctree::
   :maxdepth: 2

   quickstart
   tfsformat
   compatibility
   modules/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
