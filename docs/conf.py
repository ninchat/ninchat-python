# -*- coding: utf-8 -*-

import os
import sys
from glob import glob

sys.path.insert(0, "..")
sys.path = glob("../build/lib.*/") + sys.path

extensions = ["sphinx.ext.autodoc"]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "ninchat-python"
copyright = "2012-2017, Somia Reality Oy"
version = "1.0"
release = "1.0rc0"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
html_theme = "default"
html_static_path = ["_static"]
