#==============================================================================#
#                                  ez_message                                  #
#==============================================================================#

#============#
#  Includes  #
#============#
from datetime import datetime
from Crypto.Hash import SHA # Shorter IDs than with 256
import ez_crypto as ec

#==============================================================================#
#                                class Message                                 #
#==============================================================================#

crypted_content = ['cipher', 'ciphered_key', 'iv', 'crypt_mode', 'signature']
components = ['time', 'recipient', 'msg_id'] + crypted_content

class Message(object):
  """
  This is the object that will be permanently saved in the database.
  It generates a unique ID based on sender, recipient and exact date.
  Unencrypted is recipient, year-month, injection vector and crypt_mode.
  Crypted is the message as cipher(AES) and key as ciphered_key(RSA).
  """

  def __init__(self, sender, recipient, content, dtime = datetime.now(),
               _dict=None):
    if _dict is not None:
      # We have to take care not to import local database information
      for x in components:
        self.__dict__.update({x : _dict[x]})
    else:
      # todo: (bcn 2014-07-06) Isoformat is at least localization independent but
      # timezone information is still missing !
      self.time       = str(dtime.year) + '-' + str(dtime.month)
      self.recipient  = recipient
      self.exact_time = dtime.isoformat(' ')
      self.msg_id     = SHA.new(sender + recipient + str(self.exact_time))\
                            .hexdigest()
      # Fake it till you make it
      #crypt_dict = ec.eZ_Crypto.encrypt(dtime.isoformat(' '), sender, content)
      crypt_dict = { 'cipher' : 'laskjdhflkaj', 'ciphered_key' : 'alskdjaskldj',
                     'iv' : 'uiofoqhehf', 'crypt_mode' : 1, 'signature' : 'lajd'}
      for x in crypted_content:
        self.__dict__.update({x : crypt_dict[x]})

  def __str__(self):
    lst = [str(k) + ' : ' + str(v) for k, v in self.__dict__.items()]
    return '\n'.join(lst)

  def content(self):
    return (self.time, self.recipient, self.msg_id, self.cipher,
        self.ciphered_key, self.iv, self.crypt_mode, self.signature)
