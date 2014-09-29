"""
This module encapsulates personal user preferences and should be used where
appropriate
"""
from os import path, makedirs
from sys import exit

key_location = 'tests'
command_history = '.cmd_history'

def check_key_location():
  """
  Makes sure that key_location exists and creates it if necessary and if the user
  has checked that it is the correct directory.
  This has to be called either at start up or made interactive with CLI and GUI.
  """
  if not path.isdir(key_location):
    print("Chosen key location doesn't exist")
    answer = raw_input("Should I create " + path.abspath(key_location) + \
                       " for you? [y/n] ")
    if answer == 'y':
      makedirs(key_location)
    else:
      exit("Please fix key location.")
