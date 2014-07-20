# -*- coding: utf_8 -*- =======================================================#
#                                  ez_crypto                                   #
#==============================================================================#

#============#
#  Includes  #
#============#
from Crypto.Hash import SHA256 # considered more secure than SHA1
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto import Random
import ez_preferences as ep
import os.path as path

# Strong random generator as file object:
RNG = Random.new()

#==============================================================================#
#                            class CryptoBaseClass                             #
#==============================================================================#
class CryptoBaseClass(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  Base class defining common functions.
  """
  def __init__(self, plaintext='', **kwargs):
    self.input_wrapper()
    if plaintext:
      self.args_handler(plaintext)
    if kwargs:
      self.attribute_setter(**kwargs)

  def attribute_setter(self, **kwargs):
    """
    Sets kwargs as instance attributes.
    """
    for key, value in kwargs.iteritems():
      setattr(self, key, value)

  def return_dict(self, return_list):
    """
    Extracts instance attributes into dictionary from return_list.
    """
    return {k:v for k, v in self.__dict__.iteritems() if k in return_list}

  def input_wrapper(self):
    pass

  def args_handler(self, *args): # pragma: no cover
    pass

#==============================================================================#
#                            class eZ_CryptoScheme                             #
#==============================================================================#
class eZ_CryptoScheme(CryptoBaseClass):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  Outer crypto API to encrypt+sign and decrypt+verify message objects.
  Encryption must be provided with following arguments as dictionary:
  @ARGS: etime, sender, recipient, content
  """
  def encrypt_sign(self):
    """
    Pack content, exact time and sender to plaintext block. Sign and encrypt
    plaintext block. Return crypto items as dictionary.

    """
    # Pack plaintext block:
    _plain_block = "\1".join([self.etime, self.sender, self.content])

    _private_key = eZ_RSA().get_private_key(self.sender)
    _public_key = eZ_RSA().get_public_key(self.recipient)

    # Encode with AES:
    _aes_output = eZ_AES(_plain_block).encrypt()
    # Set AES output as attributes:
    self.attribute_setter(**_aes_output)
    # encode AES-key with public RSA key:
    self.ciphered_key = eZ_RSA().encrypt(_public_key, self.key)
    # Sign with private RSA key:
    self.signature = eZ_RSA().sign(_private_key, _plain_block)

    _encrypt_items  = ['ciphered_key', 'iv', 'crypt_mode', 'cipher',
        'signature', 'recipient']
    return self.return_dict(_encrypt_items)

  def decrypt_verify(self):
    """
    Decrypt and unpack cipher block, check signature. Return signature check
    result in 'authorized' key, as well as the other plaintext attributes.
    """
    _private_key = eZ_RSA().get_private_key(self.recipient)
    # Decrypt AES key:
    self.key = eZ_RSA().decrypt(_private_key, self.ciphered_key)

    # Decrypt cipher block:
    _aes_items  = ['key', 'iv', 'crypt_mode', 'cipher']
    _aes_input  = self.return_dict(_aes_items)
    _aes_output = eZ_AES(**_aes_input).decrypt()
    # Set AES output as attributes:
    self.attribute_setter(**_aes_output)

    # Unpack plaintext block
    (self.etime, self.sender, self.content) = self.plain.split("\1")
    _public_key = eZ_RSA().get_public_key(self.sender)
    # Check signature
    self.authorized = eZ_RSA().verify(_public_key, self.plain, self.signature)
    decrypt_items  = ['etime', 'content', 'sender', 'recipient', 'authorized']
    return self.return_dict(decrypt_items)


#==============================================================================#
#                                 class eZ_RSA                                 #
#==============================================================================#

class eZ_RSA(CryptoBaseClass):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  RSA cipher object. Provides asymmetric encrytpion.
  """
  def input_wrapper(self):
    self.rsa_key_length = 2048

  def key_loc(self, user):
    """
    Sets the path for the keyfiles.
    """
    pub_loc = path.join(ep.key_location, 'ez_rsa_' + user + '.pub')
    priv_loc = path.join(ep.key_location, 'ez_rsa_' + user + '.priv')
    return pub_loc, priv_loc

  def get_private_key(self, user):
    """
    Import the senders keypair from Harddisk.
    """
    with open(self.key_loc(user)[1], 'r') as keypairfile:
      keypair = RSA.importKey(keypairfile.read())
    return keypair

  def get_public_key(self, user):
    """
    Get recipient public key from database.
    """
    #@TODO-----------------------------------------------
    # currently a mock, insert here the db retrieve function
    # and remove with-statement
    #
    with open(self.key_loc(user)[0], 'r') as pub_file:
      pub_key = RSA.importKey(pub_file.read())
    return pub_key

  def generate_keys(self, user, write=True):
    """
    Create RSA keypair and return them as tuple. if write argument is true,
    also write them to disk.
    """
    key_exists = path.isfile(self.key_loc(user)[1])
    if not write or not key_exists:
      fresh_key   = RSA.generate(self.rsa_key_length)
      private_key = fresh_key
      public_key  = fresh_key.publickey()
      if not write:
        return private_key, public_key
    # Out of performance reasons, we don't cover this. If it wouldn't work,
    # tests would fail anyway.
    if write and not key_exists: # pragma: no cover
      try:
        with open(self.key_loc(user)[0], 'aw') as pub_file, \
             open(self.key_loc(user)[1], 'aw') as priv_file:
          pub_file.write(public_key.exportKey())
          priv_file.write(private_key.exportKey())
      except IOError:
        print("Failed to write keys to disk")

  def encrypt(self, public_key, plaintext):
    """
    RSA encrypt method, PKCS1_OAEP. (See PyCrypto documentation for further
    information.)
    """
    cipher_scheme = PKCS1_OAEP.new(public_key)
    cipher = cipher_scheme.encrypt(plaintext)
    return cipher.encode('base64')

  def decrypt(self, private_key, ciphertext):
    """
    RSA decrypt method, PKCS1_OAEP. (See PyCrypto documentation for further
    information.)
    """
    decipher_scheme = PKCS1_OAEP.new(private_key)
    plaintext = decipher_scheme.decrypt(ciphertext.decode('base64'))
    return plaintext

  def sign(self, private_key, plaintext):
    """
    Sign plaintext with private key.
    """
    msg_hash = SHA256.new(plaintext)
    signer = PKCS1_PSS.new(private_key)
    signature = signer.sign(msg_hash)
    return signature.encode('base64')

  def verify(self, public_key, plaintext, signature):
    """
    Verify signature agains plaintext with public key. Return True if
    sucessful.
    """
    msg_hash = SHA256.new(plaintext)
    verifier = PKCS1_PSS.new(public_key)
    return verifier.verify(msg_hash, signature.decode('base64'))


#==============================================================================#
#                                 class eZ_AES                                 #
#==============================================================================#
class eZ_AES(CryptoBaseClass):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  AES cipher object. Provides symmetric encryption. Requires plaintext string
  or ciphered dictionary object. Cipherobject needs folowing entries:
  @PARAMS: ['iv', 'key', 'cipher']
  Encryption parameters as of crypt_mode_1: keylength = 32 Bytes,
  padding = '\01\00\00...', AES cipher mode = Cipher Block Chain.
  """
  def args_handler(self, plaintext):
    """
    Handles single argument string plaintext
    """
    assert type(plaintext) is str, """Single argument must be plaintext
    string!"""
    self.plain      = plaintext
    self.crypt_mode = 0

  def input_wrapper(self):
    crypt_parameters_mode_1 = {'KEY_LENGTH':32, 'INTERRUPT':"\1", 'PAD':"\0",
        'MODE': AES.MODE_CBC}
    self.attribute_setter(**crypt_parameters_mode_1)

  def encrypt(self):
    """
    Creates random IV (Injection Vector) and random symmetric key. Encrypts
    padded text. Returns dictionary with base64 encoded ciphertext, key, IV and
    the crypt_mode used.
    """
    assert self.crypt_mode is 0, "Can not encrypt. Data already encrypted"
    _iv             = RNG.read(AES.block_size)
    _key            = RNG.read(self.KEY_LENGTH)
    _crypter        = AES.new(_key, mode=self.MODE, IV=_iv)
    padded_text     = self.add_padding(self.plain)
    self.crypt_mode = 1
    self.cipher     = _crypter.encrypt(padded_text).encode('base64')
    self.key        = _key.encode('base64')
    self.iv         = _iv.encode('base64')
    encrypt_items   = ['key', 'iv', 'crypt_mode', 'cipher']
    return self.return_dict(encrypt_items)

  def decrypt(self):
    """
    Produces plaintext from ciphertext, if provided with correct key and
    encryption parameters.
    """
    assert self.crypt_mode is not 0, "Can not decrypt. Data is not encrypted"
    _key        = self.key.decode('base64')
    _iv         = self.iv.decode('base64')
    _cipher     = self.cipher.decode('base64')
    decrypter   = AES.new(_key, mode=self.MODE, IV=_iv)
    padded_text = decrypter.decrypt(_cipher)
    self.plain      = self.remove_padding(padded_text)
    self.crypt_mode = 0
    plain_items = ['plain', 'crypt_mode']
    return self.return_dict(plain_items)

  def add_padding(self, text):
    """
    Pads text to whole blocks (AES blocksize = 16). Padding scheme is binary
    '100000...'. If message length is multiple of blocksize, a whole additional
    block will be padded.
    """
    pad_length = AES.block_size - len(text) % AES.block_size
    if pad_length:
      text = text + self.INTERRUPT + (pad_length-1) * self.PAD
    else:
      text = text + self.INTERRUPT + (AES.block_size-1) * self.PAD
    return text

  def remove_padding(self, text):
    """
    Unpads decrypted text. Removes rightmost zeros and one (interrupt) byte.
    """
    return text.rstrip(self.PAD)[:-1]
