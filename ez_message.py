# encoding=utf-8 ==============================================================#
#                                  ez_message                                  #
#==============================================================================#

#============#
#  Includes  #
#============#
from datetime import datetime
from Crypto.Hash import SHA # Shorter IDs than with 256
import ez_crypto as ec
import ez_database as ed

#==============================================================================#
#                                class Message                                 #
#==============================================================================#

class Message(object):
  """
  This is the object that will be permanently saved in the database.
  It generates a unique ID based on sender, recipient and exact datetime.
  Unencrypted is recipient, year-month, injection vector and crypt_mode.
  Crypted is the message as cipher(AES) and key as ciphered_key(RSA).
  """
  crypto_content = ['cipher', 'ciphered_key', 'iv', 'crypt_mode',
                    'ciphered_mac']
  components = ['time', 'recipient', 'UID'] + crypto_content
  def __init__(self, sender='', recipient='', content='',
               dtime=None, _dict=None):

    if dtime == None:
      dtime=datetime.now()

    if _dict:
      for component in Message.components:
        setattr(self, component, _dict[component])
    else:
      # todo: (bcn 2014-07-06) Isoformat is at least localization independent
      # but timezone information is still missing !
      self.time = str(dtime.year) + '-' + str(dtime.month)
      exact_time = dtime.isoformat(' ')
      self.recipient = recipient
      self.UID = SHA.new(sender + recipient + exact_time).hexdigest()
      package = {'etime' : exact_time, 'sender' : sender,
                 'recipient' : recipient, 'content' : content}
      crypt_dict = ec.eZ_CryptoScheme(**package).encrypt_sign()
      for crypto_component in Message.crypto_content:
        setattr(self, crypto_component, crypt_dict[crypto_component])

  def __str__(self):
    """ Full representation including local database information """
    lst = [str(k) + ' : ' + str(getattr(self, k)) for k in Message.components]
    return '-'*80 + '\n' + '\n'.join(lst)

  def clear_text(self):
    """ Return the decrypted text, given the private key is found on disk """
    crypt_dict = {x : getattr(self, x) for x in Message.crypto_content}
    crypt_dict.update({'recipient' : self.recipient})
    clear_dict = ec.eZ_CryptoScheme(**crypt_dict).decrypt_verify()
    if clear_dict['authorized']:
      sig_symb = '✓'
    else:
      sig_symb = '✗'
    lst = [clear_dict['sender'], "@", clear_dict['etime'], ":\n",
        clear_dict['content'], "\n:HMAC:", "[", sig_symb, "]"]
    return ' '.join(lst)

#==============================================================================#
#                            class MessageDatabase                             #
#==============================================================================#

class MessageDatabase(ed.Database):
  """
  The MessageDatabase class gives access to the saved, encrypted messages in the
  SQL database
  """

  def __init__(self, **kwargs):
    """
    Opens a local sqlite database in the default location default_db,
    which is saved to and loaded from disk automatically. To create a merely
    temporary database in memory use 'sqlite:///:memory:'
    """
    ed.Database.__init__(self, 'Messages', Message, **kwargs)

message_database = MessageDatabase()
