import logging
import os
from shutil import unpack_archive

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound

from digikamdb import Digikam

from .base import DigikamTestBase
from .sanity import SanityCheck
from .data import TestData
from .comments import CheckComments
from .newdata import NewData


log = logging.getLogger(__name__)


class SQLiteTestBase(DigikamTestBase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        archive = os.path.join(
            os.path.dirname(__file__),
            'data',
            'testdb.tar.gz')
        unpack_archive(archive, cls.mydir)
        cls.root_override = {
            'ids':      {1: 'TEST'},
            'paths':    {1: cls.mydir}
        }
        cls.test_data = {
            'albumroots': [{
                'id': 1,
                'label': 'Pictures',
                'mountpoint': 'TEST',
                'path': 'MYDIR'}],
            'albums': [{'id': 1, 'path': 'MYDIR'}],
            'images': [{
                'id': 1,
                'name': '20210806_165143.jpg',
                'comments': {
                    'title': {
                        '_default':     'New title for image 1',
                        'de-DE':        'Die Destillerie',
                    },
                    'caption': {
                        '_default':     'New caption for image 1',
                        'de-DE': {
                            'RCW':      'Ein Kommentar von RCW',
                        },
                    },
                },
            }],
            'tags': [{'id': 22, 'pid': 0, 'name': 'France'}]
        }
    
    def setUp(self):
        dbfile = os.path.join(self.mydir, 'digikam4.db')
        db = create_engine('sqlite:///' + dbfile)
        self.dk = Digikam(db, root_override = self.root_override)
    
    def tearDown(self):
        self.dk.destroy()


class SQLite_01_SanityCheck(SQLiteTestBase, SanityCheck):
    
    def test00_sqlite(self):
        self.assertFalse(self.dk.is_mysql)
        with self.assertRaises(NoResultFound):
            _ = self.dk.tags._root


class SQLite_02_TestData(SQLiteTestBase, TestData):
    pass


class SQLite_03_CheckComments(SQLiteTestBase, CheckComments):
    pass


class SQLite_04_NewData(SQLiteTestBase, NewData):
    pass

