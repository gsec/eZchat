# encoding=utf-8 ==============================================================#
#                                  ez_crypto                                   #
#==============================================================================#

#============#
#  Includes  #
#============#
from Crypto.Hash import SHA256  # considered more secure than SHA1
from Crypto.Hash import HMAC
from Crypto.Cipher import PKCS1_OAEP, AES
from ez_gpg import ez_gpg
from Crypto.Signature import PKCS1_PSS

from Crypto import Random
import os.path as path
import ez_preferences as ep
import ez_user as eu

#==============================================================================#
#                            class CryptoBaseClass                             #
#==============================================================================#

class CryptoBaseClass(object):
  """
  Base class defining common functions.
  """

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
    return {k: v for k, v in self.__dict__.iteritems() if k in return_list}

#==============================================================================#
#                            class eZ_CryptoScheme                             #
#==============================================================================#

class eZ_CryptoScheme(CryptoBaseClass):
  """
  Outer crypto API to encrypt+sign and decrypt+verify message objects.
  Encryption must be provided as dictionary with following keys:
  ['etime', 'sender', 'recipient', 'content']
  """

  def __init__(self, **kwargs):
    self.attribute_setter(**kwargs)

  def encrypt_sign(self):
    """
    Pack content, exact time and sender to plaintext block. Sign and encrypt
    plaintext block. Return crypto items as dictionary.
    """

    encrypt_items = ['ciphered_key', 'iv', 'crypt_mode', 'cipher',
                     'recipient', 'ciphered_mac']

    # Encode with AES:
    _plain_block = "\1".join([self.etime, self.sender, self.content])
    _aes_output = eZ_AES(_plain_block).encrypt()
    self.attribute_setter(**_aes_output)

    # encode AES-key and HMAC with public RSA key:
    import cPickle as pickle
    ciphered_key = ez_gpg.encrypt_msg(self.recipient, self.key)
    self.ciphered_key = pickle.dumps(ciphered_key.data)
    ciphered_mac = ez_gpg.encrypt_msg(self.recipient, self.hmac)
    self.ciphered_mac = pickle.dumps(ciphered_mac.data)

    return self.return_dict(encrypt_items)

  def decrypt_verify(self):
    """
    Decrypt and unpack cipher block, check HMAC. Return HMAC check
    result in 'authorized' key, as well as the other plaintext attributes.
    """

    _aes_items = ['key', 'iv', 'crypt_mode', 'cipher', 'hmac']
    decrypt_items = ['etime', 'content', 'sender', 'recipient', 'authorized']

    # Decrypt AES key and HMAC:
    import cPickle as pickle
    # type(key_crypto) = Crypt.

    key_crypto = ez_gpg.decrypt_msg(pickle.loads(str(self.ciphered_key)))
    self.key = key_crypto.data

    # todo: replace self.sender by key_crypto.sender?! in case the user fakes
    # their fingerprint

    hmac_crypto = ez_gpg.decrypt_msg(pickle.loads(str(self.ciphered_mac)))
    self.hmac = hmac_crypto.data

    # Decrypt cipher block (and HMAC check inside AES class):
    _aes_input = self.return_dict(_aes_items)
    _aes_output = eZ_AES(**_aes_input).decrypt()
    self.attribute_setter(**_aes_output)

    # Unpack plaintext block
    (self.etime, self.sender, self.content) = self.plain.split("\1")

    return self.return_dict(decrypt_items)

