2 Minutes to tfs-pandas
=======================

Yes, 2 minutes.
That's how little it takes!

Basic Usage
-----------

The package is imported as `tfs`, and exports top-level functions for reading and writing:

.. code-block:: python

   import tfs

   # Loading a TFS file is simple
   df = tfs.read("path_to_input.tfs", index="index_column")

   # Writing out to disk is simple too
   tfs.write("path_to_output.tfs", df, save_index="index_column")

Once loaded, you get your data in a `~.TfsDataFrame`, which is a `pandas.DataFrame` with a `dict` of headers attached to it.
You can access and manipulate all data as you would with a `DataFrame`:

.. autolink-preface:: import tfs
.. code-block:: python

   # Access and modify the headers with the .headers attribute
   useful_variable = data_frame.headers["SOME_KEY"]
   data_frame.headers["NEW_KEY"] = some_variable

   # Manipulate data as you do with pandas DataFrames
   data_frame["NEWCOL"] = data_frame.COLUMN_A * data_frame.COLUMN_B

   # You can check the TfsDataFrame validity, and choose the behavior in case of errors
   tfs.frame.validate(data_frame, non_unique_behavior="raise")  # or choose "warn"

Compression
-----------

A **TFS** file being text-based, it benefits heavily from compression.
Thankfully, `tfs-pandas` supports automatic reading and writing of various compression formats.
Just use the API as you would normally, and the compression will be handled automatically based on the extension:

.. autolink-preface:: import tfs
.. code-block:: python

   # Compression format is inferred from the file extension
   df = tfs.read("filename.tfs.gz", index="index_column")

   # Same thing when writing to disk
   tfs.write("path_to_output.tfs.zip", df)

A special module is provided to interface to the ``HDF5`` format.
First though, one needs to install the package with the `hdf5` extra requirements:

.. code-block:: bash

   python -m pip install --upgrade "tfs-pandas[hdf5]"

Then, access the functionality from `tfs.hdf`.

.. autolink-preface:: import tfs
.. code-block:: python

   from tfs.hdf import read_hdf, write_hdf
   
   # Read a TfsDataFrame from an HDF5 file
   df = tfs.hdf.read_hdf("path_to_input.hdf5", key="key_in_hdf5_file")

   # Write a TfsDataFrame to an HDF5 file
   tfs.hdf.write_hdf("path_to_output.hdf5", df, key="key_in_hdf5_file")

Validation
----------

As **TFS** files typically come from the output of simulations codes, validation modes are available to ensure compatibility with said codes.
This is done through the `tfs.frame.validate` function, or relevant arguments in both the reader and writer functions.

As validation modes and compatibility details are complex, validation warrants its own documentation page.
Please refer to the :doc:`compatibility and validation guide <compatibility>` for more information.

Function Replacements
---------------------

Finally, some replacement functions are provided for some `pandas` operations which, if used, would return a `pandas.DataFrame` instead of a `~.TfsDataFrame`.

.. autolink-preface:: import tfs, pandas as pd
.. code-block:: python

   df1 = tfs.read("file1.tfs")
   df2 = tfs.read("file2.tfs")

   # This returns a pandas.DataFrame and makes you lose the headers
   result = pd.concat([df1, df2])

   # Instead, use our own wrapper
   result = tfs.frame.concat([df1, df2])  # you can choose how to merge headers too
   assert isinstance(result, tfs.TfsDataFrame)  # that's ok!
   assert getattr(result, "headers", None) is not None  # headers are not lost

That's it!
