import logging
import os
from shutil import copyfile, rmtree, unpack_archive
from subprocess import run, CalledProcessError
from tempfile import mkdtemp

from sqlalchemy.exc import NoResultFound    # noqa: F401

from digikamdb import *                                     # noqa: F403

from .base import DigikamTestBase


log = logging.getLogger(__name__)


class DigikamRCTest(DigikamTestBase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.old_home = os.environ['HOME']
    
    @classmethod
    def tearDownClass(cls):
        os.environ['HOME'] = cls.old_home
        super().tearDownClass()
    
    def setUp(self):
        super().setUp()
        self.home = mkdtemp()
        os.environ['HOME'] = self.home
        os.mkdir(os.path.join(self.home, '.config'))
        os.mkdir(os.path.join(self.home, 'Pictures'))
    
    def tearDown(self):
        rmtree(os.environ['HOME'])
        super().tearDown()
    
    def test_rc_nofile(self):
        with self.assertRaises(DigikamConfigError):
            self.dk = Digikam('digikamrc')
    
    def test_rc_sqlite(self):
        unpack_archive(
            os.path.join(self.datadir, 'testdb.tar.gz'),
            os.path.join(self.home, 'Pictures')
        )
        
        with open(
            os.path.join(self.datadir, 'digikamrc.sqlite'),
            'r'
        ) as infile:
            with open(
                os.path.join(self.home, '.config', 'digikamrc'),
                'w'
            ) as outfile:
                for line in infile.readlines():
                    outfile.write(line.replace('@@HOME@@', self.home))
        
        self.dk = Digikam('digikamrc')
        for al in self.dk.albums:
            self.assertIsInstance(al.relativePath, str)
    
    def test_rc_mysql(self):
        try:
            import mysql_data
            run(
                'xzcat {4} | mysql -h {0} -u {1} -p"{2}" {3}'.format(
                    mysql_data.db_host,
                    mysql_data.db_user,
                    mysql_data.db_pass,
                    mysql_data.db_name,
                    os.path.join(self.datadir, 'testdb.sql.xz'),
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
                
        with open(
            os.path.join(self.datadir, 'digikamrc.mysql'),
            'r'
        ) as infile:
            with open(
                os.path.join(self.home, '.config', 'digikamrc'),
                'w'
            ) as outfile:
                for line in infile.readlines():
                    outfile.write(
                        line
                        .replace('@@DB_HOST@@', mysql_data.db_host)
                        .replace('@@DB_USER@@', mysql_data.db_user)
                        .replace('@@DB_PASS@@', mysql_data.db_pass)
                        .replace('@@DB_NAME@@', mysql_data.db_name)
                    )

        self.dk = Digikam('digikamrc')
        for al in self.dk.albums:
            self.assertIsInstance(al.relativePath, str)
    
    def test_rc_mysql_internal(self):
        copyfile(
            os.path.join(self.datadir, 'digikamrc.mysql-internal'),
            os.path.join(self.home, '.config', 'digikamrc')
        )
        
        with self.assertRaises(DigikamConfigError):
            self.dk = Digikam('digikamrc')
        
