#==============================================================================#
#                                  ez_ping.py                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

import socket
from ez_process_base import ez_process_base, p2pCommand
import cPickle as pickle

#------------------------------------------------------------------------------#
# schematic view of the ping process                                           #
#------------------------------------------------------------------------------#
#              /----------\       ping request        /----------\             #
#              | client A |-------------------------> | client B |             #
#              `----------'              \            `----------'             #
#   start timer     |        ping failed /                  |                  #
#                   |        x-----.----'                   /                  #
#                   |               `---------------------'                    #
#   ping success    | cancel timer  /                                          #
#      <------------+--------------'                                           #
#                   \                                                          #
#                    `-> Time over -> ping failed                              #
#------------------------------------------------------------------------------#

#==============================================================================#
#                                   ez_ping                                    #
#==============================================================================#

class ez_ping(ez_process_base):

  def __init__(self, *args, **kwargs):
    super(ez_ping, self).__init__(*args, **kwargs)

#================#
#  ping methods  #
#================#

  def ping_request(self, cmd, testing=False):
    """
    Starts a ping request. Client A must be connected to Client B, i.e. they
    must be both in clients user database, otherwise the ping process fails. To
    enforce the precondition the argument requires the user_id. The user_addr is
    retrieved from the user db.

    - user_id = cmd.data
    """
    try:
      assert('user_id' in cmd.data)
      user_id = cmd.data['user_id']
    except:
      print "no user_id in cmd.data"
      return

    process_id = ('ping_reply', user_id)
    if not process_id in self.background_processes:

      if 'success_callback' in cmd.data:
        self.success_callback[process_id] = cmd.data['success_callback']

      if 'error_callback' in cmd.data:
        error_callback = cmd.data['error_callback']
      else:
        def error_callback(self_timer):
          cmd = self.error("ping failed: " + user_id)
          self.replyQueue.put(cmd)
          del self.background_processes[process_id]

      if not user_id in self.ips:
        self.replyQueue.put(self.error("user not in client list"))
        if testing:
          return str(user_id) + " is not in client list"
      else:
        master  = self.ips[user_id]
        cmd_dct = {'user_id': user_id}
        ping    = {'ping_reply': cmd_dct}
        msg     = pickle.dumps(ping)
        try:
          self.sockfd.sendto(msg, master)
          bgp = p2pCommand('start_background_process',
                {'process_id'    : process_id,
                 'callback'      : error_callback,
                 'interval'      : 5})
          self.commandQueue.put(bgp)

        except IOError as e:
          self.replyQueue.put(self.error(str(e)))
          self.replyQueue.put(self.error("ping unsuccessful"))
    else:
      self.replyQueue.put(self.error("cannot ping again, " + \
                                     "still waiting for response"))

  def ping_reply(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    Client As ping request arrived and Client B responds with a ping_success

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    try:
      user_id = cmd.data['user_id']
      user_addr = (cmd.data['host'], cmd.data['port'])
    except:
      print "user_id/host/port not properly specified in ping_reply"

    self.replyQueue.put(self.success("ping request from: " + str(user_addr)))
    cmd_dct = {'user_id': user_id}
    ping    = {'ping_success': cmd_dct}
    msg     = pickle.dumps(ping)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def ping_success(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    The ping process succeded and Client A cancels the timer background process.

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    try:
      user_id = cmd.data['user_id']
      user_addr = (cmd.data['host'], cmd.data['port'])
    except:
      print "user_id/host/port not properly specified in ping_reply"

    #user_id, user_addr = cmd.data
    if user_id in self.ips:
      if (self.ips[user_id] == user_addr or
          socket.gethostbyname('ez') == user_addr[0]):
        process_id = ('ping_reply', user_id)
        pr = self.background_processes[process_id]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[process_id]
        if process_id in self.success_callback:
          self.success_callback[process_id]()
          del self.success_callback[process_id]
        else:
          self.replyQueue.put(self.success("ping success: " + user_id))
        return True

    #if socket.gethostbyname('ez') == user_addr[0]:
      #self.replyQueue.put(self.success("ping success: " + user_id))
      #return True
    #else:
    self.replyQueue.put(self.error("Received ping_success, source unknown: " +
        str(user_addr)))
    return False

  def ping_background(self, cmd):
    process_id = ('ping_reply', 'all')

    # define the function called by the timer after the countdown
    # ping_background_func calls itself resulting in an endless ping chain.
    def ping_background_func(self_timer, queue, user_ips):
      # ping all users
      user_ids = user_ips.keys()

      # custom success_callback
      def success_ping_all():
        print "background ping successful"

      for user_id in user_ids:
        cmd_dct = {'user_id': user_id, 'success_callback': success_ping_all}
        queue.put(p2pCommand('ping_request', cmd_dct))

      # check if the process still running, i.e. that it has not been killed
      # the process might have been killed while this function called.
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(process_id)

    bgp = p2pCommand('start_background_process',
            {'process_id'    : process_id,
             'callback'      : ping_background_func,
             'interval'      : 1,
             'callback_args' : (self.commandQueue, self.ips, )})
    self.commandQueue.put(bgp)
