# -*- coding: utf_8 -*-
#==============================================================================#
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
from os.path import join as pathjoin
from os.path import isfile
RNG = Random.new()

#==============================================================================#
#                            class eZ_CryptoScheme                             #
#==============================================================================#

class eZ_CryptoScheme(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  Crypto Scheme. Cleanup and documentation needed.
  """

  def __init__(self, **kwargs):
    """
    Takes the arguments and creates an attribute for each of them.
    @ARGS: date, sender, recipient, content
    """
    for key, value in kwargs.iteritems():
      setattr(self, key, value)

  def encrypt_sign(self):
    _plain_block = '\1'.join([self.etime, self.sender, self.content])
    _private_key = eZ_RSA().get_private_key(self.sender)
    _public_key = eZ_RSA().get_public_key(self.recipient)
   # encode with AES:
    _aes_package = eZ_AES(_plain_block).encrypt()
    for key, value in _aes_package.iteritems():
      setattr(self, key, value)
    # encode AES-key with RSA:
    self.ciphered_key = eZ_RSA().encrypt(_public_key, self.key)
    self.signature = eZ_RSA().sign(_private_key, _plain_block)
    _items  = ['ciphered_key', 'iv', 'crypt_mode', 'cipher', 'signature',
        'recipient']
    _dict   = {k:v for k, v in self.__dict__.iteritems() if k in _items}
    return _dict

  def decrypt_verify(self):
    _private_key = eZ_RSA().get_private_key(self.recipient)
    self.key = eZ_RSA().decrypt(_private_key, self.ciphered_key)
    _items  = ['key', 'iv', 'crypt_mode', 'cipher']
    aes_package = {k:v for k, v in self.__dict__.iteritems() if k in _items}
    _aes_return = eZ_AES(aes_package).decrypt()
    for key, value in _aes_return.iteritems():
      setattr(self, key, value)
    (self.etime, self.sender, self.content) = self.plain.split("\1")
    _public_key = eZ_RSA().get_public_key(self.sender)
    self.authorized =  eZ_RSA().verify(_public_key, self.plain, self.signature)
    _items  = ['etime', 'content', 'sender', 'recipient', 'authorized']
    _dict   = {k:v for k, v in self.__dict__.iteritems() if k in _items}
    return _dict

#==============================================================================#
#                                 class eZ_RSA                                 #
#==============================================================================#

class eZ_RSA(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  RSA cipher object. Provides asymmetric encrytpion.
  """

  def __init__(self, package={}):
    """
    Takes arbitrary dict of items in and sets them as attributes of the eZ_RSA
    class.
    """
    self.rsa_key_length = 2048
    self.location        = '.'

    for key, value in package.iteritems():
      setattr(self, key, value)

  def key_loc(self, user, location='.'):
    pub_loc = pathjoin(location, 'ez_rsa_' + user + '.pub')
    priv_loc = pathjoin(location, 'ez_rsa_' + user + '.priv')
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
    # currently a mock, insert here the db retrieve function
    # and remove with-statement
    #
    with open(self.key_loc(user)[0], 'r') as pub_file:
      pub_key = RSA.importKey(pub_file.read())
    return pub_key

  def generate_keys(self, user='FAKE_USER', write=True):
    """
    Create RSA keypair and return them as tuple. if write argument is true,
    also write them to disk.
    """
    fresh_key   = RSA.generate(self.rsa_key_length)
    private_key = fresh_key
    public_key  = fresh_key.publickey()
    # insert check if files already exist
    try:
      if isfile(self.key_loc(user)[1]):
        write = False
        raise IOError
    except IOError:
      print("RSA Keyfile already exist at: ", self.key_loc(user)[1])

    if write:
      with open(self.key_loc(user)[0], 'aw') as pub_file, \
          open(self.key_loc(user)[1], 'aw') as priv_file:
        pub_file.write(public_key.exportKey())
        priv_file.write(private_key.exportKey())
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

  def sign(self, private_key, plaintext):
    """
    Sign a message.
    """
    msg_hash = SHA256.new(plaintext)
    signer = PKCS1_PSS.new(private_key)
    signature = signer.sign(msg_hash)
    return signature.encode('base64')

  def verify(self, public_key, plaintext, signature):
    """
    Verify signature.
    """
    msg_hash = SHA256.new(plaintext)
    verifier = PKCS1_PSS.new(public_key)
    return verifier.verify(msg_hash, signature.decode('base64'))

#==============================================================================#
#                                 class eZ_AES                                 #
#==============================================================================#

class eZ_AES(object):
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
  """
  AES cipher object. Provides symmetric encryption. Plaintext can be
  provided as string or dictionary object. Ciphertext must be dictionary
  object.
  Encryption parameters: keylength = 32bytes, padding = '\01\00\00 ...',
  cipher mode = cipher block chain.
  """

  def __init__(self, *args, **kwargs):
    self.input_wrapper(*args, **kwargs)

  def input_wrapper(self, *args, **kwargs):
    """
    If package is string, assume it is plaintext . If dict, transfer values to
    attributes. Else raise ValueError.
    """
    if type(args) == str:
      package = {'plain':args, 'crypt_mode':0}     # unpack tuple + assign
    elif type(kwargs) == dict:
      assert kwargs.has_key('crypt_mode'), "AES package has no crypt mode."
    else:
      raise TypeError("AES input type: ", type(package), """AES input has wrong
          format. Please specify plaintext string or crypt_mode compliant
          dictionary as argument.""")

    # crypt parameters for mode 1:
    crypt_mode_1 = {'KEY_LENGTH':32, 'INTERRUPT':"\1", 'PAD':"\0",
          'MODE': AES.MODE_CBC}

    self.crypt_mode    = package['crypt_mode']
    if self.crypt_mode == 0:
      self.plain    = package['plain']
    elif self.crypt_mode == 1:
      self.iv         = package['iv']
      self.key        = package['key']
      self.cipher     = package['cipher']
    else:
      raise ValueError("Undefined Crypto Mode in AES input dictionary")

    for key, value in crypt_mode_1.iteritems():
      setattr(self, key, value)

  def encrypt(self):
    """
    Creates random IV (Injection Vector) and random symmetric key. Encrypts
    padded text. Returns dictionary with base64 encoded ciphertext. Key, IV and
    padding bits are bytes.
    """
    assert self.crypt_mode is 0, "Data already encrypted"
    _iv             = RNG.read(AES.block_size)
    _key            = RNG.read(self.KEY_LENGTH)
    _crypter        = AES.new(_key, mode=self.MODE, IV=_iv)
    padded_text     = self.add_padding(self.plain)
    self.crypt_mode = 1
    self.cipher     = _crypter.encrypt(padded_text).encode('base64')
    self.key        = _key.encode('base64')
    self.iv         = _iv.encode('base64')
    _items  = ['key', 'iv', 'crypt_mode', 'cipher']
    _dict   = {k:v for k, v in self.__dict__.iteritems() if k in _items}
    return _dict

  def decrypt(self):
    """
    Produces plaintext from ciphertext with correct key and encryption
    parameters.
    """
    assert self.crypt_mode is not 0, "Data is not encrypted"
    _key  = self.key.decode('base64')
    _iv   = self.iv.decode('base64')
    _cipher = self.cipher.decode('base64')
    decrypter = AES.new(_key, mode=self.MODE, IV=_iv)
    padded_text = decrypter.decrypt(_cipher)
    self.plain = self.remove_padding(padded_text)
    self.crypt_mode = 0     # not required
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
