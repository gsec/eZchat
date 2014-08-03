# encoding=utf-8
from test_tools import *

import ez_user as eu

def test_User():
  localhost = '127.0.0.1'
  alice_port = '1234'
  bob_port = '1235'
  alice = eu.User('Alice', localhost + ':' + alice_port, public_key='TestAlice')
  bob = eu.User('Bob', localhost + ':' + bob_port, public_key='TestBob')
  eq_(alice.current_ip_and_port()[0], bob.current_ip_and_port()[0])
  eq_(alice.current_ip_and_port(), (localhost, alice_port))

class Test_UserDatabase(object):
  def setUp(self):
    """ Set up test fixture """
    self.localhost = '127.0.0.1'
    self.alice_port = '1234'
    self.bob_port = '1235'
    self.alice = eu.User(name='Alice',
                         current_ip=self.localhost + ':' + self.alice_port,
                         public_key='pubAlice')
    self.bob = eu.User(name='Bob',
                       current_ip=self.localhost + ':' + self.bob_port,
                       public_key='pubBob')
    self.database = eu.UserDatabase(localdb='sqlite:///:memory:')
    self.database.add_entry(self.alice)
    self.database.add_entry(self.bob)

  def test_check_for_ip(self):
    eq_(self.database.check_for_ip(self.localhost, self.alice_port),
        self.database.UID_list()[0])
