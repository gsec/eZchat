from __future__ import print_function
from test_tools import *
from time import sleep

from ez_p2p import client, p2pCommand

class Test_p2p(object):
  def setUp(self):
    self.server = client(name = 'server')
    self.server.start()

    cmd_dct = {'host': "", 'port': 1235}
    pr = p2pCommand('servermode', cmd_dct)
    self.server.servermode(pr)

    # localhost
    host = "127.0.0.1"
    cmd_dct['host'] = host

    alice_id = "alice"
    self.alice = client(name = alice_id)
    self.alice.start()

    bob_id = "bob"
    self.bob = client(name = bob_id)
    self.bob.start()

    pr = p2pCommand('connect_server', cmd_dct)
    self.alice.connect_server(pr)
    cmd_dct['user_id'] = 'server'
    self.alice.add_client(**cmd_dct)

    pr = p2pCommand('connect_server', cmd_dct)
    self.bob.connect_server(pr)
    # Why doesn't bob add_client("server",..) ?
    # Bob does not need to add the server as he is not requesting to establish a
    # connection with alice (which is done via the server)

    pr = p2pCommand('ips_request', {'user_id': 'server'})
    self.alice.ips_request(pr)

  def test_ping(self):
    sleep(1.25)
    result = None
    pr = p2pCommand('ping_request', data = {'user_id': "bob"})
    result = self.alice.ping_request(pr, testing=True)
    pr = p2pCommand('shutdown')
    sleep(.50)
    self.server.shutdown(pr)
    self.alice.shutdown(pr)
    self.bob.shutdown(pr)
    eq_(result, None)
