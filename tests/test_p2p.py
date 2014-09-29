from __future__ import print_function
from test_tools import *
from time import sleep

from ez_p2p import client, p2pCommand

class Test_p2p(object):
  def setUp(self):
    host, port = ("", 1235)
    self.server = client(name = 'server')
    self.server.start()

    pr = p2pCommand('servermode', (host, port))
    self.server.servermode(pr)

    host = "127.0.0.1"

    alice_id = "alice"
    self.alice = client(name = alice_id)
    self.alice.start()

    bob_id = "bob"
    self.bob = client(name = bob_id)
    self.bob.start()

    pr = p2pCommand('connect_server', (host, port))
    self.alice.connect_server(pr)
    self.alice.add_client("server", (host, port))

    pr = p2pCommand('connect_server', (host, port))
    self.bob.connect_server(pr)
    # Why doesn't bob add_client("server",..) ?
    # Bob does not need to add the client as he is not requesting to establish a
    # connection with alice (which is done via the server)

    pr = p2pCommand('ips_request', data="server")
    self.alice.ips_request(pr)
    print("setUp of Test_p2p done")

  def test_ping(self):
    sleep(1.25)
    result = None
    pr = p2pCommand('ping_request', data="bob")
    result = self.alice.ping_request(pr, testing=True)
    eq_(result, None)
    pr = p2pCommand('shutdown')
    self.server.shutdown(pr)
    self.alice.shutdown(pr)
    self.bob.shutdown(pr)
