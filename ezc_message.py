#! /usr/bin/env python
# -*- coding: utf_8 -*-
# forward compatibly
from __future__ import print_function, division, generators

from Crypto.Hash import SHA
from datetime import datetime

class Message(object):

  def __init__(self, sender, recipient, content, datatype = 'text',
      timestamp = datetime.now()):
    # TODO: (bcn 2014-07-06) Isoformat is at least localization independent but
    # timezone information is still missing !
    self.time       = timestamp.isoformat(' ')
    self.sender     = sender
    self.recipient  = recipient
    self.content    = content
    self.datatype   = datatype

    _hash      = SHA.new()
    _hash.update(self.sender + self.recipient + self.time)
    self.id_        = _hash.hexdigest()

  def __str__(self):
    return "From: " + self.sender + "\tTo: " + self.recipient + "\n@ " + \
        self.time + "\n---\n" + self.content + "\n---\n" + \
        "Message ID: " + self.id_ + " (" + self.datatype + ")"

