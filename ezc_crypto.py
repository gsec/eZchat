#! /usr/bin/env python
# -*- coding: utf_8 -*-

#from __future__ import print_function
from Crypto.Hash import SHA256 # considered more secure than SHA1
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto import Random
from os.path import join as pathjoin

RNG = Random.new()

class eZ_CryptoScheme(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  Outline of crypto scheme. NOT WORKING AT ALL
  """

  def encrypt(self, date, sender, content):
    """
    @todo:
    """
    crypt_block = date + '\t' + sender + '\n' + content + '\n'
    self.signature = self.sign(sender, content)
    self.__dict__.update(ez_AES(crypt_block).encrypt())
    self.ciphered_key = self.RSA_encrypt(self.key)
    del self.key
    return self.__dict__

  def decrypt(self, message):
    self.__dict__.update(message.__dict__)
    self.key = RSA_decrypt(self.ciphered_key)
    self__dict__.update(ez_AES(self.__dict__).decrypt())
    self.sender = self.get_sender(self.plain)
    #assert self.verify(self.signature, self.sender) == True "Invalid Signature"
    return self.plain

class eZ_RSA(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  RSA cipher object. Provides asymmetric encrytpion.
  """

  def __init__(self, **kwargs):
    """
    Takes arbitrary list of items in format > "key"=value < and sets them as
    attributes of the eZ_RSA class.
    """
    for key, value in kwargs.iteritems():
      self.key = value
    self.rsa_key_length = 2048

  def get_sender_key(self, sender):
    """
    Import the senders keypair from Harddisk.
    """
    try:
      loc = self.loc      # Set loc to attribute if present
    except:
      loc = '.'           # Else take current path
    with open(pathjoin(loc, 'ez_rsa_' + sender), 'r') as keypairfile:
      keypair = RSA.importKey(keypairfile.read())
    return keypair

  def get_recipient_key(self, recipient):
    """
    Get recipient public key from database.
    """
    # currently a mock, insert here the db retrieve function
    # and remove with-statement
    #
    with open(pathjoin('.', 'ez_rsa_' + recipient + '.pub'),
        'r') as pub_file:
      pub_key = RSA.importKey(pub_file.read())
    return pub_key

  def generate_keys(self, write=False):
    """
    @todo: temporarily duplicate of function in ezc_create_user.py
    should at the end be imported from (secured) files
    """
    fresh_key   = RSA.generate(self.rsa_key_length)
    private_key = fresh_key
    public_key  = fresh_key.publickey()
    # insert check if files already exist
    if write:
      with open(pathjoin('.', 'ez_rsa_' + new_user + '.pub'),
          'aw') as pub_file, \
      open(pathjoin('.', 'ez_rsa_' + new_user),
          'aw') as priv_file:
        pub_file.write(private_key.exportKey)
        priv_file.write(publickey.exportKey)
    return private_key, public_key

  def encrypt(self, public_key, plaintext):
    """
    RSA encrypt method.
    """
    cipher_scheme = PKCS1_OAEP.new(public_key)
    cipher = cipher_scheme.encrypt(plaintext)
    return cipher.encode('base64')

  def decrypt(self, private_key, ciphertext):
    """
    RSA decrypt method.
    """
    decipher_scheme = PKCS1_OAEP.new(private_key)
    plaintext = decipher_scheme.decrypt(ciphertext.decode('base64'))
    return plaintext

  def sign(self, private_key, message):
    """
    Sign a message.
    """
    msg_hash = SHA256.new(message)
    signer = PKCS1_PSS.new(private_key)
    signature = signer.sign(msg_hash)
    return signature

  def verify(self, public_key, message, signature):
    """
    Verify signature.
    """
    msg_hash = SHA256.new(message)
    verifier = PKCS1_PSS.new(public_key)
    return verifier.verify(msg_hash, signature)

class eZ_AES(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  AES cipher object. Provides symmetric encryption. Plaintext can be
  provided as string or dictionary object. Ciphertext must be dictionary
  object.
  Encryption parameters: keylength = 32bytes, padding = '\01\00\00 ...',
  cipher mode = cipher block chain.
  """

  def __init__(self, package):
    self.input_wrapper(package)

  def input_wrapper(self, package):
    """
    If package is string, assume it is plaintext. If dict, transfer values to
    attributes. Else raise ValueError.
    """
    if type(package) == str:
      plaintext         = package
      package           = {'plain':plaintext, 'crypt_mode':0}
    elif type(package) == dict:
      pass
    else:
      raise TypeError("AES package has wrong format.")

    self.crypt_mode    = package['crypt_mode']
    if self.crypt_mode == 1:
      self.iv         = package['iv']
      self.key        = package['key']
      self.cipher     = package['cipher']
      # Don't touch this:
      self.KEY_LENGTH = 32
      self.INTERRUPT  = '\1'
      self.PAD        = '\0'
      self.MODE       = AES.MODE_CBC
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
    assert self.crypt_mode is 0, "Data already encrypted"
    self.iv         = RNG.read(AES.block_size)          # never use same IV
    self.key        = RNG.read(self.KEY_LENGTH)         # with same key twice
    crypter         = AES.new(self.key, mode=self.MODE, IV=self.iv)
    padded_text     = self.add_padding(self.plain)
    self.cipher     = crypter.encrypt(padded_text)
    del self.plain
    self.crypt_mode      = 1
    #self.encrypted_key  = False
    return self.__dict__

  def decrypt(self):
    """
    Produces plaintext from ciphertext with correct key and encryption
    parameters.
    """
    assert self.crypt_mode is not 0, "Data is not encrypted"
    decrypter = AES.new(self.key, mode=self.MODE, IV=self.iv)
    padded_text = decrypter.decrypt(self.cipher)
    self.plain = self.remove_padding(padded_text)
    self.crypt_mode = 0
    return {'plain':self.plain, 'crypt_mode':0}

  def add_padding(self, text):
    """
    Pads text to whole blocks (AES blocksize = 16). Padding scheme is binary
    '100000...'. If message length is multiple of blocksize, a whole block will
    be padded.

    """
    pad_length = AES.block_size - len(text) % AES.block_size
    if pad_length:
      text = text + self.INTERRUPT + (pad_length-1) * self.PAD
    else:
      text = text + self.INTERRUPT + (AES.block_size-1) * self.PAD
    return text

  def remove_padding(self, text):
    """
    Unpads decrypted text. Removes rightmost zero and one byte.
    """
    return text.rstrip(self.PAD)[:-1]
