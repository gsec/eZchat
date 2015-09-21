#==============================================================================#
#                          ez_process_preferences.py                           #
#==============================================================================#


# TODO: nick try/except  Fr 17 Okt 2014 18:10:30 CEST

def init_process_preferences(**kwargs):
  global db_bgsync_timeout
  if 'db_bgsync_timeout' not in kwargs:
    db_bgsync_timeout = 60
  else:
    db_bgsync_timeout = kwargs['db_bgsync_timeout']

  global ping_bg_timeout
  if 'ping_bg_timeout' not in kwargs:
    ping_bg_timeout = 10
  else:
    ping_bg_timeout = kwargs['ping_bg_timeout']

  global ping_reply_timeout
  if 'ping_reply_timeout' not in kwargs:
    ping_reply_timeout = 4
  else:
    ping_reply_timeout = kwargs['ping_reply_timeout']

  global ping_retries
  if 'ping_retries' not in kwargs:
    ping_retries = 4
  else:
    ping_retries = kwargs['ping_retries']

  global silent_ping
  if 'silent_ping' not in kwargs:
    silent_ping = False
  else:
    silent_ping = kwargs['silent_ping']

