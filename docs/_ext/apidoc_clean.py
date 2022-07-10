"""
Remove older RunAPIdoc-generated files before run.

By default, :mod:`runapidoc` only writes files that do not
already exist. This extension removes destination files that
are older than their sources. It probably only works here, so
it isn't part of RunAPIdoc.
"""

__version__ = '0.1.5'

import os

from sphinx.util import logging

logger = logging.getLogger(__name__)

def do_clean(app, path, args):
    """
    Do APIdoc pre-clean

    :param app:         The application object
    :type app:          :class:`~sphinx:sphinx.application.Sphinx`
    :param str path:    Source directory passed to autodoc
    :param args:        Args that will be passed to
                        :func:`~sphinx:sphinx.ext.apidoc.recurse_tree`
    :type args:         :class:`~runapidoc.apidoc_args`
    """
    
    logger.info("[APIdoc-Clean] Scanning {0}".format(path))
    
    # Do nothing if force or dryrun are set
    if args.force:
        logger.debug("[APIdoc-Clean] Force set, skipping cleaning")
        return
    if args.dryrun:
        logger.debug("[APIdoc-Clean] Dry run set, skipping cleaning")
        return
    
    src = os.path.abspath(path)
    dst = os.path.abspath(args.destdir)
    
    logger.debug("[APIdoc-Clean] Comparing {0} to {1}".format(src, dst))
    
    srcdir = os.path.dirname(src)    
    for path, dirs, files in os.walk(src):
        module = os.path.relpath(path, srcdir).replace(os.sep, '.')
        
        for f in files:
            if not f.endswith('.py'):
                continue
            srcfile = os.path.join(path, f)
            dstfile = os.path.join(dst, module + '.' + f.replace('.py', '.rst'))
            if (os.path.isfile(dstfile) and 
                os.path.getmtime(dstfile) < os.path.getmtime(srcfile)
            ):
                logger.info("[APIdoc-Clean] Removing {0}".format(dstfile))
                os.remove(dstfile)

def setup(app):
    """
    Hook into the ``apidocrun-started`` event
    
    :param app:             The application object
    :type app:              :class:`~sphinx:sphinx.application.Sphinx`
    """
    
    # Connect our functions to Sphinx events
    app.connect('apidocrun-started', do_clean)

    return {
        'version':              __version__,
        'parallel_read_safe':   True,
        'parallel_write_safe':  True,
    }



