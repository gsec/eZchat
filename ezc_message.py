#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function
from datetime import datetime
from base64 import b64encode, b64decode, encode, decode
from StringIO import StringIO
from rsa.bigfile import *
import rsa

KEY_SIZE = 1024
SHA = rsa.pkcs1.HASH_METHODS['SHA-1']
# gui: key is generated outside, but keysize has to be global -> should be
# stored in and read from database.

class Message(object):
  """
  Creates a message object with a unique ID based on sender, recipient and
  exact creation time. Encrypts or decrypts content if provided with keys.
  @todo: message size limited by the key though!!!
         further implementation of AES needed for msg_size to be arbitrary
  """

  def __init__(self, sender, recipient, content, datatype = 'text',
      dtime = datetime.now()):
    # TODO: (bcn 2014-07-06) Isoformat is at least localization independent but
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

  def read_keys(self):
    """
    Reads keys from key-files.  Default is 'PEM' format. Returns 2-tuple, first
    element is the recipients public key, second element is the senders private
    key.
    """
    with open(self.recipient + '_key.pub', 'r') as publicfile:
      keydata = publicfile.read()
      pub_key = rsa.PublicKey.load_pkcs1(keydata)
    with open(self.sender + '_key.priv', 'r') as privatefile:
      keydata = privatefile.read()
      priv_key = rsa.PrivateKey.load_pkcs1(keydata)
    return (pub_key, priv_key)

  def encrypt(self):
    """
    Encrypts content part of the message. Stores the output in cipher
    attribute.
    """
    self.cipher = rsa.encrypt(self.content, self.pub_key).encode('base64')

  def decrypt(self):
    """
    Decrypts the cipher of the message. Stores plaintext in plain attribute.
    """
    self.plain = rsa.decrypt(self.cipher.decode('base64'), self.priv_key)

  def var_encrypt(self):
    """
    Encrypts message of arbitrary length. Requires file-object, stores output
    in var_cipher attribute.
    @TODO: BROKEN, file object behaves different than a file
    """
    plainfile  = StringIO(self.content)
    cipherfile = StringIO(self.var_cipher)
    encrypt_bigfile(plainfile, cipherfile, self.pub_key)
    plainfile.close; cipherfile.close

  def var_decrypt(self):
    """
    Decrypts message of arbitrary lengt. Requires file-object, stores output in
    var_plain attribute.
    @TODO: BROKEN, file object behaves different than a file
    """
    cipherfile = StringIO(self.var_cipher)
    plainfile  = StringIO(self.var_plain)
    decrypt_bigfile(cipherfile, plainfile, self.priv_key)
    cipherfile.close; plainfile.close
