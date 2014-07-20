from test_tools import *

import ez_database as ed
import ez_message as em
from datetime import datetime
from sys import stdout

class Test_Database(object):
  # This will be called before every test function and create our sandbox
  def setUp(self):
    """ Set up test fixture """
    msg = """ Hallo"""
    author = 'derEine'
    reader = 'derAndere'
    self.mx = em.Message(author, reader, msg,
                         dtime = datetime(2014, 07, 06, 17, 41, 05))
    self.my = em.Message(author, reader, msg,
                         dtime = datetime(2014, 06, 06, 17, 41, 05))

    self.database = ed.Database(localdb = 'sqlite:///:memory:')
    self.database2 = ed.Database(localdb = 'sqlite:///:memory:')

  def test_database_add_msg(self):
    eq_(self.database.add_msg(self.mx, out = True), 'Added entry')
    eq_(self.database.add_msg(self.mx, out = True), 'Already in ez_db')
    eq_(self.database.add_msg(self.mx, out = False), None)

  def test_database_in_DB(self):
    self.database.add_msg(self.mx)
    eq_(self.database.in_DB(self.mx), True)
    eq_(self.database.in_DB(self.mx.msg_id), True)
    eq_(self.database.in_DB(None), False)

  def test_database_sync(self):
    self.database.add_msg(self.mx)
    self.database.add_msg(self.my)
    self.database2.add_msg(self.my)
    eq_(str(self.database.get_msg(self.mx.msg_id)), str(self.mx))

    list_to_be_send_to_2 = self.database.msg_id_list()
    missing_IDs_in_2 = self.database2.necessary_msgs(list_to_be_send_to_2)
    # Only x is missing in database2
    eq_(missing_IDs_in_2, [self.mx.msg_id])
    msgs_to_be_send = self.database.get_msgs (missing_IDs_in_2)
    self.database2.add_msgs (msgs_to_be_send)
    # Succesfully synced. Rerun the other way for complete sync.
    #eq_(self.database.msg_string(), self.database2.msg_string())
    eq_(str(self.database), str(self.database2))
