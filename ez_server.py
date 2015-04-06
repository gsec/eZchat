import sys
from ez_client import client

if __name__ == "__main__":
  try:
    cmd_dct = {'host': sys.argv[1], 'port': int(sys.argv[2])}
  except (IndexError, ValueError):
    print ("usage: %s <host> <port>" % sys.argv[0])
    sys.exit(65)

  acception_rules = {}
  acception_rules['global_rule'] = 'Deny'
  acception_rules['distributeIPs'] = 'Auth'
  acception_rules['authentication_in'] = 'Allow'
  acception_rules['authentication_verify'] = 'Allow'
  acception_rules['ping_reply'] = 'Allow'
  acception_rules['ping_success'] = 'Allow'

  prefs = {'acception_rules': acception_rules}
  cl = client(name="ez", **prefs)

  cl.enableCLI = True
  cl.enqueue('servermode', cmd_dct)
  cl.start()
