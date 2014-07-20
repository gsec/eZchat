# encoding=utf-8
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

crypto_content = ['cipher', 'ciphered_key', 'iv', 'crypt_mode', 'signature']
components = ['time', 'recipient', 'msg_id'] + crypto_content

class Message(object):
  """
  This is the object that will be permanently saved in the database.
  It generates a unique ID based on sender, recipient and exact datetime.
  Unencrypted is recipient, year-month, injection vector and crypt_mode.
  Crypted is the message as cipher(AES) and key as ciphered_key(RSA).
  """

  def __init__(self, sender='', recipient='', content='',
               dtime = datetime.now(), _dict=None):
    if _dict is not None:
      for x in components:
        setattr(self, x, _dict[x])
    else:
      # todo: (bcn 2014-07-06) Isoformat is at least localization independent
      # but timezone information is still missing !
      self.time = str(dtime.year) + '-' + str(dtime.month)
      exact_time = dtime.isoformat(' ')
      self.recipient = recipient
      self.msg_id = SHA.new(sender + recipient + exact_time).hexdigest()
      package = {'etime' : exact_time, 'sender' : sender,
                 'recipient' : recipient, 'content' : content}
      crypt_dict = ec.eZ_CryptoScheme(**package).encrypt_sign()
      for x in crypto_content:
        setattr(self, x, crypt_dict[x])

  def __str__(self):
    """ Full representation including local database information """
    lst = [str(k) + ' : ' + str(getattr(self, k)) for k in components]
    return '-'*80 + '\n' + '\n'.join(lst)

  def clear_text(self):
    crypt_dict = {x : getattr(self, x) for x in crypto_content}
    crypt_dict.update({'recipient' : self.recipient})
    clear_dict = ec.eZ_CryptoScheme(**crypt_dict).decrypt_verify()
    if clear_dict['authorized']:
      sig_symb = '✓'
    else:
      sig_symb = '✗'
    lst = [clear_dict['sender'], "@", clear_dict['etime'], ":",
           clear_dict['content'], '(signature :', sig_symb, ')']
    return ' '.join(lst)
    #return [key + ' : ' + str(val) for key, val in clear_dict.iteritems()]
