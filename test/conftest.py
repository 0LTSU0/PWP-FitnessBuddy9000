"""
"Hack" to make pytest find code when running tests in VSCode
"""

import sys
from os.path import dirname as d
from os.path import abspath
root_dir = d(d(abspath(__file__)))
sys.path.append(root_dir)
