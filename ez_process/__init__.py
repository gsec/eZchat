#==============================================================================#
#                                 __init__.py                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

import ez_process_base
from ez_background_process import ez_background_process
from ez_server_client import ez_server_client
from ez_contact import ez_contact
from ez_relay import ez_relay
from ez_db_sync import ez_db_sync
from ez_ping import ez_ping
from ez_api import ez_api
from ez_connect import ez_connect

#===========#
#  Globals  #
#===========#

p2pCommand = ez_process_base.p2pCommand
p2pReply = ez_process_base.p2pReply
command_args = ez_process_base.command_args

class ez_process(ez_background_process,
                 ez_server_client,
                 ez_contact,
                 ez_relay,
                 ez_db_sync,
                 ez_ping,
                 ez_api,
                 ez_connect):
  def __init__(self, **kwargs):
    super(ez_process, self).__init__(**kwargs)


#========#
#  Info  #
#========#
__author__ = "Jean-Nicolas Lang"
__date__ = "14.2.2014"
__version__ = "0.2"
