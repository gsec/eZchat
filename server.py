import socket
import select

from thread import *

# Server
# 1. Open a socket: socket.socket
# 2. Bind to a address(and port): socket.bind
# 3. Listen for incoming connections: socket.listen
# 4. Accept connections: socket.accept
# 5. Read/Send: socket.sendall/socket.recv

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 2468 # Arbitrary non-privileged port
clients = []
server = None

#Function to broadcast chat messages to all connected clients
def broadcast_data (user, message):
  #Do not send the message to master socket and the client who has send us the message
  for socket in clients:
    if socket != server and socket != user :
      try :
        print "da"
        socket.send(message)
      except :
        # broken socket connection may be, chat client pressed ctrl+c for example
        socket.close()
        clients.remove(socket)

#Function for handling connections. This will be used to create threads
def clientthread(conn):
  #Sending message to connected client

  #infinite loop so that function do not terminate and thread do not end.
  while True:

    #Receiving from client
    data = conn.recv(1024)
    reply = 'OK...' + data
    if not data:
        break
    conn.sendall(reply)
    print reply
    break
    #conn.close()
  #came out of loop
  conn.close()


try:
  #create an AF_INET, STREAM socket (TCP)
  # AF_INET IP4
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
except socket.error, msg:
  print 'Failed to create socket. Error code: ' + str(msg[0]) +                \
        ' , Error message : ' + msg[1]
  sys.exit();

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print "Socket Created"

try:
  server.bind((HOST, PORT))
except socket.error , msg:
  print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
  sys.exit()
print "Socket Bind Complete"

server.listen(10)
print "Socket now listening"



while True:
  # The select function monitors all the client sockets and the master socket for
  # readable activity. If any of the client socket is readable then it means that
  # one of the chat client has send a message.
  readable, writeable, errors = select.select([server], clients, [server])
  for user in readable:
    # server ready to establish new connection
    if user == server:
      connection, addr = server.accept()
      clients.append(connection)
      broadcast_data(connection, "[%s:%s] entered room\n" % addr)
      #connection.send("Welcome to the server. Type something and hit enter\n")
      print 'Connected with ' + addr[0] + ':' + str(addr[1])
    # Some incoming messages from clients
    else:
      try:
        data = server.recv(1024)
        if data:
          broadcast_data(user, "\r" + '<' + str(user.getpeername()) + '> ' + data)
      except:
        broadcast_data(user, "Client (%s, %s) is offline" % addr)
        print "Client (%s, %s) is offline" % addr
        user.close()
        clients.remove(user)
        continue

  # display client information
  #start_new_thread(clientthread, (connection,))

  #while True:
    #data = connection.recv(1024)
    #if not data:
      #break
    #connection.sendall(data)
    #print data
    #connection.close()
server.close()
