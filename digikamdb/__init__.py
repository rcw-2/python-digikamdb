"""
This package provides an object-oriented interface to the Digikam metadata
by accessing the Digikam database.

Access to Digikam data is usually done with the :class:`~digikamdb.conn.Digikam`
class.
"""

from .conn import Digikam               # noqa: F401
from .exceptions import *               # noqa: F401, F403

from ._version import version
__version__ = version

