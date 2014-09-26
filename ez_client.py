import sys, errno
from ez_p2p import client, p2pCommand

try:
  name = sys.argv[1]
except (IndexError, ValueError):
  print ("usage: %s <id>" % sys.argv[0])
  sys.exit(65)
cl = client(name = sys.argv[1])
cl.start()
