#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function
from Crypto.Hash import SHA
from datetime import datetime
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256 as SHA   # considered more secure than SHA1
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

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
    self.msg_id     = SHA.new(self.sender + self.recipient + \
                              str(self.time)).hexdigest()
    self.key_size   = 4096          # 2048 bits considered secure

    # pubkey of RECIPIENT, private key of SENDER
    self.private_key, self.public_key = self.generate_keys()

  def __str__(self):
    return "\nFrom: " + self.sender + "\tTo: " + self.recipient + "\n@ "  \
            + self.time + "\n---\n" + self.content + "\n---\n" +          \
            "Message ID: " + self.msg_id + " (" + self.datatype + ")" +   \
            "\n+++++++++++++\n"

  def generate_keys(self):
      """
      @todo: temporarily duplicate of function in ezc_create_user.py
      should at the end be imported from (secured) files
      """
      fresh_key   = RSA.generate(self.key_size)
      public_key  = fresh_key.publickey().exportKey(format='PEM')
      private_key = fresh_key.exportKey(format="PEM")
      return  private_key, public_key

  def encrypt(self):
      """
      @todo:
      """
      armored_key = RSA.importKey(self.public_key)
      public_key  = PKCS1_OAEP.new(armored_key)
      cipher      = public_key.encrypt(self.content)
      return cipher.encode('base64')

  def decrypt(self, ciphertext):
      armored_key = RSA.importKey(self.private_key)
      private_key = PKCS1_OAEP.new(armored_key)
      plaintext   = private_key.decrypt(ciphertext.decode('base64'))
      return plaintext
