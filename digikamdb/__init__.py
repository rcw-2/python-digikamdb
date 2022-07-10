"""
This package provides an object-oriented interface to the Digikam metadata
by accessing the Digikam database.

Access to Digikam data is usually done with the :class:`~digikamdb.connection.Digikam`
class.
"""

from .connection import Digikam         # noqa: F401
from .exceptions import DigikamError    # noqa: F401

from ._version import version
__version__ = version

