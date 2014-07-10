#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function
from Crypto.Hash import SHA256 as SHA   # considered more secure than SHA1
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA
from Crypto import Random

RNG = Random.new()

class eZ_AES(object):
  """
  AES cipher object. Provides symmetric AES Encryption. Plaintext can be
  provided as string or dictionary object. Ciphertext must be dictionary
  object.
  """

  def __init__(self, package):
    """
    If package is string, assume it is plaintext. If dict, transfer values to
    attributes. Else raise ValueError.
    """
    if type(package) == str:
      plaintext         = package
      package           = {'plain':plaintext, 'encrypted':False}
      self.encrypted    = package['encrypted']
    elif type(package) == dict:
      self.encrypted    = package['encrypted']
    else:
      raise TypeError("AES package has wrong format.")

    assert type(self.encrypted) == bool, "Encryption Flag must be boolean"
    if self.encrypted:
      self.iv         = package['iv']
      self.key        = package['key']
      self.cipher     = package['cipher']
      self.KEY_LENGTH = package['KEY_LENGTH']
      self.INTERRUPT  = package['INTERRUPT']
      self.PAD        = package['PAD']
      self.MODE       = package['MODE']
    else:
      self.plain    = package['plain']
      # Don't touch this:
      self.KEY_LENGTH = 32
      self.INTERRUPT  = '\1'
      self.PAD        = '\0'
      self.MODE       = AES.MODE_CBC

  def encrypt(self):
    """
    Creates random IV (Injection Vector) and random symmetric key. Encrypts
    padded text. Returns dictionary with base64 encoded ciphertext. Key, IV and
    padding bits are bytes.
    @todo: Do we need base64? Probably not.
    """
    assert self.encrypted == False, "Data already encrypted"
    self.iv         = RNG.read(AES.block_size)          # never use same IV
    self.key        = RNG.read(self.KEY_LENGTH)         # with same key twice
    crypter         = AES.new(self.key, mode=self.MODE, IV=self.iv)
    padded_text     = self.add_padding(self.plain)
    self.cipher     = crypter.encrypt(padded_text).encode('base64')
    self.encrypted  = True
    del self.plain
    return self.__dict__

  def decrypt(self):
    """
    Produces plaintext from ciphertext with correct key and encryption
    parameters.
    """
    assert self.encrypted == True, "Data is not encrypted"
    decrypter = AES.new(self.key, mode=self.MODE, IV=self.iv)
    padded_text = decrypter.decrypt(self.cipher.decode('base64'))
    self.plain = self.remove_padding(padded_text)
    self.encrypted = False
    return {'plain':self.plain, 'encrypted':False}

  def add_padding(self, text):
    """
    Pads text to whole blocks (AES blocksize = 16). Padding scheme is binary
    '100000...'
    """
    pad_length = AES.block_size - len(text) % AES.block_size
    if pad_length:
      text = text + self.INTERRUPT + (pad_length-1) * self.PAD
    return text

  def remove_padding(self, text):
    """
    Unpads decrypted text. Removes rightmost zero and one bytes.
    @todo: might this be a problem? Especially in binary files?
    """
    return text.rstrip(self.PAD).rstrip(self.INTERRUPT)
