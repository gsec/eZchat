from test_tools import *
from time import sleep

from ez_p2p import client, p2pCommand

class Test_p2p(object):
  def setUp(self):
    host, port = ("", 1234)
    self.server = client()
    self.server.start()

    pr = p2pCommand('servermode', (host, port))
    self.server.servermode(pr)

    host = "127.0.0.1"

    alice_id = "alice"
    self.alice = client(alice_id)
    self.alice.start()
    bob_id = "bob"
    self.bob = client(bob_id)
    self.bob.start()
    pr = p2pCommand('connect_server', (host, port))
    #pr = p2pCommand(1, (host, port))
    self.alice.connect_server(pr)
    self.alice.add_client("server", (host, port))

    pr = p2pCommand('connect_server', (host, port))
    self.bob.connect_server(pr)

    pr = p2pCommand('ips_request', data = "server")
    self.alice.ips_request(pr)

  def test_ping(self):
    sleep(0.5)
    pr = p2pCommand('ping_request', data = "bob")
    self.alice.ping_request(pr)

    sleep(0.5)
    pr = p2pCommand('shutdown')
    self.server.shutdown(pr)
    self.alice.shutdown(pr)
    self.bob.shutdown(pr)

    # Please fix your shit
    #eq_(ping, True)


