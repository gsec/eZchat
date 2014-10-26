"""
This module encapsulates personal user preferences and should be used where
appropriate
"""
from os         import path, makedirs
from sys        import exit

#==============================================================================#
#                                 DomainError                                  #
#==============================================================================#

class DomainError(Exception):
  """
  DomainError exception is raised if the user specified a wrong domain, i.e. a
  line height that is not in the given ranges.
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

#==============================================================================#
#                                  FUNCTIONS                                   #
#==============================================================================#

def join(var, file_name):
  """
    VAR           = ('SUBDIR', "DESCRIPTION")
  Makes sure that SUBDIR exists and create it if necessary. Return the SUBDIR
  joined with the file_name
  """
  subdir, desc  = var
  location      = path.join(local_path, subdir)
  if not path.isdir(location):
    print("Creating " + location + " for " + desc)
    makedirs(location)
  return path.join(location, file_name)

#============================================#
#  CLI prefs. - Appearance and key bindings  #
#============================================#

cli_edit_range          = range(1, 30)
cli_msg_range           = range(1, 30)
cli_status_range        = range(0, 20)
cli_option_frac_range   = range(10, 50)

# TODO: JNicL the actual settings should be read from a rc file Sa 04 Okt 2014 12:29:28 CEST
# Hardcoded for now

def init_cli_preferences():

  #==============#
  #  Appearance  #
  #==============#

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

  #================#
  #  Key bindings  #
  #================#

  global cli_command_dict
  cli_command_dict = {}
  #abbreviation
  ccd = cli_command_dict
  # do not worry that I wrapped the keys as tuples, I need it to iterate over
  # keys mapped on the same command. The user will not have to specify the keys
  # in this way, and the keys will be read from an rc file.
  ccd['cli_enter_cmdline']   = (':',)
  ccd['cli_delete_one']      = ('x',)
  ccd['cli_delete']          = ('d',)
  ccd['cli_insert']          = ('i',)
  ccd['cli_append']          = ('a',)
  ccd['cli_delete']          = ('d',)
  ccd['cli_newline_low']     = ('o',)
  ccd['cli_newline_high']    = ('O',)
  ccd['cli_move_left']       = ('h', 'left')
  ccd['cli_move_right']      = ('l', 'right')
  ccd['cli_move_down']       = ('j', 'up')
  ccd['cli_move_up']         = ('k', 'down')
  ccd['cli_scroll_msg_up']   = ('K',)
  ccd['cli_scroll_msg_down'] = ('J',)

  #=======================#
  #  process preferences  #
  #=======================#

  global process_preferences
  process_preferences = {}
  # time period(seconds) with which all users are are requested to sync msges
  process_preferences['db_bgsync_timeout']  = 60
  # time period with which all users are passively pinged
  process_preferences['ping_bg_timeout']    = 10
  # pingreply waittime
  process_preferences['ping_reply_timeout'] = 4
  process_preferences['silent_ping']        = False


  #===================#
  #  acception rules  #
  #===================#

  global acception_rules
  acception_rules = {}
  acception_rules['global_rule']   = 'Allow'
  #acception_rules['distributeIPs'] = 'Auth'

  process_preferences['acception_rules'] = acception_rules


#==============#
#  User prefs  #
#==============#
# ------- Directorys --------
"""
Here we define the local path, and the subdirectories for user specific files.
The existence is ensured by join()
format:
  VAR           = ('SUBDIR', "DESCRIPTION")
"""
# TODO: (bcn 2014-10-18) This should become ~/.local/share/ezchat/
local_path = 'local'

location = {}
location['key'] = ('keys', "private key files")
location['hist'] = ('history', "history files")
location['db'] = ('database', "database files for users and messages")
location['log'] = ('log', "log files")

# ------- Files --------
command_history = join(location['hist'], 'command_history.txt')
default_db = join(location['db'], 'ez.db')

# ------- Colors --------
palette = [
      ('online', 'light green', 'dark green'),
      ('offline', 'dark red', 'light red'),
      ]
