"""
This module encapsulates personal user preferences and should be used where
appropriate
"""
from os import path, makedirs
from sys import exit

#==============================================================================#
#                                 DomainError                                  #
#==============================================================================#

class DomainError(Exception):
  """
  DomainError exception is raised if the user specified a wrong domain, e.g.
  ranges of args and metrics, wrong tensor multiplication/addition etc.
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

#=============#
#  Cli prefs  #
#=============#

cli_edit_range          = range(1, 30)
cli_msg_range           = range(1, 30)
cli_status_range        = range(0, 20)
cli_option_frac_range   = range(10, 50)

# TODO: JNicL the actual settings should be read from a rc file Sa 04 Okt 2014 12:29:28 CEST
# Hardcoded for now

def init_cli_preferences():
  global cli_edit_height
  cli_edit_height         = 5   # 10 rows + built in scrolling
  if not cli_edit_height in cli_edit_range:
    raise DomainError('cli_edit_height(' + str(cli_edit_height) +
                      ') out of range')


  global cli_msg_height
  cli_msg_height          = 20   # 25 rows + scrolling possible, however,
                                 # no focus yet
  if not cli_msg_height in cli_msg_range:
    raise DomainError('cli_msg_height(' + str(cli_msg_height) +
                      ') out of range ')


  global cli_status_height
  cli_status_height       = 4    # 4 rows = 4 status msges. Can be disabled by
                                 # setting to 0
  if not cli_status_height in cli_status_range:
    raise DomainError('cli_status_height(' + str(cli_status_height) +
                      ') out of range ')

  global cli_options_fraction
  cli_options_fraction    = 25   # 25 %
  if not cli_options_fraction in cli_option_frac_range:
    raise DomainError('cli_options_fraction(' + str(cli_options_fraction) +
                      ') out of range ')

  global cli_start_in_insertmode
  cli_start_in_insertmode = False

#==============#
#  User prefs  #
#==============#
# ------- Directorys --------
"""
Here we define the local path, and the subdirectories for user specific files.
The existence is ensure by check_location()
format:
  VAR           = ('SUBDIR', "DESCRIPTION")
"""
local_path      = 'local'

key_loc         = ('keys', "key")
hist_loc        = ('history', "history files")
log_loc         = ('logs', "chatlog files")

def return_location(var, test_func=False):
  """
  Makes sure that key_location exists and creates it if necessary and if the
  user has checked that it is the correct directory. This has to be called
  from the function requesting the path. [Could this have performance impacts?]
  """
  subdir, desc  = var
  location      = path.join(local_path, subdir)
  if path.isdir(location):
    return location
  else:
    print("Chosen " + desc + " location does not exist")
    if test_func:
      answer = test_func()
    else:
      answer = user_input(location)
    if answer == 'y':
      makedirs(location)
      return location
    else:
      #exit
      raise IOError("Please create " + desc +
            " location or specifiy other directory in ez_preferences.py")

def user_input(location):
  """
  outsourced for test module
  """
  return raw_input("Should " + path.abspath(location) + " be created? [y/n]")

# ------- Files --------
command_history = path.join(return_location(hist_loc), 'command_history.txt')
