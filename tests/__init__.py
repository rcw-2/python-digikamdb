
import logging
import logging.handlers
import os
from unittest import TestCase, skip     # noqa: F401

from digikamdb import Digikam

# Run the digikamrc tests first
from .digikamrc import (                                    # noqa: F401
    DigikamRCTest as aDigikamRCTest,
)
# Run SQLite before MySQL tests as they run faster
from .sqlite import (                                       # noqa: F401
    SQLite_00_FromString as bSQLite_00_FromString,
    SQLite_01_SanityCheck as bSQLite_01_SanityCheck,
    SQLite_02_TestData as bSQLite_02_TestData,
    SQLite_03_CheckImageData as bSQLite_03_CheckImageData,
    SQLite_04_NewData as bSQLite_04_NewData,
    SQLite_04a_NewData15 as bSQLite_04a_NewData15,
    SQLite_05_RootOverride_01 as bSQLite_05_RootOverride_01,
    SQLite_05_RootOverride_02 as bSQLite_05_RootOverride_02,
    SQLite_05_RootOverride_03 as bSQLite_05_RootOverride_03,
)
# Then, MySQL
from .mysql import (                                        # noqa: F401
    MySQL_00_FromString as cMySQL_00_FromString,
    MySQL_01_SanityCheck as cMySQL_01_SanityCheck,
    MySQL_02_TestData as cMySQL_02_TestData,
    MySQL_03_CheckImageData as cMySQL_03_CheckImageData,
    MySQL_04_NewData as cMySQL_04_NewData,
    MySQL_04a_NewData15 as cMySQL_04a_NewData15,
    MySQL_05_RootOverride_01 as cMySQL_05_RootOverride_01,
    MySQL_05_RootOverride_02 as cMySQL_05_RootOverride_02,
    MySQL_05_RootOverride_03 as cMySQL_05_RootOverride_03,
)


# Log with debug to test.log
handler = logging.handlers.RotatingFileHandler('test.log', backupCount = 3)
logging.basicConfig(
    handlers = [handler],
    level = logging.DEBUG,
    format = '%(levelname)s %(name)s:%(lineno)d %(message)s',
)
handler.doRollover()
log = logging.getLogger(__name__)

os.environ['SQLALCHEMY_WARN_20'] = 'true'


class aBasicTests(TestCase):
    
    def test_10_constructor(self):
        with self.assertRaises(TypeError):
            self.dk = Digikam(1)

