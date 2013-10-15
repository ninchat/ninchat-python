# -*- coding: utf-8 -*-

import sys, os

sys.path.insert(0, "..")

extensions = ["sphinx.ext.autodoc"]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "ninchat-python"
copyright = "2012-2014, Somia Reality Oy"
version = "1.0"
release = "1.0-pre"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
html_theme = "default"
html_static_path = ["_static"]
