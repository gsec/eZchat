#==============================================================================#
#                                  ez_server                                   #
#==============================================================================#

#============#
#  Includes  #
#============#
import sys, time
import socket, select, struct
import Queue, threading

#==============================================================================#
#                             class ServerCommand                              #
#==============================================================================#

class ServerCommand(object):
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
  connect, close, send, accept = range(4)

  def __init__(self, msgType = None, data = None):
    self.msgType  = msgType
    self.data     = data

#==============================================================================#
#                              class ServerReply                               #
#==============================================================================#

class ServerReply(object):
  """
  Encapsulate received data.
  A ServerReply instance can be appended to the reply queue.

  replyType = success:  type(data) = str
  replyType = error:    type(data) = str
  """
  success, error = range(2)

  def __init__(self, replyType = None, data = None):
    self.replyType = replyType
    self.data      = data

#==============================================================================#
#                                 class server                                 #
#==============================================================================#

class server(threading.Thread):
  """
  Server takes care of
  1. Openening sockets via socket.socket
  2. Binding to an address (and port) via socket.bind
  3. Listening for incoming connections via socket.listen
  4. Accepting connections via socket.accept
  5. and receiving/distributing data via socket.sendall/socket.recv
  """

  def __init__( self, id = "myserver", port = 2468, max_connections = 10):
    super(server, self).__init__()
    self.id = id
    self.port = port # Arbitrary non-privileged port
    self.host = ''   # Symbolic name meaning all available interfaces
    #self.host = ""
    self.max_connections = max_connections
    self.clients = []

    self.commandQueue = Queue.Queue()
    self.replyQueue   = Queue.Queue()

    self.alive = threading.Event()
    self.alive.set()

    # Storing client functionalities
    self.handlers = {
        ServerCommand.connect:    self.connect,
        ServerCommand.close:      self.close,
        ServerCommand.send:       self.send,
        ServerCommand.accept:     self.accept
        }

  def connect(self, cmd):
    host = cmd.data[0]
    port = cmd.data[1]
    try:
      # create an AF_INET, STREAM socket (TCP)
      # AF_INET IP4
      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    except socket.error, msg:
      #print('Failed to create socket. Error code: ' + str(msg[0]) +            \
            #' , Error message : ' + msg[1])
      error_msg = 'Failed to create socket. Error code: ' + str(msg[0]) +      \
                  ' , Error message : ' + msg[1]
      self.replyQueue.put(self.error(error_msg))
      print (error_msg)
      sys.exit();

    self.replyQueue.put(self.success("Socket created"))

    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
      self.server_socket.bind((host, port))
      #self.server_socket.bind((self.host, self.port))
    except socket.error , msg:
      #print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
      error_msg = 'Bind failed. Error Code : ' + str(msg[0]) +                 \
                  ' Message ' + msg[1]
      print (error_msg)
      self.replyQueue.put(self.error(error_msg))

    self.server_socket.listen(self.max_connections)
    self.replyQueue.put(self.success("Socket bind complete"))
    #print("Socket bind complete")

    self.clients.append(self.server_socket)

  def close(self, cmd):
    self.server_socket.close()
    self.replyQueue.put(self.success("Socket closed"))

  def shutdown(self):
    self.commandQueue.put(ServerCommand(ServerCommand.close))
    self.alive.clear()

  def success(self, success_msg = None):
    return ServerReply(ServerReply.success, success_msg)

  def error(self, error_msg = None):
    return ServerReply(ServerReply.error, error_msg)

  def accept(self, cmd):
    new_user, addr = self.server_socket.accept()
    self.clients.append(new_user)
    self.replyQueue.put(self.success("Client (%s, %s) connected" % addr))

    #data = "Client (%s, %s) connected" % addr
    #header = struct.pack('<L', len(data))
    #self.broadcast_data(new_user, "[%s:%s] entered room\n" % addr)

  # Function to broadcast chat messages to all connected clients
  #def broadcast(self, user, message):
  def broadcast(self, message):
    # Do not send the message to master socket and the client who has send us
    # the message
    for socket in self.clients:
      #if socket != self.server_socket and socket != user :
      if socket != self.server_socket:
        try :
          header = struct.pack('<L', len(message))
          socket.sendall(header + message)
          self.replyQueue.put(self.success("Distributed data to other users"))
        except :
          socket.close()
          self.clients.remove(socket)
          self.replyQueue.put(self.success("Client disconnected."))

  def send(self, cmd):
    message = cmd.data
    self.broadcast(message)
    # Try to receive data. Catching the exception is advised since the client
    # might close abruptly throwing an exception
    #try:
      #data = self.receive(user)
      #if data:
        #if data == "close":
          #self.shutdown()
        #else:
          #print ("data:", data)

          #self.replyQueue.put(self.success(data))
          #pass
          ##self.broadcast( user, "\r" + '<' + str(user.getpeername()) +     \
                               ##'> ' + data)
      #else:
        ##self.broadcast(user, "Client (%s, %s) is offline" % addr)
        ##print("Client (%s, %s) is offline" % addr)
        #print("Client is offline")
        #user.close()
        #self.clients.remove(user)


    #except:
      ##self.broadcast(user, "Client (%s, %s) is offline" % addr)
      ##print("Client (%s, %s) is offline" % addr)
      #print("Client is offline")
      ##print ("user:", user.data)
      #user.close()
      #self.clients.remove(user)

  def receive(self, user):
    package_size = 4
    try:
      header_data = self.receive_bytes(package_size, user)
      if len(header_data) == package_size:
        msg_len = struct.unpack('<L', header_data)[0]
        data = self.receive_bytes(msg_len, user)
        if len(data) == msg_len:
          return data
      #TODO: nick returning data ends in endless loop Fr 11 Jul 2014 00:58:09 CEST
      #return "Socket closed prematurely"
    except IOError as e:
      pass
      #return "error:" + str(e)

  def receive_bytes(self, n_bytes, user):
    data = ''
    while len(data) < n_bytes:
      chunk = user.recv(n_bytes - len(data))
      if chunk == '':
        break
      data += chunk
    return data

  def run(self):
    """
    server main loop: Processes all queued commands. The timeout (0.1) is set in
    order to allow checking self.alive
    """
    while self.alive.isSet():
      try:
        cmd = self.commandQueue.get(True, 0.1)
        self.handlers[cmd.msgType](cmd)
      except Queue.Empty as e:
        continue

  #def run(self):
    #print("Socket now listening")
    #self.server_socket.listen(self.max_connections)
    #while self.alive.isSet():

    #self.server_socket.close()

# TODO: (bcn 2014-07-12) Nick promised to remove this and adopt the P2P strategy
#if __name__ == "__main__":
  #myserver = server()
  #myserver.start()
