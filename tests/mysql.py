import logging
import os
from subprocess import run, CalledProcessError

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound                    # noqa: F401

from digikamdb import Digikam, DigikamDataIntegrityError    # noqa: F401

from .base import DigikamTestBase
from .sanity import SanityCheck
from .data import TestData
from .comments import CheckComments
from .newdata import NewData


log = logging.getLogger(__name__)


class MySQLTestBase(DigikamTestBase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import mysql_data
        
        try:
            run(
                'zcat {0} | mysql -h {1} -u {2} -p"{3}" {4}'.format(
                    os.path.join(os.path.dirname(__file__), 'data', 'testdb.sql.gz'),
                    mysql_data.db_host,
                    mysql_data.db_user,
                    mysql_data.db_pass,
                    mysql_data.db_name,
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
            raise RuntimeError(e.stderr.decode('utf-8'))
                
        cls.mysql_db = 'mysql+pymysql://{0}:{1}@{2}/{3}'.format(
            mysql_data.db_user,
            mysql_data.db_pass,
            mysql_data.db_host,
            mysql_data.db_name,
        )
        
        cls.root_override = {
            'ids': {
                'volumeid:?uuid=722b9c6f-0249-4fc2-8acf-d9926bb2995a': 'MYDIR',
            },
        }
        
        # Test data
        cls.test_data = {
            'albumroots': [{
                'id': 1,
                'label': 'Pictures',
                'mountpoint': 'MYDIR',
                'path': 'MYDIR/home/digikam2/Pictures'}],
            'albums': [{'id': 1, 'path': 'MYDIR/home/digikam2/Pictures'}],
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
            'tags': [{'id': 22, 'pid': 0, 'name': 'Normandy'}]
        }
    
    def setUp(self):
        super().setUp()
        db = create_engine(self.mysql_db)

        root_override = {}
        for group in ['ids', 'paths']:
            if group in self.root_override:
                root_override[group] = {}
                for key, value in self.root_override[group].items():
                    root_override[group][key] = self.replacepath(value)
        self.dk = Digikam(db, root_override = root_override)
    
    def tearDown(self):
        self.dk.destroy()
        

class MySQL_01_SanityCheck(MySQLTestBase, SanityCheck):
    
    def test00_mysql(self):
        self.assertTrue(self.dk.is_mysql)
    
    def test45_root_tag(self):
        root = self.dk.tags._root
        self.assertEqual(root.id, 0)
        self.assertEqual(root.pid, -1)
        self.assertIsNone(root.parent)
        self.assertEqual(root.name, '_Digikam_root_tag_')


class MySQL_02_TestData(MySQLTestBase, TestData):
    pass


class MySQL_03_CheckComments(MySQLTestBase, CheckComments):
    pass


class MySQL_04_NewData(MySQLTestBase, NewData):
    pass


