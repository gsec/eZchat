from test_tools import *

import ezc_message as em

def test_Message():
  msg = """ If your public attribute name collides with a reserved keyword,
      append a single trailing underscore to your attribute name. This is
      preferable to an abbreviation or corrupted spelling. (However,
      notwithstanding this rule, 'cls' is the preferred spelling for any
      variable or argument which is known to be a class, especially the first
      argument to a class method.)"""
  author = 'derEine'
  reader = 'derAndere'
  mx = em.Message(author, reader, msg)
  print(mx)
  eq_ (mx.sender, author)
  eq_ (mx.recipient, reader)
  # TODO: (bcn 2014-07-06) We can't check the hash as the time keeps changing.
  # Maybe allow for optional argument in constructor to specify time?
