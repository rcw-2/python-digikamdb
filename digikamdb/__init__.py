"""
This package provides an object-oriented interface to the Digikam metadata
by accessing the Digikam database.

Access to Digikam data is usually done with the :class:`~digikamdb.connection.Digikam` class.
"""

from .connection import Digikam
from .exceptions import DigikamError

from ._version import version

