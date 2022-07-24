
import logging

# Run the digikamrc tests first
from .digikamrc import (                                    # noqa: F401
    DigikamRCTest as aDigikamRCTest,
)
# Run SQLite before MySQL tests as they run faster
from .sqlite import (                                       # noqa: F401
    SQLite_01_SanityCheck as bSQLite_01_SanityCheck,
    SQLite_02_TestData as bSQLite_02_TestData,
    SQLite_03_CheckComments as bSQLite_03_CheckComments,
    SQLite_04_NewData as bSQLite_04_NewData,
)
# Then, MySQL
from .mysql import (                                        # noqa: F401
    MySQL_01_SanityCheck as cMySQL_01_SanityCheck,
    MySQL_02_TestData as cMySQL_02_TestData,
    MySQL_03_CheckComments as cMySQL_03_CheckComments,
    MySQL_04_NewData as cMySQL_04_NewData,
)


# Log with debug to test.log
logging.basicConfig(filename = 'test.log', level = logging.DEBUG)
log = logging.getLogger(__name__)

