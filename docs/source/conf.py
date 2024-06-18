# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

import setuptools_scm

# Add the module path to sys.path here.
# If the directory is relative to the documentation root,
# use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../.."))

project = "datashuttle"
copyright = "2022, Neuroinformatics Unit"
author = "Neuroinformatics Unit"

# Retrieve the version number from the package
try:
    release = setuptools_scm.get_version(root="../..", relative_to=__file__)
    release = release.split(".dev")[0]  # remove dev tag and git hash
except LookupError:
    # if git is not initialised, still allow local build
    # with a dummy version
    release = "0.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
    "numpydoc",
    "nbsphinx",
    "sphinx_autodoc_typehints",
    "sphinx_design",
]

# Configure the myst parser to enable cool markdown features
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
    "attrs_block",  # https://stackoverflow.com/questions/78183173/custom-styling-a-header-in-sphinx-website?noredirect=1#comment137843002_78183173
    "attrs_inline"
]
# Automatically add anchors to markdown headings
myst_heading_anchors = 3

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Automatically generate stub pages for API
autosummary_generate = True
numpydoc_class_members_toctree = False  # stops stubs warning
#toc_object_entries_show_parents = "all"
html_show_sourcelink = False

# Ignore links that do not work with github actions link checking
# https://github.com/neuroinformatics-unit/actions/pull/24#issue-1978966182
linkcheck_anchors_ignore_for_url = [
    "https://neuroinformatics.zulipchat.com/"
]

autodoc_default_options = {
    'members': True,
    "member-order": "bysource",
    'special-members': False,
    'private-members': False,
    'inherited-members': False,
    'undoc-members': True,
    'exclude-members': "",
}

# List of patterns, relative to source directory, that match files and
# folders to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "**.ipynb_checkpoints",
    # to ensure that include files (partial pages) aren't built, exclude them
    # https://github.com/sphinx-doc/sphinx/issues/1965#issuecomment-124732907
    "**/includes/**",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "pydata_sphinx_theme"
html_title = "datashuttle"


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = [
    'css/custom.css',
]

html_favicon = "_static/logo_light.png"

html_sidebars = {
    "pages/how_tos/*": [],
    "pages/tutorials/*": [],
    "pages/tutorials": [],
    "pages/how_tos": [],
}

# Customize the theme
html_theme_options = {
    "icon_links": [
        {
            # Label for this link
            "name": "GitHub",
            # URL where the link will redirect
            "url": "https://github.com/neuroinformatics-unit/datashuttle",  # required
            # Icon class (if "type": "fontawesome"),
            # or path to local image (if "type": "local")
            "icon": "fa-brands fa-github",
            # The type of image to be used (see below for details)
            "type": "fontawesome",
        },
        {
            "name": "Zulip (chat)",
            "url": "https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle",
            # required
            "icon": "fa-solid fa-comments",
            "type": "fontawesome",
        },
    ],
    "logo": {
        "text": f"datashuttle v{release}",
        "image_light": "_static/logo_light.png",
        "image_dark": "_static/logo_dark.png",
    },
    "footer_start": ["footer_start"],
    "footer_end": ["footer_end"],
    "show_prev_next": False,
    "show_toc_level": 2,  # sidebar levels that are expanded before scrolling
#    "secondary_sidebar_items": [],
 #   "page_sidebar_items": [],
}


# Redirect the webpage to another URL
# Sphinx will create the appropriate CNAME file in the build directory
# The default is the URL of the GitHub pages
# https://www.sphinx-doc.org/en/master/usage/extensions/githubpages.html
github_user = "JoeZiminski"
html_baseurl = "https://datashuttle.neuroinformatics.dev/"
