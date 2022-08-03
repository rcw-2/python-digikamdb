import logging
import os
from shutil import unpack_archive

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound

from digikamdb import Digikam, DigikamDataIntegrityError    # noqa: F401

from .base import DigikamTestBase
from .sanity import SanityCheck
from .data import TestData
from .comments import CheckComments
from .newdata import NewDataRoot, NewDataRootOverride, NewData


log = logging.getLogger(__name__)


class SQLiteTestBase(DigikamTestBase):
    
    test_db = 'testdb.tar.gz'
    
    # Root overrides for class
    root_override = {
        'ids':      {1: 'TEST'},
        'paths':    {1: 'MYDIR'}
    }
    
    # Test data
    test_data = {
        'albumroots': [{
            'id': 1,
            'label': 'Pictures',
            'mountpoint': 'TEST',
            'path': 'MYDIR'}],
        'albums': [{'id': 1, 'path': 'MYDIR'}],
        'images': [
            {
                'id': 1,
                'name': '20210806_165143.jpg',
                'title': 'The Distillery',
                'position': None,
            }
        ],
        'tags': [{'id': 22, 'pid': 0, 'name': 'France'}]
    }
    
    test_comments = [
        {
            'id': 1,
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
        }
    ]
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        unpack_archive(os.path.join(cls.datadir, cls.test_db), cls.mydir)
    
    def setUp(self):
        super().setUp()
        dbfile = os.path.join(self.mydir, 'digikam4.db')
        db = create_engine('sqlite:///' + dbfile)
        
        self.dk = Digikam(db, root_override = self.replace_root_override())


class SQLite_00_FromString(SQLiteTestBase):
    
    def setUp(self):
        super().setUp()
        self.dk = Digikam(
            'sqlite:///' + os.path.join(self.mydir, 'digikam4.db'),
            root_override = self.replace_root_override()
        )
    
    def test_data(self):
        for al in self.dk.albums:
            self.assertIsInstance(al.relativePath, str)


class SQLite_01_SanityCheck(SQLiteTestBase, SanityCheck):
    
    def test00_sqlite(self):
        self.assertFalse(self.dk.is_mysql)
    
    def test45_root_tag(self):
        with self.assertRaises(NoResultFound):
            _ = self.dk.tags._root
        with self.assertRaises(NoResultFound):
            _ = self.dk.tags[0]


class SQLite_02_TestData(SQLiteTestBase, TestData):
    pass


class SQLite_03_CheckComments(SQLiteTestBase, CheckComments):
    pass


class SQLite_04_NewData(SQLiteTestBase, NewData):
    
    # Use empty database without root_override
    test_db = 'empty.tar.xz'
    root_override = None


class SQLite_05_RootOverride_01(SQLiteTestBase, NewDataRoot):
    
    # Use empty database without root_override
    test_db = 'empty.tar.xz'
    root_override = {}


class SQLite_05_RootOverride_02(SQLiteTestBase, NewDataRoot):
    
    # Use empty database without root_override
    test_db = 'empty.tar.xz'
    root_override = { 'ids': {}, 'paths': {} }


class SQLite_05_RootOverride_03(SQLiteTestBase, NewDataRootOverride):
    
    # Use empty database without root_override
    test_db_dump = 'empty.tar.xz'
    root_override = None

