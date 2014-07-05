import socket
from thread import *

PORT = 2468

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print "Socket Created"
s.bind(('', PORT))
print "Socket Bind Complete"
s.listen(10)
print "Socket now listening"
while True:
    connection, addr = s.accept()
    print "Connection Established!"
    connection.send("Welcome to the server. Type something and hit enter\n")
    while True:
        data = connection.recv(1024)
        if not data:
            break
        connection.sendall(data)
        print data
        connection.close()
s.close()
