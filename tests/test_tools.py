# Adding the modules from the main path
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

# Most important tools are assertion tests via `eq_`
from nose.tools import *
# Mock objects to allow for unit tests in complex environments
import mock
