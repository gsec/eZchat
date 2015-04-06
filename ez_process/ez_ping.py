#==============================================================================#
#                                  ez_ping.py                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

import socket
from ez_process_base import ez_process_base, p2pCommand
import cPickle as pickle
import ez_process_preferences as epp

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

  def ping_request(self, master, **kwargs):
    """
    Starts a ping request. Client A must be connected to Client B, i.e. they
    must be both in clients user database, otherwise the ping process fails. To
    enforce the precondition the argument requires the user_id. The user_addr is
    retrieved from the user db.
    """
    if master not in self.ips:
      raise Exception('Master ' + str(master) + ' not in registered ips')
    process_id = ('ping_reply', str(master))
    if process_id not in self.background_processes:

      if 'success_callback' in kwargs:
        self.success_callback[process_id] = kwargs['success_callback']

      if 'error_callback' in kwargs:
        error_callback = kwargs['error_callback']
      else:
        def error_callback(self_timer):
          if not epp.silent_ping:
            cmd = self.error("ping failed: " + str(master))
            self.replyQueue.put(cmd)
          try:
            #master = self.get_master(user_id=user_id)
            if master in self.ips:
              user_id, _ = self.ips[master]
              del self.ips[master]
              if not epp.silent_ping:
                self.success('Removed user : ' + user_id + ' from ips')
          except:
            self.error('Failed to remove user : ' + user_id + ' from ips.')
          del self.background_processes[process_id]

      try:
        #master = self.get_master(user_id=user_id)
        user_id, _ = self.ips[master]
        cmd_dct = {'user_id': user_id}
        ping = {'ping_reply': cmd_dct}
        msg = pickle.dumps(ping)
        try:
          self.sockfd.sendto(msg, master)
          bgp = p2pCommand('start_background_process',
                           {'process_id': process_id,
                            'callback': error_callback,
                            'interval': epp.ping_reply_timeout})
          self.commandQueue.put(bgp)

        except IOError as e:
          self.error('ping unsuccessful: ' + str(e))
      except Exception as e:
        self.error('ping unsuccessful: ' + str(e))
    else:
      self.error('cannot ping again, still waiting for response')

  def ping_reply(self, user_id, host, port):
    """
    Not to be called by the user, but automatically invoked.

    Client As ping request arrived and Client B responds with a ping_success

    :param user_id: User nickname
    :type  user_id: string


    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    user_addr = (host, port)
    if not epp.silent_ping:
      self.success("ping request from: " + str(user_addr))

    cmd_dct = {'user_id': user_id}
    ping = {'ping_success': cmd_dct}
    msg = pickle.dumps(ping)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.error(str(e))

  def ping_success(self, user_id, host, port):
    """
    Not to be called by the user, but automatically invoked.

    The ping process succeded and Client A cancels the timer background process.

    :param user_id: User nickname
    :type  user_id: string

    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    user_addr = (host, port)
    if user_addr in self.ips:
      if(self.ips[user_addr][0] == user_id or
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
          if not epp.silent_ping:
            self.success("ping success: " + user_id)
        return True

    self.error("Received ping_success, source unknown: " + str(user_addr))
    return False

  def ping_background(self):
    process_id = ('ping_reply', 'all')

    # define the function called by the timer after the countdown
    # ping_background_func calls itself resulting in an endless ping chain.
    def ping_background_func(self_timer, queue, user_ips):
      # ping all users
      user_ids = [u[0] for u in user_ips.values()]

      # custom success_callback - just for demonstration purpose
      def success_ping_all():
        pass
        #print "background ping successful"

      for user_id in user_ids:
        cmd_dct = {'user_id': user_id, 'success_callback': success_ping_all}
        queue.put(p2pCommand('ping_request', cmd_dct))

      # check if the process still running, i.e. that it has not been killed
      # the process might have been killed while this function called.
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(process_id)

    bgp = p2pCommand('start_background_process',
                     {'process_id': process_id,
                      'callback': ping_background_func,
                      'interval': epp.ping_bg_timeout,
                      'callback_args': (self.commandQueue, self.ips, )})
    self.commandQueue.put(bgp)
