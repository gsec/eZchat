import socket, sys, select

# 1. Create a socket
# 2. Connect to remote server
# 3. Send some data
# 4. Receive a reply

try:
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.eror, msg:
  print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
  sys.exit()

print "Socket Created"

#Get host and port info to connect
host = "192.168.1.6"
port = 2468
try:
  client.connect((host, port))
except:
  print "Host unavailable"
  sys.exit()

while True:
  #Send some data to the remote server

  clients = [sys.stdin, client]
  readable, writeable, errors = select.select(clients, [], [])
  for user in readable:
    if user == client:
      reply = client.recv(1024)
      if reply:
        print reply
      else:
        print "Disconnected"
        sys.exit()
    else:
      message = raw_input(">>>  ")

      #set the whole string
      client.sendall(message)
      reply = client.recv(1024)
      print reply
