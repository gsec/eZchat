#==============================================================================#
#                             ez_server_client.py                              #
#==============================================================================#

#============#
#  Includes  #
#============#
from sys import getsizeof
from ez_process_base import ez_process_base, p2pReply, p2pCommand
import cPickle as pickle
import ez_message as em
import re
import random
from ez_gpg import ez_gpg

#==============================================================================#
#                            class ez_server_client                            #
#==============================================================================#

class ez_server_client(ez_process_base):

  authentication_words = {}
  authentications = {}

  def __init__(self, *args, **kwargs):
    super(ez_server_client, self).__init__(*args, **kwargs)

#============================#
#  authentication process  #
#============================#

  def authentication_request(self, host, port):
    """
    Start an authentication process.

    :param host: specifying the clients/servers IP
    :type  host: string

    :param host: specifying the clients/servers port
    :type  host: int

    See :py:class:`ez_process.ez_process_base.p2pCommand` on how to queue
    commands.
    """

    master = (host, port)
    cmd_dct = {'user_id': self.name}
    auth_in = {'authentication_in': cmd_dct}
    msg = pickle.dumps(auth_in)
    self.success('Started authentication.')

    def authentication_failed_func(self_timer, host, port, user_id):
      self.error("Authentication with server failed, retrying.")
      conn_success = {'authentication_in': {'user_id': user_id}}
      msg = pickle.dumps(conn_success)
      try:
        self.sockfd.sendto(msg, master)
      except IOError as e:
        self.error(str(e))

      process_id = ('authentication', (host, port))
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(process_id)

    process_id = ('authentication', (host, port))
    bgp = p2pCommand('start_background_process',
                     {'process_id': process_id,
                      'callback': authentication_failed_func,
                      'interval': 5,
                      'callback_args': (host, port, self.name)})
    self.commandQueue.put(bgp)

    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.error(str(e))

  def authentication_in(self, user_id, host, port):
    """
    A client requests a proposes an authentication.

    All arguments are specified as keyword arguments in cmd.data.

    :param user_id: id specifying the username
    :type  user_id: string

    :param host: hosts IP
    :type  host: string

    :param port: hosts port
    :type  port: integer
    """

    self.success('started authentication_in')

    # The message to-be signed is a random float between 0 and 1
    msg = str(random.random())
    self.authentication_words[user_id] = msg

    master = (host, port)
    cmd_dct = {'msg': msg, 'user_id': self.name}
    auth_out = {'authentication_out': cmd_dct}
    msg = pickle.dumps(auth_out)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.error(str(e))

  def authentication_out(self, msg, host, port):
    """
    A client response for authentication.

    All arguments are specified as keyword arguments in cmd.data.

    :param msg: The message which has to be encrypted and send back to the
    server
    :type  msg: string

    :param host: hosts IP
    :type  host: string

    :param port: hosts port
    :type  port: integer
    """

    process_id = ('authentication', (host, port))
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    isdigit = re.search('^(0\.\d+)$', msg)
    try:
      assert(len(isdigit.groups()) == 1)
    except:
      err_msg = ('Verification rejected.  The message to be signed is not a' +
                 ' positive float smaller 1.')
      self.error(err_msg)
      return

    try:
      sig = ez_gpg.sign_msg(str(msg))
    except:
      self.error('Failed to sign message.')
      return

    master = (host, port)
    cmd_dct = {'reply_msg': sig, 'user_id': self.name}
    auth_vfy = {'authentication_verify': cmd_dct}
    msg = pickle.dumps(auth_vfy)

    def authentication_verify_failed_func(self_timer, host, port):
      self.error("Authentication verification response. " +
                 "Connection has probably been rejected.")

      process_id = ('authentication_verify', (host, port))
      if process_id in self.background_processes:
        pr = self.background_processes[process_id]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[process_id]

    process_id = ('authentication_verify', (host, port))
    bgp = p2pCommand('start_background_process',
                     {'process_id': process_id,
                      'callback': authentication_verify_failed_func,
                      'interval': 5,
                      'callback_args': (host, port,)})
    self.commandQueue.put(bgp)

    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.error(str(e))

  def authentication_verify(self, reply_msg, user_id, host, port):
    """
    Validates the signature and the returned message.

    :param reply_msg: The message which has to be encrypted and send back to the
    server
    :type  msg: ? todo  gpg sign instance

    :param user_id: id specifying the username
    :type  user_id: string

    :param host: hosts IP
    :type  host: string

    :param port: hosts port
    :type  port: integer
    """

    self.success('started authentication_verify')
    try:
      # check that the decripted message matches the original message.
      if ez_gpg.verify_signed_msg(reply_msg):
        auth_msg = ez_gpg.separate_msg_signature(reply_msg)
        if auth_msg == self.authentication_words[user_id]:
          cmd_dct = {'user_id': user_id, 'host': host, 'port': port}
          self.add_client(**cmd_dct)
          self.client_authenticated(**cmd_dct)

          auth_success = {'authentication_success': {}}
          msg = pickle.dumps(auth_success)

          master = (host, port)
          self.sockfd.sendto(msg, master)

          self.success('User trusted and correct msg.')
        else:
          self.error('Declined user: ' + user_id + '. Wrong msg: ' + auth_msg)

    except:
      self.error('Declined user: ' + user_id + '. Not trusted.')

  def authentication_success(self, host, port):
    """
    Not to be called by the user, but automatically invoked.

    Client B receives the news that Client A succeded and Client B adds Client A
    to the user db.
    """

    process_id = ('authentication_verify', (host, port))
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    self.success("Authentication with server established")

  def client_authenticated(self, **kwargs):
    try:
      user_id = kwargs['user_id']
      master = (kwargs['host'], int(kwargs['port']))
      self.authentications[master] = user_id
    except:
      self.error('user_id, host, port not properly ' +
                 'specified in authentication_success')

#==================#
#  connect_server  #
#==================#

  def connect_server(self, host, port):
    """
    Connects to an endpoint without the use of NAT traversal techniques. The
    endpoint should be a server(-like) system listening on some port.
    """

    port = int(port)
    master = (host, port)
    cmd_dct = {'user_id': self.name}
    conn_success = {'connection_success': cmd_dct}
    msg = pickle.dumps(conn_success)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.error(str(e))

    def connection_failed_func(self_timer, host, port, user_id):
      self.error("connection to server failed, retrying")
      conn_success = {'connection_success': {'user_id': user_id}}
      msg = pickle.dumps(conn_success)
      try:
        self.sockfd.sendto(msg, master)
      except IOError as e:
        self.error(str(e))

      process_id = 'connect_server'
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(process_id)

    process_id = 'connect_server'
    bgp = p2pCommand('start_background_process',
                     {'process_id': process_id,
                      'callback': connection_failed_func,
                      'interval': 5,
                      'callback_args': (host, port, self.name)})
    self.commandQueue.put(bgp)

  def servermode(self, host, port):
    """
    Start listening on port.
    """
    self.sockfd.bind((str(host), int(port)))
    self.success("listening socket")
    self.server = True

  def shutdown(self, *args):
    if self.sockfd is not None:
      self.sockfd.close()
    self.alive.clear()

  def send(self, user_id, data):
    """
    Send data to a user.

    :param user_id: id specifying the username
    :type  user_id: string


    :param data: The message or pickled object to be sent.
    :type  data: string
    """

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      if getsizeof(data) > self.socket_buffsize:
        self.error('Data is too large, must be packed.')
        return

      try:
        self.sockfd.sendto(data, user_addr)
      except IOError as e:
        self.error(str(e))

    else:
      self.error("not connected to user")
