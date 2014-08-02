from test_tools import *

import ez_preferences as ep

def test_check_key_location():
  ep.key_location = 'tests'
  # TODO: (bcn 2014-08-01) How to test raw_input ?
  #ep.check_key_location()
