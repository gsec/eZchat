# encoding=utf-8
from test_tools import *

import ez_message as em
import ez_user as new_user
from datetime import datetime

def test_Message():
  msg = """If your public attribute name collides with a reserved keyword,
  append a single trailing underscore to your attribute name. This is
  preferable to an abbreviation or corrupted spelling. (However,
  notwithstanding this rule, 'cls' is the preferred spelling for any variable
  or argument which is known to be a class, especially the first argument to a
  class method.)"""
  short_msg = "hi, was geht"
  author = 'derEine'
  reader = 'derAndere'
  mx = em.Message(author, reader, msg, datetime(2014, 07, 06, 17, 41, 05))

  print("Testing the basic message object: \n" + str(mx))
  eq_ (mx.recipient, reader)
  eq_ (mx.msg_id, 'd22a9cb0b7f87ffc1905944a754fdc5a326b5f53')
  eq_ (mx.time, '2014-7')

  # Making sure no security leaks can be abused
  assert_raises(AttributeError, getattr, mx, 'etime')
  assert_raises(AttributeError, getattr, mx, 'plaintext')
  assert_raises(AttributeError, getattr, mx, 'content')
  assert_raises(AttributeError, getattr, mx, 'sender')

  # I can only decrypt it with rsa_derAndere.priv
  print(mx.clear_text())
  # 'trying to hijack this': properly formatted, but wrong ciphered mac
  mx.ciphered_mac = """
  cql2uQqwu10lnSK+sNBdpOz4o2QYQOdLRfYf+ITX8Tk/lHbn0CqWnDNUcFkB2xgJD0QyGUsP/JQe
  pXYHRgma4y0MThZ4QA47c/IpIMi4RwuGdpGGPgovZgsrKYSg57pzZHI0KdsUSY+gl/nxzxVRTxaT
  h8xYlW5eLqS328jLc5jcxr6LvB3GsdfR45ukjNx8ZES2t9qdSa3WONRlfsmBFOrrrrfuSyinRqxO
  FUziCxVI3lVC8k517bWDqX3xh1fb3USqhS5c2mlCuk+95CIlS8gVIBgWpEK1knwlI4lGApIyXenA
  jlOoIMizUmFgoQRGZ1hUONpZzthQ/CpyumJu/w== """
  invalid = ':HMAC: [ ✗ ]'
  eq_ (mx.clear_text()[-len(invalid):], invalid)

#new_user.User(author)
#new_user.User(reader)

#mx = em.Message(author, reader, msg, dtime = datetime(2014, 07, 06, 17,
  #41, 05))
#print("Testing the basic message object: \n" + str(mx) + str(my))
# at the moment sender=recipient

#mx_secret = mx.encrypt()
#print("Encrypted + armored: \n-----\n", mx_secret)
#print("Decrypted again: \n-----\n", mx.decrypt(mx_secret))
