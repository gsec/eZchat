# encoding=utf-8
from __future__ import print_function
from test_tools import *

import ez_message as em
from datetime import datetime

def test_Message():
  msg = """If your public attribute name collides with a reserved keyword,
  append a single trailing underscore to your attribute name. This is
  preferable to an abbreviation or corrupted spelling. (However,
  notwithstanding this rule, 'cls' is the preferred spelling for any variable
  or argument which is known to be a class, especially the first argument to a
  class method.)"""
  author = 'Alice'
  reader = 'Bob'
  mx = em.Message(author, reader, msg, datetime(2014, 07, 06, 17, 41, 05))

  print("Testing the basic message object: \n" + str(mx))
  eq_ (mx.recipient, reader)
  # UIDs are deterministic
  eq_ (mx.UID, 'ae7451571369e490d3f79498c7fb0bb545e7a8c9')
  eq_ (mx.time, '2014-7')

  # Making sure no security leaks can be abused
  assert_raises(AttributeError, getattr, mx, 'etime')
  assert_raises(AttributeError, getattr, mx, 'plaintext')
  assert_raises(AttributeError, getattr, mx, 'content')
  assert_raises(AttributeError, getattr, mx, 'sender')

  # I can only decrypt it with ez_rsa_Bob.priv
  print(mx.clear_text())
  # bcn : This leads to an incorrect decryption! Please clarify! What is the
  # difference between mac and signature?
  # gsec : 'trying to hijack this': properly formatted, but wrong ciphered mac
  mx.ciphered_mac = """
  cql2uQqwu10lnSK+sNBdpOz4o2QYQOdLRfYf+ITX8Tk/lHbn0CqWnDNUcFkB2xgJD0QyGUsP/JQe
  pXYHRgma4y0MThZ4QA47c/IpIMi4RwuGdpGGPgovZgsrKYSg57pzZHI0KdsUSY+gl/nxzxVRTxaT
  h8xYlW5eLqS328jLc5jcxr6LvB3GsdfR45ukjNx8ZES2t9qdSa3WONRlfsmBFOrrrrfuSyinRqxO
  FUziCxVI3lVC8k517bWDqX3xh1fb3USqhS5c2mlCuk+95CIlS8gVIBgWpEK1knwlI4lGApIyXenA
  jlOoIMizUmFgoQRGZ1hUONpZzthQ/CpyumJu/w== """
  invalid = ':HMAC: [ ✗ ]'
  # TODO: Make this work again !!! I want coverage
  #eq_ (mx.clear_text()[-len(invalid):], invalid)

