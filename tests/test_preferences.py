from test_tools import *

import ez_preferences as ep
from shutil import rmtree

#def test_check_key_location():
  #ep.key_location = 'tests'
  # TODO: (bcn 2014-08-01) How to test raw_input ?
  #ep.check_key_location()

# def test_return_location():
#   ep.local = 'tests/local'
#   if not ep.path.isdir(ep.local):
#     ep.makedirs(ep.local)
#   for var in [ep.key_loc, ep.hist_loc, ep.log_loc]:
#     print("Checking for " + var[1] + " directory.")
#     #ep.makedirs(var[0])       # remove this line for testing of raw input
#     print(ep.return_location(var, test_func=(lambda:"y")))
#     if ep.path.isdir(var[0]):
#       print( var[0] + " location exists now.")
#   # dont delete non-test directories
#   assert '/tests/' in ep.path.abspath(ep.local)
#   rmtree(ep.local)
