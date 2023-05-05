import logging
import os
from datetime import datetime
from subprocess import run, CalledProcessError

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound                    # noqa: F401

from digikamdb import Digikam, DigikamDataIntegrityError    # noqa: F401
from digikamdb.types import *                               # noqa: F403

from .base import DigikamTestBase
from .sanity import SanityCheck
from .data import TestData
from .imagedata import CheckImageData
from .newdata import NewDataRoot, NewDataRootOverride, NewData


log = logging.getLogger(__name__)


class MySQLTestBase(DigikamTestBase):
    
    # File containing test database
    test_db_dump = 'testdb.sql.xz'
    
    # Root override for test DB
    root_override = {
        'ids': {
            'volumeid:?uuid=722b9c6f-0249-4fc2-8acf-d9926bb2995a': 'MYDIR',
        },
    }
    
    # Test data
    test_data = {
        'albumroots': [{
            'id': 1,
            'label': 'Pictures',
            'mountpoint': 'MYDIR',
            'path': 'MYDIR/home/digikam2/Pictures'}],
        'albums': [{'id': 1, 'path': 'MYDIR/home/digikam2/Pictures'}],
        'images': [
            {
                'id': 1,
                'name': '20210806_165143.jpg',
                'title': 'The distillery',
                'position': None,
                'information': {
                    'width':        4032,
                    'height':       3024,
                    'format':       'JPG',
                    'colorDepth':   8,
                    'rating':       -1,
                },
                'imagemeta': {
                    'make':             'samsung',
                    'model':            'SM-G970F',
                    'aperture':         2.4,
                    'focalLength':      4.32,
                    'focalLength35':    26,
                    'exposureTime':     0.0012531328320802004,
                },
                'captions': {
                    ('x-default', None):   (
                        'At the distillery Christian Drouin',
                        datetime.fromisoformat('2022-07-10T12:42:56'),
                    ),
                },
            },
            {
                'id':   3,
                'name': 'IMG39991.JPG',
                'imagemeta': {
                    'lens': 'Canon EF-S 10-22mm f/3.5-4.5 USM',
                },
            },
            {
                'id':       5,
                'name':     '20220722_190613.jpg',
                'position': (49.875974899927776, 8.66468980047438, 529),
            },
        ],
        'tags': [{'id': 22, 'pid': 0, 'name': 'Normandy'}],
        'image_queries': [{
            'where':    ['modificationDate >= "2022-07-20 00:00:00"'],
            'result':   [4, 5, 6],
        }],
    }
    
    # Test data for comment changes
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
                    'RCW': (
                        'Ein Kommentar von RCW',
                        datetime.now().replace(microsecond = 0)
                    ),
                },
            },
        },
    ]
    
    # Test data for image information
    test_info = {
        1:  { 'rating':   2 },
    }
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import mysql_data
        
        if cls.test_db_dump.endswith('.xz'):
            cat = 'xzcat'
        elif cls.test_db_dump.endswith('gz'):
            cat = 'zcat'
        elif cls.test_db_dump.endswith('bz2'):
            cat = 'bzcat'
        else:
            cat = 'cat'
        
        try:
            run(
                '{4} {5} | mysql -v -h {0} -u {1} -p"{2}" {3}'.format(
                    mysql_data.db_host,
                    mysql_data.db_user,
                    mysql_data.db_pass,
                    mysql_data.db_name,
                    cat,
                    os.path.join(cls.datadir, cls.test_db_dump),
                ),
                shell = True,
                check = True,
                capture_output = True
            )
        except CalledProcessError as e:
            # Replace password in command line
            e.cmd = e.cmd.replace(mysql_data.db_pass, 'XXX')
            # Raise another Exception to make stderr visible
            # in unittest output
            log.error('Error: %s', e)
            log.debug('STDOUT: %s', e.stdout.decode('utf-8'))
            log.debug('STDERR: %s', e.stderr.decode('utf-8'))
            raise RuntimeError(e.stderr.decode('utf-8'))
        
        cls.mysql_db = 'mysql+pymysql://{0}:{1}@{2}/{3}'.format(
            mysql_data.db_user,
            mysql_data.db_pass,
            mysql_data.db_host,
            mysql_data.db_name,
        )
    
    def setUp(self):
        super().setUp()
        db = create_engine(self.mysql_db)

        self.dk = Digikam(db, root_override = self.replace_root_override())


class MySQL_00_FromString(MySQLTestBase):
    
    def setUp(self):
        super().setUp()
        self.dk = Digikam(self.mysql_db, root_override = self.replace_root_override())
    
    def test_data(self):
        for al in self.dk.albums:
            self.assertIsInstance(al.relativePath, str)


class MySQL_01_SanityCheck(MySQLTestBase, SanityCheck):
    
    def test00_mysql(self):
        self.assertTrue(self.dk.is_mysql)
    
    def test45_root_tag(self):
        root = self.dk.tags._root
        self.assertEqual(root.id, 0)
        self.assertEqual(root.pid, -1)
        self.assertIsNone(root.parent)
        self.assertEqual(root.name, '_Digikam_root_tag_')

    def test46_tags_move(self):
        with self.assertRaises(NotImplementedError):
            tag = self.dk.tags[5]
            tag._pid = 0
            self.dk.session.commit()
    

class MySQL_02_TestData(MySQLTestBase, TestData):
    pass


class MySQL_03_CheckImageData(MySQLTestBase, CheckImageData):
    pass


class MySQL_04_NewData(MySQLTestBase, NewData):
    
    # Use empty database without root_override
    test_db_dump = 'empty.sql.xz'
    root_override = None


class MySQL_04a_NewData15(MySQLTestBase, NewData):
    
    # Use empty database without root_override
    test_db_dump = 'empty-15.sql.xz'
    root_override = None


class MySQL_05_RootOverride_01(MySQLTestBase, NewDataRoot):
    
    # Use empty database with empty root_override
    test_db_dump = 'empty.sql.xz'
    root_override = {}


class MySQL_05_RootOverride_02(MySQLTestBase, NewDataRoot):
    
    # Use empty database with root_override containing empty sub-dicts
    test_db_dump = 'empty.sql.xz'
    root_override = { 'ids': {}, 'paths': {} }


class MySQL_05_RootOverride_03(MySQLTestBase, NewDataRootOverride):
    
    # Use empty database without root_override
    test_db_dump = 'empty.sql.xz'
    root_override = None

