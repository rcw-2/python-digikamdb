
import logging

from .sqlite import (                                       # noqa: F401
    SQLite_01_SanityCheck,
    SQLite_02_TestData,
    SQLite_03_CheckComments,
    SQLite_04_NewData
)
from .mysql import (                                        # noqa: F401
    MySQL_01_SanityCheck,
    MySQL_02_TestData,
    MySQL_03_CheckComments,
    MySQL_04_NewData
)

logging.basicConfig(filename = 'test.log', level = logging.DEBUG)
log = logging.getLogger(__name__)

