#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function
from test_tools import *
import ezc_crypto as ec

def test_AES():
  text01 = """ If your public attribute name collides with a reserved keyword,
      append a single trailing underscore to your attribute name. This is
      preferable to an abbreviation or corrupted spelling. (However,
      notwithstanding this rule, 'cls' is the preferred spelling for any
      variable or argument which is known to be a class, especially the first
      argument to a class method.)"""
  text02 = "hi, was geht"
  author = 'derEine'
  reader = 'derAndere'

  plain_package = {'plain':text01, 'crypt_mode':0}
  msg_object = ec.eZ_AES(plain_package)
  geheim = msg_object.encrypt()
  print("Crypted Object:\n", geheim)
  crypt_object = ec.eZ_AES(geheim)
  ungeheim = crypt_object.decrypt()
  print("Plain:\n", ungeheim)

  text03 = "123456"
  msg = ec.eZ_AES(text01)
  #print(msg.add_padding(text03),"MMMMM")
  eq_(msg.add_padding(text03), "123456\1\0\0\0\0\0\0\0\0\0")
  text04 = "123456\1\0\0\0\0\0\0\0\0\0\1\1\1\0\0\0"
  eq_(msg.remove_padding(msg.add_padding(text04)), text04)
