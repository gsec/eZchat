#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function, division, generators
# forward compabilty, should be in all files
from Crypto.Hash import SHA
from datetime import datetime

class Message(object):

    def __init__(self, sender, recipient, content, datatype='text'):
        _time           = datetime.now()
        self.time       = _time.ctime()
        self.sender     = sender
        self.recipient  = recipient
        self.content    = content
        self.datatype   = datatype
        
        _hash      = SHA.new()
        _hash.update(self.sender + self.recipient + str(_time))
        self.id_        = _hash.hexdigest()

    def __str__(self):
        return "From: " + self.sender + "\tTo: " + self.recipient + "\n@ " +  \
                self.time + "\n---\n" + self.content + "\n---\n" +            \
                "Message ID: " + self.id_ + " (" + self.datatype + ")"

#::: main :::

msg = """If your public attribute name collides with a reserved keyword, append
a single trailing underscore to your attribute name. This is preferable to an
abbreviation or corrupted spelling. (However, notwithstanding this rule, 'cls'
is the preferred spelling for any variable or argument which is known to be a
class, especially the first argument to a class method.)"""

mx = Message('derEine','derAndere', msg)
my = Message('derEine','derAndere', msg)

print(mx)
