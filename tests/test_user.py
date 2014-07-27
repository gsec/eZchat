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
