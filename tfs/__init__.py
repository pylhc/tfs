"""
Exposes TfsDataFrame, read and write directly in tfs namespace, as well as the package version.
"""
from tfs.errors import TfsFormatError
from tfs.frame import TfsDataFrame, concat
from tfs.hdf import read_hdf, write_hdf
from tfs.reader import read_tfs
from tfs.writer import write_tfs

__version__ = "3.8.0"

# aliases
read = read_tfs
write = write_tfs

__all__ = ["concat", "read", "write", "read_hdf", "write_hdf", "TfsDataFrame", "TfsFormatError", "__version__"]
