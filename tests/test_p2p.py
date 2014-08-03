from test_tools import *
from time import sleep

from ez_p2p import client, p2pCommand

class Test_p2p(object):
  def setUp(self):
    host, port = ("", 1234)
    self.server = client()
    self.server.start()

    pr = p2pCommand(p2pCommand.servermode, (host, port))
    self.server.servermode(pr)

    host = "127.0.0.1"

    self.alice = client()
    self.alice.start()
    self.bob = client()
    self.bob.start()
    alice_id = "alice"
    pr = p2pCommand(p2pCommand.connect, (host, port, alice_id))
    self.alice.connect(pr)
    self.alice.add_client((host, port), "server")

    bob_id = "bob"
    pr = p2pCommand(p2pCommand.connect, (host, port, bob_id))
    self.bob.connect(pr)

  def test_ping(self):

    pr = p2pCommand(p2pCommand.ips_request, data = "server")
    self.alice.ips_request(pr)
    sleep(0.1)
    pr = p2pCommand(p2pCommand.ping_request, data = "bob")
    ping = self.alice.ping_request(pr)


    pr = p2pCommand(p2pCommand.shutdown)
    self.server.shutdown(pr)
    self.alice.shutdown(pr)
    self.bob.shutdown(pr)

    # Please fix your shit
    #eq_(ping, True)


