import os
import pytest
from . import context
from tfs import read_tfs, write_tfs
from collection import TfsCollection


class CollectionTest(TfsCollection):
