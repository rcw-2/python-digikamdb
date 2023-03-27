# Test base

import logging
import os
import sys
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip     # noqa: F401
from typing import Any, Mapping, Optional       # noqa: F401


log = logging.getLogger(__name__)


class DigikamTestBase(TestCase):
    """Base Class"""
    
    _do_cleanup = True
    
    @classmethod
    def setUpClass(cls):
        log.info('Setting up %s', cls.__name__)
        cls.mydir = mkdtemp()
        cls.datadir = os.path.join(os.path.dirname(__file__), 'data')

    @classmethod
    def tearDownClass(cls):
        log.info('Tearing down %s', cls.__name__)
        if cls._do_cleanup:
            rmtree(cls.mydir)
        else:
            log.warning('Not removing temporary directory %s', cls.mydir)

    def setUp(self):
        # Log class and real test method name so we can see
        # to which test function the log data belongs.
        log.info(
            'Setting up %s object for %s',
            self.__class__.__name__,
            getattr(self, self._testMethodName).__name__
        )
        if not self.__class__._do_cleanup:
            log.warning('_do_cleanup is False')
    
    def tearDown(self):
        log.info('Tearing down %s object', self.__class__.__name__)
        if hasattr(self, 'dk'):
            self.dk.destroy()
        
        if sys.version_info.major > 3 or sys.version_info.minor > 10:
            return
            # The following stuff does not work in Python 3.11.
        
        result = self.defaultTestResult()
        self._feedErrorsToResult(result, self._outcome.errors)
        if all(test != self for test, text in result.errors + result.failures):
            return

        log.error('Test failed')
        if self._outcome.result.failfast:
            self.__class__._do_cleanup = False
    
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


        
