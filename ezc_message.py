#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function, division, generators
import datetime as dtime

class Message(object):

    def __init__(self, sender, recipient, content):
        self.time       = dtime.datetime.now()
        self.sender     = sender
        self.recipient  = recipient
        self.content    = content
        self.id         = hash(self.sender+self.recipient+self.time.ctime())

#::: main test

m = Message('Gui','derAndere','TESTMESSAGE')
