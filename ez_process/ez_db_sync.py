#==============================================================================#
#                                ez_db_sync.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base, p2pCommand
import cPickle   as pickle

#==============================================================================#
#                               class ez_db_sync                               #
#==============================================================================#

class ez_db_sync(ez_process_base):

  def __init__(self, *args, **kwargs):
    super(ez_db_sync, self).__init__(*args, **kwargs)

  def db_sync_request_out(self, cmd):
    user_id = cmd.data
    if user_id in self.ips:
      user_addr = self.ips[user_id]
      cmd_dct = {'user_id': self.name, 'UID_list': self.MsgDatabase.UID_list()}
      db_sync_request = {'db_sync_request_in': cmd_dct}
      msg             = pickle.dumps(db_sync_request)
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

  def db_sync_request_in(self, cmd):
    try:
      user_id  = cmd.data['user_id']
      UID_list = cmd.data['UID_list']
    except:
      print "user_id/UID_list not properly specified in db_sync_request_in"
      return

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      UIDs_to_sync = self.MsgDatabase.complement_entries(UID_list)
      if len(UIDs_to_sync) != 0:
        msges = self.MsgDatabase.get_entries(UIDs_to_sync)
        for msg in msges:
          cmd_dct = {'user_id': user_id, 'data': msg}
          self.commandQueue.put(p2pCommand('send', cmd_dct))

