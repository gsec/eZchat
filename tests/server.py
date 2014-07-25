import sys, errno
from ez_p2p import client, p2pCommand

if __name__ == "__main__":
  try:
    master = (sys.argv[1], int(sys.argv[2]))
  except (IndexError, ValueError):
    print ("usage: %s <host> <port>" % sys.argv[0])
    sys.exit(65)
  cl = client()
  cl.start()
  cl.commandQueue.put(p2pCommand(p2pCommand.servermode,
                                 master))
  #while True:
    #pass

