import sys, errno
from ez_client import client
from ez_process import p2pCommand

if __name__ == "__main__":
  try:
    cmd_dct = {'host': sys.argv[1], 'port': int(sys.argv[2])}
  except (IndexError, ValueError):
    print ("usage: %s <host> <port>" % sys.argv[0])
    sys.exit(65)

  acception_rules = {}
  acception_rules['global_rule']             = 'Deny'
  acception_rules['distributeIPs']           = 'Auth'
  acception_rules['authentification_in']     = 'Allow'
  acception_rules['authentification_verify'] = 'Allow'
  acception_rules['ping_reply']              = 'Allow'

  prefs = {'acception_rules':acception_rules}
  cl = client(name = "server", **prefs)

  cl.enableCLI = True
  cl.commandQueue.put(p2pCommand('servermode', cmd_dct))
  cl.start()
