# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(1, os.path.abspath('_ext'))


# -- Project information -----------------------------------------------------

try:
    from tomllib import load
except ModuleNotFoundError:
    from tomli import load

with open('../pyproject.toml', 'rb') as f:
    meta = load(f)['project']

project = meta['name']
description = meta['description']
authors = [a['name'] or a['email'] for a in meta['authors']]
author = ', '.join(authors)

from digikamdb._version import version as release
version = '.'.join(release.split('.')[:3])

copyright   = '2022 ' + author

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.ifconfig',
    'sphinx.ext.extlinks',
    'apidoc_run',
    'apidoc_clean',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

# Insert version in .rst files
rst_epilog = """
.. |Version| replace:: %s
.. |Release| replace:: %s
""" % (version, release)

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'classic'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
#html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}
html_sidebars = {
    '**':    ['globaltoc.html', 'relations.html',
             'sourcelink.html', 'searchbox.html'],
}

# More options:
html_short_title = 'Home'
globaltoc_maxdepth = 4

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'DigikamDBDoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, project, description,
     author, 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, project, description,
     authors, 3)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, project, description,
     author, project, description,
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options autodoc ---------------------------------------------------------

#autodoc_member_order = 'groupwise'
autodoc_default_options = {
    'exclude-members':      'metadata, prepare, registry, ' +
                            '_reflect_table, _sa_decl_prepare, ' +
                            '_sa_deferred_table_resolver, _sa_raise_deferred_config, ' + 
                            '_sa_class_manager, _sa_registry',
    'inherited-members':    True,
    'member-order':         'groupwise',
    'private-members':      False,
    'show-inheritance':     True,
#    'special-members':      '__init__',
    'undoc-members':        False,
}
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
#autodoc_class_signature = 'separated'

# -- Options for APIDoc extension --------------------------------------------

apidocrun_destdir = '_api'
apidocrun_maxdepth = 3
apidocrun_implicit_namespaces = False
apidocrun_separate_modules = True
apidocrun_tocfile = None
apidocrun_module_first = True

apidocrun_module_paths = {
    '../digikamdb': {},
}

# Override default APIDOC options since they are set in autodoc_default_options:
os.environ['SPHINX_APIDOC_OPTIONS'] = 'members'

# -- Options for ExtLinks extension ------------------------------------------

extlinks = {
    'docurl':   (meta['urls']['documentation'] + '/%s', '[doc:%s]'),
    'source':   (meta['urls']['homepage'] + '/%s', 'Digikam-DB on Girhub: %s'),
}

# -- Local overrides ---------------------------------------------------------

if (os.path.isfile('/etc/.0acb81c396') or
    os.path.isfile(os.path.join(os.path.expanduser('~'), '.0acb81c396'))
):
    # We're at home, so set some private settings
    include_private_content = True

    # HTML Theme
    html_theme = 'rcw'
    logo_name = None
    html_theme_options = {}
    
    # Document private entities
    autodoc_default_options.update({
        'undoc-members':    True,
        'private-members':  True,
    })
    
    # Private ToDo extension
    extensions.append('sphinxcontrib.rcw_private.todo')
    todo_include_todos = True
    todo_link_only = True
    
    # InterSphinx
    extensions.append('sphinx.ext.intersphinx')
    intersphinx_mapping = {
        'python':   ('https://docs.python.org/3', None),
        'sqla': ('https://docs.sqlalchemy.org/en/14', None),
    }
else:
    extensions.append('sphinx.ext.todo')
    todo_include_todos = False

def setup(app):
    app.add_config_value('include_private_content', False, 'env')

