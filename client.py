#==============================================================================#
#                                 class client                                 #
#==============================================================================#

import socket, sys, select

class client(object):

  """
  1. Create a socket
  2. Connect to remote server
  3. Send some data
  4. Receive a reply
  """

  def __init__(self, user = " ", port = 2468, buffersize = 1024):
    """@todo: to be defined1. """
    self.user = user
    self.port = port
    self.host = "localhost"

    try:
      self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.eror, msg:
      print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
      sys.exit()

    print "Socket Created"
    try:
      self.client.connect((self.host, self.port))
    except:
      print "Host unavailable"
      sys.exit()

    print "Connected to host"
    self.prompt()

    while True:
      #Send some data to the remote server

      clients = [sys.stdin, self.client]
      readable, writeable, errors = select.select(clients, [], [])
      for user in readable:
        if user == self.client:
          print "receiving data"
          reply = self.client.recv(1024)
          if reply:
            print reply
            self.prompt()
          else:
            print "Disconnected"
            sys.exit()
        else:
          message = sys.stdin.readline()
          self.client.send(message)
          self.prompt()


  def prompt(self) :
    sys.stdout.write('>> ')
    sys.stdout.flush()

user = client()
