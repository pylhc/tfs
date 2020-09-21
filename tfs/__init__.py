"""Exposes TfsDataFrame, read_tfs and write_tfs directly in tfs namespace."""
from tfs.handler import TfsDataFrame, read_tfs, write_tfs

__title__ = "tfs-pandas"
__description__ = "Read and write tfs files."
__url__ = "https://github.com/pylhc/tfs"
__version__ = "2.0.0"
__author__ = "pylhc"
__author_email__ = "pylhc@github.com"
__license__ = "MIT"

# aliases
read = read_tfs
write = write_tfs

__all__ = [read, read_tfs, write, write_tfs, __version__]
