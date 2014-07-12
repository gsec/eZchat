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
       dtime = datetime(2014, 07, 06, 17, 41, 05))
  my = em.Message(author, reader, msg,
       dtime = datetime(2014, 06, 06, 17, 41, 05))

  #print(mx)

  database = ed.Database(localdb = 'sqlite:///:memory:')

  eq_(database.add_msg(mx, out = True), 'Added entry')
  eq_(database.add_msg(mx, out = True), 'Already in ezc_db')
  eq_(database.add_msg(mx, out = False), '')
  database.add_msg(my)

  print(database)

  # This is more as an export to another program but also shows what is inside
  # the database
  #ed.dataset.freeze(ed.msg_table.all(), format='json', filename='archive.json')
