# encoding=utf-8
from test_tools import *

import ez_database as ed
import ez_message as em
import ez_user as eu
from datetime import datetime

class Test_MessageDatabase(object):
  def setUp(self):
    """ Set up test fixture """
    msg = """ Hallo"""
    author = 'Alice'
    reader = 'Bob'
    self.mx = em.Message(author, reader, msg,
                         dtime = datetime(2014, 07, 06, 17, 41, 05))
    self.my = em.Message(author, reader, msg,
                         dtime = datetime(2014, 06, 06, 17, 41, 05))
    # These are distinct
    self.database = em.MessageDatabase(localdb = 'sqlite:///:memory:')
    self.database2 = em.MessageDatabase(localdb = 'sqlite:///:memory:')

  def test_database_add_entry(self):
    eq_(self.database.add_entry(self.mx, out = True), 'Added entry')
    eq_(self.database.add_entry(self.mx, out = True), 'Already in ez_db')
    eq_(self.database.add_entry(self.mx, out = False), None)

  def test_database_in_DB(self):
    self.database.add_entry(self.mx)
    eq_(self.database.in_DB(UID=self.mx.UID), True)
    eq_(self.database.in_DB(UID=self.mx.UID), True)
    eq_(self.database.in_DB(UID=None), False)

  def test_database_update_entry(self):
    self.database.add_entry(self.mx)
    self.mx.recipient = 'Charlie'
    self.database.update_entry(self.mx)
    eq_(str(self.database.get_entry(recipient='Charlie')), str(self.mx))

  def test_database_sync(self):
    self.database.add_entry(self.mx)
    self.database.add_entry(self.my)
    self.database2.add_entry(self.my)
    eq_(str(self.database.get_entry(UID=self.mx.UID)), str(self.mx))

    list_to_be_send_to_2 = self.database.UID_list()
    missing_IDs_in_2 = self.database2.necessary_entries(list_to_be_send_to_2)
    # Only x is missing in database2
    eq_(missing_IDs_in_2, [self.mx.UID])
    entries_to_be_send = self.database.get_entries (missing_IDs_in_2)
    self.database2.add_entries (entries_to_be_send)
    # Succesfully synced. Rerun the other way for complete sync.
    eq_(str(self.database), str(self.database2))
