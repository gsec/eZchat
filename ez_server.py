import sys, errno
from ez_p2p import client, p2pCommand

if __name__ == "__main__":
  try:
    cmd_dct = {'host': sys.argv[1], 'port': int(sys.argv[2])}
  except (IndexError, ValueError):
    print ("usage: %s <host> <port>" % sys.argv[0])
    sys.exit(65)
  cl = client(name = "server")
  cl.enableCLI = True
  cl.commandQueue.put(p2pCommand('servermode', cmd_dct))
  cl.start()
  #while True:
    #pass

