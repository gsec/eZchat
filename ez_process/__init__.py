#==============================================================================#
#                                 __init__.py                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

import ez_process_base        as epb
import ez_background_process  as ebp
import ez_server_client       as esc
import ez_contact             as ec
import ez_relay               as er
import ez_db_sync             as eds
import ez_ping                as ep
import ez_connect             as et
import ez_api                 as ea

#===========#
#  Globals  #
#===========#

p2pCommand = epb.p2pCommand
p2pReply   = epb.p2pReply


class ez_process( ebp.ez_background_process,
                  esc.ez_server_client,
                  ec.ez_contact,
                  er.ez_relay,
                  eds.ez_db_sync,
                  ep.ez_ping,
                  ea.ez_api,
                  et.ez_connect):
  def __init__(self, **kwargs):
    super(ez_process, self).__init__(**kwargs)


#========#
#  Info  #
#========#

__author__  = "Jean-Nicolas lang"
__date__    = "8.10. 2014"
__version__ = "0.1"
