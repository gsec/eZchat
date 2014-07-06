#==============================================================================#
#                                 class server                                 #
#==============================================================================#

import socket, select, sys

class server(object):

  """
  Server
  1. Open a socket: socket.socket
  2. Bind to a address(and port): socket.bind
  3. Listen for incoming connections: socket.listen
  4. Accept connections: socket.accept
  5. Read/Send: socket.sendall/socket.recv
  """

  def __init__( self, id = "myserver", port = 2468,
                max_connections = 10, buffersize = 1024):
    self.id = id
    self.port = port # Arbitrary non-privileged port
    #self.host = ''   # Symbolic name meaning all available interfaces
    self.host = "localhost"
    self.max_connections = max_connections
    self.buffersize = buffersize
    self.clients = []

    try:
      #create an AF_INET, STREAM socket (TCP)
      # AF_INET IP4
      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    except socket.error, msg:
      print 'Failed to create socket. Error code: ' + str(msg[0]) +            \
            ' , Error message : ' + msg[1]
      sys.exit();

    print "Socket Created"
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
      self.server_socket.bind((self.host, self.port))
    except socket.error , msg:
      print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
      sys.exit()
    print "Socket Bind Complete"

    self.clients.append(self.server_socket)

  # Function to broadcast chat messages to all connected clients
  def broadcast_data (self, user, message):
    # Do not send the message to master socket and the client who has send us the
    # message
    for socket in self.clients:
      if socket != self.server_socket and socket != user :
        try :
          socket.send(message)
        except :
          # broken socket connection may be,
          # chat client pressed ctrl+c for example
          socket.close()
          self.clients.remove(socket)

  def listen(self):
    """@todo: Docstring for listen.
    :returns: @todo

    """
    print "Socket now listening"
    self.server_socket.listen(10)
    while 1:
      # The select function monitors all the client sockets and the master
      # socket for readable activity. If any of the client socket is readable
      # then it means that one of the chat client has send a message.

      # Get the list sockets which are ready to be read through select
      readable, writeable, errors = select.select(self.clients, [], [])
      #readable = self.clients

      for user in readable:
        #New connection
        if user == self.server_socket:
          # Handle the case in which there is a new connection recieved through
          # server_socket
          new_user, addr = self.server_socket.accept()
          self.clients.append(new_user)

          print "Client (%s, %s) connected" % addr
          self.broadcast_data(new_user, "[%s:%s] entered room\n" % addr)

        #Some incoming message from a client
        else:
          # Data recieved from client, process it
          #A TCP program might close abruptly throwing the exception
          # "Connection reset by peer"
          try:
            data = user.recv(self.buffersize)
            if data:
              self.broadcast_data( user, "\r" + '<' + str(user.getpeername()) +     \
                              '> ' + data)
            else:
              self.broadcast_data(user, "Client (%s, %s) is offline" % addr)
              print "Client (%s, %s) is offline" % addr
              user.close()
              self.clients.remove(user)


          except:
            self.broadcast_data(user, "Client (%s, %s) is offline" % addr)
            print "Client (%s, %s) is offline" % addr
            user.close()
            self.clients.remove(user)
            continue

    self.server_socket.close()

myserver = server()
myserver.listen()
