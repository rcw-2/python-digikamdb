"""
Generate APIdoc .rst files from within sphinx-build

sphinx-apidoc does a great job scanning for .py files and creating stub
.rst files. However, there seems to be no option to integrate this step
into the standard Sphinx workflow. This module is an attempt to du just
that. It calls the appropriate functions of AutoDoc and has options for
most command line switches of :command:`sphinx-apidoc`.
"""

__version__ = '0.1.5'

import os

from sphinx.util.osutil import ensuredir
from sphinx.ext.apidoc import recurse_tree, create_modules_toc_file
from sphinx.util import logging
from sphinx.errors import ExtensionError

args_translate = {
    "follow_links":     "followlinks",
    "separate_modules": "separatemodules",
    "include_private":  "includeprivate",
    "module_first":     "modulefirst",
}

logger = logging.getLogger(__name__)

class apidoc_args(object):
    """
    Object to store args for recurse_tree
    
    :param app:             The application object
    :type app:              :class:`~sphinx:sphinx.application.Sphinx`
    :param str module_path: Path to the Python modules to document
    :param dict config:     Configuration for the given path
    """
    def __init__(self, app, module_path, config):
        """
        Constructor
        """
        
        # Set defaults
        self.module_path = module_path
        self.exclude_patterns = app.config.apidocrun_exclude_patterns
        self.destdir = app.config.apidocrun_destdir
        self.quiet = app.quiet
        self.maxdepth = app.config.apidocrun_maxdepth
        # TODO: set from app
        self.force = False
        self.followlinks = app.config.apidocrun_follow_links
        #TODO: set from app
        self.dryrun = False
        self.separatemodules = app.config.apidocrun_separate_modules
        self.includeprivate = app.config.apidocrun_include_private
        self.tocfile = app.config.apidocrun_tocfile
        self.create_headings = app.config.apidocrun_create_headings
        self.modulefirst = app.config.apidocrun_module_first
        self.implicit_namespaces = app.config.apidocrun_implicit_namespaces
        self.suffix = app.config.apidocrun_suffix
        self.templatedir = app.config.apidocrun_templatedir
        self.header = app.config.apidocrun_header
        if self.header is None:
            self.header = app.config.project
                
        for key, value in config.items():
            if key in args_translate:
                key = args_translate[key]
            
            setattr(self, key, value)
        
        if not os.path.isabs(self.destdir):
            self.destdir = os.path.abspath(os.path.join(app.srcdir, self.destdir))
        
        self.noheadings = not self.create_headings
        
        if self.suffix.startswith("."):
            self.suffix = self.suffix[1:]
        
        if self.header is None:
            self.header = os.path.basename(self.module_path)
        # Args initialized

def run_apidoc(app):
    """
    Run ``recurse_tree()`` from :mod:`sphinx:sphinx.ext.apidoc`.

    :param app:             The application object
    :type app:              :class:`~sphinx:sphinx.application.Sphinx`
    
    
    """
    
    # Iterate through all module paths
    for path, config in app.config.apidocrun_module_paths.items():
        logger.info("[APIdoc-Run] Scanning {0}".format(path))
        args = apidoc_args(app, path, config)
        
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(app.srcdir, path))
        app.emit('apidocrun-started', path, args)
        
        root_dir = path
        excludes = [
            excl if os.path.isabs(excl) 
            else os.path.abspath(os.path.join(app.srcdir, excl))
            for excl in args.exclude_patterns
        ]
        
        if not os.path.isdir(root_dir):
            raise ExtensionError("{0} is not a directory".format(root_dir))
        
        if not args.dryrun:
            ensuredir(args.destdir)
        
        modules = recurse_tree(root_dir, excludes, args, args.templatedir)
        
        if args.tocfile:
            create_modules_toc_file(modules, args, args.tocfile, args.templatedir)
        
        app.emit('apidocrun-finished', path, args)

def setup(app):
    """
    Hook into the ``builder-inited`` event and
    add the configuration options to the application.
    
    :param app:             The application object
    :type app:              :class:`~sphinx:sphinx.application.Sphinx`
    """
    
    # Connect our functions to Sphinx events
    app.connect("builder-inited", run_apidoc)
    
    # Register events
    app.add_event("apidocrun-started")
    app.add_event("apidocrun-finished")
    
    # Register configuration variables
    app.add_config_value("apidocrun_module_paths", None, "env", [dict])
    app.add_config_value("apidocrun_exclude_patterns", [], "env")
    app.add_config_value("apidocrun_destdir", "apidoc", "env")
    app.add_config_value("apidocrun_maxdepth", 4, "env")
    app.add_config_value("apidocrun_follow_links", False, "env")
    app.add_config_value("apidocrun_separate_modules", False, "env")
    app.add_config_value("apidocrun_include_private", False, "env")
    app.add_config_value("apidocrun_tocfile", "modules", "env", [str, type(None)])
    app.add_config_value("apidocrun_create_headings", True, "env")
    app.add_config_value("apidocrun_module_first", False, "env")
    app.add_config_value("apidocrun_implicit_namespaces", False, "env")
    app.add_config_value("apidocrun_suffix", "rst", "env")
    app.add_config_value("apidocrun_templatedir", None, "env")
    app.add_config_value("apidocrun_header", None, "env")
    
    return {
        'version':              __version__,
        'parallel_read_safe':   True,
        'parallel_write_safe':  True,
    }

