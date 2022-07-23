# Test base

import logging
import os
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip     # noqa: F401
from typing import Any, Mapping, Optional       # noqa: F401


log = logging.getLogger(__name__)


class DigikamTestBase(TestCase):
    """Base Class"""
    
    @classmethod
    def setUpClass(cls):
        log.info('Setting up %s', cls.__name__)
        cls.mydir = mkdtemp()
        cls.datadir = os.path.join(os.path.dirname(__file__), 'data')

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
    
    def tearDown(self):
        if hasattr(self, 'dk'):
            self.dk.destroy()
    
    def replacepath(self, path):
        return path.replace('MYDIR', self.mydir)
    
    def replace_root_override(self) -> Optional[Mapping]:
        if self.root_override is None:
            return None
        
        root_override = {}
        for group in ['ids', 'paths']:
            if group in self.root_override:
                root_override[group] = {}
                for key, value in self.root_override[group].items():
                    root_override[group][key] = self.replacepath(value)
        
        return root_override


        
