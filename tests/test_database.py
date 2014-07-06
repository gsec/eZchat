from test_tools import *

import ezc_database as ed
import ezc_message as em
from datetime import datetime
from sys import stdout

def test_database():
  msg = """ Hallo"""
  author = 'derEine'
  reader = 'derAndere'
  mx = em.Message(author, reader, msg, 
       timestamp = datetime(2014, 07, 06, 17, 41, 05))

  database = ed.Database(localdb = 'sqlite:///:memory:')

  eq_(database.add_msg(mx, out = True), 'Added entry')
  eq_(database.add_msg(mx, out = True), 'Already in ezc_db')
  eq_(database.add_msg(mx, out = False), '')

  # TODO: (bcn 2014-07-06) Implement iteration over database
  #print(ed.database)

  # This is more as an export to another program but also shows what is inside
  # the database
  #ed.dataset.freeze(ed.msg_table.all(), format='json', filename='archive.json')
