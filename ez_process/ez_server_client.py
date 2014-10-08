#==============================================================================#
#                             ez_server_client.py                              #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base, p2pReply, p2pCommand
import cPickle   as pickle

#==============================================================================#
#                            class ez_server_client                            #
#==============================================================================#

class ez_server_client(ez_process_base):

  def __init__(self, *args, **kwargs):
    super(ez_server_client, self).__init__(*args, **kwargs)

#==================#
#  connect_server  #
#==================#

  def connect_server(self, cmd):
    """
    Connects to an endpoint without the use of NAT traversal techniques. The
    endpoint should be a server(-like) system listening on some port.

    - (host_ip, host_port) = cmd.data
    """
    try:
      assert('host' in cmd.data)
      host = cmd.data['host']
    except:
      print "no host specified in connect_server"
      return
    try:
      assert('port' in cmd.data)
      port = int(cmd.data['port'])
    except:
      print "no port specified in servermode"
      return

    master       = (host, port)
    cmd_dct      = {'user_id': self.name}
    conn_success = {'connection_success': cmd_dct}
    msg          = pickle.dumps(conn_success)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

    def connection_failed_func(self_timer, host, port, user_id):
      cmd = self.error("connection to server failed, retrying")
      self.replyQueue.put(cmd)
      conn_success = {'connection_success': {'user_id': user_id}}
      msg          = pickle.dumps(conn_success)
      try:
        self.sockfd.sendto(msg, master)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

      process_id = 'connect_server'
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(process_id)

    process_id = 'connect_server'
    bgp = p2pCommand('start_background_process',
              {'process_id'      : process_id,
               'callback'        : connection_failed_func,
               'interval'        : 5,
               'callback_args'   : (host, port, self.name)})
    self.commandQueue.put(bgp)

  def servermode(self, cmd):
    """
    Start listening on port. Mandatory arguments:

    - cmd.data['host'] = host
    - cmd.data['port'] = port
    """
    try:
      assert('host' in cmd.data)
      host = cmd.data['host']
    except:
      print "no host specified in servermode"
      return

    try:
      assert('port' in cmd.data)
      port = cmd.data['port']
    except:
      print "no port specified in servermode"
      return

    self.sockfd.bind((str(host), int(port)))
    self.replyQueue.put(self.success("listening socket"))
    self.server = True

  def shutdown(self, cmd):
    if self.sockfd != None:
      self.sockfd.close()
    self.alive.clear()

  def send(self, cmd):
    """
    Send data to a user. Mandatory arguments:

    - cmd.data['user_id'] = user_id
    - cmd.data['data']    = data
    """
    try:
      assert('user_id' in cmd.data)
      user_id = cmd.data['user_id']
    except:
      print "user not registered"

    try:
      assert('data' in cmd.data)
      data = cmd.data['data']
    except:
      print "No data which could be sent"

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      try:
        self.sockfd.sendto(data, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "not connected to user"))
