# -*- coding: utf_8 -*- =======================================================#
#                                  ez_crypto                                   #
#==============================================================================#

#============#
#  Includes  #
#============#
from Crypto.Hash import SHA256 # considered more secure than SHA1
from Crypto.Hash import HMAC
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

  def input_wrapper(self): # pragma: no cover
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
    encrypt_items = ['ciphered_key', 'iv', 'crypt_mode', 'cipher',
        'recipient', 'ciphered_mac']

    # Encode with AES:
    _plain_block  = "\1".join([self.etime, self.sender, self.content])
    _aes_output   = eZ_AES(_plain_block).encrypt()
    self.attribute_setter(**_aes_output)

    # encode AES-key and HMAC with public RSA key:
    _public_key       = eZ_RSA().get_public_key(self.recipient)
    self.ciphered_key = eZ_RSA().encrypt(_public_key, self.key)
    self.ciphered_mac = eZ_RSA().encrypt(_public_key, self.hmac)

    return self.return_dict(encrypt_items)

  def decrypt_verify(self):
    """
    Decrypt and unpack cipher block, check HMAC. Return HMAC check
    result in 'authorized' key, as well as the other plaintext attributes.
    """
    _aes_items      = ['key', 'iv', 'crypt_mode', 'cipher', 'hmac']
    decrypt_items   = ['etime', 'content', 'sender', 'recipient', 'authorized']

    # Decrypt AES key and HMAC:
    _private_key    = eZ_RSA().get_private_key(self.recipient)
    self.key        = eZ_RSA().decrypt(_private_key, self.ciphered_key)
    self.hmac       = eZ_RSA().decrypt(_private_key, self.ciphered_mac)

    # Decrypt cipher block (and HMAC check inside AES class):
    _aes_input  = self.return_dict(_aes_items)
    _aes_output = eZ_AES(**_aes_input).decrypt()
    self.attribute_setter(**_aes_output)
    # Unpack plaintext block
    (self.etime, self.sender, self.content) = self.plain.split("\1")

    return self.return_dict(decrypt_items)


#==============================================================================#
#                                 class eZ_RSA                                 #
#==============================================================================#

class eZ_RSA(CryptoBaseClass):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  RSA cipher object. Provides asymmetric encrytpion. Recommended minimal
  keylength: 2048 bit.
  """
  def input_wrapper(self):
    self.rsa_key_length = 2048

  def key_loc(self, user):
    """
    Sets the path for the keyfiles. Base path retrieved from the user
    preferences.
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
    Verify signature against plaintext with public key. Return True if
    successful, false otherwise.
    """
    msg_hash = SHA256.new(plaintext)
    verifier = PKCS1_PSS.new(public_key)
    try:
      return verifier.verify(msg_hash, signature.decode('base64'))
    except:
      return False


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
    self.hmac       = self.hmac_digest(_key, self.plain)    # Create HMAC
    encrypt_items   = ['key', 'iv', 'crypt_mode', 'cipher', 'hmac']
    return self.return_dict(encrypt_items)

  def decrypt(self):
    """
    Produces plaintext from ciphertext, if provided with correct key and
    encryption parameters.
    """
    assert self.crypt_mode is not 0, "Can not decrypt. Data is not encrypted"
    _key            = self.key.decode('base64')
    _iv             = self.iv.decode('base64')
    _cipher         = self.cipher.decode('base64')
    decrypter       = AES.new(_key, mode=self.MODE, IV=_iv)
    padded_text     = decrypter.decrypt(_cipher)
    self.plain      = self.remove_padding(padded_text)
    self.crypt_mode = 0
    _hmac_sig       = self.hmac   # Verify HMAC
    self.authorized = self.hmac_verify(_key, self.plain, _hmac_sig)
    plain_items     = ['plain', 'crypt_mode', 'authorized']
    return self.return_dict(plain_items)

  def hmac_verify(self, key, plaintext, hexmac_to_verify):
    """
    Return bool. True if verification sucessfull, False otherwise.
    """
    mac_object      = HMAC.new(key, digestmod=SHA256)
    mac_object.update(plaintext)
    if mac_object.hexdigest() == hexmac_to_verify:
      authorized = True
    else:
      authorized = False
    return authorized

  def hmac_digest(self, key, plaintext):
    """
    Returns the hexdigest of a message,  if provided with key.
    """
    mac_object      = HMAC.new(key, digestmod=SHA256)
    mac_object.update(plaintext)
    return mac_object.hexdigest()


  def add_padding(self, text):
    """
    Pads text to whole blocks (AES blocksize = 16). Padding scheme is binary
    '100000...'. If message length is multiple of blocksize, a whole additional
    block will be padded.
    """
    pad_length = AES.block_size - len(text) % AES.block_size
    if pad_length:
      pass
    else:
      pad_length = AES.block_size
    return text + self.INTERRUPT + (pad_length - 1) * self.PAD

  def remove_padding(self, text):
    """
    Unpads decrypted text. Removes rightmost zeros and one (interrupt) byte.
    """
    return text.rstrip(self.PAD)[:-1]