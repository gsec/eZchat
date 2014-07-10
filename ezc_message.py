#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function
from datetime import datetime

class Message(object):
  """
  Creates a message object with a unique ID based on sender, recipient and
  exact creation time. Encrypts or decrypts content if provided with keys.
  @todo: message size limited by the key though!!!
         further implementation of AES needed for msg_size to be arbitrary
  """

  def __init__(self, sender, recipient, content, datatype = 'text',
      dtime = datetime.now()):
    # todo: (bcn 2014-07-06) Isoformat is at least localization independent but
    # timezone information is still missing !

    self.time       = dtime.isoformat(' ')
    self.sender     = sender
    self.recipient  = recipient
    self.content    = content
    self.datatype   = datatype
    self.msg_id     = SHA(self.sender + self.recipient + \
                              str(self.time)).hexdigest()
    self.pub_key, self.priv_key = self.read_keys()
    self.cipher     = self.var_cipher = ''
    self.plain      = self.var_plain = ''

  def __str__(self):
    return "\nFrom: " + self.sender + "\tTo: " + self.recipient + "\n@ "  \
            + self.time + "\n---\n" + self.content + "\n---\n" +          \
            "Message ID: " + self.msg_id + " (" + self.datatype + ")" +   \
            "\n+++++++++++++\n"
