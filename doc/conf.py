#
# TFS-Pandas documentation build configuration file, created by
# sphinx-quickstart on Tue Feb  6 12:10:18 2018.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.
import pathlib
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

TOPLEVEL_DIR = pathlib.Path(__file__).parent.parent.absolute()
ABOUT_FILE = TOPLEVEL_DIR / "tfs" / "__init__.py"

if str(TOPLEVEL_DIR) not in sys.path:
    sys.path.insert(0, str(TOPLEVEL_DIR))


def about_package(init_posixpath: pathlib.Path) -> dict:
    """
    Return package information defined with dunders in __init__.py as a dictionary, when
    provided with a PosixPath to the __init__.py file.
    """
    about_text: str = init_posixpath.read_text()
    return {
        entry.split(" = ")[0]: entry.split(" = ")[1].strip('"')
        for entry in about_text.strip().split("\n")
        if entry.startswith("__")
    }


ABOUT_TFS = about_package(ABOUT_FILE)

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # Include documentation from docstrings
    "sphinx.ext.autosectionlabel",  # Create explicit doc targets for each section
    "sphinx.ext.coverage",  # Collect doc coverage stats
    "sphinx.ext.doctest",  # Test snippets in the documentation
    "sphinx.ext.githubpages",  # Publish HTML docs in GitHub Pages
    "sphinx.ext.intersphinx",  # Link to other projects' documentation
    "sphinx.ext.mathjax",  # Render math via JavaScript
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
    "sphinx.ext.todo",  # Support for todo items
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx_copybutton",  # Add a "copy" button to code blocks
    "sphinx-prompt",  # prompt symbols will not be copy-pastable
    "sphinx_codeautolink",  # Automatically link example code to documentation source
]

# Config for autosectionlabel extension
autosectionlabel_prefix_document = True  # Make sure the target is unique
autosectionlabel_maxdepth = 2

# Config for the napoleon extension
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_preprocess_types = True
napoleon_attr_annotations = True

# Configuration for sphinx.ext.todo
todo_include_todos = True

# Add any paths that contain templates here, relative to this directory.
# templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = ABOUT_TFS["__title__"]
copyright_ = "2018, pyLHC/OMC-TEAM"
author = ABOUT_TFS["__author__"]

# Override link in 'Edit on Github'
rst_prolog = f"""
:github_url: {ABOUT_TFS['__url__']}
"""

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = ABOUT_TFS["__version__"][:3]
# The full version, including alpha/beta/rc tags.
release = ABOUT_TFS["__version__"]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "obj"

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "collapse_navigation": False,
    "display_version": True,
    "logo_only": True,
    "navigation_depth": 3,
}

html_logo = "_static/img/omc_logo.svg"
html_static_path = ["_static"]
html_context = {
    "display_github": True,
    # the following are only needed if :github_url: is not set
    "github_user": author,
    "github_repo": project,
    "github_version": "master/doc/",
}
html_css_files = ["css/custom.css"]

smartquotes_action = "qe"  # renders only quotes and ellipses (...) but not dashes (option: D)

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    "**": [
        "relations.html",  # needs 'show_related': True theme option to display
        "searchbox.html",
    ]
}

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "tfspandasdoc"

# -- Options for LaTeX output ---------------------------------------------

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
    (master_doc, "tfs-pandas.tex", "tfs-pandas Documentation", "pyLHC/OMC-TEAM", "manual"),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "tfs-pandas", "tfs-pandas Documentation", [author], 1)]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "tfs-pandas",
        "tfs-pandas Documentation",
        author,
        "pylhc/OMC-TEAM",
        "One line description of project.",
        "Miscellaneous",
    ),
]

# -- Instersphinx Configuration ----------------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
# use in refs e.g:
# :ref:`comparison manual <python:comparisons>`
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "cpymad": ("https://hibtc.github.io/cpymad/", None),
}
