import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "Socket Created"

#Get host and port info to connect
host = "192.168.1.6"
port = 2468
s.connect((host, port))

while True:   
  #Send some data to the remote server
  message = raw_input(">>>  ")

  #set the whole string
  s.sendall(message)

  reply = s.recv(1024)
  print reply
