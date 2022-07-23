# Test base

import logging
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip     # noqa: F401


log = logging.getLogger(__name__)


class DigikamTestBase(TestCase):
    """Base Class"""
    
    @classmethod
    def setUpClass(cls):
        log.info('Setting up %s', cls.__name__)
        cls.mydir = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        log.info('Tearing down %s', cls.__name__)
        rmtree(cls.mydir)

    def setUp(self):
        # Log class and real test method name so we can see
        # to which test function the log data belongs.
        log.info(
            'Setting up %s object for %s',
            self.__class__.__name__,
            getattr(self, self._testMethodName).__name__
        )
    
    def replacepath(self, path):
        return path.replace('MYDIR', self.mydir)

