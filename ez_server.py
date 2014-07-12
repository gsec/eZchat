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
#                                 class server                                 #
#==============================================================================#

class server(object):
  """
  Server takes care of
  1. Openening sockets via socket.socket
  2. Binding to an address (and port) via socket.bind
  3. Listening for incoming connections via socket.listen
  4. Accepting connections via socket.accept
  5. and receiving/distributing data via socket.sendall/socket.recv
  """

  def __init__( self, id = "myserver", port = 2468, max_connections = 10):
    self.id = id
    self.port = port # Arbitrary non-privileged port
    self.host = ''   # Symbolic name meaning all available interfaces
    #self.host = ""
    self.max_connections = max_connections
    self.clients = []
    self.alive = threading.Event()
    self.alive.set()

    try:
      #create an AF_INET, STREAM socket (TCP)
      # AF_INET IP4
      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    except socket.error, msg:
      print('Failed to create socket. Error code: ' + str(msg[0]) +            \
            ' , Error message : ' + msg[1])
      sys.exit();

    print("Socket Created")
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
      self.server_socket.bind((self.host, self.port))
    except socket.error , msg:
      print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
      sys.exit()
    print("Socket Bind Complete")

    self.clients.append(self.server_socket)

  # Function to broadcast chat messages to all connected clients
  def broadcast_data (self, user, message):
    # Do not send the message to master socket and the client who has send us
    # the message
    for socket in self.clients:
      if socket != self.server_socket and socket != user :
        print("Distributing data to other users")
        try :
          header = struct.pack('<L', len(message))
          socket.send(header + message)
          print("data distributed")
        except :
          socket.close()
          self.clients.remove(socket)

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

  def listen(self):
    print("Socket now listening")
    self.server_socket.listen(self.max_connections)
    while 1:
      # The select function monitors all the client sockets and the master
      # socket for readable activity. If any of the client socket is readable
      # then it means that one of the chat client has send a message.

      # Get the list sockets which are ready to be read through select
      readable, writeable, errors = select.select(self.clients, [], [])

      for user in readable:
        # Found new client
        if user == self.server_socket:
          # Handle the case in which there is a new connection recieved through
          # server_socket
          new_user, addr = self.server_socket.accept()
          self.clients.append(new_user)

          data = "Client (%s, %s) connected" % addr
          header = struct.pack('<L', len(data))
          self.broadcast_data(new_user, "[%s:%s] entered room\n" % addr)

        #Some incoming message from a client
        else:
          # Data recieved from client -> process it
          # Try to receive data. Catching the exception is advised since the
          # client might close abruptly throwing an exception
          try:
            data = self.receive(user)
            if data:
              self.broadcast_data( user, "\r" + '<' + str(user.getpeername()) +     \
                                   '> ' + data)
            else:
              self.broadcast_data(user, "Client (%s, %s) is offline" % addr)
              print("Client (%s, %s) is offline" % addr)
              user.close()
              self.clients.remove(user)


          except:
            self.broadcast_data(user, "Client (%s, %s) is offline" % addr)
            print("Client (%s, %s) is offline" % addr)
            user.close()
            self.clients.remove(user)
            continue

    self.server_socket.close()

# TODO: (bcn 2014-07-12) Nick promised to remove this and adopt the P2P strategy
if __name__ == "__main__":
  myserver = server()
  myserver.listen()
