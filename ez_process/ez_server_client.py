#==============================================================================#
#                             ez_server_client.py                              #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base, p2pReply, p2pCommand
import cPickle as pickle
import ez_message as em
import random

#==============================================================================#
#                            class ez_server_client                            #
#==============================================================================#

class ez_server_client(ez_process_base):

  authentifcation_words = {}

  def __init__(self, *args, **kwargs):
    super(ez_server_client, self).__init__(*args, **kwargs)

#============================#
#  authentification process  #
#============================#

  def authentification_request(self, cmd):
    """
    Start an authenticiation process.

    :param cmd: The connection process requires the keywords ``'host'`` and
                ``'port'`` specifying the clients/servers endpoint.
    :type  cmd: p2pCommand instance. See
    :py:class:`ez_process.ez_process_base.p2pCommand` on how to queue commands.
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

    master  = (host, port)
    cmd_dct = {'user_id': self.name}
    auth_in = {'authentification_in': cmd_dct}
    msg     = pickle.dumps(auth_in)
    self.replyQueue.put(self.success('Started authentification.'))

    def authentification_failed_func(self_timer, host, port, user_id):
      cmd = self.error("Authentification with server failed, retrying.")
      self.replyQueue.put(cmd)
      conn_success = {'authentification_in': {'user_id': user_id}}
      msg          = pickle.dumps(conn_success)
      try:
        self.sockfd.sendto(msg, master)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

      process_id = ('authentification', (host, port))
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(process_id)

    process_id = ('authentification', (host, port))
    bgp = p2pCommand('start_background_process',
              {'process_id'      : process_id,
               'callback'        : authentification_failed_func,
               'interval'        : 5,
               'callback_args'   : (host, port, self.name)})
    self.commandQueue.put(bgp)

    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))


  def authentification_in(self, cmd):
    """
    A client requests a proposes an authentification.

    All arguments are specified as keyword arguments in cmd.data.

    :param user_id: id specifying the username
    :type  user_id: string

    :param host: hosts IP
    :type  host: string

    :param port: hosts port
    :type  port: integer
    """
    try:
      user_id    = cmd.data['user_id']
      host, port = cmd.data['host'], cmd.data['port']
    except:
      print "user_id/host/port not properly specified in authentification_in."
      return

    self.replyQueue.put(self.success('started authentification_in'))
    msg = str(random.random())
    self.authentifcation_words[user_id] = msg

    master   = (host, port)
    cmd_dct  = {'msg': msg, 'user_id':self.name}
    auth_out = {'authentification_out': cmd_dct}
    msg      = pickle.dumps(auth_out)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def authentification_out(self, cmd):
    """
    A client response for authentification.

    All arguments are specified as keyword arguments in cmd.data.

    :param msg: The message which has to be encrypted and send back to the
    server
    :type  msg: string

    :param host: hosts IP
    :type  host: string

    :param port: hosts port
    :type  port: integer
    """
    try:
      msg        = cmd.data['msg']
      user_id    = cmd.data['user_id']
      host, port = cmd.data['host'], cmd.data['port']
    except:
      print "user_id/host/port not properly specified in authentification_out."
      return

    process_id = ('authentification', (host, port))
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    mx = em.Message(self.name, user_id, str(msg))

    master   = (host, port)
    cmd_dct  = {'reply_msg': mx, 'user_id':self.name}
    auth_vfy = {'authentification_verify': cmd_dct}
    msg      = pickle.dumps(auth_vfy)

    def authentification_verify_failed_func(self_timer, host, port):
      cmd = self.error("Authentification verification response. " +
                       "Connection has probably been rejected.")
      self.replyQueue.put(cmd)

      process_id = ('authentification_verify', (host, port))
      if process_id in self.background_processes:
        pr = self.background_processes[process_id]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[process_id]

    process_id = ('authentification_verify', (host, port))
    bgp = p2pCommand('start_background_process',
              {'process_id'      : process_id,
               'callback'        : authentification_verify_failed_func,
               'interval'        : 5,
               'callback_args'   : (host,port,)})
    self.commandQueue.put(bgp)

    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def authentification_verify(self, cmd):
    try:
      reply_msg  = cmd.data['reply_msg']
      user_id    = cmd.data['user_id']
      host, port = cmd.data['host'], cmd.data['port']
    except:
      print "user_id/host/port not properly specified in authentification_verify."
      return

    self.replyQueue.put(self.success('started authentification_verify'))
    try:
      # check that the decripted message matches the original message.
      reply_msg = reply_msg.clear_text().split('\n')[1]
      self.replyQueue.put(self.success(self.authentifcation_words[user_id] in
        reply_msg))
      if self.authentifcation_words[user_id] in reply_msg:
        cmd_dct = {'user_id': user_id, 'host': host, 'port': port}
        self.add_client(**cmd_dct)

        auth_success = {'authentification_success': {}}
        msg          = pickle.dumps(auth_success)

        master = (host, port)
        #self.sockfd.sendto(msg, master)

    except:
      self.replyQueue.put(self.success('Declined user: ' + user_id))

  def authentification_success(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    Client B receives the news that Client A succeded and Client B adds Client A
    to the user db.
    """
    try:
      host    = cmd.data['host']
      port    = cmd.data['port']
    except:
      print "user_id, host, port not properly specified in connection_success"

    process_id = ('authentification_verify', (host, port))
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    self.replyQueue.put(self.success("Authentification with server established"))


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

  def shutdown(self, *args):
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