#==============================================================================#
#                                 class eZ_AES                                 #
#==============================================================================#
class eZ_AES(CryptoBaseClass):
  """
  AES cipher object. Provides symmetric encryption. Requires plaintext string
  or ciphered dictionary object. Dictionary object must contain following keys:
  ['iv', 'key', 'cipher']
  Encryption parameters as of crypt_mode_1: keylength = 32 Bytes,
  padding = '\01\00\00...', AES cipher mode = Cipher Block Chain.
  """

  def __init__(self, plaintext=None, **kwargs):
    crypt_parameters_mode_1 = {'KEY_LENGTH': 32, 'INTERRUPT': "\1", 'PAD': "\0",
                               'MODE': AES.MODE_CBC}
    self.attribute_setter(**crypt_parameters_mode_1)
    if type(plaintext) is str:
      self.plain = plaintext
      self.crypt_mode = 0
    if kwargs:
      self.attribute_setter(**kwargs)

  def encrypt(self):
    """
    Creates random IV (Injection Vector) and random symmetric key. Encrypts
    padded text. Returns dictionary with base64 encoded ciphertext, key, IV and
    the crypt_mode used.
    """

    assert self.crypt_mode is 0, "Can not encrypt. Data already encrypted"
    # changed to EtA
    # !! check for iv and mac still needed
    #        http://crypto.stackexchange.com/questions/202/
    #        should-we-mac-then-encrypt-or-encrypt-then-mac
    #        http://cseweb.ucsd.edu/~mihir/papers/oem.html
    _iv = RNG.read(AES.block_size)
    _key = RNG.read(self.KEY_LENGTH)
    _crypter = AES.new(_key, mode=self.MODE, IV=_iv)
    padded_text = self.add_padding(self.plain)
    self.crypt_mode = 1
    self.cipher = _crypter.encrypt(padded_text).encode('base64')
    self.key = _key.encode('base64')
    self.iv = _iv.encode('base64')
    self.hmac = self.hmac_digest(_key, self.cipher)    # Create HMAC
    encrypt_items = ['key', 'iv', 'crypt_mode', 'cipher', 'hmac']
    return self.return_dict(encrypt_items)

  def decrypt(self):
    """
    Produces plaintext from ciphertext, if provided with correct key and
    encryption parameters.
    """

    assert self.crypt_mode is not 0, "Can not decrypt. Data is not encrypted"
    _key = self.key.decode('base64')
    _iv = self.iv.decode('base64')
    _cipher = self.cipher.decode('base64')
    self.authorized = self.hmac_verify(_key, self.cipher, self.hmac)
    if self.authorized:
      decrypter = AES.new(_key, mode=self.MODE, IV=_iv)
      padded_text = decrypter.decrypt(_cipher)
      self.plain = self.remove_padding(padded_text)
      self.crypt_mode = 0
    else:
      raise ValueError("HMAC Authentification failed")
      self.crypt_mode = 1
      self.plain = None
    plain_items = ['plain', 'crypt_mode', 'authorized']
    return self.return_dict(plain_items)

  def hmac_verify(self, key, plaintext, hexmac_to_verify):
    """
    Return bool. True if verification sucessfull, False otherwise.
    """

    mac_object = HMAC.new(key, digestmod=SHA256)
    mac_object.update(plaintext)
    if mac_object.hexdigest() == hexmac_to_verify:
      authorized = True
    else:
      authorized = False
    return authorized

  def hmac_digest(self, key, plaintext):
    """
    Returns the hexdigest of a message, if provided with key.
    """

    mac_object = HMAC.new(key, digestmod=SHA256)
    mac_object.update(plaintext)
    return mac_object.hexdigest()

  def add_padding(self, text):
    r"""
    Pads text to whole blocks (AES blocksize = 16). Padding scheme is binary
    '100000...'. If message length is multiple of blocksize, a whole additional
    block will be padded.

    >>> self = eZ_AES()
    >>> self.add_padding("teststring")
    'teststring\x01\x00\x00\x00\x00\x00'
    >>> self.add_padding("teststring123456")
    'teststring123456\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    """

    pad_length = AES.block_size - len(text) % AES.block_size
    if pad_length:
      pass
    else:
      pad_length = AES.block_size
    return text + self.INTERRUPT + (pad_length - 1) * self.PAD

  def remove_padding(self, text):
    r"""
    Unpads decrypted text. Removes rightmost zeros and one (interrupt) byte.

    >>> self = eZ_AES()
    >>> self.remove_padding("teststring\x01\x00\x00\x00\x00\x00")
    'teststring'
    >>> self.remove_padding("teststring123456\x01\x00\x00\x00\x00\x00\x00" +
    ...                     "\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    'teststring123456'
    """
    return text.rstrip(self.PAD)[:-1]

  #def test_doc(self, string):
    #"""
    #doctest test method
    #>>> eZ_AES().test_doc("Hi")
    #'Hi'
    #"""
    #return string

#==============================================================================#
#                               GLOBAL INSTANCES                               #
#==============================================================================#

# Strong random generator as file object:
RNG = Random.new()

if __name__ == "__main__":
  import doctest
  doctest.testmod()
