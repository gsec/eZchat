from test_tools import *

import ezc_message as em
from datetime import datetime

def test_Message():
  msg = """ If your public attribute name collides with a reserved keyword,
      append a single trailing underscore to your attribute name. This is
      preferable to an abbreviation or corrupted spelling. (However,
      notwithstanding this rule, 'cls' is the preferred spelling for any
      variable or argument which is known to be a class, especially the first
      argument to a class method.)"""
  author = 'derEine'
  reader = 'derAndere'
  mx = em.Message(author, reader, msg, timestamp = datetime(2014, 07, 06, 17,
    41, 05))
  print("Testing the basic message object: \n" + str(mx))
  eq_ (mx.sender, author)
  eq_ (mx.recipient, reader)
  eq_ (mx.id_, 'd22a9cb0b7f87ffc1905944a754fdc5a326b5f53')
  eq_ (mx.time, '2014-07-06 17:41:05')
