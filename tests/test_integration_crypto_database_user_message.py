# encoding=utf-8
from test_tools import *

import ez_message as em
import ez_user as eu

class Test_MessageDatabase(object):
  def setUp(self):
    """ Set up test fixture """
  localhost = '127.0.0.1'
  alice_port = '1234'
  bob_port = '1235'

  def test_integration(self):
    # The pub key is build (slow!) when the constructor is called. We could also
    # fake the pub key but I would like to check its actually working
    if not eu.user_database.in_DB(name='Alice'):
      eu.user_database.add_entry(eu.User('Alice', localhost + ':' + alice_port))
    if not eu.user_database.in_DB(name='Bob'):
      eu.user_database.add_entry(eu.User('Bob', localhost + ':' + bob_port))
    # Now Alice and Bobs pub keys are in the db and their private keys on disk

