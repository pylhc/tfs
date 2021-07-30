"""
Exposes TfsDataFrame, read and write directly in tfs namespace, as well as the package version.
"""
from tfs.errors import TfsFormatError
from tfs.frame import TfsDataFrame
from tfs.reader import read_tfs
from tfs.writer import write_tfs

__title__ = "tfs-pandas"
__description__ = "Read and write tfs files."
__url__ = "https://github.com/pylhc/tfs"
__version__ = "2.2.0"
__author__ = "pylhc"
__author_email__ = "pylhc@github.com"
__license__ = "MIT"

# aliases
read = read_tfs
write = write_tfs

__all__ = [read, write, TfsDataFrame, __version__]
