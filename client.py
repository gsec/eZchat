#==============================================================================#
#                                 class client                                 #
#==============================================================================#

import sys, errno
import socket, struct, select
import Queue, threading

class ClientCommand(object):

  """
  A ClienCommand encapsulates commands which are then appended to the command
  queue ready for execution.
  The msgType "connect, close, send, receive" determines the data type, but yet
  there is no explicit type check.

  msgType = connect: type(data) = tuple
                           data = (host, port) = (str, int)
  msgType = close:   type(data) = NoneType
  msgType = send:    type(data) = str
  msgType = receive: type(data) = NoneType
  """
  connect, close, send, receive = range(4)

  def __init__(self, msgType = None, data = None, clientID = None, ):
    self.clientID = clientID
    self.msgType  = msgType
    self.data     = data

class ClientReply(object):

  """
  Encapsulate received data.
  A ServerReply instance can be appended to the reply queue.

  replyType = success:  type(data) = str
  replyType = error:    type(data) = str
  """
  success, error = range(2)

  def __init__(self, replyType = None, data = None, clientID = None):
    self.clientID  = clientID
    self.replyType = replyType
    self.data      = data

class client(threading.Thread):

  """
  Client class with queue system. Commands are executed by appending
  ClientCommand instances to the client commandQueue.
  The connect command allows to:
    1. Create a socket
    2. Connects to a remote server
  Send command:
    3. Data is send to all connected clients
  The receive commands:
    4. Receive a reply. The result is appended to the replyQueue.
  """

  def __init__(self, user = " "):

    super(client, self).__init__()
    self.clientID = user

    self.commandQueue = Queue.Queue()
    self.replyQueue   = Queue.Queue()

    # As long as the client is alive queue is checked for commands and replies
    self.alive = threading.Event()
    self.alive.set()

    # Storing client functionalities
    self.handlers = {
        ClientCommand.connect:  self.connect,
        ClientCommand.close:    self.close,
        ClientCommand.send:     self.send,
        ClientCommand.receive:  self.receive
        }

  def success(self, success_msg = None):
    return ClientReply(ClientReply.success, success_msg)

  def error(self, error_msg = None):
    return ClientReply(ClientReply.error, error_msg)

  def connect(self, cmd):
    try:
      self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.eror, msg:
      error_msg =  'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + \
                    msg[1]
      self.replyQueue.put(self.error(error_msg))
      sys.exit()

    self.replyQueue.put(self.success("Socket created"))
    try:
      host, port = cmd.data
      self.host  = host
      self.port  = port
      self.client_socket.connect((host, port))
    except:
      self.replyQueue.put(self.error("Host unavailable"))
      sys.exit()

    self.replyQueue.put(self.success("Connected to host"))

  def close(self, cmd):
    self.client_socket.close()
    self.replyQueue.put(ClientReply(ClientReply.success, "socket closed"))

  def shutdown(self):
    self.commandQueue.put(ClientCommand(ClientCommand.close))
    self.alive.clear()

  def send(self, cmd):
    """
    The struct module is used to handle binary data stored in files or from
    network connections. Sofar it is assumend that cmd.data is a string.
    The first four bytes are reserved to store the size of the data (header).
    """
    header = struct.pack('<L', len(cmd.data))
    try:
      self.client_socket.sendall(header + cmd.data)
      self.replyQueue.put(self.success("send data"))
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def receive(self, cmd):
    """
    First the header_data is retrieved which holds the size to be received.
    """
    package_size = 4
    try:
      header_data = self.receive_bytes(package_size)
      if len(header_data) == package_size:
        msg_len = struct.unpack('<L', header_data)[0]
        data = self.receive_bytes(msg_len)
        if len(data) == msg_len:
          self.replyQueue.put(self.success(data))
          return
      self.replyQueue.put(self.error("Socket closed prematurely"))
      self.shutdown()
    except IOError as e:
      print "error", e
      self.replyQueue.put(self.error(str(e)))

  def receive_bytes(self, n_bytes):
    data = ''
    while len(data) < n_bytes:
      chunk = self.client_socket.recv(n_bytes - len(data))
      if chunk == '':
        break
      data += chunk
    return data

  def run(self):
    """
    client main loop: Processes all queued commands. The timeout (0.1) is set in
    order to allow checking self.alive
    """
    while self.alive.isSet():
      try:
        cmd = self.commandQueue.get(True, 0.1)
        self.handlers[cmd.msgType](cmd)
      except Queue.Empty as e:
        continue

