#==============================================================================#
#                                ez_db_sync.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import (ez_process_base, p2pCommand, p2pReply,
                             command_args, user_arguments)
import cPickle as pickle
import ez_process_preferences as epp

#==============================================================================#
#                               class ez_db_sync                               #
#==============================================================================#

class ez_db_sync(ez_process_base):
  """
  A method for requesting a message database update.

  The call db_sync_request_out will request syncs with online users. The method
  db_sync_request_in is not intended to be called by the user, but is
  automaticallly invoked as a db sync request enters.
  """

  def __init__(self, *args, **kwargs):
    super(ez_db_sync, self).__init__(*args, **kwargs)

  @user_arguments
  def db_sync_request_out(self, master):
    """
    Start a message database sync request with the specified user.

    :param user_id: the user with whom to sync
    :type  user_id: string
    """
    cmd_dct = {'UID_list': self.MsgDatabase.UID_list()}
    db_sync_request = {'db_sync_request_in': cmd_dct}
    msg = pickle.dumps(db_sync_request)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
        self.error(str(e))

  def db_sync_request_in(self, host, port, UID_list):
    """ Answer to a db_sync_request_out. Do not call.  """
    master = (host, port)
    if master in self.ips:
      user_id = self.ips[master][0]
      self.success('Received msg db sync request from: ' + user_id)
    self.success('Received ' + str(UID_list))
    UIDs_to_sync = self.MsgDatabase.complement_entries(UID_list)
    self.success('Sending ' + str(UIDs_to_sync))
    if len(UIDs_to_sync) != 0:
      msges = self.MsgDatabase.get_entries(UIDs_to_sync)

      self.success('Sending ' + str(len(msges)) + ' messages  to : ' +
                   user_id)
      for msg in msges:
        data = pickle.dumps(msg)
        cmd_dct = {'user_specs': master, 'data': data}
        self.send(cmd_dct)

  def db_sync_background(self):
    process_id = ('db_sync_request_out', 'all')

    def db_sync_func(self_timer, queue, user_ips, user_ips_gen):
      # get the next user with whom to sync
      try:
        user_addr = user_ips_gen.next()
      except:
        user_ips_gen = (u for u in user_ips)
        user_addr = user_ips_gen.next()

      #for user_addr in user_ips:
      cmd_dct = {'master': user_addr}
      queue.put(p2pCommand('db_sync_request_out', cmd_dct))

      if process_id in self.background_processes:
        self.reset_background_process(process_id)

    bgp = {'process_id': process_id,
           'callback': db_sync_func,
           'interval': epp.db_bgsync_timeout,
           'callback_args': (self.commandQueue, self.ips, None, )}
    self.enqueue('start_background_process', bgp)
